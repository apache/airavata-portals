import base64
import json
import logging
import os
import warnings
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.gzip import gzip_page
from rest_framework import mixins, pagination, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from airavata_sdk.generated.org.apache.airavata.model.experiment.experiment_pb2 import (
    ExperimentModel as ExperimentModelProto,
)
from django_airavata.apps.admin.models import UserDataArchiveEntry
from django_airavata.apps.api import user_storage
from django_airavata.apps.api.proto_helpers import proto_to_dict, proto_list_to_dicts, dict_to_proto
from django_airavata.apps.api.view_utils import (
    APIBackedViewSet,
    APIResultIterator,
    APIResultPagination,
    DataProductSharedDirPermission,
    GenericAPIBackedViewSet,
    IsInAdminsGroupPermission,
    UserStorageSharedDirPermission,
)
from django_airavata.apps.auth import iam_admin_client
from django_airavata.apps.auth.models import EmailVerification
from django_airavata.proto_compat import (
    ResourcePermissionType,
    Status,
    SummaryType,
)

from . import exceptions, helpers, models, output_views, serializers, signals, tus, view_utils
from . import queue_settings as queue_settings_calculators

READ_PERMISSION_TYPE = "{}:READ"

log = logging.getLogger(__name__)


class GroupViewSet(APIBackedViewSet):
    serializer_class = serializers.GroupSerializer
    lookup_field = "group_id"
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:group-list"

    def get_list(self) -> APIResultIterator:
        view = self

        class GroupResultsIterator(APIResultIterator):
            def get_results(self, limit: int = -1, offset: int = 0) -> list[Any]:
                groups = view.request.airavata_client.sharing.get_groups()
                end = offset + limit if limit > 0 else len(groups)
                return groups[offset:end] if groups else []

        return GroupResultsIterator()

    def get_instance(self, lookup_value: str) -> Any:
        return self.request.airavata_client.sharing.get_group(lookup_value)

    def perform_create(self, serializer: Any) -> None:
        group = serializer.save()
        group_id = self.request.airavata_client.sharing.create_group(group)
        group.id = group_id
        users_added_to_group = set(group.members) - {group.ownerId}
        self._send_users_added_to_group(users_added_to_group, group)

    def perform_update(self, serializer: Any) -> None:
        group = serializer.save()
        sharing_client = self.request.airavata_client.sharing
        if len(group._added_members) > 0:
            sharing_client.add_users_to_group(group._added_members, group.id)
            self._send_users_added_to_group(group._added_members, group)
        if len(group._removed_members) > 0:
            sharing_client.remove_users_from_group(group._removed_members, group.id)
        if len(group._added_admins) > 0:
            sharing_client.add_group_admins(group.id, group._added_admins)
        if len(group._removed_admins) > 0:
            sharing_client.remove_group_admins(group.id, group._removed_admins)
        sharing_client.update_group(group)

    def perform_destroy(self, instance: Any) -> None:  # type: ignore[override]
        self.request.airavata_client.sharing.delete_group(instance.id, instance.ownerId)

    def _send_users_added_to_group(self, internal_user_ids: set[str], group: Any) -> None:
        for internal_user_id in internal_user_ids:
            user_id, gateway_id = internal_user_id.rsplit("@", maxsplit=1)
            user_profile = self.request.airavata_client.iam.get_user_profile_by_id(user_id, gateway_id)
            signals.user_added_to_group.send(
                sender=self.__class__, user=user_profile, groups=[group], request=self.request
            )


class ProjectViewSet(viewsets.ViewSet):
    lookup_field = "project_id"

    def list(self, request: Request) -> Response:
        projects = request.airavata_client.research.get_user_projects(
            settings.GATEWAY_ID, request.user.username, -1, 0
        )
        return Response(proto_list_to_dicts(projects))

    def retrieve(self, request: Request, project_id: str | None = None) -> Response:
        project = request.airavata_client.research.get_project(project_id)
        return Response(proto_to_dict(project))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
            Project as ProjectProto,
        )

        proto = ProjectProto(
            owner=request.user.username,
            gateway_id=settings.GATEWAY_ID,
            name=request.data.get("name", ""),
            description=request.data.get("description", "") or "",
        )
        project_id = request.airavata_client.research.create_project(settings.GATEWAY_ID, proto)
        proto.project_id = project_id
        self._update_most_recent_project(request, project_id)
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, project_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
            Project as ProjectProto,
        )

        proto = ProjectProto(
            project_id=project_id,
            owner=request.data.get("owner", request.user.username),
            gateway_id=request.data.get("gateway_id", settings.GATEWAY_ID),
            name=request.data.get("name", ""),
            description=request.data.get("description", ""),
        )
        request.airavata_client.research.update_project(project_id, proto)
        self._update_most_recent_project(request, project_id)
        return Response(proto_to_dict(proto))

    def destroy(self, request: Request, project_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.status.status_pb2 import ExperimentState

        # Check for running experiments
        experiments = request.airavata_client.research.get_experiments_in_project(project_id, -1, 0)
        running_states = {
            ExperimentState.EXPERIMENT_STATE_EXECUTING,
            ExperimentState.EXPERIMENT_STATE_LAUNCHED,
            ExperimentState.EXPERIMENT_STATE_SCHEDULED,
            ExperimentState.EXPERIMENT_STATE_VALIDATED,
        }
        running = [
            e for e in experiments
            if e.experiment_status and e.experiment_status[-1].state in running_states
        ]
        if running:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"Cannot delete: {len(running)} experiment(s) still running. "
                "Cancel or wait for them to complete first."
            )

        # Delete all experiments in the project
        for experiment in experiments:
            try:
                request.airavata_client.research.delete_experiment(experiment.experiment_id)
            except Exception:
                log.warning("Failed to delete experiment %s during project cascade", experiment.experiment_id)

        # Delete the project itself
        request.airavata_client.research.delete_project(project_id)
        return Response(status=204)

    @action(detail=False)
    def list_all(self, request: Request) -> Response:
        projects = request.airavata_client.research.get_user_projects(
            settings.GATEWAY_ID, request.user.username, -1, 0
        )
        return Response(proto_list_to_dicts(projects))

    @action(detail=True)
    def experiments(self, request: Request, project_id: str | None = None) -> Response:
        experiments = request.airavata_client.research.get_experiments_in_project(project_id, -1, 0)
        return Response(proto_list_to_dicts(experiments))

    @staticmethod
    def _update_most_recent_project(request: Request, project_id: str) -> None:
        prefs = helpers.WorkspacePreferencesHelper().get(request)
        prefs.most_recent_project_id = project_id
        prefs.save()


class ExperimentViewSet(viewsets.ViewSet):
    lookup_field = "experiment_id"

    def retrieve(self, request: Request, experiment_id: str | None = None) -> Response:
        experiment = request.airavata_client.research.get_experiment(experiment_id)
        return Response(proto_to_dict(experiment))

    def create(self, request: Request) -> Response:
        experiment = dict_to_proto(
            request.data,
            ExperimentModelProto,
        )
        experiment.gateway_id = settings.GATEWAY_ID
        experiment.user_name = request.user.username
        experiment_id = request.airavata_client.research.create_experiment(settings.GATEWAY_ID, experiment)
        self._update_workspace_preferences(
            request,
            project_id=experiment.project_id,
            group_resource_profile_id=experiment.user_configuration_data.group_resource_profile_id,
            compute_resource_id=experiment.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        experiment.experiment_id = experiment_id
        return Response(proto_to_dict(experiment), status=201)

    def update(self, request: Request, experiment_id: str | None = None) -> Response:
        experiment = dict_to_proto(
            request.data,
            ExperimentModelProto,
        )
        experiment.gateway_id = settings.GATEWAY_ID
        experiment.user_name = request.user.username
        request.airavata_client.research.update_experiment(experiment_id, experiment)
        self._update_workspace_preferences(
            request,
            project_id=experiment.project_id,
            group_resource_profile_id=experiment.user_configuration_data.group_resource_profile_id,
            compute_resource_id=experiment.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        return Response(proto_to_dict(experiment))

    @action(methods=["post"], detail=True)
    def launch(self, request: Request, experiment_id: str | None = None) -> Response:
        try:
            experiment = request.airavata_client.research.get_experiment(experiment_id)
            if experiment.enable_email_notification:
                del experiment.email_addresses[:]
                experiment.email_addresses.append(request.user.email)
            request.airavata_client.research.update_experiment(experiment_id, experiment)
            request.airavata_client.research.launch_experiment(experiment_id, settings.GATEWAY_ID)
            return Response({"success": True})
        except Exception as e:
            log.exception(f"Failed to launch experiment {experiment_id}", extra={"request": request})
            return Response({"success": False, "errorMessage": str(e)})

    @action(methods=["get"], detail=True)
    def jobs(self, request: Request, experiment_id: str | None = None) -> Response:
        jobs = request.airavata_client.research.get_job_details(experiment_id)
        return Response(proto_list_to_dicts(jobs))

    @action(methods=["post"], detail=True)
    def clone(self, request: Request, experiment_id: str | None = None) -> Response:
        cloned_experiment_id = request.airavata_client.research.clone_experiment(experiment_id)
        cloned_experiment = request.airavata_client.research.get_experiment(cloned_experiment_id)
        return Response(proto_to_dict(cloned_experiment))

    @action(methods=["post"], detail=True)
    def cancel(self, request: Request, experiment_id: str | None = None) -> Response:
        try:
            request.airavata_client.research.terminate_experiment(experiment_id, settings.GATEWAY_ID)
            return Response({"success": True})
        except Exception as e:
            log.exception("Cancel action has thrown the following error", extra={"request": request})
            raise e

    @action(methods=["post"], detail=True)
    def fetch_intermediate_outputs(self, request: Request, experiment_id: str | None = None) -> Response:
        if "outputNames" not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            request.airavata_client.research.get_intermediate_outputs(experiment_id, request.data["outputNames"])
            return Response({"success": True})
        except Exception as e:
            log.exception("fetchIntermediateOutputs failed with the following error", extra={"request": request})
            raise e

    @staticmethod
    def _update_workspace_preferences(
        request: Request, project_id: str, group_resource_profile_id: str, compute_resource_id: str
    ) -> None:
        prefs = helpers.WorkspacePreferencesHelper().get(request)
        prefs.most_recent_project_id = project_id
        prefs.most_recent_group_resource_profile_id = group_resource_profile_id
        prefs.most_recent_compute_resource_id = compute_resource_id
        prefs.save()


class ExperimentSearchViewSet(viewsets.ViewSet):
    def list(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.experiment.experiment_pb2 import (
            ExperimentSearchFields as ProtoSearchFields,
        )

        filters: dict[int, str] = {}
        for key, value in request.query_params.items():
            if key in ProtoSearchFields.keys():
                filters[ProtoSearchFields.Value(key)] = value

        limit = int(request.query_params.get("limit", "-1"))
        offset = int(request.query_params.get("offset", "0"))
        results = request.airavata_client.research.search_experiments(
            settings.GATEWAY_ID, request.user.username, filters, limit, offset
        )
        return Response(proto_list_to_dicts(results))


class FullExperimentViewSet(viewsets.ViewSet):
    lookup_field = "experiment_id"

    def retrieve(self, request: Request, experiment_id: str | None = None) -> Response:
        """Retrieve full experiment with resolved references."""
        from airavata_sdk.generated.org.apache.airavata.model.application.io.application_io_pb2 import (
            DataType as ProtoDataType,
        )

        experiment = request.airavata_client.research.get_experiment(experiment_id)

        # Collect output data products
        output_data_products = [
            request.airavata_client.research.get_data_product(output.value)
            for output in experiment.experiment_outputs
            if (
                output.value
                and output.value.startswith("airavata-dp")
                and output.type in (ProtoDataType.URI, ProtoDataType.STDOUT, ProtoDataType.STDERR)
            )
        ]
        output_data_products += [
            request.airavata_client.research.get_data_product(dp)
            for output in experiment.experiment_outputs
            if (output.value and output.type == ProtoDataType.URI_COLLECTION)
            for dp in output.value.split(",")
            if output.value.startswith("airavata-dp")
        ]

        # Load application interface
        app_interface_id = experiment.execution_id
        try:
            application_interface = request.airavata_client.research.get_application_interface(app_interface_id)
        except Exception as e:
            log.warning(f"Failed to load app interface: {e}")
            application_interface = None

        # Output views — output_views module still expects compat-style attribute names
        # (experimentOutputs, applicationModules, etc.) so we create a thin adapter
        exp_output_views = self._get_output_views(request, experiment, application_interface)

        # Collect input data products
        input_data_products = [
            request.airavata_client.research.get_data_product(inp.value)
            for inp in experiment.experiment_inputs
            if (
                inp.value
                and inp.value.startswith("airavata-dp")
                and inp.type in (ProtoDataType.URI, ProtoDataType.STDOUT, ProtoDataType.STDERR)
            )
        ]
        input_data_products += [
            request.airavata_client.research.get_data_product(dp)
            for inp in experiment.experiment_inputs
            if (inp.value and inp.type == ProtoDataType.URI_COLLECTION)
            for dp in inp.value.split(",")
            if inp.value.startswith("airavata-dp")
        ]

        # Load application module
        application_module = None
        try:
            if application_interface is not None:
                app_module_id = application_interface.application_modules[0]
                application_module = request.airavata_client.research.get_application_module(app_module_id)
            else:
                log.warning("Cannot load application model since app interface failed to load")
        except Exception:
            log.exception("Failed to load app interface/module", extra={"request": request})

        # Load compute resource
        compute_resource_id = None
        user_conf = experiment.user_configuration_data
        if user_conf and user_conf.computational_resource_scheduling:
            compute_resource_id = user_conf.computational_resource_scheduling.resource_host_id
        try:
            compute_resource = (
                request.airavata_client.compute.get_compute_resource(compute_resource_id)
                if compute_resource_id
                else None
            )
        except Exception:
            log.exception(f"Failed to load compute resource for {compute_resource_id}", extra={"request": request})
            compute_resource = None

        # Load project (user may only have access to experiment, not project)
        username = request.user.username
        gateway_id = settings.GATEWAY_ID
        if request.airavata_client.sharing.user_has_access(
            experiment.project_id, username + "@" + gateway_id, "READ"
        ):
            project = request.airavata_client.research.get_project(experiment.project_id)
        else:
            project = None

        # Load job details
        job_details = request.airavata_client.research.get_job_details(experiment_id)

        # Assemble response dict
        result = {
            "experiment_id": experiment_id,
            "experiment": proto_to_dict(experiment),
            "project": proto_to_dict(project),
            "output_data_products": proto_list_to_dicts(output_data_products),
            "input_data_products": proto_list_to_dicts(input_data_products),
            "application_module": proto_to_dict(application_module),
            "compute_resource": proto_to_dict(compute_resource),
            "job_details": proto_list_to_dicts(job_details),
            "output_views": exp_output_views,
        }
        return Response(result)

    @staticmethod
    def _get_output_views(request: Request, experiment: Any, application_interface: Any) -> dict[str, list[dict[str, Any]]]:
        """Adapter: output_views module expects compat-style camelCase attributes.

        Create a thin namespace that maps experimentOutputs -> experiment_outputs
        so the existing output_views.get_output_views function works with proto objects.
        """
        from types import SimpleNamespace

        # Wrap each output so output.type uses compat DataType values
        from django_airavata.proto_compat import DataType as CompatDataType
        from airavata_sdk.generated.org.apache.airavata.model.application.io.application_io_pb2 import (
            DataType as ProtoDataType,
        )

        # Build a proto->compat DataType mapping
        _type_map = {}
        for compat_name in CompatDataType.__members__:
            if hasattr(ProtoDataType, compat_name):
                _type_map[ProtoDataType.Value(compat_name)] = CompatDataType[compat_name]

        wrapped_outputs = []
        for output in experiment.experiment_outputs:
            ns = SimpleNamespace(
                name=output.name,
                value=output.value,
                type=_type_map.get(output.type, output.type),
                metaData=output.meta_data,
            )
            wrapped_outputs.append(ns)

        # Wrap experiment to expose experimentOutputs
        exp_ns = SimpleNamespace(experimentOutputs=wrapped_outputs)

        # Wrap application interface to expose applicationOutputs / applicationModules
        app_iface_ns = None
        if application_interface is not None:
            wrapped_app_outputs = [
                SimpleNamespace(name=o.name, metaData=o.meta_data, value=o.value, type=o.type)
                for o in application_interface.application_outputs
            ]
            app_iface_ns = SimpleNamespace(
                applicationOutputs=wrapped_app_outputs,
                applicationModules=list(application_interface.application_modules),
            )

        return output_views.get_output_views(request, exp_ns, app_iface_ns)


class ApplicationModuleViewSet(viewsets.ViewSet):
    lookup_field = "app_module_id"

    def list(self, request: Request) -> Response:
        modules = request.airavata_client.research.get_accessible_app_modules(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(modules))

    def retrieve(self, request: Request, app_module_id: str | None = None) -> Response:
        module = request.airavata_client.research.get_application_module(app_module_id)
        return Response(proto_to_dict(module))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment.app_deployment_pb2 import (
            ApplicationModule as AppModuleProto,
        )

        proto = dict_to_proto(request.data, AppModuleProto)
        app_module_id = request.airavata_client.research.register_application_module(settings.GATEWAY_ID, proto)
        proto.app_module_id = app_module_id
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, app_module_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment.app_deployment_pb2 import (
            ApplicationModule as AppModuleProto,
        )

        proto = dict_to_proto(request.data, AppModuleProto)
        proto.app_module_id = app_module_id
        request.airavata_client.research.update_application_module(app_module_id, proto)
        return Response(proto_to_dict(proto))

    def destroy(self, request: Request, app_module_id: str | None = None) -> Response:
        request.airavata_client.research.delete_application_module(app_module_id)
        return Response(status=204)

    @action(detail=True)
    def application_interface(self, request: Request, app_module_id: str) -> Response:
        all_app_interfaces = request.airavata_client.research.get_all_application_interfaces(settings.GATEWAY_ID)
        app_interfaces = [
            ai for ai in all_app_interfaces
            if ai.application_modules and app_module_id in ai.application_modules
        ]
        if len(app_interfaces) == 1:
            return Response(proto_to_dict(app_interfaces[0]))
        elif len(app_interfaces) > 1:
            log.error(
                f"More than one application interface found for module {app_module_id}: {app_interfaces}",
                extra={"request": request},
            )
            raise Exception(f"More than one application interface found for module {app_module_id}")
        else:
            raise Http404(f"No application interface found for module id {app_module_id}")

    @action(detail=True)
    def application_deployments(self, request: Request, app_module_id: str) -> Response:
        all_deployments = request.airavata_client.research.get_all_application_deployments(settings.GATEWAY_ID)
        app_deployments = [dep for dep in all_deployments if dep.app_module_id == app_module_id]
        return Response(proto_list_to_dicts(app_deployments))

    @action(methods=["post"], detail=True)
    def favorite(self, request: Request, app_module_id: str) -> HttpResponse:
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = workspace_preferences.applicationpreferences_set.get(application_id=app_module_id)
            application_preferences.favorite = True
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username, application_id=app_module_id, favorite=True
            )
        return HttpResponse(status=204)

    @action(methods=["post"], detail=True)
    def unfavorite(self, request: Request, app_module_id: str) -> HttpResponse:
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        try:
            application_preferences = workspace_preferences.applicationpreferences_set.get(application_id=app_module_id)
            application_preferences.favorite = False
            application_preferences.save()
        except ObjectDoesNotExist:
            workspace_preferences.applicationpreferences_set.create(
                username=request.user.username, application_id=app_module_id, favorite=False
            )
        return HttpResponse(status=204)

    @action(detail=False)
    def list_all(self, request: Request, format: str | None = None) -> Response:
        all_modules = request.airavata_client.research.get_all_app_modules(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(all_modules))


class ApplicationInterfaceViewSet(viewsets.ViewSet):
    lookup_field = "app_interface_id"

    def list(self, request: Request) -> Response:
        interfaces = request.airavata_client.research.get_all_application_interfaces(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(interfaces))

    def retrieve(self, request: Request, app_interface_id: str | None = None) -> Response:
        try:
            interface = request.airavata_client.research.get_application_interface(app_interface_id)
        except Exception:
            # If it failed to load, check to see if it exists at all
            all_interfaces = request.airavata_client.research.get_all_application_interfaces(settings.GATEWAY_ID)
            interface_ids = [i.application_interface_id for i in all_interfaces]
            if app_interface_id not in interface_ids:
                raise Http404("Application interface does not exist") from None
            else:
                raise  # re-raise
        return Response(proto_to_dict(interface))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appinterface.app_interface_pb2 import (
            ApplicationInterfaceDescription as AppInterfaceProto,
        )

        proto = dict_to_proto(request.data, AppInterfaceProto)
        self._update_input_metadata(proto)
        log.debug(f"application_interface: {proto}")
        app_interface_id = request.airavata_client.research.register_application_interface(
            settings.GATEWAY_ID, proto
        )
        proto.application_interface_id = app_interface_id
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, app_interface_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appinterface.app_interface_pb2 import (
            ApplicationInterfaceDescription as AppInterfaceProto,
        )

        proto = dict_to_proto(request.data, AppInterfaceProto)
        proto.application_interface_id = app_interface_id
        self._update_input_metadata(proto)
        request.airavata_client.research.update_application_interface(app_interface_id, proto)
        return Response(proto_to_dict(proto))

    def destroy(self, request: Request, app_interface_id: str | None = None) -> Response:
        request.airavata_client.research.delete_application_interface(app_interface_id)
        return Response(status=204)

    @staticmethod
    def _update_input_metadata(app_interface: Any) -> None:
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

    @action(detail=True)
    def compute_resources(self, request: Request, app_interface_id: str) -> Response:
        compute_resources = request.airavata_client.research.get_available_app_interface_compute_resources(
            app_interface_id
        )
        return Response(compute_resources)


class ApplicationDeploymentViewSet(viewsets.ViewSet):
    lookup_field = "app_deployment_id"

    def list(self, request: Request) -> Response:
        app_module_id = request.query_params.get("appModuleId", None)
        group_resource_profile_id = request.query_params.get("groupResourceProfileId", None)
        if (app_module_id and not group_resource_profile_id) or (not app_module_id and group_resource_profile_id):
            raise ParseError("Query params appModuleId and groupResourceProfileId are required together.")
        if app_module_id and group_resource_profile_id:
            deployments = request.airavata_client.research.get_application_deployments_for_app_module_and_group_resource_profile(
                app_module_id, group_resource_profile_id
            )
        else:
            deployments = request.airavata_client.research.get_accessible_application_deployments(
                settings.GATEWAY_ID
            )
        return Response(proto_list_to_dicts(deployments))

    def retrieve(self, request: Request, app_deployment_id: str | None = None) -> Response:
        deployment = request.airavata_client.research.get_application_deployment(app_deployment_id)
        return Response(proto_to_dict(deployment))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment.app_deployment_pb2 import (
            ApplicationDeploymentDescription as AppDeploymentProto,
        )

        proto = dict_to_proto(request.data, AppDeploymentProto)
        app_deployment_id = request.airavata_client.research.register_application_deployment(
            settings.GATEWAY_ID, proto
        )
        proto.app_deployment_id = app_deployment_id
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, app_deployment_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment.app_deployment_pb2 import (
            ApplicationDeploymentDescription as AppDeploymentProto,
        )

        proto = dict_to_proto(request.data, AppDeploymentProto)
        proto.app_deployment_id = app_deployment_id
        request.airavata_client.research.update_application_deployment(app_deployment_id, proto)
        return Response(proto_to_dict(proto))

    def destroy(self, request: Request, app_deployment_id: str | None = None) -> Response:
        request.airavata_client.research.delete_application_deployment(app_deployment_id)
        return Response(status=204)

    @action(detail=True)
    def queues(self, request: Request, app_deployment_id: str) -> Response:
        """Return queues for this deployment with defaults overridden by deployment defaults if they exist."""
        app_deployment = request.airavata_client.research.get_application_deployment(app_deployment_id)
        compute_resource = request.airavata_client.compute.get_compute_resource(app_deployment.compute_host_id)
        # Override defaults with app deployment default queue, if defined
        batch_queues = []
        for batch_queue in compute_resource.batch_queues:
            if app_deployment.default_queue_name:
                if app_deployment.default_queue_name == batch_queue.queue_name:
                    batch_queue.is_default_queue = True
                    batch_queue.default_node_count = app_deployment.default_node_count
                    batch_queue.default_cpu_count = app_deployment.default_cpu_count
                    batch_queue.default_walltime = app_deployment.default_walltime
                else:
                    batch_queue.is_default_queue = False
            batch_queues.append(batch_queue)
        return Response(proto_list_to_dicts(batch_queues))


class ComputeResourceViewSet(viewsets.ViewSet):
    lookup_field = "compute_resource_id"

    def list(self, request: Request) -> Response:
        all_names = request.airavata_client.compute.get_all_compute_resource_names()
        results = []
        for rid in all_names:
            proto = request.airavata_client.compute.get_compute_resource(rid)
            results.append(proto_to_dict(proto))
        return Response(results)

    def retrieve(self, request: Request, compute_resource_id: str | None = None) -> Response:
        proto = request.airavata_client.compute.get_compute_resource(compute_resource_id)
        return Response(proto_to_dict(proto))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource.compute_resource_pb2 import (
            ComputeResourceDescription as ComputeResourceDescriptionProto,
        )

        proto = dict_to_proto(request.data, ComputeResourceDescriptionProto)
        resource_id = request.airavata_client.compute.register_compute_resource(proto)
        proto.compute_resource_id = resource_id
        return Response(proto_to_dict(proto), status=status.HTTP_201_CREATED)

    def update(self, request: Request, compute_resource_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource.compute_resource_pb2 import (
            ComputeResourceDescription as ComputeResourceDescriptionProto,
        )

        proto = dict_to_proto(request.data, ComputeResourceDescriptionProto)
        proto.compute_resource_id = compute_resource_id
        request.airavata_client.compute.update_compute_resource(compute_resource_id, proto)
        updated = request.airavata_client.compute.get_compute_resource(compute_resource_id)
        return Response(proto_to_dict(updated))

    def destroy(self, request: Request, compute_resource_id: str | None = None) -> Response:
        request.airavata_client.compute.delete_compute_resource(compute_resource_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def all_names(self, request: Request, format: str | None = None) -> Response:
        """Return a map of compute resource names keyed by resource id."""
        return Response(request.airavata_client.compute.get_all_compute_resource_names())

    @action(detail=False)
    def all_names_list(self, request: Request, format: str | None = None) -> Response:
        """Return a list of compute resource names keyed by resource id."""
        all_names = request.airavata_client.compute.get_all_compute_resource_names()
        return Response(
            [
                {
                    "host_id": host_id,
                    "host": host,
                    "url": request.build_absolute_uri(
                        reverse("django_airavata_api:compute-resource-detail", args=[host_id])
                    ),
                }
                for host_id, host in all_names.items()
            ]
        )

    @action(detail=True)
    def queues(self, request: Request, compute_resource_id: str, format: str | None = None) -> Response:
        details = request.airavata_client.compute.get_compute_resource(compute_resource_id)
        data = proto_to_dict(details)
        return Response([queue["queue_name"] for queue in data.get("batch_queues", [])])


class LocalJobSubmissionView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        job_submission_id = request.query_params["id"]
        result = request.airavata_client.compute.get_local_job_submission(job_submission_id)
        return Response(proto_to_dict(result))


class CloudJobSubmissionView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        job_submission_id = request.query_params["id"]
        result = request.airavata_client.compute.get_cloud_job_submission(job_submission_id)
        return Response(proto_to_dict(result))


class GlobusJobSubmissionView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        job_submission_id = request.query_params["id"]
        try:
            result = request.airavata_client.compute.get_globus_job_submission(job_submission_id)
        except Exception:
            log.warning("get_globus_job_submission is not implemented on the server", exc_info=True)
            return Response(None)
        return Response(proto_to_dict(result))


class SshJobSubmissionView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        job_submission_id = request.query_params["id"]
        result = request.airavata_client.compute.get_ssh_job_submission(job_submission_id)
        return Response(proto_to_dict(result))


class UnicoreJobSubmissionView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        job_submission_id = request.query_params["id"]
        result = request.airavata_client.compute.get_unicore_job_submission(job_submission_id)
        return Response(proto_to_dict(result))


class GridFtpDataMovementView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        data_movement_id = request.query_params["id"]
        result = request.airavata_client.storage.get_grid_ftp_data_movement(data_movement_id)
        return Response(proto_to_dict(result))


class ScpDataMovementView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        data_movement_id = request.query_params["id"]
        result = request.airavata_client.storage.get_scp_data_movement(data_movement_id)
        return Response(proto_to_dict(result))


class UnicoreDataMovementView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        data_movement_id = request.query_params["id"]
        try:
            result = request.airavata_client.compute.get_unicore_data_movement(data_movement_id)
        except Exception:
            log.warning("get_unicore_data_movement is not implemented on the server", exc_info=True)
            return Response(None)
        return Response(proto_to_dict(result))


class LocalDataMovementView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        data_movement_id = request.query_params["id"]
        result = request.airavata_client.storage.get_local_data_movement(data_movement_id)
        return Response(proto_to_dict(result))


class DataProductView(APIView):
    permission_classes = [IsAuthenticated, DataProductSharedDirPermission]

    def get(self, request: Request, format: str | None = None) -> Response:
        data_product_uri = request.query_params["product-uri"]
        data_product = request.airavata_client.research.get_data_product(data_product_uri)
        return Response(proto_to_dict(data_product))

    def put(self, request: Request, format: str | None = None) -> Response:
        data_product_uri = request.query_params["product-uri"]
        data_product = request.airavata_client.research.get_data_product(data_product_uri)
        if request.data and "fileContentText" in request.data:
            user_storage.update_data_product_content(
                request=request, data_product=data_product, fileContentText=request.data["fileContentText"]
            )
            return self.get(request=request, format=format)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(http_method_names=["POST"])
def upload_input_file(request: Request) -> JsonResponse:
    try:
        input_file = request.FILES["file"]
        data_product = user_storage.save_input_file(request, input_file, content_type=input_file.content_type)
        return JsonResponse({"uploaded": True, "data-product": proto_to_dict(data_product)})
    except Exception as e:
        log.error("Failed to upload file", exc_info=True, extra={"request": request})
        resp = JsonResponse({"uploaded": False, "error": str(e)})
        resp.status_code = 500
        return resp


@api_view(http_method_names=["POST"])
def tus_upload_finish(request: Request) -> JsonResponse:
    uploadURL = request.POST["uploadURL"]

    def save_upload(file_path, file_name, file_type):
        with open(file_path, "rb") as uploaded_file:
            return user_storage.save_input_file(request, uploaded_file, name=file_name, content_type=file_type)

    try:
        data_product = tus.save_tus_upload(uploadURL, save_upload)
        return JsonResponse({"uploaded": True, "data-product": proto_to_dict(data_product)})
    except Exception as e:
        return exceptions.generic_json_exception_response(e, status=400)


@gzip_page
@api_view()
def download_file(request: Request) -> HttpResponse:
    # TODO: remove this deprecated view
    warnings.warn("download_file view has moved to SDK", DeprecationWarning, stacklevel=2)
    # redirect to /sdk/download
    data_product_uri = request.GET.get("data-product-uri", "")
    return redirect(user_storage.get_download_url(request, data_product_uri=data_product_uri))


@api_view(http_method_names=["DELETE"])
@permission_classes([IsAuthenticated, DataProductSharedDirPermission])
def delete_file(request: Request) -> HttpResponse:
    # TODO check that user has write access to this file using sharing API
    data_product_uri = request.GET.get("data-product-uri", "")
    data_product = None
    try:
        data_product = request.airavata_client.research.get_data_product(data_product_uri)
    except Exception as e:
        log.warning(f"Failed to load DataProduct for {data_product_uri}", exc_info=True)
        raise Http404("data product does not exist") from e
    try:
        if data_product.gateway_id != settings.GATEWAY_ID or data_product.owner_name != request.user.username:
            raise PermissionDenied()
        user_storage.delete(request, data_product)
        return HttpResponse(status=204)
    except ObjectDoesNotExist as e:
        raise Http404(str(e)) from e


class UserProfileViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.UserProfileSerializer

    def get_list(self) -> list[Any]:
        return self.request.airavata_client.iam.get_all_user_profiles_in_gateway(self.gateway_id, 0, -1)

    def get_instance(self, lookup_value: str) -> Any:
        return self.request.airavata_client.iam.get_user_profile_by_id(self.request.user.username, self.gateway_id)


class GroupResourceProfileViewSet(viewsets.ViewSet):
    lookup_field = "group_resource_profile_id"

    def list(self, request: Request) -> Response:
        results = request.airavata_client.compute.get_group_resource_list(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(results))

    def retrieve(self, request: Request, group_resource_profile_id: str | None = None) -> Response:
        result = request.airavata_client.compute.get_group_resource_profile(group_resource_profile_id)
        return Response(proto_to_dict(result))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.groupresourceprofile.group_resource_profile_pb2 import (
            GroupResourceProfile as GroupResourceProfileProto,
        )

        proto = dict_to_proto(request.data, GroupResourceProfileProto)
        proto.gateway_id = settings.GATEWAY_ID
        profile_id = request.airavata_client.compute.create_group_resource_profile(
            group_resource_profile=proto
        )
        created = request.airavata_client.compute.get_group_resource_profile(profile_id)
        return Response(proto_to_dict(created), status=status.HTTP_201_CREATED)

    def update(self, request: Request, group_resource_profile_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.groupresourceprofile.group_resource_profile_pb2 import (
            GroupResourceProfile as GroupResourceProfileProto,
        )

        # Fetch existing profile to handle removals
        existing = request.airavata_client.compute.get_group_resource_profile(group_resource_profile_id)
        existing_dict = proto_to_dict(existing)

        incoming_data = request.data

        # Detect removed compute preferences and remove them
        existing_pref_ids = {
            p.get("compute_resource_id") for p in existing_dict.get("compute_preferences", [])
        }
        incoming_pref_ids = {
            p.get("compute_resource_id") or p.get("computeResourceId")
            for p in incoming_data.get("compute_preferences", [])
        }
        for removed_id in existing_pref_ids - incoming_pref_ids:
            if removed_id:
                try:
                    request.airavata_client.compute.remove_group_compute_prefs(
                        removed_id, group_resource_profile_id
                    )
                except Exception:
                    log.warning("Failed to remove compute pref %s", removed_id, exc_info=True)

        # Detect removed compute resource policies and remove them
        existing_policy_ids = {
            p.get("resource_policy_id") for p in existing_dict.get("compute_resource_policies", [])
            if p.get("resource_policy_id")
        }
        incoming_policy_ids = {
            p.get("resource_policy_id") or p.get("resourcePolicyId")
            for p in incoming_data.get("compute_resource_policies", [])
            if p.get("resource_policy_id") or p.get("resourcePolicyId")
        }
        for removed_policy_id in existing_policy_ids - incoming_policy_ids:
            if removed_policy_id:
                try:
                    request.airavata_client.compute.remove_group_compute_resource_policy(removed_policy_id)
                except Exception:
                    log.warning("Failed to remove compute resource policy %s", removed_policy_id, exc_info=True)

        # Detect removed batch queue resource policies and remove them
        existing_bq_policy_ids = {
            p.get("resource_policy_id") for p in existing_dict.get("batch_queue_resource_policies", [])
            if p.get("resource_policy_id")
        }
        incoming_bq_policy_ids = {
            p.get("resource_policy_id") or p.get("resourcePolicyId")
            for p in incoming_data.get("batch_queue_resource_policies", [])
            if p.get("resource_policy_id") or p.get("resourcePolicyId")
        }
        for removed_bq_policy_id in existing_bq_policy_ids - incoming_bq_policy_ids:
            if removed_bq_policy_id:
                try:
                    request.airavata_client.compute.remove_group_batch_queue_resource_policy(removed_bq_policy_id)
                except Exception:
                    log.warning("Failed to remove batch queue resource policy %s", removed_bq_policy_id, exc_info=True)

        proto = dict_to_proto(incoming_data, GroupResourceProfileProto)
        proto.group_resource_profile_id = group_resource_profile_id
        proto.gateway_id = settings.GATEWAY_ID
        request.airavata_client.compute.update_group_resource_profile(proto)
        updated = request.airavata_client.compute.get_group_resource_profile(group_resource_profile_id)
        return Response(proto_to_dict(updated))

    def destroy(self, request: Request, group_resource_profile_id: str | None = None) -> Response:
        request.airavata_client.compute.remove_group_resource_profile(group_resource_profile_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SharedEntityViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.SharedEntitySerializer
    lookup_field = "entity_id"

    def get_instance(self, lookup_value: str) -> dict[str, Any]:
        users = {}
        # Only load *directly* granted permissions since these are the only
        # ones that can be edited
        # Load accessible users in order of permission precedence: users that
        # have WRITE permission should also have READ
        users.update(self._load_directly_accessible_users(lookup_value, ResourcePermissionType.READ))
        users.update(self._load_directly_accessible_users(lookup_value, ResourcePermissionType.WRITE))
        users.update(self._load_directly_accessible_users(lookup_value, ResourcePermissionType.MANAGE_SHARING))
        owner_ids = self._load_directly_accessible_users(lookup_value, ResourcePermissionType.OWNER)
        # Assume that there is one and only one DIRECT owner (there may be one
        # or more INDIRECT cascading owners, which would the owners of the
        # ancestor entities, but getAllDirectlyAccessibleUsers does not return
        # indirectly cascading owners)
        owner_id = list(owner_ids.keys())[0]
        # Remove owner from the users list
        del users[owner_id]
        user_list = []
        for user_id in users:
            user_list.append({"user": self._load_user_profile(user_id), "permissionType": users[user_id]})
        groups = {}
        groups.update(self._load_directly_accessible_groups(lookup_value, ResourcePermissionType.READ))
        groups.update(self._load_directly_accessible_groups(lookup_value, ResourcePermissionType.WRITE))
        groups.update(self._load_directly_accessible_groups(lookup_value, ResourcePermissionType.MANAGE_SHARING))
        group_list = []
        for group_id in groups:
            group_list.append({"group": self._load_group(group_id), "permissionType": groups[group_id]})
        return {
            "entityId": lookup_value,
            "userPermissions": user_list,
            "groupPermissions": group_list,
            "owner": self._load_user_profile(owner_id),
        }

    def _load_accessible_users(self, entity_id: str, permission_type: Any) -> dict[str, Any]:
        users = self.request.airavata_client.sharing.get_all_accessible_users(entity_id, permission_type)
        return {user_id: permission_type for user_id in users}

    def _load_directly_accessible_users(self, entity_id: str, permission_type: Any) -> dict[str, Any]:
        users = self.request.airavata_client.sharing.get_all_directly_accessible_users(entity_id, permission_type)
        return {user_id: permission_type for user_id in users}

    def _load_user_profile(self, user_id: str) -> Any:
        username = user_id[0 : user_id.rindex("@")]
        return self.request.airavata_client.iam.get_user_profile_by_id(username, settings.GATEWAY_ID)

    def _load_accessible_groups(self, entity_id: str, permission_type: Any) -> dict[str, Any]:
        groups = self.request.airavata_client.sharing.get_all_accessible_groups(entity_id, permission_type)
        return {group_id: permission_type for group_id in groups}

    def _load_directly_accessible_groups(self, entity_id: str, permission_type: Any) -> dict[str, Any]:
        groups = self.request.airavata_client.sharing.get_all_directly_accessible_groups(entity_id, permission_type)
        return {group_id: permission_type for group_id in groups}

    def _load_group(self, group_id: str) -> Any:
        return self.request.airavata_client.sharing.get_group(group_id)

    def perform_update(self, serializer: Any) -> None:
        shared_entity = serializer.save()
        entity_id = shared_entity["entityId"]
        if len(shared_entity["_user_grant_read_permission"]) > 0:
            self._share_with_users(entity_id, ResourcePermissionType.READ, shared_entity["_user_grant_read_permission"])
        if len(shared_entity["_user_grant_write_permission"]) > 0:
            self._share_with_users(
                entity_id, ResourcePermissionType.WRITE, shared_entity["_user_grant_write_permission"]
            )
        if len(shared_entity["_user_grant_manage_sharing_permission"]) > 0:
            self._share_with_users(
                entity_id, ResourcePermissionType.MANAGE_SHARING, shared_entity["_user_grant_manage_sharing_permission"]
            )
        if len(shared_entity["_user_revoke_read_permission"]) > 0:
            self._revoke_from_users(
                entity_id, ResourcePermissionType.READ, shared_entity["_user_revoke_read_permission"]
            )
        if len(shared_entity["_user_revoke_write_permission"]) > 0:
            self._revoke_from_users(
                entity_id, ResourcePermissionType.WRITE, shared_entity["_user_revoke_write_permission"]
            )
        if len(shared_entity["_user_revoke_manage_sharing_permission"]) > 0:
            self._revoke_from_users(
                entity_id,
                ResourcePermissionType.MANAGE_SHARING,
                shared_entity["_user_revoke_manage_sharing_permission"],
            )
        if len(shared_entity["_group_grant_read_permission"]) > 0:
            self._share_with_groups(
                entity_id, ResourcePermissionType.READ, shared_entity["_group_grant_read_permission"]
            )
        if len(shared_entity["_group_grant_write_permission"]) > 0:
            self._share_with_groups(
                entity_id, ResourcePermissionType.WRITE, shared_entity["_group_grant_write_permission"]
            )
        if len(shared_entity["_group_grant_manage_sharing_permission"]) > 0:
            self._share_with_groups(
                entity_id,
                ResourcePermissionType.MANAGE_SHARING,
                shared_entity["_group_grant_manage_sharing_permission"],
            )
        if len(shared_entity["_group_revoke_read_permission"]) > 0:
            self._revoke_from_groups(
                entity_id, ResourcePermissionType.READ, shared_entity["_group_revoke_read_permission"]
            )
        if len(shared_entity["_group_revoke_write_permission"]) > 0:
            self._revoke_from_groups(
                entity_id, ResourcePermissionType.WRITE, shared_entity["_group_revoke_write_permission"]
            )
        if len(shared_entity["_group_revoke_manage_sharing_permission"]) > 0:
            self._revoke_from_groups(
                entity_id,
                ResourcePermissionType.MANAGE_SHARING,
                shared_entity["_group_revoke_manage_sharing_permission"],
            )

    def _share_with_users(self, entity_id: str, permission_type: Any, user_ids: list[str]) -> None:
        self.request.airavata_client.sharing.share_resource_with_users(
            entity_id, {user_id: permission_type for user_id in user_ids}
        )

    def _revoke_from_users(self, entity_id: str, permission_type: Any, user_ids: list[str]) -> None:
        self.request.airavata_client.sharing.revoke_sharing_of_resource_from_users(
            entity_id, {user_id: permission_type for user_id in user_ids}
        )

    def _share_with_groups(self, entity_id: str, permission_type: Any, group_ids: list[str]) -> None:
        self.request.airavata_client.sharing.share_resource_with_groups(
            entity_id, {group_id: permission_type for group_id in group_ids}
        )

    def _revoke_from_groups(self, entity_id: str, permission_type: Any, group_ids: list[str]) -> None:
        self.request.airavata_client.sharing.revoke_sharing_of_resource_from_groups(
            entity_id, {group_id: permission_type for group_id in group_ids}
        )

    @action(methods=["put"], detail=True)
    def merge(self, request: Request, entity_id: str | None = None) -> Response:
        # Validate updated sharing settings
        updated = self.get_serializer(data=request.data)
        updated.is_valid(raise_exception=True)
        # Get the existing sharing settings and merge in the updated settings
        existing_instance = self.get_object()
        existing = self.get_serializer(instance=existing_instance)
        merged_data = existing.data
        merged_data["userPermissions"] = existing.data["userPermissions"] + updated.initial_data["userPermissions"]
        merged_data["groupPermissions"] = existing.data["groupPermissions"] + updated.initial_data["groupPermissions"]
        # Create a merged_serializer from the existing sharing settings and the
        # merged settings. This will calculate all permissions that need to be
        # granted and revoked to go from the exisitng settings to the merged
        # settings.
        merged_serializer = self.get_serializer(existing_instance, data=merged_data)
        merged_serializer.is_valid(raise_exception=True)
        self.perform_update(merged_serializer)
        return Response(merged_serializer.data)

    @action(methods=["get"], detail=True)
    def all(self, request: Request, entity_id: str | None = None) -> Response:
        """Load direct plus indirectly (inherited) shared permissions."""
        assert entity_id is not None, "entity_id is required"
        users = {}
        # Load accessible users in order of permission precedence: users that
        # have WRITE permission should also have READ
        users.update(self._load_accessible_users(entity_id, ResourcePermissionType.READ))
        users.update(self._load_accessible_users(entity_id, ResourcePermissionType.WRITE))
        users.update(self._load_accessible_users(entity_id, ResourcePermissionType.MANAGE_SHARING))
        owner_ids = self._load_accessible_users(entity_id, ResourcePermissionType.OWNER)
        # Assume that there is one and only one DIRECT owner (there may be one
        # or more INDIRECT cascading owners, which would the owners of the
        # ancestor entities, but getAllAccessibleUsers does not return
        # indirectly cascading owners)
        owner_id = list(owner_ids.keys())[0]
        # Remove owner from the users list
        del users[owner_id]
        user_list = []
        for user_id in users:
            user_list.append({"user": self._load_user_profile(user_id), "permissionType": users[user_id]})
        groups = {}
        groups.update(self._load_accessible_groups(entity_id, ResourcePermissionType.READ))
        groups.update(self._load_accessible_groups(entity_id, ResourcePermissionType.WRITE))
        groups.update(self._load_accessible_groups(entity_id, ResourcePermissionType.MANAGE_SHARING))
        group_list = []
        for group_id in groups:
            group_list.append({"group": self._load_group(group_id), "permissionType": groups[group_id]})
        shared_entity = {
            "entityId": entity_id,
            "userPermissions": user_list,
            "groupPermissions": group_list,
            "owner": self._load_user_profile(owner_id),
        }
        serializer = self.serializer_class(shared_entity, context={"request": request})
        return Response(serializer.data)


class CredentialSummaryViewSet(APIBackedViewSet):
    serializer_class = serializers.CredentialSummarySerializer

    def get_list(self) -> list[Any]:
        ssh_creds = self.request.airavata_client.credential.get_all_credential_summaries(self.gateway_id, SummaryType.SSH)
        pwd_creds = self.request.airavata_client.credential.get_all_credential_summaries(self.gateway_id, SummaryType.PASSWD)
        return ssh_creds + pwd_creds

    def get_instance(self, lookup_value: str) -> Any:
        return self.request.airavata_client.credential.get_credential_summary(lookup_value, self.gateway_id)

    @action(detail=False)
    def ssh(self, request: Request) -> Response:
        summaries = self.request.airavata_client.credential.get_all_credential_summaries(self.gateway_id, SummaryType.SSH)
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def password(self, request: Request) -> Response:
        summaries = self.request.airavata_client.credential.get_all_credential_summaries(self.gateway_id, SummaryType.PASSWD)
        serializer = self.get_serializer(summaries, many=True)
        return Response(serializer.data)

    @action(methods=["post"], detail=False)
    def create_ssh(self, request: Request) -> Response:
        if "description" not in request.data:
            raise ParseError("'description' is required in request")
        description = request.data.get("description")
        token_id = self.request.airavata_client.credential.generate_and_register_ssh_keys(
            self.gateway_id, self.username, description
        )
        credential_summary = self.request.airavata_client.credential.get_credential_summary(token_id, self.gateway_id)
        serializer = self.get_serializer(credential_summary)
        return Response(serializer.data)

    @action(methods=["post"], detail=False)
    def create_password(self, request: Request) -> Response:
        if "username" not in request.data or "password" not in request.data or "description" not in request.data:
            raise ParseError("'username', 'password' and 'description' are all required in request")
        username = request.data.get("username")
        password = request.data.get("password")
        description = request.data.get("description")
        from airavata_sdk.generated.org.apache.airavata.model.credential.store.credential_store_pb2 import (
            PasswordCredential,
        )

        pwd_cred = PasswordCredential(
            portal_user_name=username,
            login_user_name=username,
            password=password,
            description=description,
            gateway_id=self.gateway_id,
        )
        token_id = self.request.airavata_client.credential.register_pwd_credential(self.gateway_id, pwd_cred)
        credential_summary = self.request.airavata_client.credential.get_credential_summary(token_id, self.gateway_id)
        serializer = self.get_serializer(credential_summary)
        return Response(serializer.data)

    def perform_destroy(self, instance: Any) -> None:
        if instance.type == SummaryType.SSH:
            self.request.airavata_client.credential.delete_ssh_pub_key(instance.token, self.gateway_id)
        elif instance.type == SummaryType.PASSWD:
            self.request.airavata_client.credential.delete_pwd_credential(instance.token, self.gateway_id)


class CurrentGatewayResourceProfile(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        gateway_resource_profile = request.airavata_client.compute.get_gateway_resource_profile(settings.GATEWAY_ID)
        return Response(proto_to_dict(gateway_resource_profile))

    def put(self, request: Request, format: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.gatewayprofile.gateway_resource_profile_pb2 import (
            GatewayResourceProfile as GatewayResourceProfileProto,
        )

        proto = dict_to_proto(request.data, GatewayResourceProfileProto)
        request.airavata_client.compute.update_gateway_resource_profile(settings.GATEWAY_ID, proto)
        updated = request.airavata_client.compute.get_gateway_resource_profile(settings.GATEWAY_ID)
        return Response(proto_to_dict(updated))


class ExperimentArchiveView(APIView):
    def get(self, request: Request, experiment_id: str | None = None, format: str | None = None) -> Response:
        experiment = request.airavata_client.research.get_experiment(experiment_id)
        result = dict(
            archived=False,
            archive_name=None,
            created_date=None,
            max_age=settings.GATEWAY_USER_DATA_ARCHIVE_MAX_AGE_DAYS,
        )
        try:
            archive_entry = UserDataArchiveEntry.objects.get(
                entry_path=experiment.user_configuration_data.experiment_data_dir,
                user_data_archive__rolled_back=False,
            )
            result["archived"] = True
            result["archive_name"] = archive_entry.user_data_archive.archive_name
            result["created_date"] = archive_entry.user_data_archive.created_date
        except UserDataArchiveEntry.DoesNotExist:
            pass
        return Response(result, status=status.HTTP_200_OK)


class StorageResourceViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.StorageResourceSerializer
    lookup_field = "storage_resource_id"

    def get_instance(self, lookup_value: str, format: str | None = None) -> Any:
        from django_airavata.proto_compat import StorageResourceDescription as StorageCompat

        proto = self.request.airavata_client.storage.get_storage_resource(lookup_value)
        return StorageCompat(
            storageResourceId=proto.storage_resource_id,
            hostName=proto.host_name,
            storageResourceDescription=proto.storage_resource_description,
            enabled=proto.enabled,
            creationTime=proto.creation_time if proto.creation_time else None,
            updateTime=proto.update_time if proto.update_time else None,
        )

    def perform_create(self, serializer):
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.storageresource.storage_resource_pb2 import (
            StorageResourceDescription as StorageResourceDescriptionProto,
        )

        compat_obj = serializer.save()
        proto_obj = StorageResourceDescriptionProto(
            host_name=getattr(compat_obj, "hostName", ""),
            storage_resource_description=getattr(compat_obj, "storageResourceDescription", ""),
            enabled=getattr(compat_obj, "enabled", True),
        )
        resource_id = self.request.airavata_client.storage.register_storage_resource(proto_obj)
        compat_obj.storageResourceId = resource_id

    def perform_update(self, serializer):
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.storageresource.storage_resource_pb2 import (
            StorageResourceDescription as StorageResourceDescriptionProto,
        )

        compat_obj = serializer.save()
        resource_id = getattr(compat_obj, "storageResourceId", "")
        proto_obj = StorageResourceDescriptionProto(
            storage_resource_id=resource_id,
            host_name=getattr(compat_obj, "hostName", ""),
            storage_resource_description=getattr(compat_obj, "storageResourceDescription", ""),
            enabled=getattr(compat_obj, "enabled", True),
        )
        self.request.airavata_client.storage.update_storage_resource(resource_id, proto_obj)

    def perform_destroy(self, instance):
        self.request.airavata_client.storage.delete_storage_resource(instance.storageResourceId)

    @action(detail=False)
    def all_names(self, request: Request, format: str | None = None) -> Response:
        """Return a map of compute resource names keyed by resource id."""
        return Response(request.airavata_client.storage.get_all_storage_resource_names())


class StoragePreferenceViewSet(viewsets.ViewSet):
    lookup_field = "storage_resource_id"

    def list(self, request: Request) -> Response:
        results = request.airavata_client.compute.get_all_gateway_storage_preferences(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(results))

    def retrieve(self, request: Request, storage_resource_id: str | None = None) -> Response:
        result = request.airavata_client.compute.get_gateway_storage_preference(settings.GATEWAY_ID, storage_resource_id)
        return Response(proto_to_dict(result))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.gatewayprofile.gateway_resource_profile_pb2 import (
            StoragePreference as StoragePreferenceProto,
        )

        proto = dict_to_proto(request.data, StoragePreferenceProto)
        request.airavata_client.compute.add_gateway_storage_preference(
            settings.GATEWAY_ID, proto.storage_resource_id, proto
        )
        return Response(proto_to_dict(proto), status=status.HTTP_201_CREATED)

    def update(self, request: Request, storage_resource_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.gatewayprofile.gateway_resource_profile_pb2 import (
            StoragePreference as StoragePreferenceProto,
        )

        proto = dict_to_proto(request.data, StoragePreferenceProto)
        proto.storage_resource_id = storage_resource_id
        request.airavata_client.compute.update_gateway_storage_preference(
            settings.GATEWAY_ID, storage_resource_id, proto
        )
        updated = request.airavata_client.compute.get_gateway_storage_preference(settings.GATEWAY_ID, storage_resource_id)
        return Response(proto_to_dict(updated))

    def destroy(self, request: Request, storage_resource_id: str | None = None) -> Response:
        request.airavata_client.compute.delete_gateway_storage_preference(
            settings.GATEWAY_ID, storage_resource_id
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParserViewSet(viewsets.ViewSet):
    lookup_field = "parser_id"

    def list(self, request: Request) -> Response:
        parsers = request.airavata_client.research.list_all_parsers(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(parsers))

    def retrieve(self, request: Request, parser_id: str | None = None) -> Response:
        parser = request.airavata_client.research.get_parser(parser_id, settings.GATEWAY_ID)
        return Response(proto_to_dict(parser))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.parser.parser_pb2 import (
            Parser as ParserProto,
        )

        proto = dict_to_proto(request.data, ParserProto)
        parser_id = request.airavata_client.research.save_parser(proto)
        proto.id = parser_id
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, parser_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.parser.parser_pb2 import (
            Parser as ParserProto,
        )

        proto = dict_to_proto(request.data, ParserProto)
        proto.id = parser_id
        request.airavata_client.research.save_parser(proto)
        return Response(proto_to_dict(proto))


class UserStoragePathView(APIView):
    serializer_class = serializers.UserStoragePathSerializer
    permission_classes = (IsAuthenticated, UserStorageSharedDirPermission)

    def get(self, request: Request, path: str = "/", format: str | None = None) -> Response:
        # AIRAVATA-3460 Allow passing path as a query parameter instead
        path = request.query_params.get("path", path)
        experiment_id = request.query_params.get("experiment-id")
        return self._create_response(request, path, experiment_id=experiment_id)

    def post(
        self, request: Request, path: str = "/", format: str | None = None, file_name: str | None = None
    ) -> Response:
        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        if not user_storage.dir_exists(request, path, experiment_id=experiment_id):
            _, resource_path = user_storage.create_user_dir(request, path, experiment_id=experiment_id)
            # create_user_dir may create the directory with a different name
            # than requested, for example, converting spaces to underscores, so
            # use as the path the path that is returned by create_user_dir
            path = resource_path

        data_product = None
        # Handle direct upload
        if "file" in request.FILES:
            user_file = request.FILES["file"]
            data_product = user_storage.save(
                request, path, user_file, content_type=user_file.content_type, experiment_id=experiment_id
            )
        # Handle a tus upload
        elif "uploadURL" in request.POST:
            uploadURL = request.POST["uploadURL"]

            def save_file(file_path, file_name, file_type):
                with open(file_path, "rb") as uploaded_file:
                    return user_storage.save(
                        request,
                        path,
                        uploaded_file,
                        name=file_name,
                        content_type=file_type,
                        experiment_id=experiment_id,
                    )

            data_product = tus.save_tus_upload(uploadURL, save_file)
        return self._create_response(request, path, uploaded=data_product, experiment_id=experiment_id)

    # Accept wither to replace file or to replace file content text.
    def put(self, request: Request, path: str = "/", format: str | None = None) -> Response:
        path = request.POST.get("path", path)
        # Replace the file if the request has a file upload.
        if "file" in request.FILES:
            self.delete(request=request, path=path, format=format)
            dir_path, file_name = os.path.split(path)
            self.post(request=request, path=dir_path, format=format, file_name=file_name)
        # Replace only the file content if the request body has the `fileContentText`
        elif request.data and "fileContentText" in request.data:
            user_storage.update_file_content(
                request=request, path=path, fileContentText=request.data["fileContentText"]
            )
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return self._create_response(request=request, path=path)

    def delete(self, request: Request, path: str = "/", format: str | None = None) -> Response:
        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        if user_storage.dir_exists(request, path, experiment_id=experiment_id):
            user_storage.delete_dir(request, path, experiment_id=experiment_id)
        else:
            user_storage.delete_user_file(request, path, experiment_id=experiment_id)

        return Response(status=204)

    def _create_response(
        self, request: Request, path: str, uploaded: Any = None, experiment_id: str | None = None
    ) -> Response:
        if user_storage.dir_exists(request, path, experiment_id=experiment_id):
            directories, files = user_storage.listdir(request, path, experiment_id=experiment_id)
            data: dict[str, Any] = {"isDir": True, "directories": directories, "files": files}
            if uploaded is not None:
                data["uploaded"] = uploaded
            data["parts"] = self._split_path(path)
            data["path"] = path
            serializer = self.serializer_class(data, context={"request": request})
            return Response(serializer.data)
        else:
            file = user_storage.get_file_metadata(request, path, experiment_id=experiment_id)
            data: dict[str, Any] = {"isDir": False, "directories": [], "files": [file]}
            if uploaded is not None:
                data["uploaded"] = uploaded
            data["parts"] = self._split_path(path)
            serializer = self.serializer_class(data, context={"request": request})
            return Response(serializer.data)

    def _split_path(self, path: str) -> list[str]:
        head, tail = os.path.split(path)
        if head != path:
            return self._split_path(head) + [tail]
        elif tail != "":
            return [tail]
        else:
            return []


class ExperimentStoragePathView(APIView):
    serializer_class = serializers.ExperimentStoragePathSerializer

    def get(
        self, request: Request, experiment_id: str | None = None, path: str = "", format: str | None = None
    ) -> Response:
        assert experiment_id is not None, "experiment_id is required"
        return self._create_response(request, experiment_id, path)

    def _create_response(self, request: Request, experiment_id: str, path: str) -> Response:
        if user_storage.experiment_dir_exists(request, experiment_id, path):
            directories, files = user_storage.list_experiment_dir(request, experiment_id, path)

            def add_expid(d):
                d["experiment_id"] = experiment_id
                return d

            data: dict[str, Any] = {
                "isDir": True,
                "directories": map(add_expid, directories),
                "files": map(add_expid, files),
            }
            data["parts"] = self._split_path(path)
            serializer = self.serializer_class(data, context={"request": request})
            return Response(serializer.data)
        else:
            raise Http404(f"Path '{path}' does not exist for {experiment_id}")

    def _split_path(self, path: str) -> list[str]:
        head, tail = os.path.split(path)
        if head != "":
            return self._split_path(head) + [tail]
        elif tail != "":
            return [tail]
        else:
            return []


class WorkspacePreferencesView(APIView):
    serializer_class = serializers.WorkspacePreferencesSerializer

    def get(self, request: Request, format: str | None = None) -> Response:
        helper = helpers.WorkspacePreferencesHelper()
        workspace_preferences = helper.get(request)
        serializer = self.serializer_class(workspace_preferences, context={"request": request})
        return Response(serializer.data)


class ManageNotificationViewSet(viewsets.ViewSet):
    lookup_field = "notification_id"

    def list(self, request: Request) -> Response:
        notifications = request.airavata_client.research.get_all_notifications(settings.GATEWAY_ID)
        return Response(proto_list_to_dicts(notifications))

    def retrieve(self, request: Request, notification_id: str | None = None) -> Response:
        notification = request.airavata_client.research.get_notification(settings.GATEWAY_ID, notification_id)
        return Response(proto_to_dict(notification))

    def create(self, request: Request) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
            Notification as NotificationProto,
        )

        proto = dict_to_proto(request.data, NotificationProto)
        proto.gateway_id = settings.GATEWAY_ID
        notification_id = request.airavata_client.research.create_notification(proto)
        proto.notification_id = notification_id
        self._update_notification_extension(request, notification_id)
        return Response(proto_to_dict(proto), status=201)

    def update(self, request: Request, notification_id: str | None = None) -> Response:
        from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
            Notification as NotificationProto,
        )

        proto = dict_to_proto(request.data, NotificationProto)
        proto.notification_id = notification_id
        request.airavata_client.research.update_notification(proto)
        self._update_notification_extension(request, notification_id)
        return Response(proto_to_dict(proto))

    def destroy(self, request: Request, notification_id: str | None = None) -> Response:
        request.airavata_client.research.delete_notification(settings.GATEWAY_ID, notification_id)
        return Response(status=204)

    @staticmethod
    def _update_notification_extension(request: Request, notification_id: str) -> None:
        """Persist the showInDashboard extension in the Django model."""
        if "showInDashboard" in request.data:
            existing_entries = models.NotificationExtension.objects.filter(notification_id=notification_id)
            if existing_entries.exists():
                existing_entries.update(showInDashboard=request.data["showInDashboard"])
            else:
                models.NotificationExtension.objects.create(
                    notification_id=notification_id, showInDashboard=request.data["showInDashboard"]
                )


class AckNotificationViewSet(APIView):
    def get(self, request: Request, format: str | None = None) -> HttpResponse:
        if "id" in request.GET:
            notification_id = request.GET["id"]
            try:
                notification = models.User_Notifications.objects.get(
                    notification_id=notification_id, username=request.user.username
                )
                notification.is_read = True
                notification.save()
            except ObjectDoesNotExist:
                models.User_Notifications.objects.create(
                    username=request.user.username, notification_id=notification.notificationId
                )
        return HttpResponse(status=204)


class IAMUserViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericAPIBackedViewSet,
):
    serializer_class = serializers.IAMUserProfile
    pagination_class = APIResultPagination
    permission_classes = (
        IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    def get_list(self) -> APIResultIterator:
        search = self.request.GET.get("search", None)

        convert_user_profile = self._convert_user_profile

        class IAMUsersResultIterator(APIResultIterator):
            def get_results(self, limit: int = -1, offset: int = 0) -> Any:
                return map(convert_user_profile, iam_admin_client.get_users(offset, limit, search))

        return IAMUsersResultIterator(query_params=self.request.query_params.copy())

    def get_instance(self, lookup_value: str) -> dict[str, Any]:
        return self._convert_user_profile(iam_admin_client.get_user(lookup_value))

    def perform_update(self, serializer: Any) -> None:
        managed_user_profile = serializer.save()
        sharing_client = self.request.airavata_client.sharing
        iam_client = self.request.airavata_client.iam
        user_id = managed_user_profile["airavataInternalUserId"]
        added_groups = []
        for group_id in managed_user_profile["_added_group_ids"]:
            group = sharing_client.get_group(group_id)
            sharing_client.add_users_to_group([user_id], group_id)
            added_groups.append(group)
        if len(added_groups) > 0:
            user_profile = iam_client.get_user_profile_by_id(managed_user_profile["userId"], settings.GATEWAY_ID)
            signals.user_added_to_group.send(
                sender=self.__class__, user=user_profile, groups=added_groups, request=self.request
            )
        for group_id in managed_user_profile["_removed_group_ids"]:
            sharing_client.remove_users_from_group([user_id], group_id)

    def perform_destroy(self, instance: dict[str, Any]) -> None:
        iam_admin_client.delete_user(instance["userId"])

    @action(methods=["post"], detail=True)
    def enable(self, request: Request, user_id: str | None = None) -> Response:
        assert user_id is not None, "user_id is required"
        iam_admin_client.enable_user(user_id)
        instance = self.get_instance(user_id)
        serializer = self.serializer_class(instance=instance, context={"request": request})
        return Response(serializer.data)

    @action(methods=["put"], detail=False)
    def update_username(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_username = serializer.validated_data["userId"]
        new_username = serializer.validated_data["newUsername"]
        iam_admin_client.update_username(old_username, new_username)
        # set username_initialized to True so it is treated as valid.
        django_user = get_user_model().objects.get(username=old_username)
        django_user.user_profile.username_initialized = True
        django_user.user_profile.save()
        # Not strictly necessary since next time the user logs in, the Django
        # user record for the user will get updated to have the new username.
        # But this is done to keep it consistent.
        django_user.username = new_username
        django_user.save()
        instance = self.get_instance(new_username)
        serializer = self.serializer_class(instance=instance, context={"request": request})
        return Response(serializer.data)

    def _convert_user_profile(self, user_profile: Any) -> dict[str, Any]:
        iam_client = self.request.airavata_client.iam
        sharing_client = self.request.airavata_client.sharing
        airavata_user_profile_exists = iam_client.does_user_exist(user_profile.userId, self.gateway_id)
        groups = []
        if airavata_user_profile_exists:
            groups = sharing_client.get_all_groups_user_belongs(user_profile.airavataInternalUserId)
        return {
            "airavataInternalUserId": user_profile.airavataInternalUserId,
            "userId": user_profile.userId,
            "gatewayId": user_profile.gatewayId,
            "email": user_profile.emails[0],
            "firstName": user_profile.firstName,
            "lastName": user_profile.lastName,
            "enabled": user_profile.State == Status.ACTIVE,
            "emailVerified": (user_profile.State == Status.CONFIRMED or user_profile.State == Status.ACTIVE),
            "airavataUserProfileExists": airavata_user_profile_exists,
            "creationTime": user_profile.creationTime,
            "groups": groups,
        }


class ExperimentStatisticsView(APIView):
    # TODO: restrict to only Admins or Read Only Admins group members

    def get(self, request: Request, format: str | None = None) -> Response:
        if "fromTime" in request.GET:
            from_time = view_utils.convert_utc_iso8601_to_date(request.GET["fromTime"]).timestamp() * 1000
        else:
            from_time = (datetime.utcnow() - timedelta(days=7)).timestamp() * 1000
        from_time = int(from_time)
        if "toTime" in request.GET:
            to_time = view_utils.convert_utc_iso8601_to_date(request.GET["toTime"]).timestamp() * 1000
        else:
            to_time = datetime.utcnow().timestamp() * 1000
        to_time = int(to_time)
        username = request.GET.get("userName", None)
        application_name = request.GET.get("applicationName", None)
        resource_hostname = request.GET.get("resourceHostName", None)
        limit = int(request.GET.get("limit", "50"))
        offset = int(request.GET.get("offset", "0"))

        statistics = request.airavata_client.research.get_experiment_statistics(
            settings.GATEWAY_ID, from_time, to_time, username, application_name, resource_hostname, limit, offset
        )
        stats_dict = proto_to_dict(statistics)

        paginator = pagination.LimitOffsetPagination()
        paginator.count = statistics.all_experiment_count
        paginator.limit = limit
        paginator.offset = offset
        paginator.request = request
        response = paginator.get_paginated_response(stats_dict)
        response.data["limit"] = limit
        response.data["offset"] = offset
        return response


class UnverifiedEmailUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.UnverifiedEmailUserProfile
    pagination_class = APIResultPagination
    permission_classes = (
        IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    def get_list(self) -> APIResultIterator:
        get_users = self._get_unverified_email_user_profiles

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            def get_results(self, limit: int = -1, offset: int = 0) -> list[dict[str, Any]]:
                return get_users(limit, offset)

        return UnverifiedEmailUsersResultIterator()

    def get_instance(self, lookup_value: str) -> dict[str, Any]:
        users = self._get_unverified_email_user_profiles(limit=1, username=lookup_value)
        if len(users) == 0:
            raise Http404(f"No unverified email record found for user {lookup_value}")
        else:
            return users[0]

    def _get_unverified_email_user_profiles(
        self, limit: int = -1, offset: int = 0, username: str | None = None
    ) -> list[dict[str, Any]]:
        unverified_emails = (
            EmailVerification.objects.filter(verified=False).order_by("username").values("username").distinct()
        )
        if username is not None:
            unverified_emails = unverified_emails.filter(username=username)
        if limit > 0:
            unverified_emails = unverified_emails[offset : offset + limit]
        results = []
        for unverified_email in unverified_emails:
            unverified_username = unverified_email["username"]
            if iam_admin_client.is_user_exist(unverified_username):
                user_profile = iam_admin_client.get_user(unverified_username)
                if user_profile.State == Status.CONFIRMED or user_profile.State == Status.ACTIVE:
                    # TODO: test this
                    EmailVerification.objects.filter(username=unverified_username).update(verified=True)
                    continue
                results.append(
                    {
                        "userId": user_profile.userId,
                        "gatewayId": user_profile.gatewayId,
                        "email": user_profile.emails[0],
                        "firstName": user_profile.firstName,
                        "lastName": user_profile.lastName,
                        "enabled": user_profile.State == Status.ACTIVE,
                        "emailVerified": (
                            user_profile.State == Status.CONFIRMED or user_profile.State == Status.ACTIVE
                        ),
                        "creationTime": user_profile.creationTime,
                    }
                )
            else:
                # Delete the EmailVerification records since that user no
                # longer exists in the IAM service
                EmailVerification.objects.filter(username=unverified_username).delete()
        return results


class LogRecordConsumer(APIView):
    serializer_class = serializers.LogRecordSerializer

    def post(self, request: Request, format: str | None = None) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        log_record = serializer.validated_data
        log_level = getattr(logging, log_record["level"], None)
        if log_level is not None:
            stacktrace = "".join(map(lambda a: "\n    " + a, log_record["stacktrace"]))
            log.log(
                log_level,
                "Frontend error: {}: {}\nstacktrace: {}".format(
                    log_record["message"], json.dumps(log_record["details"], indent=4), stacktrace
                ),
                extra={"request": request},
            )
        return Response(serializer.data)


class SettingsAPIView(APIView):
    serializer_class = serializers.SettingsSerializer

    def get(self, request: Request, format: str | None = None) -> Response:
        data = {
            "fileUploadMaxFileSize": settings.FILE_UPLOAD_MAX_FILE_SIZE,
            "tusEndpoint": settings.TUS_ENDPOINT,
            "pgaUrl": settings.PGA_URL,
        }
        serializer = self.serializer_class(data, context={"request": request})
        return Response(serializer.data)


class APIServerStatusCheckView(APIView):
    def get(self, request: Request, format: str | None = None) -> Response:
        try:
            request.airavata_client.research.get_user_projects(
                settings.GATEWAY_ID,
                request.user.username,
                1,  # limit
                0,
            )  # offset
            data = {"apiServerUp": True}
        except Exception as e:
            log.debug(f"API server status check failed: {str(e)}")
            data = {"apiServerUp": False}
        return Response(data)


@api_view()
def notebook_output_view(request: Request) -> HttpResponse:
    provider_id = request.GET["provider-id"]
    experiment_id = request.GET["experiment-id"]
    experiment_output_name = request.GET["experiment-output-name"]
    data = output_views.generate_data(request, provider_id, experiment_output_name, experiment_id)
    return HttpResponse(data["output"])


@api_view()
def html_output_view(request: Request) -> JsonResponse:
    data = _generate_output_view_data(request)
    return JsonResponse(data)


@api_view()
def image_output_view(request: Request) -> JsonResponse:
    data = _generate_output_view_data(request)
    # data should contain 'image' as a file-like object or raw bytes with the
    # file data and 'mime-type' with the images mimetype
    data["image"] = base64.b64encode(data["image"]).decode("utf-8")
    return JsonResponse(data)


@api_view()
def link_output_view(request: Request) -> JsonResponse:
    data = _generate_output_view_data(request)
    return JsonResponse(data)


def _generate_output_view_data(request: Request) -> dict[str, Any]:
    params = request.GET.copy()
    provider_id = params.pop("provider-id")[0]
    experiment_id = params.pop("experiment-id")[0]
    experiment_output_name = params.pop("experiment-output-name")[0]
    test_mode = "test-mode" in params and params.pop("test-mode")[0] == "true"
    return output_views.generate_data(
        request, provider_id, experiment_output_name, experiment_id, test_mode=test_mode, **params.dict()
    )


class QueueSettingsCalculatorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericAPIBackedViewSet):
    serializer_class = serializers.QueueSettingsCalculatorSerializer

    def get_list(self) -> list[Any]:
        return queue_settings_calculators.get_all()

    def get_instance(self, lookup_value: str) -> Any:
        calcs = queue_settings_calculators.get_all()
        calc = [calc for calc in calcs if calc.id == lookup_value]
        if len(calc) == 0:
            return None
        return calc[0]

    @action(methods=["post"], detail=True, serializer_class=serializers.ExperimentSerializer)
    def calculate(self, request: Request, pk: str | None = None) -> Response:

        serializer = self.get_serializer(data=request.data)
        result = {}
        # Just ignore invalid experiment model since likely caused by late initialization
        if serializer.is_valid():
            experiment_model = serializer.save()
            result = queue_settings_calculators.calculate_queue_settings(pk, request, experiment_model)
        return Response(result)
