import base64
import io
import json
import logging
import os
from datetime import UTC, datetime, timedelta

from airavata_sdk.helpers import experiment_orchestration, queue_settings
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.urls import reverse

from django_airavata import context_processors
from django_airavata.apps.api import web
from django_airavata.apps.api.view_utils import (
    APIBackedViewSet,
    APIResultIterator,
    APIResultPagination,
    DataProductSharedDirPermission,
    GenericAPIBackedViewSet,
    IsInAdminsGroupPermission,
    SdkResourceViewSet,
    UserStorageSharedDirPermission,
)
from django_airavata.apps.auth import iam_admin_client

from . import exceptions, helpers, output_views, serializers, signals, tus, view_utils

# Input files uploaded for an experiment are staged under this directory in the
# user's storage (mirrors the legacy SDK's TMP_INPUT_FILE_UPLOAD_DIR).
TMP_INPUT_FILE_UPLOAD_DIR = "tmp"

log = logging.getLogger(__name__)


# First replica's ~/-prefixed file path from a proto DataProductModel.
_data_product_file_path = view_utils.data_product_file_path


def _storage_upload_and_register(
    request, dir_path, uploaded_file, name=None, content_type=None, experiment_id=None
):
    """Write the bytes via the ``storage`` facade, then register a data product
    via the ``research`` facade so the file gets a canonical product URI."""
    storage = request.airavata.storage
    name = name or os.path.basename(getattr(uploaded_file, "name", "") or "")
    # Full file path resolved against the storage root (or experiment data dir).
    upload_path = _user_storage_path(
        os.path.join(dir_path, name), experiment_id, request
    )
    content = uploaded_file.read()
    storage.upload_file(
        path=upload_path, content=content, name=name, content_type=content_type or ""
    )
    # The upload response is minimal; resolve the absolute path the backend wrote
    # to and register the full data product via the SDK research_resources
    # helpers (which absorbed the legacy ``grpc_requests.data_product_for_upload``
    # proto-assembly).
    from airavata_sdk.helpers import research_resources

    metadata = storage.get_file_metadata(upload_path)
    product_uri = research_resources.register_data_product(
        request.airavata,
        research_resources.data_product_for_upload(
            gateway_id=settings.GATEWAY_ID,
            owner_name=request.user.username,
            product_name=name,
            file_path=metadata.path,
            storage_resource_id=storage.get_default_storage_resource_id(),
            content_type=content_type,
            product_size=metadata.size,
        ),
    )
    return request.airavata.research.get_data_product(product_uri)


def _render_uploaded_data_product(request, data_product):
    """Snake_case proto-direct render of a freshly registered upload.

    Wrapped in a ``WithAccess`` so the frontend ``DataProduct`` model receives
    ``is_owner`` / ``user_has_write_access``: the uploader owns the new file, so
    both are True (matching the legacy owner-has-write rule).
    """
    from airavata_sdk.helpers._envelope import WithAccess

    from django_airavata.apps.api.proto_render import to_jsonable

    is_owner = bool(data_product.owner_name) and (
        data_product.owner_name == request.user.username
    )
    return to_jsonable(
        WithAccess(message=data_product, is_owner=is_owner, user_has_write_access=True)
    )


class GroupViewSet(APIBackedViewSet):
    """Groups resource. SDK returns ``WithGroupAccess[GroupModel]``.

    The ``user_added_to_group`` notification fan-out (needs ``request`` +
    ``iam.get_user_profile_by_id`` + a Django signal) stays in the portal; the
    SDK create/update helpers return the raw proto + the set of newly added
    member ids so this ViewSet can replay it.
    """

    lookup_field = "group_id"
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:group-list"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import sharing_resources

        return sharing_resources

    def _gateway_groups(self):
        # GATEWAY_GROUPS is never written to the session, so this is always None;
        # the SDK helpers fetch the groups via GetGatewayGroups when not provided.
        return None

    def get_list(self):
        """Iterator yielding ``WithGroupAccess[GroupModel]`` for the gateway."""
        view = self

        class GroupResultsIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return view._sdk().list_groups(
                    view.request.airavata,
                    limit=limit,
                    offset=offset,
                    gateway_groups=view._gateway_groups(),
                )

        return GroupResultsIterator()

    def get_instance(self, lookup_value):
        """Return ``WithGroupAccess[GroupModel]`` for *lookup_value*."""
        return self._sdk().get_group(
            self.request.airavata, lookup_value, gateway_groups=self._gateway_groups()
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_list()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(list(page))
        return web.Response(queryset.get_results())

    def retrieve(self, request, *args, **kwargs):
        return web.Response(self.get_object())

    def create(self, request, *args, **kwargs):
        data = request.data if isinstance(request.data, dict) else {}
        result, group, added_members = self._sdk().create_group(
            request.airavata, data, gateway_groups=self._gateway_groups()
        )
        self._send_users_added_to_group(added_members, group)
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        group_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        result, group, added_members = self._sdk().update_group(
            request.airavata, group_id, data, gateway_groups=self._gateway_groups()
        )
        self._send_users_added_to_group(added_members, group)
        return web.Response(result)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # ``get_object`` now yields a ``WithGroupAccess`` envelope, so delegate
        # to the SDK ``delete_group`` (which re-fetches the proto to recover the
        # ``owner_id`` the DeleteGroup RPC requires) keyed on the lookup id.
        self._sdk().delete_group(self.request.airavata, self.kwargs[self.lookup_field])

    def _send_users_added_to_group(self, internal_user_ids, group):
        for internal_user_id in internal_user_ids:
            user_id, gateway_id = internal_user_id.rsplit("@", maxsplit=1)
            user_profile = self.request.airavata.iam.get_user_profile_by_id(
                user_id, gateway_id
            )
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=[group],
                request=self.request,
            )


class ProjectViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Projects resource. SDK returns ``WithAccess[Project]``."""

    lookup_field = "project_id"
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:project-list"
    paginate = True

    list_fn = "list_projects"
    get_fn = "get_project"
    create_fn = "create_project"
    update_fn = "update_project"

    @staticmethod
    def sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        self._update_most_recent_project(response.data.message.project_id)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self._update_most_recent_project(self.kwargs[self.lookup_field])
        return response

    def perform_destroy(self, instance):
        # ``get_object`` yields a ``WithAccess`` envelope; the proto is under
        # ``.message`` (the dataclass doesn't proxy field access).
        self.request.airavata.research.delete_project(instance.message.project_id)

    @web.action(detail=False)
    def list_all(self, request):
        return web.Response(self.sdk().list_projects(request.airavata))

    @web.action(detail=True)
    def experiments(self, request, project_id=None):
        # WithAccess[ExperimentModel] list, rendered proto-direct. The
        # EXECUTING-state intermediate-output enrichment is an ExperimentViewSet
        # detail concern and is not applied to this list.
        return web.Response(
            self.sdk().get_experiments_in_project(
                request.airavata, project_id, limit=-1, offset=0
            )
        )

    def _update_most_recent_project(self, project_id):
        prefs = helpers.WorkspacePreferencesHelper().get(self.request)
        prefs.most_recent_project_id = project_id
        prefs.save()


class ExperimentViewSet(
    web.mixins.CreateModelMixin,
    web.mixins.RetrieveModelMixin,
    web.mixins.UpdateModelMixin,
    GenericAPIBackedViewSet,
):
    """Experiments-core resource. SDK returns ``WithAccess[ExperimentModel]``
    (the whole process/task/job tree included).

    The EXECUTING-state intermediate-output enrichment is replayed by
    ``_add_intermediate_output_information`` against the rendered snake_case dict
    (it needs ``request.airavata`` + backend calls, so it can't live in the SDK
    proto-direct return).
    """

    lookup_field = "experiment_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def get_instance(self, lookup_value):
        return self._sdk().get_experiment(self.request.airavata, lookup_value)

    def _render(self, with_access, request):
        # Flatten the proto, then layer the EXECUTING-state intermediate-output
        # enrichment on top (a plain dict is safe — ProtoJSONRenderer recurses).
        from django_airavata.apps.api.proto_render import to_jsonable

        data = to_jsonable(with_access)
        self._add_intermediate_output_information(with_access.message, data, request)
        return data

    def retrieve(self, request, *args, **kwargs):
        with_access = self.get_object()
        return web.Response(self._render(with_access, request))

    def create(self, request, *args, **kwargs):
        sdk = self._sdk()
        data = request.data if isinstance(request.data, dict) else {}
        result = sdk.create_experiment(request.airavata, data)
        experiment = result.message
        self._update_workspace_preferences(
            project_id=experiment.project_id,
            group_resource_profile_id=experiment.user_configuration_data.group_resource_profile_id,
            compute_resource_id=experiment.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        return web.Response(
            self._render(result, request), status=web.status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        sdk = self._sdk()
        experiment_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        result = sdk.update_experiment(request.airavata, experiment_id, data)
        experiment = result.message
        self._update_workspace_preferences(
            project_id=experiment.project_id,
            group_resource_profile_id=experiment.user_configuration_data.group_resource_profile_id,
            compute_resource_id=experiment.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        return web.Response(self._render(result, request))

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def _add_intermediate_output_information(self, experiment, data, request):
        """Replay the old serializer's EXECUTING-state output enrichment.

        When the experiment's latest status is EXECUTING, each experiment output
        gains an ``intermediate_output`` block (fetchability + per-output process
        status + any already-staged data products).  This needs backend calls,
        so it lives in the ViewSet rather than the SDK proto-direct return —
        mirroring ``ExperimentSerializer._add_intermediate_output_information``,
        but emitting snake_case keys and rendering the nested protos via
        ``to_jsonable`` (no DRF serializer).
        """
        from airavata_sdk.generated.org.apache.airavata.model.status import (
            status_pb2,
        )

        from django_airavata.apps.api.proto_render import to_jsonable

        if not (
            experiment.experiment_status
            and experiment.experiment_status[-1].state
            == status_pb2.ExperimentState.EXPERIMENT_STATE_EXECUTING
        ):
            return
        for output in data.get("experiment_outputs", []):
            output["intermediate_output"] = {"process_status": None}
            try:
                can_fetch = experiment_orchestration.can_fetch_intermediate_output(
                    request.airavata, experiment, output["name"]
                )
                output["intermediate_output"]["can_fetch"] = can_fetch
                process_status = (
                    experiment_orchestration.get_intermediate_output_process_status(
                        request.airavata, experiment, output["name"]
                    )
                )
                if process_status:
                    output["intermediate_output"]["process_status"] = to_jsonable(
                        process_status
                    )
                data_products = (
                    experiment_orchestration.get_intermediate_output_data_products(
                        request.airavata, experiment, output["name"]
                    )
                )
                output["intermediate_output"]["data_products"] = [
                    to_jsonable(dp) for dp in data_products
                ]
            except Exception:
                log.debug("Failed to get intermediate output status", exc_info=True)

    @web.action(methods=["post"], detail=True)
    def launch(self, request, experiment_id=None):
        try:
            experiment = request.airavata.research.get_experiment(experiment_id)
            if experiment.enable_email_notification:
                experiment.email_addresses[:] = [request.user.email]
            request.airavata.research.update_experiment(experiment_id, experiment)
            experiment_orchestration.launch(
                request.airavata,
                experiment_id,  # ty: ignore[invalid-argument-type]  # detail=True action; experiment_id always supplied by the URL router
                username=request.user.username,
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                f"Failed to launch experiment {experiment_id}",
                extra={"request": request},
            )
            return web.Response({"success": False, "errorMessage": str(e)})

    @web.action(methods=["get"], detail=True)
    def jobs(self, request, experiment_id=None):
        # list_experiment_jobs returns raw JobModel protos; ProtoJSONRenderer
        # flattens each to snake_case (job_state enum as NAME, int64 timestamps
        # as epoch-millis strings).
        return web.Response(
            self._sdk().list_experiment_jobs(request.airavata, experiment_id)
        )

    @web.action(methods=["post"], detail=True)
    def clone(self, request, experiment_id=None):
        # clone() stages the input files (download+re-upload to tmp) and returns
        # the new experiment id; re-fetch the cloned experiment as a
        # WithAccess[ExperimentModel] so the rendered shape matches retrieve.
        cloned_experiment_id = experiment_orchestration.clone(
            request.airavata,
            experiment_id,  # ty: ignore[invalid-argument-type]  # detail=True action; experiment_id always supplied by the URL router
            username=request.user.username,
        )
        with_access = self._sdk().get_experiment(request.airavata, cloned_experiment_id)
        return web.Response(self._render(with_access, request))

    @web.action(methods=["post"], detail=True)
    def cancel(self, request, experiment_id=None):
        try:
            request.airavata.research.terminate_experiment(
                experiment_id, self.gateway_id
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                "Cancel action has thrown the following error",
                extra={"request": request},
            )
            raise e

    @web.action(methods=["post"], detail=True)
    def fetch_intermediate_outputs(self, request, experiment_id=None):
        # snake_case body in the proto-direct contract; accept the legacy
        # camelCase key too while the frontend migrates.
        output_names = request.data.get("output_names", request.data.get("outputNames"))
        if output_names is None:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)
        try:
            experiment_orchestration.fetch_intermediate_output(
                request.airavata,
                experiment_id,  # ty: ignore[invalid-argument-type]  # detail=True action; experiment_id always supplied by the URL router
                *output_names,
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                "fetchIntermediateOutputs failed with the following error",
                extra={"request": request},
            )
            raise e

    def _update_workspace_preferences(
        self, project_id, group_resource_profile_id, compute_resource_id
    ):
        prefs = helpers.WorkspacePreferencesHelper().get(self.request)
        prefs.most_recent_project_id = project_id
        prefs.most_recent_group_resource_profile_id = group_resource_profile_id
        prefs.most_recent_compute_resource_id = compute_resource_id
        prefs.save()


class ExperimentSearchViewSet(web.mixins.ListModelMixin, GenericAPIBackedViewSet):
    """Experiment-search resource (list-only). SDK returns a list of
    ``WithAccess[ExperimentSummaryModel]``.

    The gRPC ``SearchExperiments`` call takes ``filters`` as a ``map<string,
    string>`` keyed by ``ExperimentSearchFields`` member name (the query-param
    key already is one).
    """

    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:experiment-search-list"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def _filters(self):
        from airavata_sdk.generated.org.apache.airavata.model.experiment import (
            experiment_pb2,
        )

        valid_fields = {
            v.name for v in experiment_pb2.ExperimentSearchFields.DESCRIPTOR.values
        }
        filters = {}
        for key, value in self.request.query_params.items():
            if key in valid_fields:
                filters[key] = value
        return filters

    def get_list(self):
        view = self
        filters = self._filters()

        class ExperimentSearchResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return view._sdk().search_experiments(
                    view.request.airavata, filters=filters, limit=limit, offset=offset
                )

        # Preserve query parameters when moving to next and previous links
        return ExperimentSearchResultIterator(
            query_params=self.request.query_params.copy()
        )

    def get_instance(self, lookup_value):
        raise NotImplementedError()

    def list(self, request, *args, **kwargs):
        queryset = self.get_list()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(list(page))
        return web.Response(queryset.get_results())


class FullExperimentViewSet(web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    """Full-experiment resource — a composed ``FullExperiment`` pydantic model
    whose fields carry the component protos / ``WithAccess`` envelopes wholesale.

    The ViewSet resolves the request-bound inputs the SDK cannot derive (whether
    the caller may READ the referenced project, the gateway-admin write flag for
    the nested module, the per-data-product write flag, and the output-views map)
    and passes them into the SDK helper.
    """

    lookup_field = "experiment_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def _data_product_write(self, request):
        # Write rule (no backend calls): owner always; inside a gateway shared
        # directory only gateway admins; otherwise allowed.
        def _write(dp):
            owner = dp.owner_name
            if owner and owner == request.user.username:
                return True
            replicas = dp.replica_locations
            if (
                replicas
                and replicas[0].file_path
                and view_utils.is_shared_path(replicas[0].file_path)
            ):
                return request.is_gateway_admin
            return True

        return _write

    def _output_views(self, request):
        def _fn(experiment, application_interface):
            return output_views.get_output_views(
                request, experiment, application_interface
            )

        return _fn

    def retrieve(self, request, *args, **kwargs):
        sdk = self._sdk()
        experiment_id = self.kwargs[self.lookup_field]
        project_has_read = serializers.user_has_access(
            request,
            request.airavata.research.get_experiment(experiment_id).project_id,
            "READ",
        )
        module_has_write = getattr(request, "is_gateway_admin", False)
        result = sdk.get_full_experiment(
            request.airavata,
            experiment_id,
            project_has_read=project_has_read,
            module_has_write=module_has_write,
            data_product_write_fn=self._data_product_write(request),
            output_views_fn=self._output_views(request),
        )
        return web.Response(result)


class ApplicationModuleViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Application modules resource. SDK returns ``WithAccess[ApplicationModule]``.

    A gateway-level catalog entry, not a per-user shared resource:
    ``user_has_write_access`` is the gateway-admin flag, passed into the SDK
    function as ``has_write``.
    """

    lookup_field = "app_module_id"
    list_fn = "list_application_modules"
    get_fn = "get_application_module"
    create_fn = "create_application_module"
    update_fn = "update_application_module"

    @staticmethod
    def sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def extra_kwargs(self):
        return {"has_write": getattr(self.request, "is_gateway_admin", False)}

    def list_kwargs(self):
        return {**self.extra_kwargs(), "accessible_only": True}

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_module(
            instance.message.app_module_id
        )

    @web.action(detail=True)
    def application_interface(self, request, app_module_id):
        all_app_interfaces = list(
            request.airavata.research.get_all_application_interfaces(self.gateway_id)
        )
        app_interfaces = []
        for app_interface in all_app_interfaces:
            if not app_interface.application_modules:
                continue
            if app_module_id in app_interface.application_modules:
                app_interfaces.append(app_interface)
        if len(app_interfaces) == 1:
            # The application-interface family is proto-direct: wrap the matched
            # interface proto in a gateway-catalog WithAccess so ProtoJSONRenderer
            # flattens it to snake_case (no hyperlink injection — the frontend
            # builds URLs from application_interface_id).
            from airavata_sdk.helpers._envelope import WithAccess

            has_write = getattr(request, "is_gateway_admin", False)
            return web.Response(
                WithAccess(
                    message=app_interfaces[0],
                    is_owner=False,
                    user_has_write_access=has_write,
                )
            )
        elif len(app_interfaces) > 1:
            log.error(
                f"More than one application interface found for module {app_module_id}: {app_interfaces}",
                extra={"request": request},
            )
            raise Exception(
                f"More than one application interface found for module {app_module_id}"
            )
        else:
            raise Http404(
                f"No application interface found for module id {app_module_id}"
            )

    @web.action(detail=True)
    def application_deployments(self, request, app_module_id):
        # WithAccess[ApplicationDeploymentDescription] list (per-deployment
        # sharing WRITE lookup), rendered proto-direct.
        return web.Response(
            self.sdk().list_application_deployments_for_module(
                request.airavata, app_module_id
            )
        )

    @web.action(methods=["post"], detail=True)
    def favorite(self, request, app_module_id):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = (
                workspace_preferences.applicationpreferences_set.get(
                    application_id=app_module_id
                )
            )
            application_preferences.favorite = True
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username,
                application_id=app_module_id,
                favorite=True,
            )

        return HttpResponse(status=204)

    @web.action(methods=["post"], detail=True)
    def unfavorite(self, request, app_module_id):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = (
                workspace_preferences.applicationpreferences_set.get(
                    application_id=app_module_id
                )
            )
            application_preferences.favorite = False
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username,
                application_id=app_module_id,
                favorite=False,
            )

        return HttpResponse(status=204)

    @web.action(detail=False)
    def list_all(self, request):
        has_write = getattr(request, "is_gateway_admin", False)
        return web.Response(
            self.sdk().list_application_modules(
                request.airavata, has_write=has_write, accessible_only=False
            )
        )


class ApplicationInterfaceViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Application interfaces resource. SDK returns
    ``WithAccess[ApplicationInterfaceDescription]``.

    A gateway-level catalog entry: ``user_has_write_access`` is the gateway-admin
    flag, passed into the SDK function as ``has_write``.

    ``_update_input_metadata`` stays in the ViewSet because it massages proto
    input ``meta_data`` outside the SDK.
    """

    lookup_field = "app_interface_id"
    list_fn = "list_application_interfaces"
    get_fn = "get_application_interface"

    @staticmethod
    def sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def extra_kwargs(self):
        return {"has_write": getattr(self.request, "is_gateway_admin", False)}

    def get_instance(self, lookup_value):
        try:
            return super().get_instance(lookup_value)
        except Exception:
            # If it failed to load, check to see if it exists at all
            all_interfaces = (
                self.request.airavata.research.get_all_application_interfaces(
                    self.gateway_id
                )
            )
            interface_ids = [i.application_interface_id for i in all_interfaces]
            if lookup_value not in interface_ids:
                raise Http404("Application interface does not exist") from None
            else:
                raise  # re-raise

    def create(self, request, *args, **kwargs):
        sdk = self.sdk()
        has_write = getattr(request, "is_gateway_admin", False)
        data = request.data if isinstance(request.data, dict) else {}
        # Build the proto, massage input metadata, register, then re-fetch.
        application_interface = sdk._build_application_interface(request.airavata, data)
        self._update_input_metadata(application_interface)
        app_interface_id = request.airavata.research.register_application_interface(
            self.gateway_id, application_interface
        )
        result = sdk.get_application_interface(
            request.airavata, app_interface_id, has_write=has_write
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        sdk = self.sdk()
        app_interface_id = self.kwargs[self.lookup_field]
        has_write = getattr(request, "is_gateway_admin", False)
        data = request.data if isinstance(request.data, dict) else {}
        base = request.airavata.research.get_application_interface(app_interface_id)
        application_interface = sdk._build_application_interface(
            request.airavata, data, base=base
        )
        application_interface.application_interface_id = app_interface_id
        self._update_input_metadata(application_interface)
        request.airavata.research.update_application_interface(
            app_interface_id, application_interface
        )
        result = sdk.get_application_interface(
            request.airavata, app_interface_id, has_write=has_write
        )
        return web.Response(result)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_interface(
            instance.message.application_interface_id
        )

    def _update_input_metadata(self, app_interface):
        for app_input in app_interface.application_inputs:
            if app_input.meta_data:
                metadata = json.loads(app_input.meta_data)
                # Automatically add {showOptions: {isRequired: true/false}} to
                # toggle isRequired on hidden/shown inputs
                if (
                    "editor" in metadata
                    and "dependencies" in metadata["editor"]
                    and "show" in metadata["editor"]["dependencies"]
                ):
                    if "showOptions" not in metadata["editor"]["dependencies"]:
                        metadata["editor"]["dependencies"]["showOptions"] = {}
                    o = metadata["editor"]["dependencies"]["showOptions"]
                    o["isRequired"] = app_input.is_required
                    app_input.meta_data = json.dumps(metadata)

    @web.action(detail=True)
    def compute_resources(self, request, app_interface_id):
        compute_resources = (
            request.airavata.research.get_available_app_interface_compute_resources(
                app_interface_id
            )
        )
        return web.Response(compute_resources)


class ApplicationDeploymentViewSet(APIBackedViewSet):
    """Application deployments resource. SDK returns
    ``WithAccess[ApplicationDeploymentDescription]``.

    The ``queues`` action renders the compute resource's ``BatchQueue`` protos
    directly via ``to_jsonable`` (after overlaying this deployment's defaults).
    """

    lookup_field = "app_deployment_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def _has_write(self, request, app_deployment_id):
        """Per-deployment sharing-registry WRITE lookup (legacy
        ``user_has_access``)."""
        return request.airavata.sharing.user_has_access(
            resource_id=app_deployment_id,
            user_id=self.username,
            permission_type="WRITE",
        )

    def list(self, request, *args, **kwargs):
        sdk = self._sdk()
        app_module_id = request.query_params.get("appModuleId", None)
        group_resource_profile_id = request.query_params.get(
            "groupResourceProfileId", None
        )
        if (app_module_id and not group_resource_profile_id) or (
            not app_module_id and group_resource_profile_id
        ):
            raise web.ParseError(
                "Query params appModuleId and "
                "groupResourceProfileId are required together."
            )
        if app_module_id and group_resource_profile_id:
            deployments = sdk.list_application_deployments_for_module_and_profile(
                request.airavata, app_module_id, group_resource_profile_id
            )
        else:
            deployments = sdk.list_application_deployments(request.airavata)
        return web.Response(deployments)

    def retrieve(self, request, *args, **kwargs):
        sdk = self._sdk()
        app_deployment_id = self.kwargs[self.lookup_field]
        return web.Response(
            sdk.get_application_deployment(request.airavata, app_deployment_id)
        )

    def create(self, request, *args, **kwargs):
        sdk = self._sdk()
        data = request.data if isinstance(request.data, dict) else {}
        # The legacy create did not compute user_has_write_access from sharing on
        # the freshly created resource; the owner always has write access, so
        # report True for the created record.
        result = sdk.create_application_deployment(
            request.airavata, data, has_write=True
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        sdk = self._sdk()
        app_deployment_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        result = sdk.update_application_deployment(
            request.airavata,
            app_deployment_id,
            data,
            has_write=self._has_write(request, app_deployment_id),
        )
        return web.Response(result)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_application_deployment(
            instance.app_deployment_id
        )

    def get_instance(self, lookup_value):
        return self.request.airavata.research.get_application_deployment(lookup_value)

    @web.action(detail=True)
    def queues(self, request, app_deployment_id):
        """Return queues for this deployment with defaults overridden by deployment defaults if they exist"""
        from django_airavata.apps.api.proto_render import to_jsonable

        app_deployment = self.request.airavata.research.get_application_deployment(
            app_deployment_id
        )
        compute_resource = request.airavata.compute.get_compute_resource(
            app_deployment.compute_host_id
        )
        # Override defaults with app deployment default queue, if defined
        batch_queues = []
        for batch_queue in compute_resource.batch_queues:
            if app_deployment.default_queue_name:
                if app_deployment.default_queue_name == batch_queue.queue_name:
                    batch_queue.is_default_queue = True
                    batch_queue.default_node_count = (
                        app_deployment.default_node_count or 0
                    )
                    batch_queue.default_cpu_count = (
                        app_deployment.default_cpu_count or 0
                    )
                    batch_queue.default_walltime = app_deployment.default_walltime or 0
                else:
                    batch_queue.is_default_queue = False
            batch_queues.append(batch_queue)
        return web.Response(to_jsonable(batch_queues))


class ComputeResourceViewSet(web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    """Compute-resources resource. SDK returns the raw
    ``ComputeResourceDescription`` proto (no ownership/sharing, no envelope).

    The ``all_names`` / ``all_names_list`` actions return id-keyed maps whose keys
    are opaque compute-resource ids; they keep the default ``JSONRenderer`` via a
    per-action ``renderer_classes`` override so those keys pass through untouched
    (snake_case rendering would otherwise mangle them).
    """

    lookup_field = "compute_resource_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import compute_resources

        return compute_resources

    def get_instance(self, lookup_value):
        return self._sdk().get_compute_resource(self.request.airavata, lookup_value)

    def retrieve(self, request, *args, **kwargs):
        return web.Response(self.get_object())

    @web.action(detail=False)
    def all_names(self, request):
        """Return a map of compute resource names keyed by resource id."""
        return web.Response(self._sdk().list_compute_resource_names(request.airavata))

    @web.action(detail=False)
    def all_names_list(self, request):
        """Return a list of compute resource names keyed by resource id."""
        all_names = self._sdk().list_compute_resource_names(request.airavata)
        return web.Response(
            [
                {
                    "host_id": host_id,
                    "host": host,
                    "url": request.build_absolute_uri(
                        reverse(
                            "django_airavata_api:compute-resource-detail",
                            args=[host_id],
                        )
                    ),
                }
                for host_id, host in all_names.items()
            ]
        )

    @web.action(detail=True)
    def queues(self, request, compute_resource_id):
        """Return the resource's batch-queue names (a plain string list)."""
        details = self._sdk().get_compute_resource(
            request.airavata, compute_resource_id
        )
        return web.Response([queue.queue_name for queue in details.batch_queues])


def _data_product_has_write(request, data_product):
    # WRITE rule: owner always; inside a gateway shared directory only gateway
    # admins; otherwise allowed. Request-bound, so the SDK can't derive it.
    owner = data_product.owner_name
    if owner and owner == request.user.username:
        return True
    replicas = data_product.replica_locations
    if (
        replicas
        and replicas[0].file_path
        and view_utils.is_shared_path(replicas[0].file_path)
    ):
        return request.is_gateway_admin
    return True


class DataProductView(web.APIView):
    """Data product resource. SDK returns ``WithAccess[DataProductModel]``;
    ``user_has_write_access`` is computed via :func:`_data_product_has_write`.

    The PUT write body carries ``file_content_text`` (snake_case); the legacy
    ``fileContentText`` wire key is still accepted for compatibility.
    """

    permission_classes = [web.IsAuthenticated, DataProductSharedDirPermission]

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def get(self, request):
        data_product_uri = request.query_params["product-uri"]
        data_product = request.airavata.research.get_data_product(data_product_uri)
        has_write = _data_product_has_write(request, data_product)
        result = self._sdk().get_data_product(
            request.airavata, data_product_uri, has_write=has_write
        )
        return web.Response(result)

    def put(self, request):
        data_product_uri = request.query_params["product-uri"]
        data_product = request.airavata.research.get_data_product(data_product_uri)
        # The body carries ``file_content_text`` (snake_case); the legacy
        # ``fileContentText`` wire key is still accepted for compatibility.
        file_content = None
        if request.data:
            if "file_content_text" in request.data:
                file_content = request.data["file_content_text"]
            elif "fileContentText" in request.data:
                file_content = request.data["fileContentText"]
        if file_content is not None:
            file_path = _data_product_file_path(data_product)
            if file_path is None:
                return web.Response(status=web.status.HTTP_400_BAD_REQUEST)
            # Overwrite the file content in place at the replica's path.
            request.airavata.storage.upload_file(
                path=file_path,
                content=file_content.encode("utf-8"),
                name=data_product.product_name or os.path.basename(file_path),
            )
            return self.get(request=request)
        else:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)


@web.api_view(http_method_names=["POST"])
def upload_input_file(request):
    try:
        input_file = request.FILES["file"]
        data_product = _storage_upload_and_register(
            request,
            TMP_INPUT_FILE_UPLOAD_DIR,
            input_file,
            content_type=input_file.content_type,
        )
        return JsonResponse(
            {
                "uploaded": True,
                "data-product": _render_uploaded_data_product(request, data_product),
            }
        )
    except Exception as e:
        log.error("Failed to upload file", exc_info=True, extra={"request": request})
        resp = JsonResponse({"uploaded": False, "error": str(e)})
        resp.status_code = 500
        return resp


@web.api_view(http_method_names=["POST"])
def tus_upload_finish(request):
    uploadURL = request.POST["uploadURL"]

    def save_upload(file_path, file_name, file_type):
        with open(file_path, "rb") as uploaded_file:
            return _storage_upload_and_register(
                request,
                TMP_INPUT_FILE_UPLOAD_DIR,
                uploaded_file,
                name=file_name,
                content_type=file_type,
            )

    try:
        data_product = tus.save_tus_upload(uploadURL, save_upload)
        return JsonResponse(
            {
                "uploaded": True,
                "data-product": _render_uploaded_data_product(request, data_product),
            }
        )
    except Exception as e:
        log.error("Failed to finish tus upload", exc_info=True, extra={"request": request})
        return exceptions.generic_json_exception_response(e, status=400)


@web.api_view()
def download(request):
    """Stream the bytes of a data product's first replica.

    Resolves ``?data-product-uri=`` via the research registry and streams the
    file from the storage facade.
    """
    data_product_uri = request.GET.get("data-product-uri", "")
    try:
        data_product = request.airavata.research.get_data_product(data_product_uri)
    except Exception as e:
        log.warning(
            f"Failed to load DataProduct for {data_product_uri}",
            exc_info=True,
            extra={"request": request},
        )
        raise Http404("data product does not exist") from e
    file_path = _data_product_file_path(data_product)
    if file_path is None:
        raise Http404("data product has no replica to download")
    resp = request.airavata.storage.download_file(file_path)
    file_name = resp.name or data_product.product_name or os.path.basename(file_path)
    response = FileResponse(
        io.BytesIO(resp.content),
        as_attachment=False,
        filename=file_name,
        content_type=resp.content_type or "application/octet-stream",
    )
    return response


@web.api_view(http_method_names=["DELETE"])
@web.permission_classes([web.IsAuthenticated, DataProductSharedDirPermission])
def delete_file(request):
    # TODO check that user has write access to this file using sharing API
    data_product_uri = request.GET.get("data-product-uri", "")
    data_product = None
    try:
        data_product = request.airavata.research.get_data_product(data_product_uri)
    except Exception as e:
        log.warning(f"Failed to load DataProduct for {data_product_uri}", exc_info=True)
        raise Http404("data product does not exist") from e
    try:
        if (
            data_product.gateway_id != settings.GATEWAY_ID
            or data_product.owner_name != request.user.username
        ):
            raise PermissionDenied()
        file_path = _data_product_file_path(data_product)
        if file_path is None:
            raise Http404("data product has no replica to delete")
        request.airavata.storage.delete_file(file_path)
        return HttpResponse(status=204)
    except ObjectDoesNotExist as e:
        raise Http404(str(e)) from e


class UserProfileViewSet(
    web.mixins.RetrieveModelMixin, web.mixins.ListModelMixin, GenericAPIBackedViewSet
):
    """User profiles resource (read-only). SDK returns the raw ``UserProfile``
    proto (no envelope)."""

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import iam_resources

        return iam_resources

    def list(self, request, *args, **kwargs):
        data = self._sdk().get_all_user_profiles_in_gateway(
            request.airavata, offset=0, limit=-1
        )
        return web.Response(data)

    def retrieve(self, request, *args, **kwargs):
        # Matches the legacy get_instance: look up by the authenticated user,
        # not by the URL lookup value.
        data = self._sdk().get_user_profile(request.airavata, request.user.username)
        return web.Response(data)


class GroupResourceProfileViewSet(APIBackedViewSet):
    """Group resource profiles. SDK returns ``WithAccess[GroupResourceProfile]``.

    ``user_has_write_access`` is a composite the SDK can't derive: WRITE sharing
    on the profile id AND READ access to every credential token (the default
    token plus each compute-preference resource-specific token). The ViewSet
    computes it in ``_compute_has_write`` and passes it in as ``has_write``. The
    list endpoint is unpaginated, matching the pre-migration contract.
    """

    lookup_field = "group_resource_profile_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import compute_resources

        return compute_resources

    # get_object()/destroy still uses this.
    def get_list(self):
        return list(self.request.airavata.compute.get_group_resource_list())

    def get_instance(self, lookup_value):
        return self.request.airavata.compute.get_group_resource_profile(lookup_value)

    def _compute_has_write(self, profile):
        # WRITE on the profile AND READ on every credential token (see class doc).
        from django_airavata.apps.api.serializers import user_has_access

        request = self.request
        if not user_has_access(request, profile.group_resource_profile_id, "WRITE"):
            return False
        tokens = set(
            [profile.default_credential_store_token]
            + [
                cp.resource_specific_credential_store_token
                for cp in profile.compute_preferences
            ]
        )

        def check_token(token):
            return not token or user_has_access(request, token, "READ")

        return all(map(check_token, tokens))

    def list(self, request, *args, **kwargs):
        # The composite write flag needs each profile proto, so resolve the map
        # from the raw list, then let the SDK wrap each proto in WithAccess.
        profiles = self.get_list()
        has_write_by_id = {
            p.group_resource_profile_id: self._compute_has_write(p) for p in profiles
        }
        return web.Response(
            self._sdk().list_group_resource_profiles(
                request.airavata, has_write_by_id=has_write_by_id
            )
        )

    def retrieve(self, request, *args, **kwargs):
        group_resource_profile_id = self.kwargs[self.lookup_field]
        profile = self.get_instance(group_resource_profile_id)
        if profile is None:
            raise Http404
        return web.Response(
            self._sdk().get_group_resource_profile(
                request.airavata,
                group_resource_profile_id,
                has_write=self._compute_has_write(profile),
            )
        )

    def create(self, request, *args, **kwargs):
        data = request.data if isinstance(request.data, dict) else {}
        result = self._sdk().create_group_resource_profile(request.airavata, data)
        # Re-fetch to resolve the composite write flag against the persisted
        # profile (the create result has the server-assigned id + tokens).
        profile = self.get_instance(result.message.group_resource_profile_id)
        result.user_has_write_access = self._compute_has_write(profile)
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        group_resource_profile_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        result = self._sdk().update_group_resource_profile(
            request.airavata, group_resource_profile_id, data
        )
        profile = self.get_instance(group_resource_profile_id)
        result.user_has_write_access = self._compute_has_write(profile)
        return web.Response(result)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        group_resource_profile_id = self.kwargs[self.lookup_field]
        self._sdk().delete_group_resource_profile(
            request.airavata, group_resource_profile_id
        )
        return web.Response(status=web.status.HTTP_204_NO_CONTENT)


class SharedEntityViewSet(
    web.mixins.RetrieveModelMixin, web.mixins.UpdateModelMixin, GenericAPIBackedViewSet
):
    """Shared-entities resource — a composed ``SharedEntity`` carrying the
    ``UserProfile`` protos and ``WithGroupAccess`` group envelopes wholesale.

    Write model (``update`` / ``partial_update`` / ``merge``): grant/revoke deltas
    are computed and applied by ``sharing_resources.apply_sharing_update``
    (NAME-keyed permission maps); ``_normalize_permission`` accepts either the
    legacy integer or the member-NAME ``permission_type``.
    """

    lookup_field = "entity_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import sharing_resources

        return sharing_resources

    def _gateway_groups(self):
        # GATEWAY_GROUPS is never written to the session, so this is always None;
        # the SDK helpers fetch the groups via GetGatewayGroups when not provided.
        return None

    def retrieve(self, request, *args, **kwargs):
        entity_id = self.kwargs[self.lookup_field]
        return web.Response(
            self._sdk().get_shared_entity(
                request.airavata, entity_id, gateway_groups=self._gateway_groups()
            )
        )

    @web.action(methods=["get"], detail=True)
    def all(self, request, entity_id=None):
        """Load direct plus indirectly (inherited) shared permissions."""
        return web.Response(
            self._sdk().get_all_shared_entity(
                request.airavata, entity_id, gateway_groups=self._gateway_groups()
            )
        )

    @classmethod
    def _normalize_permission(cls, value):
        """Coerce a body ``permission_type`` to the member NAME string.

        Accepts either a legacy ``ResourcePermissionType`` integer (resolved via
        the proto enum's own ``Name()``, so it tracks the proto numbering) or the
        new member NAME, so the write path is stable across the cutover.
        """
        if isinstance(value, int):
            from airavata_sdk.generated.org.apache.airavata.model.group.group_manager_pb2 import (
                ResourcePermissionType,
            )

            return ResourcePermissionType.Name(value)
        return value

    @classmethod
    def _permission_map(cls, permissions, id_field):
        """Build an ``{id -> permission_name}`` map from a permission list.

        *permissions* is the snake_case list of
        ``{<user|group>: {...}, permission_type: <int|name>}`` dicts; *id_field*
        names the nested id key (``airavata_internal_user_id`` for users, ``id``
        for groups).
        """
        result = {}
        for entry in permissions:
            nested = entry.get("user", entry.get("group", {}))
            result[nested[id_field]] = cls._normalize_permission(
                entry["permission_type"]
            )
        return result

    def _existing_permission_maps(self, entity_id):
        """Return ``(existing_user_map, existing_group_map)`` from the server.

        Reads the *directly* granted permissions (the only editable ones) via
        the SDK ``SharedEntity`` object and reduces them to
        ``{id -> permission_name}`` maps — the same ``existing`` state the write
        delta computation diffs against.
        """
        existing = self._sdk().get_shared_entity(
            self.request.airavata, entity_id, gateway_groups=self._gateway_groups()
        )
        existing_users = {
            up.user.airavata_internal_user_id: up.permission_type
            for up in existing.user_permissions
        }
        existing_groups = {
            gp.group.message.id: gp.permission_type for gp in existing.group_permissions
        }
        return existing_users, existing_groups

    def _apply(self, entity_id, new_user_map, new_group_map):
        existing_users, existing_groups = self._existing_permission_maps(entity_id)
        self._sdk().apply_sharing_update(
            self.request.airavata,
            entity_id,
            existing_user_permissions=existing_users,
            new_user_permissions=new_user_map,
            existing_group_permissions=existing_groups,
            new_group_permissions=new_group_map,
        )

    def update(self, request, *args, **kwargs):
        entity_id = self.kwargs[self.lookup_field]
        # The body is snake_case (``user_permissions`` / ``group_permissions`` /
        # ``permission_type``).
        body = request.data if isinstance(request.data, dict) else {}
        new_user_map = self._permission_map(
            body.get("user_permissions", []), "airavata_internal_user_id"
        )
        new_group_map = self._permission_map(body.get("group_permissions", []), "id")
        self._apply(entity_id, new_user_map, new_group_map)
        return self.retrieve(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @web.action(methods=["put"], detail=True)
    def merge(self, request, entity_id=None):
        """Merge the request body's grants on top of the existing settings.

        Unlike ``update`` (which replaces the sharing settings), ``merge`` adds
        the body's permissions to the existing ones, so the effective "new"
        state is ``existing | body`` (body wins on conflicting ids — it appears
        last, matching the old serializer's list concatenation + dict build).
        """
        body = request.data if isinstance(request.data, dict) else {}

        existing_users, existing_groups = self._existing_permission_maps(entity_id)
        body_user_map = self._permission_map(
            body.get("user_permissions", []), "airavata_internal_user_id"
        )
        body_group_map = self._permission_map(body.get("group_permissions", []), "id")
        # Merge: existing first, body overrides on conflict (body is "last").
        merged_users = {**existing_users, **body_user_map}
        merged_groups = {**existing_groups, **body_group_map}

        self._sdk().apply_sharing_update(
            request.airavata,
            entity_id,
            existing_user_permissions=existing_users,
            new_user_permissions=merged_users,
            existing_group_permissions=existing_groups,
            new_group_permissions=merged_groups,
        )
        return web.Response(
            self._sdk().get_shared_entity(
                request.airavata, entity_id, gateway_groups=self._gateway_groups()
            )
        )


class CredentialSummaryViewSet(
    web.mixins.RetrieveModelMixin,
    web.mixins.ListModelMixin,
    web.mixins.DestroyModelMixin,
    GenericAPIBackedViewSet,
):
    """Credential-summaries resource. SDK returns ``WithAccess[CredentialSummary]``
    (``user_has_write_access`` keyed on the credential ``token``).

    Read + delete + the custom ``ssh``/``password`` list filters and
    ``create_ssh``/``create_password`` actions (the generic create/update verbs
    are not exposed; credentials are created via those typed actions)."""

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import credential_resources

        return credential_resources

    # APIBackedViewSet integration — get_instance still used by destroy

    def get_list(self):
        return self._sdk().get_all_credential_summaries(self.request.airavata)

    def get_instance(self, lookup_value):
        return self.request.airavata.credential.get_credential_summary(
            lookup_value, self.gateway_id
        )

    def list(self, request, *args, **kwargs):
        return web.Response(self._sdk().get_all_credential_summaries(request.airavata))

    def retrieve(self, request, *args, **kwargs):
        lookup_value = self.kwargs[self.lookup_field or "pk"]
        return web.Response(
            self._sdk().get_credential_summary(request.airavata, lookup_value)
        )

    @web.action(detail=False)
    def ssh(self, request):
        pb2 = serializers._credential_store_pb2()
        return web.Response(
            self._sdk().get_all_credential_summaries(
                request.airavata, summary_type=pb2.SummaryType.SSH
            )
        )

    @web.action(detail=False)
    def password(self, request):
        pb2 = serializers._credential_store_pb2()
        return web.Response(
            self._sdk().get_all_credential_summaries(
                request.airavata, summary_type=pb2.SummaryType.PASSWD
            )
        )

    @web.action(methods=["post"], detail=False)
    def create_ssh(self, request):
        if "description" not in request.data:
            raise web.ParseError("'description' is required in request")
        return web.Response(
            self._sdk().create_ssh_credential(request.airavata, request.data)
        )

    @web.action(methods=["post"], detail=False)
    def create_password(self, request):
        if (
            "username" not in request.data
            or "password" not in request.data
            or "description" not in request.data
        ):
            raise web.ParseError(
                "'username', 'password' and 'description' are all required in request"
            )
        return web.Response(
            self._sdk().create_password_credential(request.airavata, request.data)
        )

    def perform_destroy(self, instance):
        self._sdk().delete_credential_summary(self.request.airavata, instance)


class CurrentGatewayResourceProfile(web.APIView):
    """Current gateway resource profile. SDK returns
    ``WithAccess[GatewayResourceProfile]``.

    A gateway-level resource: ``user_has_write_access`` is the gateway-admin flag,
    which the view computes and passes into the SDK helper.
    """

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import compute_resources

        return compute_resources

    def get(self, request):
        has_write = getattr(request, "is_gateway_admin", False)
        return web.Response(
            self._sdk().get_gateway_resource_profile(
                request.airavata, settings.GATEWAY_ID, has_write=has_write
            )
        )

    def put(self, request):
        has_write = getattr(request, "is_gateway_admin", False)
        data = request.data if isinstance(request.data, dict) else {}
        return web.Response(
            self._sdk().update_gateway_resource_profile(
                request.airavata, settings.GATEWAY_ID, data, has_write=has_write
            ),
            status=web.status.HTTP_201_CREATED,
        )


class ExperimentArchiveView(web.APIView):
    def get(self, request, experiment_id=None):
        # Archive status was sourced from the portal's UserDataArchive DB tables
        # (written by an offline batch job). With no database, the portal always
        # reports not-archived; there is no server-side RPC to query this yet.
        result = {
            "archived": False,
            "archive_name": None,
            "created_date": None,
            "max_age": settings.GATEWAY_USER_DATA_ARCHIVE_MAX_AGE_DAYS,
        }
        return web.Response(result, status=web.status.HTTP_200_OK)


class StorageResourceViewSet(web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    """Storage resource catalog (read-only). SDK returns the raw
    ``StorageResourceDescription`` proto (no envelope)."""

    lookup_field = "storage_resource_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import storage_resources

        return storage_resources

    def get_instance(self, lookup_value):
        return self._sdk().get_storage_resource(self.request.airavata, lookup_value)

    def retrieve(self, request, *args, **kwargs):
        return web.Response(self.get_instance(self.kwargs[self.lookup_field]))

    @web.action(detail=False)
    def all_names(self, request):
        return web.Response(self._sdk().list_storage_resource_names(request.airavata))


class StoragePreferenceViewSet(SdkResourceViewSet):
    """Gateway storage preferences. SDK returns the bare ``StoragePreference``
    proto (no envelope). Every helper threads ``GATEWAY_ID`` as the leading arg.
    The list endpoint is unpaginated, matching the pre-migration contract."""

    lookup_field = "storage_resource_id"
    list_fn = "list_gateway_storage_preferences"
    get_fn = "get_gateway_storage_preference"
    create_fn = "create_gateway_storage_preference"
    update_fn = "update_gateway_storage_preference"

    @staticmethod
    def sdk():
        from airavata_sdk.helpers import compute_resources

        return compute_resources

    def list_args(self):
        return (settings.GATEWAY_ID,)

    def get_args(self, lookup_value):
        return (settings.GATEWAY_ID, lookup_value)

    def create_args(self, data):
        return (settings.GATEWAY_ID, data)

    def update_args(self, lookup_value, data):
        return (settings.GATEWAY_ID, lookup_value, data)

    def destroy(self, request, *args, **kwargs):
        self.sdk().delete_gateway_storage_preference(
            request.airavata, settings.GATEWAY_ID, self.kwargs[self.lookup_field]
        )
        return web.Response(status=web.status.HTTP_204_NO_CONTENT)


class ParserViewSet(SdkResourceViewSet):
    """Parsers resource (gateway-level catalog). SDK returns the raw ``Parser``
    proto (no envelope)."""

    lookup_field = "parser_id"
    list_fn = "list_parsers"
    get_fn = "get_parser"
    create_fn = "create_parser"
    update_fn = "update_parser"

    @staticmethod
    def sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources


def _user_storage_path(path, experiment_id=None, request=None):
    # Shim over the SDK resolver for portal callers that pass a Django request
    # (the SDK helper takes the request.airavata client).
    from airavata_sdk.helpers import storage_resources

    return storage_resources.resolve_user_storage_path(
        request.airavata,  # ty: ignore[unresolved-attribute]  # callers always pass a request; .airavata client injected by auth middleware
        path,
        experiment_id,
    )


class UserStoragePathView(web.APIView):
    """User-storage browse/listing over the SDK ``storage_resources`` helpers.

    The per-entry path-permission flags (``user_has_write_access`` for files,
    ``user_has_write_access`` / ``is_shared_dir`` for directories) are
    ``GATEWAY_DATA_SHARED_DIRECTORIES`` / ``is_gateway_admin`` decisions, not
    backend fields, so they are layered on the rendered proto here.

    The write paths (upload / tus / file-content replace / delete) stay in the
    portal — HTTP concerns, not part of the read contract.
    """

    permission_classes = (web.IsAuthenticated, UserStorageSharedDirPermission)

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import storage_resources

        return storage_resources

    def get(self, request, path="/"):
        # AIRAVATA-3460 Allow passing path as a query parameter instead
        path = request.query_params.get("path", path)
        experiment_id = request.query_params.get("experiment-id")
        return self._create_response(request, path, experiment_id=experiment_id)

    def post(self, request, path="/"):
        sdk = self._sdk()
        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        resolved = sdk.resolve_user_storage_path(request.airavata, path, experiment_id)
        if not sdk.dir_exists(request.airavata, resolved):
            sdk.create_dir(request.airavata, resolved)

        data_product = None
        # Handle direct upload
        if "file" in request.FILES:
            user_file = request.FILES["file"]
            data_product = _storage_upload_and_register(
                request,
                path,
                user_file,
                name=user_file.name,
                content_type=user_file.content_type,
                experiment_id=experiment_id,
            )
        # Handle a tus upload
        elif "uploadURL" in request.POST:
            uploadURL = request.POST["uploadURL"]

            def save_file(file_path, file_name, file_type):
                with open(file_path, "rb") as uploaded_file:
                    return _storage_upload_and_register(
                        request,
                        path,
                        uploaded_file,
                        name=file_name,
                        content_type=file_type,
                        experiment_id=experiment_id,
                    )

            data_product = tus.save_tus_upload(uploadURL, save_file)
        return self._create_response(
            request, path, uploaded=data_product, experiment_id=experiment_id
        )

    # Accept either to replace file or to replace file content text.
    def put(self, request, path="/"):
        sdk = self._sdk()
        path = request.POST.get("path", path)
        # Replace the file if the request has a file upload.
        if "file" in request.FILES:
            self.delete(request=request, path=path)
            dir_path, _file_name = os.path.split(path)
            self.post(request=request, path=dir_path)
        # Replace only the file content if the request body has the `fileContentText`
        elif request.data and "fileContentText" in request.data:
            request.airavata.storage.upload_file(
                path=sdk.resolve_user_storage_path(request.airavata, path),
                content=request.data["fileContentText"].encode("utf-8"),
                name=os.path.basename(path),
            )
        else:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)

        return self._create_response(request=request, path=path)

    def delete(self, request, path="/"):
        sdk = self._sdk()
        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        resolved = sdk.resolve_user_storage_path(request.airavata, path, experiment_id)
        if sdk.dir_exists(request.airavata, resolved):
            sdk.delete_dir(request.airavata, resolved)
        else:
            sdk.delete_file(request.airavata, resolved)

        return web.Response(status=204)

    # Per-entry path-permission flags (mirrors the legacy serializer fields)

    def _dir_write_access(self, request, path):
        """WRITE flag for a directory entry: gateway-admin on a shared path,
        ``True`` otherwise (mirrors ``UserHasWriteAccessToPathSerializer``)."""
        if view_utils.is_shared_path(path):
            return request.is_gateway_admin
        return True

    def _user_has_write_access(self, request, path):
        """Top-level ``user_has_write_access`` (mirrors the legacy base serializer).

        ``True`` for non-shared paths; the gateway-admin flag for shared paths.
        """
        if view_utils.is_shared_path(path):
            return request.is_gateway_admin
        return True

    def _create_response(self, request, path, uploaded=None, experiment_id=None):
        from django_airavata.apps.api.proto_render import to_jsonable

        sdk = self._sdk()
        resolved = sdk.resolve_user_storage_path(request.airavata, path, experiment_id)
        top_write_access = self._user_has_write_access(request, path)
        if sdk.dir_exists(request.airavata, resolved):
            listing = sdk.list_dir(request.airavata, resolved)
            # The proto path is absolute (/storage/...); expose it home-relative
            # so the frontend's ~/-prefixed navigation doesn't double the root.
            base_rel = path[2:] if path.startswith("~/") else path.lstrip("/")
            directories = []
            for d in listing.directories:
                rendered = to_jsonable(d)
                rendered["path"] = os.path.join(base_rel, d.name)
                rendered["user_has_write_access"] = self._dir_write_access(
                    request, d.path
                )
                rendered["is_shared_dir"] = view_utils.is_shared_dir(d.path)
                directories.append(rendered)
            files = []
            for f in listing.files:
                rendered = to_jsonable(f)
                rendered["path"] = os.path.join(base_rel, f.name)
                rendered["user_has_write_access"] = True
                files.append(rendered)
            data = {
                "is_dir": True,
                "directories": directories,
                "files": files,
            }
        else:
            rendered = to_jsonable(sdk.get_file_metadata(request.airavata, resolved))
            rendered["user_has_write_access"] = True
            data = {
                "is_dir": False,
                "directories": [],
                "files": [rendered],
            }
        if uploaded is not None:
            # uploaded is a proto DataProductModel; ProtoJSONRenderer renders it
            # to snake_case via to_jsonable on the response path.
            data["uploaded"] = uploaded
        data["parts"] = self._split_path(path)
        data["path"] = path
        data["user_has_write_access"] = top_write_access
        return web.Response(data)

    def _split_path(self, path):
        head, tail = os.path.split(path)
        if head != path:
            return [*self._split_path(head), tail]
        elif tail != "":
            return [tail]
        else:
            return []


class ExperimentStoragePathView(web.APIView):
    """Experiment data-dir browse/listing over the SDK ``storage_resources``
    helpers.

    Entry ``path`` is rewritten relative to the experiment data dir (the legacy
    ``ListExperimentDir`` exposed relative paths). File entries carry
    ``user_has_write_access`` — always ``True`` since an experiment data dir is
    never a gateway-shared path.
    """

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import storage_resources

        return storage_resources

    def get(self, request, experiment_id=None, path=""):
        return self._create_response(request, experiment_id, path)

    def _create_response(self, request, experiment_id, path):
        from django_airavata.apps.api.proto_render import to_jsonable

        sdk = self._sdk()
        resolved = sdk.resolve_user_storage_path(request.airavata, path, experiment_id)
        if not sdk.dir_exists(request.airavata, resolved):
            raise Http404(f"Path '{path}' does not exist for {experiment_id}")

        base = resolved.rstrip("/")

        def rel(entry_path):
            # Expose the path relative to the experiment data dir, as the legacy
            # list_experiment_dir did (resolved is the absolute experiment path).
            if entry_path.startswith(base + "/"):
                return entry_path[len(base) + 1 :]
            return os.path.basename(entry_path)

        def rel_path(entry_path):
            r = rel(entry_path)
            return os.path.join(path, r) if path else r

        listing = sdk.list_experiment_dir(request.airavata, resolved)
        directories = []
        for d in listing.directories:
            rendered = to_jsonable(d)
            rendered["path"] = rel_path(d.path)
            directories.append(rendered)
        files = []
        for f in listing.files:
            rendered = to_jsonable(f)
            rendered["path"] = rel_path(f.path)
            rendered["user_has_write_access"] = True
            files.append(rendered)
        data = {
            "is_dir": True,
            "directories": directories,
            "files": files,
            "parts": self._split_path(path),
        }
        return web.Response(data)

    def _split_path(self, path):
        head, tail = os.path.split(path)
        if head != "":
            return [*self._split_path(head), tail]
        elif tail != "":
            return [tail]
        else:
            return []


class WorkspacePreferencesView(web.APIView):
    def get(self, request):
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        return web.Response(
            serializers.workspace_preferences_data(workspace_preferences)
        )


class ManageNotificationViewSet(APIBackedViewSet):
    """Notifications resource. SDK returns ``WithAccess[Notification]``
    (gateway-level; ``user_has_write_access`` is the gateway-admin flag).

    Each action merges the portal-only ``show_in_dashboard`` flag (the Django
    ``NotificationExtension`` table — not part of the proto, so the SDK cannot
    supply it) onto the flattened JSON.
    """

    lookup_field = "notification_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    # APIBackedViewSet integration — still used by the destroy mixin

    def get_instance(self, lookup_value):
        return self.request.airavata.research.get_notification(
            settings.GATEWAY_ID, lookup_value
        )

    def get_list(self):
        return list(
            self.request.airavata.research.get_all_notifications(self.gateway_id)
        )

    # Portal-only ``show_in_dashboard`` extension (Django ``NotificationExtension``)

    def _show_in_dashboard(self, notification_id):
        """Resolve the ``show_in_dashboard`` extension flag for one notification."""
        return helpers.show_in_dashboard_map(self.gateway_id).get(
            notification_id, False
        )

    def _show_in_dashboard_map(self, notification_ids):
        """Build ``{notification_id: show_in_dashboard}`` from the cache map."""
        flags = helpers.show_in_dashboard_map(self.gateway_id)
        return {nid: flags.get(nid, False) for nid in notification_ids}

    def _render(self, with_access, show_in_dashboard):
        """Flatten a ``WithAccess[Notification]`` and merge the portal-only flag.

        ``to_jsonable`` renders the proto to snake_case JSON merged with the
        access scalars; ``show_in_dashboard`` (the Django extension flag) is
        merged on top here because it is not a proto / SDK field.
        """
        from django_airavata.apps.api.proto_render import to_jsonable

        data = to_jsonable(with_access)
        data["show_in_dashboard"] = bool(show_in_dashboard)
        return data

    def _update_notification_extension(self, request, notification_id):
        """Persist the portal-only ``show_in_dashboard`` extension flag.

        Mirrors the legacy ``NotificationSerializer.update_notification_extension``
        — only acts when the request body carries ``show_in_dashboard`` (the
        request body is already snake_case)."""
        if "show_in_dashboard" not in request.data:
            return
        helpers.set_show_in_dashboard(
            self.gateway_id, notification_id, request.data["show_in_dashboard"]
        )

    def list(self, request, *args, **kwargs):
        sdk = self._sdk()
        has_write = request.is_gateway_admin
        results = sdk.list_notifications(request.airavata, has_write=has_write)
        dashboard_map = self._show_in_dashboard_map(
            r.message.notification_id for r in results
        )
        data = [
            self._render(r, dashboard_map.get(r.message.notification_id, False))
            for r in results
        ]
        return web.Response(data)

    def retrieve(self, request, *args, **kwargs):
        sdk = self._sdk()
        notification_id = self.kwargs[self.lookup_field]
        result = sdk.get_notification(
            request.airavata, notification_id, has_write=request.is_gateway_admin
        )
        return web.Response(
            self._render(result, self._show_in_dashboard(notification_id))
        )

    def create(self, request, *args, **kwargs):
        sdk = self._sdk()
        # request.data is already snake_case
        data = request.data if isinstance(request.data, dict) else {}
        show_in_dashboard = bool(data.get("show_in_dashboard", False))
        result = sdk.create_notification(
            request.airavata, data, has_write=request.is_gateway_admin
        )
        self._update_notification_extension(request, result.message.notification_id)
        return web.Response(
            self._render(result, show_in_dashboard), status=web.status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        sdk = self._sdk()
        notification_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        show_in_dashboard = bool(
            data.get("show_in_dashboard", self._show_in_dashboard(notification_id))
        )
        result = sdk.update_notification(
            request.airavata, notification_id, data, has_write=request.is_gateway_admin
        )
        self._update_notification_extension(request, notification_id)
        return web.Response(self._render(result, show_in_dashboard))

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.request.airavata.research.delete_notification(
            settings.GATEWAY_ID, instance.notification_id
        )


class AckNotificationViewSet(web.APIView):
    def get(self, request):
        if "id" in request.GET:
            notification_id = request.GET["id"]
            context_processors.mark_notification_read(
                request.user.username, notification_id
            )
        return HttpResponse(status=204)


class IAMUserViewSet(
    web.mixins.RetrieveModelMixin,
    web.mixins.UpdateModelMixin,
    web.mixins.ListModelMixin,
    web.mixins.DestroyModelMixin,
    GenericAPIBackedViewSet,
):
    """IAM (managed Keycloak) users — a composed pydantic ``IAMUser``.

    The ViewSet supplies the parts the IAM service cannot compute: the
    ``DoesUserExist`` result, the sharing group list, ``request.is_gateway_admin``,
    and the two Django-ORM lookups.

    The ``update`` / ``update_username`` write path validates the incoming
    camelCase body with plain validators in ``serializers`` (write validation
    only — off the OUTPUT path), so it needs the plain ``JSONParser`` (no key
    transform).
    """

    pagination_class = APIResultPagination
    permission_classes = (
        web.IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import iam_resources

        return iam_resources

    # Composed-part resolvers (the parts the owning IAM service can't compute)

    def _user_profile_exists(self, user_profile):
        return self.request.airavata.iam.does_user_exist(
            user_profile.user_id, self.gateway_id
        )

    def _user_groups(self, user_profile, exists):
        """Resolve the GroupModel protos the user belongs to (write path uses
        these too; only resolved when the airavata user profile exists)."""
        if not exists:
            return []
        return list(
            self.request.airavata.sharing.gm_get_all_groups_user_belongs(
                user_profile.airavata_internal_user_id
            )
        )

    def _external_idp_user_info(self, user_id):
        # TODO(Phase C): external IDP claims were mirrored into the local Django
        # UserProfile.idp_userinfo, which no longer exists. Expose them via a
        # backend RPC / the Keycloak identity broker if this admin column is
        # still needed.
        return {}

    def _user_profile_invalid_fields(self, user_id):
        # TODO(Phase C): profile validity was computed from the local Django
        # UserProfile, which no longer exists. Profile validity is Keycloak's
        # concern now; surface it via a backend RPC if this admin column is
        # still needed.
        return []

    def _build_iam_user(self, user_profile, request, *, exists=None, groups=None):
        """Compose an ``IAMUser`` from a proto ``UserProfile``.

        Resolves the composed parts (``DoesUserExist`` result, the user's groups
        as ``WithGroupAccess`` envelopes rendered proto-direct, gateway-admin
        flag, two Django-ORM lookups) and hands them to the SDK ``get_iam_user``,
        which computes the proto-derived scalars and returns the pydantic model.
        """
        from airavata_sdk.helpers import sharing_resources

        from django_airavata.apps.api.proto_render import to_jsonable

        if exists is None:
            exists = self._user_profile_exists(user_profile)
        if groups is None:
            groups = self._user_groups(user_profile, exists)

        return self._sdk().get_iam_user(
            request.airavata,
            user_profile,
            airavata_user_profile_exists=exists,
            user_has_write_access=request.is_gateway_admin,
            groups=to_jsonable(sharing_resources.wrap_groups(request.airavata, groups)),
            external_idp_user_info=self._external_idp_user_info(user_profile.user_id),
            user_profile_invalid_fields=self._user_profile_invalid_fields(
                user_profile.user_id
            ),
        )

    def list(self, request, *args, **kwargs):
        search = request.GET.get("search", None)

        view = self

        class IAMUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return list(
                    view._sdk().list_iam_users(
                        request.airavata,
                        offset=offset,
                        limit=limit,
                        search=search or "",
                    )
                )

        queryset = IAMUsersResultIterator(query_params=request.query_params.copy())
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._build_iam_user(u, request) for u in page]
            return self.get_paginated_response(data)
        data = [self._build_iam_user(u, request) for u in queryset.get_results()]
        return web.Response(data)

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        user_profile = iam_admin_client.get_user(user_id)
        return web.Response(self._build_iam_user(user_profile, request))

    # APIResultIterator / write-path plumbing (serializer-backed)

    def get_list(self):
        search = self.request.GET.get("search", None)

        convert_user_profile = self._convert_user_profile

        class IAMUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return map(
                    convert_user_profile,
                    iam_admin_client.get_users(offset, limit, search),
                )

        return IAMUsersResultIterator(query_params=self.request.query_params.copy())

    def get_instance(self, lookup_value):
        return self._convert_user_profile(iam_admin_client.get_user(lookup_value))

    def update(self, request, *args, **kwargs):
        # Validate the camelCase body, apply the group-membership diff, then
        # render the refreshed profile through the SDK output path.
        instance = self.get_object()
        try:
            data = serializers.validate_iam_user_body(request.data)
        except serializers.ValidationError as e:
            return web.Response(e.detail, status=web.status.HTTP_400_BAD_REQUEST)
        self._apply_group_diff(instance, data)
        user_profile = iam_admin_client.get_user(data["userId"])
        return web.Response(self._build_iam_user(user_profile, request))

    def _apply_group_diff(self, instance, data):
        added_group_ids, removed_group_ids = serializers.iam_user_group_diff(
            instance["groups"], data
        )
        sharing = self.request.airavata.sharing
        user_id = instance["airavataInternalUserId"]
        added_groups = []
        for group_id in added_group_ids:
            group = sharing.gm_get_group(group_id)
            sharing.gm_add_users_to_group([user_id], group_id)
            added_groups.append(group)
        if len(added_groups) > 0:
            user_profile = self.request.airavata.iam.get_user_profile_by_id(
                data["userId"], settings.GATEWAY_ID
            )
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=added_groups,
                request=self.request,
            )
        for group_id in removed_group_ids:
            sharing.gm_remove_users_from_group([user_id], group_id)

    def perform_destroy(self, instance):
        iam_admin_client.delete_user(instance["userId"])

    @web.action(methods=["post"], detail=True)
    def enable(self, request, user_id=None):
        iam_admin_client.enable_user(user_id)
        user_profile = iam_admin_client.get_user(user_id)
        return web.Response(self._build_iam_user(user_profile, request))

    @web.action(methods=["put"], detail=False)
    def update_username(self, request):
        try:
            old_username, new_username = serializers.parse_update_username(request.data)
        except serializers.ValidationError as e:
            return web.Response(e.detail, status=web.status.HTTP_400_BAD_REQUEST)
        iam_admin_client.update_username(old_username, new_username)
        # The username is updated in Keycloak (the source of truth); there is no
        # longer a Django UserProfile mirror to keep in sync.
        user_profile = iam_admin_client.get_user(new_username)
        return web.Response(self._build_iam_user(user_profile, request))

    def _convert_user_profile(self, user_profile):
        # iam_admin_client returns a protobuf UserProfile; read proto fields
        # directly and build the dict the IAMUserProfile serializer consumes on
        # the write path (the read/output path composes the SDK IAMUser via
        # _build_iam_user).
        from airavata_sdk.generated.org.apache.airavata.model.user import (
            user_profile_pb2,
        )

        Status = user_profile_pb2.Status
        airavata_user_profile_exists = self.request.airavata.iam.does_user_exist(
            user_profile.user_id, self.gateway_id
        )
        groups = []
        if airavata_user_profile_exists:
            groups = list(
                self.request.airavata.sharing.gm_get_all_groups_user_belongs(
                    user_profile.airavata_internal_user_id
                )
            )
        return {
            "airavataInternalUserId": user_profile.airavata_internal_user_id,
            "userId": user_profile.user_id,
            "gatewayId": user_profile.gateway_id,
            "email": user_profile.emails[0],
            "firstName": user_profile.first_name,
            "lastName": user_profile.last_name,
            "enabled": user_profile.state == Status.ACTIVE,
            "emailVerified": (
                user_profile.state == Status.CONFIRMED
                or user_profile.state == Status.ACTIVE
            ),
            "airavataUserProfileExists": airavata_user_profile_exists,
            "creationTime": user_profile.creation_time,
            "groups": groups,
        }


class ExperimentStatisticsView(web.APIView):
    """Experiment-statistics resource. SDK returns the ``ExperimentStatistics``
    proto wholesale; the view nests it under ``results`` in a pagination envelope
    keyed on the proto's ``all_experiment_count``."""

    # TODO: restrict to only Admins or Read Only Admins group members

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import research_resources

        return research_resources

    def get(self, request):
        if "fromTime" in request.GET:
            from_time = (
                view_utils.convert_utc_iso8601_to_date(
                    request.GET["fromTime"]
                ).timestamp()
                * 1000
            )
        else:
            from_time = (datetime.now(UTC) - timedelta(days=7)).timestamp() * 1000
        from_time = int(from_time)
        if "toTime" in request.GET:
            to_time = (
                view_utils.convert_utc_iso8601_to_date(
                    request.GET["toTime"]
                ).timestamp()
                * 1000
            )
        else:
            to_time = datetime.now(UTC).timestamp() * 1000
        to_time = int(to_time)
        username = request.GET.get("userName", None)
        application_name = request.GET.get("applicationName", None)
        resource_hostname = request.GET.get("resourceHostName", None)
        limit = int(request.GET.get("limit", "50"))
        offset = int(request.GET.get("offset", "0"))

        stats = self._sdk().get_experiment_statistics(
            request.airavata,
            from_time=from_time,
            to_time=to_time,
            user_name=username,
            application_name=application_name,
            resource_host_name=resource_hostname,
            limit=limit,
            offset=offset,
        )

        paginator = web.LimitOffsetPagination()
        paginator.count = stats.all_experiment_count  # ty: ignore[unresolved-attribute]  # DRF-shim pagination attr set dynamically
        paginator.limit = limit
        paginator.offset = offset
        paginator.request = request
        # The proto is nested under ``results``; ProtoJSONRenderer recurses the
        # paginated dict and flattens it to snake_case JSON.
        response = paginator.get_paginated_response(stats)
        # Also add limit and offset to the response
        response.data["limit"] = limit
        response.data["offset"] = offset
        return response


class UnverifiedEmailUserViewSet(
    web.mixins.ListModelMixin, web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet
):
    """Users whose email is not yet verified — a pydantic ``UnverifiedEmailUser``
    (a strict subset of ``IAMUser``). The ViewSet supplies
    ``request.is_gateway_admin``."""

    pagination_class = APIResultPagination
    permission_classes = (
        web.IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    @staticmethod
    def _sdk():
        from airavata_sdk.helpers import iam_resources

        return iam_resources

    def _build_unverified(self, user_profile, request):
        return self._sdk().get_unverified_email_user(
            request.airavata,
            user_profile,
            user_has_write_access=request.is_gateway_admin,
        )

    def list(self, request, *args, **kwargs):
        view = self

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return view._get_unverified_email_user_profiles(limit, offset)

        queryset = UnverifiedEmailUsersResultIterator()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._build_unverified(u, request) for u in page]
            return self.get_paginated_response(data)
        data = [self._build_unverified(u, request) for u in queryset.get_results()]
        return web.Response(data)

    def retrieve(self, request, *args, **kwargs):
        user_id = self.kwargs[self.lookup_field]
        users = self._get_unverified_email_user_profiles(limit=1, username=user_id)
        if len(users) == 0:
            raise Http404(f"No unverified email record found for user {user_id}")
        return web.Response(self._build_unverified(users[0], request))

    def get_list(self):
        get_users = self._get_unverified_email_user_profiles

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            def get_results(self, limit=-1, offset=0):
                return get_users(limit, offset)

        return UnverifiedEmailUsersResultIterator()

    def get_instance(self, lookup_value):
        users = self._get_unverified_email_user_profiles(limit=1, username=lookup_value)
        if len(users) == 0:
            raise Http404(f"No unverified email record found for user {lookup_value}")
        else:
            return users[0]

    def _get_unverified_email_user_profiles(self, limit=-1, offset=0, username=None):
        # TODO(Phase C): self-registration email verification is now owned by
        # Keycloak (the local EmailVerification model was removed with the Django
        # account surface). Surface unverified-email users via a backend RPC /
        # Keycloak admin query if this admin view is still needed.
        return []


class LogRecordConsumer(web.APIView):
    def post(self, request):
        try:
            log_record = serializers.parse_log_record(request.data)
        except serializers.ValidationError as e:
            return web.Response(e.detail, status=web.status.HTTP_400_BAD_REQUEST)
        log_level = getattr(logging, log_record["level"], None)
        if log_level is not None:
            stacktrace = "".join("\n    " + a for a in log_record["stacktrace"])
            log.log(
                log_level,
                "Frontend error: {}: {}\nstacktrace: {}".format(
                    log_record["message"],
                    json.dumps(log_record["details"], indent=4),
                    stacktrace,
                ),
                extra={"request": request},
            )
        return web.Response(serializers.render_log_record(log_record))


class SettingsAPIView(web.APIView):
    def get(self, request):
        return web.Response(
            serializers.settings_data(
                settings.FILE_UPLOAD_MAX_FILE_SIZE,
                settings.TUS_ENDPOINT,
                settings.PGA_URL,
            )
        )


class APIServerStatusCheckView(web.APIView):
    def get(self, request):
        try:
            request.airavata.research.get_user_projects(
                gateway_id=settings.GATEWAY_ID,
                user_name=request.user.username,
                limit=1,
                offset=0,
            )
            data = {"apiServerUp": True}
        except Exception as e:
            log.debug(f"API server status check failed: {e!s}")
            data = {"apiServerUp": False}
        return web.Response(data)


@web.api_view()
def notebook_output_view(request):
    provider_id = request.GET["provider-id"]
    experiment_id = request.GET["experiment-id"]
    experiment_output_name = request.GET["experiment-output-name"]
    data = output_views.generate_data(
        request, provider_id, experiment_output_name, experiment_id
    )
    return HttpResponse(data["output"])


@web.api_view()
def html_output_view(request):
    data = _generate_output_view_data(request)
    return JsonResponse(data)


@web.api_view()
def image_output_view(request):
    data = _generate_output_view_data(request)
    # data should contain 'image' as a file-like object or raw bytes with the
    # file data and 'mime-type' with the images mimetype
    data["image"] = base64.b64encode(data["image"]).decode("utf-8")
    return JsonResponse(data)


@web.api_view()
def link_output_view(request):
    data = _generate_output_view_data(request)
    return JsonResponse(data)


def _generate_output_view_data(request):
    params = request.GET.copy()
    provider_id = params.pop("provider-id")[0]
    experiment_id = params.pop("experiment-id")[0]
    experiment_output_name = params.pop("experiment-output-name")[0]
    test_mode = "test-mode" in params and params.pop("test-mode")[0] == "true"
    return output_views.generate_data(
        request,
        provider_id,
        experiment_output_name,
        experiment_id,
        test_mode=test_mode,
        **params.dict(),
    )


class QueueSettingsCalculatorViewSet(
    web.mixins.ListModelMixin, web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet
):
    def get_list(self):
        return queue_settings.get_all()

    def get_instance(self, lookup_value):
        calcs = queue_settings.get_all()
        calc = [calc for calc in calcs if calc.id == lookup_value]
        if len(calc) == 0:
            return None
        return calc[0]

    def list(self, request, *args, **kwargs):
        return web.Response(
            [serializers.queue_settings_calculator_data(c) for c in self.get_list()]
        )

    def retrieve(self, request, *args, **kwargs):
        return web.Response(
            serializers.queue_settings_calculator_data(self.get_object())
        )

    @web.action(methods=["post"], detail=True)
    def calculate(self, request, pk=None):
        from airavata_sdk.helpers import research_resources

        data = request.data if isinstance(request.data, dict) else {}
        result = {}
        # Build the proto ExperimentModel from the request; ignore a malformed
        # body (likely a late-initialization partial) and return empty settings.
        try:
            experiment_model = research_resources.build_experiment(
                request.airavata, data
            )
        except Exception:
            log.debug(
                "Ignoring invalid experiment model for queue calculation", exc_info=True
            )
            experiment_model = None
        if experiment_model is not None:
            result = queue_settings.calculate_queue_settings(
                pk, request, experiment_model
            )
        return web.Response(result)
