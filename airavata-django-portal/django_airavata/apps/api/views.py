from __future__ import annotations

import base64
import builtins
import io
import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, override

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import (
    FileResponse,
    Http404,
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.urls import reverse
from pydantic import BaseModel, ConfigDict

from django_airavata import context_processors
from django_airavata.apps.api import queue_settings, web
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
from django_airavata.request import AiravataRequest

from . import (
    exceptions,
    experiment_builder,
    helpers,
    output_views,
    serializers,
    signals,
    tus,
    view_utils,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from airavata.model.appcatalog.appdeployment import app_deployment_pb2
    from airavata.model.appcatalog.appinterface import app_interface_pb2
    from airavata.model.appcatalog.computeresource import compute_resource_pb2
    from airavata.model.appcatalog.gatewayprofile import gateway_profile_pb2
    from airavata.model.appcatalog.groupresourceprofile import (
        group_resource_profile_pb2,
    )
    from airavata.model.appcatalog.parser import parser_pb2 as parser_model_pb2
    from airavata.model.appcatalog.storageresource import storage_resource_pb2
    from airavata.model.application.io import application_io_pb2 as io_pb2
    from airavata.model.credential.store import credential_store_pb2
    from airavata.model.data.replica import replica_catalog_pb2 as rc
    from airavata.model.experiment import experiment_pb2
    from airavata.model.group import group_manager_pb2
    from airavata.model.job import job_pb2
    from airavata.model.parallelism import parallelism_pb2
    from airavata.model.process import process_pb2
    from airavata.model.status import status_pb2
    from airavata.model.user import user_profile_pb2
    from airavata.model.workspace import workspace_pb2
    from airavata.services import application_catalog_service_pb2 as ac_pb2
    from airavata.services import credential_service_pb2 as cred_pb2
    from airavata.services import experiment_service_pb2 as exp_pb2
    from airavata.services import (
        gateway_resource_profile_service_pb2 as gw_pb2,
    )
    from airavata.services import group_manager_service_pb2 as gm_pb2
    from airavata.services import (
        group_resource_profile_service_pb2 as grp_pb2,
    )
    from airavata.services import notification_service_pb2 as notif_pb2
    from airavata.services import project_service_pb2 as proj_pb2
    from airavata.services import sharing_service_pb2 as sharing_pb2
    from airavata.services.application_catalog_service_pb2_grpc import (
        ApplicationCatalogServiceStub,
    )
    from airavata.services.credential_service_pb2_grpc import (
        CredentialServiceStub,
    )
    from airavata.services.data_product_service_pb2_grpc import (
        DataProductServiceStub,
    )
    from airavata.services.experiment_service_pb2_grpc import (
        ExperimentServiceStub,
    )
    from airavata.services.file_service_pb2_grpc import (
        UserStorageServiceStub,
    )
    from airavata.services.gateway_resource_profile_service_pb2_grpc import (
        GatewayResourceProfileServiceStub,
    )
    from airavata.services.group_manager_service_pb2_grpc import (
        GroupManagerServiceStub,
    )
    from airavata.services.group_resource_profile_service_pb2_grpc import (
        GroupResourceProfileServiceStub,
    )
    from airavata.services.iam_admin_service_pb2_grpc import (
        IamAdminServiceStub,
    )
    from airavata.services.notification_service_pb2_grpc import (
        NotificationServiceStub,
    )
    from airavata.services.parser_service_pb2_grpc import (
        ParserServiceStub,
    )
    from airavata.services.project_service_pb2_grpc import (
        ProjectServiceStub,
    )
    from airavata.services.resource_service_pb2_grpc import (
        ResourceServiceStub,
    )
    from airavata.services.sharing_service_pb2_grpc import (
        SharingServiceStub,
    )
    from airavata.services.user_profile_service_pb2_grpc import (
        UserProfileServiceStub,
    )

# Input files uploaded for an experiment are staged under this directory in the
# user's storage (mirrors the legacy SDK's TMP_INPUT_FILE_UPLOAD_DIR).
TMP_INPUT_FILE_UPLOAD_DIR = "tmp"

log = logging.getLogger(__name__)


# First replica's ~/-prefixed file path from a proto DataProductModel.
_data_product_file_path = view_utils.data_product_file_path


def _user_storage_stub(request: AiravataRequest) -> UserStorageServiceStub:
    """Raw UserStorageService stub bound to the request's authed channel."""
    from airavata.services.file_service_pb2_grpc import (
        UserStorageServiceStub,
    )

    return UserStorageServiceStub(request.airavata_channel)


def _data_product_stub(request: AiravataRequest) -> DataProductServiceStub:
    """Raw DataProductService stub bound to the request's authed channel."""
    from airavata.services.data_product_service_pb2_grpc import (
        DataProductServiceStub,
    )

    return DataProductServiceStub(request.airavata_channel)


def _get_data_product_proto(
    request: AiravataRequest, data_product_uri: str
) -> rc.DataProductModel:
    """Bare ``DataProductModel`` for *data_product_uri* via the raw stub."""
    from airavata.services import data_product_service_pb2 as dp_pb2

    return _data_product_stub(request).GetDataProduct(
        dp_pb2.GetDataProductRequest(product_uri=data_product_uri)
    )


def _build_upload_data_product(
    *,
    owner_name: str | None,
    product_name: str | None,
    file_path: str,
    storage_resource_id: str | None,
    content_type: str | None = None,
    product_size: int = 0,
) -> rc.DataProductModel:
    """Assemble the ``DataProductModel`` proto an upload registers so the file
    gets a canonical URI (``storage.UploadFile`` only transfers bytes). One
    GATEWAY_DATA_STORE / TRANSIENT replica points at *file_path*; the content
    type goes under ``mime-type`` metadata. Mirrors the SDK
    ``research_resources.data_product_for_upload``.
    """
    from airavata.model.data.replica import (
        replica_catalog_pb2 as rc,
    )

    product_metadata = {"mime-type": content_type} if content_type else {}
    return rc.DataProductModel(
        gateway_id=settings.GATEWAY_ID or "",
        owner_name=owner_name or "",
        product_name=product_name or "",
        data_product_type=rc.DataProductType.FILE,
        product_size=product_size or 0,
        product_metadata=product_metadata,
        replica_locations=[
            rc.DataReplicaLocationModel(
                replica_name=f"{product_name} gateway data store copy",
                replica_location_category=rc.ReplicaLocationCategory.GATEWAY_DATA_STORE,
                replica_persistent_type=rc.ReplicaPersistentType.TRANSIENT,
                storage_resource_id=storage_resource_id or "",
                file_path=file_path,
            )
        ],
    )


def _storage_upload_and_register(
    request: AiravataRequest,
    dir_path: str,
    uploaded_file: Any,
    name: str | None = None,
    content_type: str | None = None,
    experiment_id: str | None = None,
) -> rc.DataProductModel:
    """Write the bytes via the raw user-storage stub, then register a data
    product via the data-product stub so the file gets a canonical product URI."""
    from airavata.services import data_product_service_pb2 as dp_pb2
    from airavata.services import file_service_pb2 as fs_pb2

    storage = _user_storage_stub(request)
    name = name or os.path.basename(getattr(uploaded_file, "name", "") or "")
    # Full file path resolved against the storage root (or experiment data dir).
    upload_path = _user_storage_path(
        os.path.join(dir_path, name), experiment_id, request
    )
    content = uploaded_file.read()
    storage.UploadFile(
        fs_pb2.UploadFileRequest(
            storage_resource_id="",
            path=upload_path,
            name=name,
            content_type=content_type or "",
            content=content,
        )
    )
    # The upload response is minimal; resolve the absolute path the backend wrote
    # to and register the full data product so the file gets a canonical URI.
    metadata = storage.GetFileMetadata(
        fs_pb2.GetFileMetadataRequest(storage_resource_id="", path=upload_path)
    )
    storage_resource_id = storage.GetDefaultStorageResourceId(
        fs_pb2.GetDefaultStorageResourceIdRequest()
    ).storage_resource_id
    product_uri = (
        _data_product_stub(request)
        .RegisterDataProduct(
            dp_pb2.RegisterDataProductRequest(
                data_product=_build_upload_data_product(
                    owner_name=request.user.username,
                    product_name=name,
                    file_path=metadata.path,
                    storage_resource_id=storage_resource_id,
                    content_type=content_type,
                    product_size=metadata.size,
                )
            )
        )
        .product_uri
    )
    return _get_data_product_proto(request, product_uri)


def _render_uploaded_data_product(
    request: AiravataRequest, data_product: rc.DataProductModel
) -> dict[str, Any]:
    """Snake_case proto-direct render of a freshly registered upload.

    Wrapped in a ``DataProductWithAccess`` proto so the frontend ``DataProduct``
    model receives ``is_owner`` / ``user_has_write_access``: the uploader owns the
    new file, so both are True (matching the legacy owner-has-write rule). The
    renderer flattens the proto to the same shape the retired ``_envelope``
    wrapper produced.
    """
    from airavata.model.commons import commons_pb2
    from airavata.services import experiment_service_pb2 as pb2

    from django_airavata.apps.api.proto_render import to_jsonable

    is_owner = bool(data_product.owner_name) and (
        data_product.owner_name == request.user.username
    )
    return to_jsonable(
        pb2.DataProductWithAccess(
            data_product=data_product,
            access=commons_pb2.AccessFlags(
                is_owner=is_owner, user_has_write_access=True
            ),
        )
    )


class GroupViewSet(APIBackedViewSet):
    """Groups resource — wired to the raw GroupManagerService stub.

    Reads return the raw ``GroupWithAccess`` proto (the renderer flattens the six
    ``GroupAccessFlags`` onto the ``GroupModel`` exactly as the retired
    ``_envelope.WithGroupAccess`` did; the server computes the flags and gates the
    member roster to insiders). Create / update build the ``GroupModel`` in the
    portal and call ``CreateGroupReconciled`` / ``UpdateGroupReconciled``, which
    reconcile members + admins server-side.

    The ``user_added_to_group`` notification fan-out (needs ``request`` +
    ``UserProfileService.GetUserProfileById`` + a Django signal) stays in the
    portal, so the ViewSet computes the newly added member ids itself (the
    reconcile RPCs return only the ``GroupWithAccess``, not the membership delta).
    """

    request: AiravataRequest
    lookup_field = "group_id"
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:group-list"

    def _group_mgr(self) -> GroupManagerServiceStub:
        from airavata.services.group_manager_service_pb2_grpc import (
            GroupManagerServiceStub,
        )

        return GroupManagerServiceStub(self.request.airavata_channel)

    def _build_group(self, data: dict[str, Any]) -> group_manager_pb2.GroupModel:
        """Build a ``GroupModel`` from the request body; ``owner_id`` is forced
        from the caller context (``user@gateway``). Mirrors the retired SDK
        ``sharing_resources._build_group``."""
        from airavata.model.group import (
            group_manager_pb2,
        )

        return group_manager_pb2.GroupModel(
            name=data.get("name") or "",
            description=data.get("description") or "",
            members=list(data.get("members") or []),
            admins=list(data.get("admins") or []),
            owner_id=f"{self.username}@{self.gateway_id}",
        )

    @staticmethod
    def _member_admin_diff(
        existing: group_manager_pb2.GroupModel, data: dict[str, Any]
    ) -> dict[str, builtins.list[str]]:
        """Reconciled member/admin roster + the added-member ids for the signal.

        New lists default to the existing proto values when absent from *data*;
        admins not yet members are promoted to members and counted as added.
        Mirrors the retired SDK ``sharing_resources._member_admin_diff``.
        """
        old_members = set(existing.members)
        new_members = (
            set(data["members"]) if "members" in data else set(existing.members)
        )
        new_admins = set(data["admins"]) if "admins" in data else set(existing.admins)

        added_members = list(new_members - old_members)
        final_members = list(new_members)
        # Admins not yet members become members too (and count as added).
        extra = list(new_admins - new_members)
        added_members = added_members + extra
        final_members = final_members + extra
        return {
            "members": final_members,
            "admins": list(new_admins),
            "added_members": added_members,
        }

    @override
    def get_list(self) -> APIResultIterator:
        """Iterator yielding raw ``GroupWithAccess`` protos for the gateway.
        ``GetGroupsWithAccess`` returns the full list; limit/offset slice it
        in-process (mirrors the retired SDK ``list_groups``)."""
        view = self

        class GroupResultsIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> list[gm_pb2.GroupWithAccess]:
                from airavata.services import (
                    group_manager_service_pb2 as pb2,
                )

                rows = list(
                    view._group_mgr().GetGroupsWithAccess(pb2.GetGroupsRequest()).groups
                )
                end = offset + limit if limit > 0 else len(rows)
                return rows[offset:end] if rows else []

        return GroupResultsIterator()

    @override
    def get_instance(self, lookup_value: str) -> gm_pb2.GroupWithAccess:
        """Return the raw ``GroupWithAccess`` proto for *lookup_value*."""
        from airavata.services import group_manager_service_pb2 as pb2

        return self._group_mgr().GetGroupWithAccess(
            pb2.GetGroupRequest(group_id=lookup_value)
        )

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        queryset = self.get_list()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(list(page))
        return web.Response(queryset.get_results())

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return web.Response(self.get_object())

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import group_manager_service_pb2 as pb2

        data = request.data if isinstance(request.data, dict) else {}
        group = self._build_group(data)
        # New group: every desired non-owner member/admin is newly added (the
        # server adds admins as members too, matching the reconcile).
        added_members = list(
            (set(group.members) | set(group.admins)) - {group.owner_id}
        )
        result = self._group_mgr().CreateGroupReconciled(
            pb2.CreateGroupRequest(group=group)
        )
        self._send_users_added_to_group(added_members, result.group)
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import group_manager_service_pb2 as pb2

        group_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        # Read the current roster to compute the added-member set for the signal;
        # UpdateGroupReconciled applies the membership/admin changes server-side.
        group = self._group_mgr().GetGroup(pb2.GetGroupRequest(group_id=group_id))
        if "name" in data:
            group.name = data["name"] or ""
        if "description" in data:
            group.description = data["description"] or ""
        diff = self._member_admin_diff(group, data)
        group.members[:] = diff["members"]
        group.admins[:] = diff["admins"]
        result = self._group_mgr().UpdateGroupReconciled(
            pb2.UpdateGroupRequest(group=group)
        )
        self._send_users_added_to_group(diff["added_members"], result.group)
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def perform_destroy(self, instance: gm_pb2.GroupWithAccess) -> None:
        from airavata.services import group_manager_service_pb2 as pb2

        # ``instance`` is the GroupWithAccess from get_object(); it already carries
        # the owner_id the DeleteGroup RPC requires, so no re-fetch is needed.
        self._group_mgr().DeleteGroup(
            pb2.DeleteGroupRequest(
                group_id=instance.group.id, owner_id=instance.group.owner_id
            )
        )

    def _send_users_added_to_group(
        self,
        internal_user_ids: builtins.list[str],
        group: group_manager_pb2.GroupModel,
    ) -> None:
        from airavata.services import user_profile_service_pb2 as up_pb2
        from airavata.services.user_profile_service_pb2_grpc import (
            UserProfileServiceStub,
        )

        for internal_user_id in internal_user_ids:
            user_id, gateway_id = internal_user_id.rsplit("@", maxsplit=1)
            user_profile = UserProfileServiceStub(
                self.request.airavata_channel
            ).GetUserProfileById(
                up_pb2.GetUserProfileByIdRequest(user_id=user_id, gateway_id=gateway_id)
            )
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=[group],
                request=self.request,
            )


class ProjectViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Projects resource — fully wired to the raw project stub. Reads return the
    ``ProjectWithAccess`` proto (renderer flattens it); create/delete are single
    stub calls; update is a read-modify-write of the mutable fields (name /
    description) since ``UpdateProjectWithAccess`` is full-replace."""

    request: AiravataRequest
    lookup_field = "project_id"
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:project-list"
    paginate = True

    def _projects(self) -> ProjectServiceStub:
        from airavata.services.project_service_pb2_grpc import (
            ProjectServiceStub,
        )

        return ProjectServiceStub(self.request.airavata_channel)

    def _experiments(self) -> ExperimentServiceStub:
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        return ExperimentServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> proj_pb2.ProjectWithAccess:
        from airavata.services import project_service_pb2 as pb2

        return self._projects().GetProjectWithAccess(
            pb2.GetProjectRequest(project_id=lookup_value)
        )

    @override
    def _list_results(
        self, limit: int = -1, offset: int = 0
    ) -> list[proj_pb2.ProjectWithAccess]:
        from airavata.services import project_service_pb2 as pb2

        response = self._projects().GetUserProjectsWithAccess(
            pb2.GetUserProjectsRequest(
                gateway_id=self.gateway_id,
                user_name=self.username,
                limit=limit,
                offset=offset,
            )
        )
        return list(response.projects)

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.model.workspace import (
            workspace_pb2,
        )
        from airavata.services import project_service_pb2 as pb2

        data = self._body()
        project = workspace_pb2.Project(
            owner=self.username,
            gateway_id=self.gateway_id,
            name=data.get("name") or "",
            description=data.get("description") or "",
        )
        result = self._projects().CreateProjectWithAccess(
            pb2.CreateProjectRequest(gateway_id=self.gateway_id, project=project)
        )
        self._update_most_recent_project(result.project.project_id)
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        # Only name / description are mutable; UpdateProjectWithAccess is
        # full-replace, so read-modify-write the fetched project to preserve the
        # immutable fields (owner, gateway, creation time).
        from airavata.services import project_service_pb2 as pb2

        project_id = self.kwargs[self.lookup_field]
        data = self._body()
        project = self._projects().GetProject(
            pb2.GetProjectRequest(project_id=project_id)
        )
        if "name" in data:
            project.name = data["name"] or ""
        if "description" in data:
            project.description = data["description"] or ""
        result = self._projects().UpdateProjectWithAccess(
            pb2.UpdateProjectRequest(project_id=project_id, project=project)
        )
        self._update_most_recent_project(project_id)
        return web.Response(result)

    @override
    def perform_destroy(self, instance: proj_pb2.ProjectWithAccess) -> None:
        # ``get_object`` yields the raw ``ProjectWithAccess`` proto.
        from airavata.services import project_service_pb2 as pb2

        self._projects().DeleteProject(
            pb2.DeleteProjectRequest(project_id=instance.project.project_id)
        )

    @web.action(detail=False)
    def list_all(self, request: AiravataRequest) -> web.Response:
        return web.Response(self._list_results())

    @web.action(detail=True)
    def experiments(
        self, request: AiravataRequest, project_id: str | None = None
    ) -> web.Response:
        # Raw ExperimentWithAccess list for the project; the EXECUTING-state
        # intermediate-output enrichment is an ExperimentViewSet detail concern
        # and is not applied here.
        from airavata.services import experiment_service_pb2 as exp_pb2

        response = self._experiments().GetExperimentsInProjectWithAccess(
            exp_pb2.GetExperimentsInProjectRequest(
                project_id=project_id, limit=-1, offset=0
            )
        )
        return web.Response(list(response.experiments))

    def _update_most_recent_project(self, project_id: str) -> None:
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
    (it needs extra backend calls + a process-tree walk, so it can't be a plain
    proto-direct return).
    """

    request: AiravataRequest
    lookup_field = "experiment_id"

    def _experiments(self) -> ExperimentServiceStub:
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        return ExperimentServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> exp_pb2.ExperimentWithAccess:
        from airavata.services import experiment_service_pb2 as pb2

        return self._experiments().GetExperimentWithAccess(
            pb2.GetExperimentRequest(experiment_id=lookup_value)
        )

    def _render(
        self, proto: exp_pb2.ExperimentWithAccess, request: AiravataRequest
    ) -> dict[str, Any]:
        # Flatten the proto, then layer the EXECUTING-state intermediate-output
        # enrichment on top (a plain dict is safe — ProtoJSONRenderer recurses).
        # to_jsonable flattens the 2-field ExperimentWithAccess {experiment, access}
        # identically to the old envelope shape.
        from django_airavata.apps.api.proto_render import to_jsonable

        data = to_jsonable(proto)
        self._add_intermediate_output_information(proto.experiment, data, request)
        return data

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        proto = self.get_object()
        return web.Response(self._render(proto, request))

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import experiment_service_pb2 as pb2

        data = request.data if isinstance(request.data, dict) else {}
        experiment = experiment_builder.build_experiment(
            gateway_id=self.gateway_id, user_name=self.username, data=data
        )
        result = self._experiments().CreateExperimentWithAccess(
            pb2.CreateExperimentRequest(
                gateway_id=self.gateway_id, experiment=experiment
            )
        )
        created = result.experiment
        self._update_workspace_preferences(
            project_id=created.project_id,
            group_resource_profile_id=created.user_configuration_data.group_resource_profile_id,
            compute_resource_id=created.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        return web.Response(
            self._render(result, request), status=web.status.HTTP_201_CREATED
        )

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import experiment_service_pb2 as pb2

        experiment_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        experiment = experiment_builder.build_experiment(
            gateway_id=self.gateway_id, user_name=self.username, data=data
        )
        experiment.experiment_id = experiment_id
        result = self._experiments().UpdateExperimentWithAccess(
            pb2.UpdateExperimentRequest(
                experiment_id=experiment_id, experiment=experiment
            )
        )
        updated = result.experiment
        self._update_workspace_preferences(
            project_id=updated.project_id,
            group_resource_profile_id=updated.user_configuration_data.group_resource_profile_id,
            compute_resource_id=updated.user_configuration_data.computational_resource_scheduling.resource_host_id,
        )
        return web.Response(self._render(result, request))

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    def _add_intermediate_output_information(
        self,
        experiment: experiment_pb2.ExperimentModel,
        data: dict[str, Any],
        request: AiravataRequest,
    ) -> None:
        """Replay the old serializer's EXECUTING-state output enrichment.

        When the experiment's latest status is EXECUTING, each experiment output
        gains an ``intermediate_output`` block (fetchability + per-output process
        status + any already-staged data products).  This needs backend calls,
        so it lives in the ViewSet rather than the SDK proto-direct return —
        mirroring ``ExperimentSerializer._add_intermediate_output_information``,
        but emitting snake_case keys and rendering the nested protos via
        ``to_jsonable`` (no DRF serializer).
        """
        from airavata.model.status import (
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
                output["intermediate_output"]["can_fetch"] = (
                    self._can_fetch_intermediate_output(experiment, output["name"])
                )
                process_status = self._intermediate_output_process_status(experiment)
                if process_status:
                    output["intermediate_output"]["process_status"] = to_jsonable(
                        process_status
                    )
                output["intermediate_output"]["data_products"] = [
                    to_jsonable(dp)
                    for dp in self._intermediate_output_data_products(
                        experiment, output["name"]
                    )
                ]
            except Exception:
                log.debug("Failed to get intermediate output status", exc_info=True)

    # Intermediate-output enrichment (EXECUTING state), ported off the SDK
    # experiment_orchestration helpers onto raw stubs + portal-side proto walks.

    @staticmethod
    def _output_fetching_processes(
        experiment: experiment_pb2.ExperimentModel,
    ) -> list[process_pb2.ProcessModel]:
        """Most-recent-first processes that carry an OUTPUT_FETCHING task."""
        from airavata.model.task import task_pb2

        processes = (
            sorted(experiment.processes, key=lambda p: p.creation_time, reverse=True)
            if experiment.processes
            else []
        )
        return [
            process
            for process in processes
            if any(task.task_type == task_pb2.OUTPUT_FETCHING for task in process.tasks)
        ]

    def _intermediate_output_process_status(
        self, experiment: experiment_pb2.ExperimentModel
    ) -> status_pb2.ProcessStatus | None:
        """ProcessStatus of the intermediate-output fetch process, or None (no
        output-fetching process / backend error)."""
        from airavata.services import experiment_service_pb2 as pb2

        if not self._output_fetching_processes(experiment):
            return None
        try:
            return self._experiments().GetIntermediateOutputProcessStatus(
                pb2.GetIntermediateOutputProcessStatusRequest(
                    experiment_id=experiment.experiment_id
                )
            )
        except Exception:
            log.debug("Failed to get intermediate output process status", exc_info=True)
            return None

    def _can_fetch_intermediate_output(
        self, experiment: experiment_pb2.ExperimentModel, output_name: str
    ) -> bool:
        """True only when at least one job is ACTIVE and there is no in-progress
        (non-terminal) intermediate-output process."""
        from airavata.model.status import status_pb2

        terminal = (
            status_pb2.PROCESS_STATE_CANCELED,
            status_pb2.PROCESS_STATE_COMPLETED,
            status_pb2.PROCESS_STATE_FAILED,
        )
        jobs = [
            job
            for process in experiment.processes
            for task in process.tasks
            for job in task.jobs
        ]

        def latest_active(job: job_pb2.JobModel) -> bool:
            return bool(job.job_statuses) and (
                job.job_statuses[-1].job_state == status_pb2.ACTIVE
            )

        if not any(latest_active(job) for job in jobs):
            return False
        try:
            process_status = self._intermediate_output_process_status(experiment)
            # No running process -> fetchable.
            if process_status is None:
                return True
            return process_status.state in terminal
        except Exception:
            return True

    def _intermediate_output_data_products(
        self, experiment: experiment_pb2.ExperimentModel, output_name: str
    ) -> list[rc.DataProductModel]:
        """DataProduct protos for the named output: the most-recent completed
        output-fetching process's matching output, with its URIs resolved."""
        from airavata.model.status import status_pb2

        processes = self._output_fetching_processes(experiment)
        matched = None
        for process in processes:
            if (
                not process.process_statuses
                or process.process_statuses[-1].state
                != status_pb2.PROCESS_STATE_COMPLETED
            ):
                continue
            for process_output in process.process_outputs:
                if process_output.name == output_name:
                    matched = process_output
                    break
            if matched is not None:
                break
        if matched is None or not matched.value.startswith("airavata-dp://"):
            return []
        return [
            _get_data_product_proto(self.request, uri)
            for uri in matched.value.split(",")
        ]

    @web.action(methods=["post"], detail=True)
    def launch(
        self, request: AiravataRequest, experiment_id: str | None = None
    ) -> web.Response:
        # The server-side composite does the storage setup (default storage ids,
        # data-dir creation, tmp-upload relocation) and launch in one call; when
        # the experiment has email notifications enabled it routes them to the
        # launching user (notification_email).
        from airavata.services import experiment_service_pb2 as pb2

        try:
            self._experiments().LaunchExperimentWithStorageSetup(
                pb2.LaunchExperimentWithStorageSetupRequest(
                    experiment_id=experiment_id,
                    gateway_id=self.gateway_id,
                    notification_email=getattr(request.user, "email", "") or "",
                )
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                f"Failed to launch experiment {experiment_id}",
                extra={"request": request},
            )
            return web.Response({"success": False, "errorMessage": str(e)})

    @web.action(methods=["get"], detail=True)
    def jobs(
        self, request: AiravataRequest, experiment_id: str | None = None
    ) -> web.Response:
        # Raw JobModel protos; ProtoJSONRenderer flattens each to snake_case
        # (job_state enum as NAME, int64 timestamps as epoch-millis strings).
        from airavata.services import experiment_service_pb2 as pb2

        response = self._experiments().GetJobDetails(
            pb2.GetJobDetailsRequest(experiment_id=experiment_id)
        )
        return web.Response(list(response.jobs))

    @web.action(methods=["post"], detail=True)
    def clone(
        self, request: AiravataRequest, experiment_id: str | None = None
    ) -> web.Response:
        # The server-side composite clones into a writable project, copies the
        # input files into fresh tmp uploads, nulls the data dir, and returns the
        # new ExperimentWithAccess (rendered like retrieve). new_experiment_name /
        # project are left empty: the server defaults the name to "Clone of
        # <source>" and resolves a writable project.
        from airavata.services import experiment_service_pb2 as pb2

        result = self._experiments().CloneExperimentWithInputFiles(
            pb2.CloneExperimentWithInputFilesRequest(experiment_id=experiment_id)
        )
        return web.Response(self._render(result, request))

    @web.action(methods=["post"], detail=True)
    def cancel(
        self, request: AiravataRequest, experiment_id: str | None = None
    ) -> web.Response:
        from airavata.services import experiment_service_pb2 as pb2

        try:
            self._experiments().TerminateExperiment(
                pb2.TerminateExperimentRequest(
                    experiment_id=experiment_id, gateway_id=self.gateway_id
                )
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                "Cancel action has thrown the following error",
                extra={"request": request},
            )
            raise e

    @web.action(methods=["post"], detail=True)
    def fetch_intermediate_outputs(
        self, request: AiravataRequest, experiment_id: str | None = None
    ) -> web.Response:
        # snake_case body in the proto-direct contract; accept the legacy
        # camelCase key too while the frontend migrates.
        output_names = request.data.get("output_names", request.data.get("outputNames"))
        if output_names is None:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)
        from airavata.services import experiment_service_pb2 as pb2

        try:
            self._experiments().FetchIntermediateOutputs(
                pb2.FetchIntermediateOutputsRequest(
                    experiment_id=experiment_id, output_names=output_names
                )
            )
            return web.Response({"success": True})
        except Exception as e:
            log.exception(
                "fetchIntermediateOutputs failed with the following error",
                extra={"request": request},
            )
            raise e

    def _update_workspace_preferences(
        self,
        project_id: str,
        group_resource_profile_id: str,
        compute_resource_id: str,
    ) -> None:
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

    request: AiravataRequest
    pagination_class = APIResultPagination
    pagination_viewname = "django_airavata_api:experiment-search-list"

    def _experiments(self) -> ExperimentServiceStub:
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        return ExperimentServiceStub(self.request.airavata_channel)

    def _filters(self) -> dict[str, str]:
        from airavata.model.experiment import (
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

    @override
    def get_list(self) -> APIResultIterator:
        view = self
        filters = self._filters()

        class ExperimentSearchResultIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> list[exp_pb2.ExperimentSummaryWithAccess]:
                from airavata.services import (
                    experiment_service_pb2 as pb2,
                )

                response = view._experiments().SearchExperimentsWithAccess(
                    pb2.SearchExperimentsRequest(
                        gateway_id=view.gateway_id,
                        user_name=view.username,
                        filters=filters,
                        limit=limit,
                        offset=offset,
                    )
                )
                return list(response.experiments)

        # Preserve query parameters when moving to next and previous links
        return ExperimentSearchResultIterator(
            query_params=self.request.query_params.copy()
        )

    @override
    def get_instance(self, lookup_value: str) -> Any:
        raise NotImplementedError()

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
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

    request: AiravataRequest
    lookup_field = "experiment_id"

    def _experiments(self) -> ExperimentServiceStub:
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        return ExperimentServiceStub(self.request.airavata_channel)

    def _projects(self) -> ProjectServiceStub:
        from airavata.services.project_service_pb2_grpc import (
            ProjectServiceStub,
        )

        return ProjectServiceStub(self.request.airavata_channel)

    def _app_catalog(self) -> ApplicationCatalogServiceStub:
        from airavata.services.application_catalog_service_pb2_grpc import (
            ApplicationCatalogServiceStub,
        )

        return ApplicationCatalogServiceStub(self.request.airavata_channel)

    def _output_views(
        self, request: AiravataRequest
    ) -> Callable[
        [
            experiment_pb2.ExperimentModel,
            app_interface_pb2.ApplicationInterfaceDescription | None,
        ],
        dict[str, list[dict[str, Any]]],
    ]:
        def _fn(
            experiment: experiment_pb2.ExperimentModel,
            application_interface: (
                app_interface_pb2.ApplicationInterfaceDescription | None
            ),
        ) -> dict[str, list[dict[str, Any]]]:
            return output_views.get_output_views(
                request, experiment, application_interface
            )

        return _fn

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        # GetFullExperiment returns the whole composite in one call (experiment +
        # access, every input/output data product with access flags, jobs, the
        # interface and compute resource). Only the project READ-gate and the
        # output-views map stay request-bound/portal-side; the module and project
        # carry no access flags in the composite, so they are re-wrapped via their
        # WithAccess endpoints.
        from airavata.services import (
            application_catalog_service_pb2 as ac_pb2,
        )
        from airavata.services import (
            experiment_service_pb2 as exp_pb2,
        )
        from airavata.services import (
            project_service_pb2 as proj_pb2,
        )

        fe = self._experiments().GetFullExperiment(
            exp_pb2.GetExperimentRequest(experiment_id=self.kwargs[self.lookup_field])
        )
        experiment = fe.experiment
        application_interface = (
            fe.application_interface if fe.HasField("application_interface") else None
        )

        # project_id comes from the composite — no extra get_experiment round-trip.
        project = None
        if serializers.user_has_access(request, experiment.project_id, "READ"):
            project = self._projects().GetProjectWithAccess(
                proj_pb2.GetProjectRequest(project_id=experiment.project_id)
            )

        application_module = None
        if (
            application_interface is not None
            and application_interface.application_modules
        ):
            try:
                application_module = self._app_catalog().GetApplicationModuleWithAccess(
                    ac_pb2.GetApplicationModuleRequest(
                        app_module_id=application_interface.application_modules[0]
                    )
                )
            except Exception:
                application_module = None

        return web.Response(
            {
                "experiment_id": experiment.experiment_id,
                "experiment": exp_pb2.ExperimentWithAccess(
                    experiment=experiment, access=fe.access
                ),
                "project": project,
                "application_module": application_module,
                "compute_resource": (
                    fe.compute_resource if fe.HasField("compute_resource") else None
                ),
                "input_data_products": list(fe.input_data_products),
                "output_data_products": list(fe.output_data_products),
                "job_details": list(fe.jobs),
                "output_views": self._output_views(request)(
                    experiment, application_interface
                ),
            }
        )


class ApplicationModuleViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Application modules resource — wired to the raw ApplicationCatalog stub.
    Reads / create / update return the ``ApplicationModuleWithAccess`` proto
    (renderer flattens it).

    A gateway-level catalog entry, not a per-user shared resource:
    ``user_has_write_access`` (the gateway-admin flag) is sourced server-side by
    the *WithAccess endpoints, so the ViewSet no longer injects has_write.
    Create / update ``RegisterApplicationModule`` / ``UpdateApplicationModule``
    then re-fetch via ``GetApplicationModuleWithAccess`` so write paths emit the
    same shape as the read path (the re-fetch sources the access flags).
    """

    request: AiravataRequest
    lookup_field = "app_module_id"

    def _app_catalog(self) -> ApplicationCatalogServiceStub:
        from airavata.services.application_catalog_service_pb2_grpc import (
            ApplicationCatalogServiceStub,
        )

        return ApplicationCatalogServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> ac_pb2.ApplicationModuleWithAccess:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        return self._app_catalog().GetApplicationModuleWithAccess(
            pb2.GetApplicationModuleRequest(app_module_id=lookup_value)
        )

    def _build_application_module(
        self,
        data: dict[str, Any],
        base: app_deployment_pb2.ApplicationModule | None = None,
    ) -> app_deployment_pb2.ApplicationModule:
        """Build an ``ApplicationModule`` proto from the (snake_case) request body.

        ``base`` (the update path) seeds the proto so absent keys keep the base
        value. Mirrors the SDK ``research_resources.create_application_module`` /
        ``update_application_module`` field handling."""
        from airavata.model.appcatalog.appdeployment import (
            app_deployment_pb2,
        )

        module = app_deployment_pb2.ApplicationModule()
        if base is not None:
            module.CopyFrom(base)
            if "app_module_name" in data:
                module.app_module_name = data["app_module_name"] or ""
            if "app_module_version" in data:
                module.app_module_version = data["app_module_version"] or ""
            if "app_module_description" in data:
                module.app_module_description = data["app_module_description"] or ""
            return module
        module.app_module_name = data.get("app_module_name") or ""
        module.app_module_version = data.get("app_module_version") or ""
        module.app_module_description = data.get("app_module_description") or ""
        return module

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        module = self._build_application_module(self._body())
        app_module_id = (
            self._app_catalog()
            .RegisterApplicationModule(
                pb2.RegisterApplicationModuleRequest(
                    gateway_id=self.gateway_id, application_module=module
                )
            )
            .app_module_id
        )
        result = self._app_catalog().GetApplicationModuleWithAccess(
            pb2.GetApplicationModuleRequest(app_module_id=app_module_id)
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        # ``app_module_name`` / ``app_module_version`` / ``app_module_description``
        # are mutable; UpdateApplicationModule is full-replace, so seed from the
        # stored module and re-pin the path id.
        app_module_id = self.kwargs[self.lookup_field]
        base = self._app_catalog().GetApplicationModule(
            pb2.GetApplicationModuleRequest(app_module_id=app_module_id)
        )
        module = self._build_application_module(self._body(), base=base)
        self._app_catalog().UpdateApplicationModule(
            pb2.UpdateApplicationModuleRequest(
                app_module_id=app_module_id, application_module=module
            )
        )
        result = self._app_catalog().GetApplicationModuleWithAccess(
            pb2.GetApplicationModuleRequest(app_module_id=app_module_id)
        )
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def _list_results(
        self, limit: int = -1, offset: int = 0
    ) -> list[ac_pb2.ApplicationModuleWithAccess]:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        response = self._app_catalog().GetAccessibleApplicationModulesWithAccess(
            pb2.GetAccessibleAppModulesRequest(gateway_id=self.gateway_id)
        )
        return list(response.modules)

    @override
    def perform_destroy(self, instance: ac_pb2.ApplicationModuleWithAccess) -> None:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        # ``get_object`` yields the raw ``ApplicationModuleWithAccess`` proto.
        self._app_catalog().DeleteApplicationModule(
            pb2.DeleteApplicationModuleRequest(
                app_module_id=instance.application_module.app_module_id
            )
        )

    @web.action(detail=True)
    def application_interface(
        self, request: AiravataRequest, app_module_id: str
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        all_app_interfaces = list(
            self._app_catalog()
            .GetAllApplicationInterfaces(
                pb2.GetAllApplicationInterfacesRequest(gateway_id=self.gateway_id)
            )
            .application_interfaces
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
            # builds URLs from application_interface_id). The gateway-admin flag
            # is the write gate for this gateway-level catalog entry.
            from airavata.model.commons import (
                commons_pb2,
            )

            has_write = getattr(request, "is_gateway_admin", False)
            return web.Response(
                pb2.ApplicationInterfaceWithAccess(
                    application_interface=app_interfaces[0],
                    access=commons_pb2.AccessFlags(
                        is_owner=False, user_has_write_access=has_write
                    ),
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
    def application_deployments(
        self, request: AiravataRequest, app_module_id: str
    ) -> web.Response:
        # The gateway-wide accessible ApplicationDeploymentWithAccess set filtered
        # to this module (renderer flattens each; the server computes the flags).
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        response = self._app_catalog().GetAccessibleApplicationDeploymentsWithAccess(
            pb2.GetAccessibleApplicationDeploymentsRequest(gateway_id=self.gateway_id)
        )
        return web.Response(
            [
                d
                for d in response.deployments
                if d.application_deployment.app_module_id == app_module_id
            ]
        )

    @web.action(methods=["post"], detail=True)
    def favorite(self, request: AiravataRequest, app_module_id: str) -> HttpResponse:
        prefs = helpers.WorkspacePreferencesHelper().get(request)
        prefs.application_favorites[app_module_id] = True
        prefs.save()
        return HttpResponse(status=204)

    @web.action(methods=["post"], detail=True)
    def unfavorite(self, request: AiravataRequest, app_module_id: str) -> HttpResponse:
        prefs = helpers.WorkspacePreferencesHelper().get(request)
        prefs.application_favorites[app_module_id] = False
        prefs.save()
        return HttpResponse(status=204)

    @web.action(detail=False)
    def list_all(self, request: AiravataRequest) -> web.Response:
        # Every module in the gateway (admin view) as ApplicationModuleWithAccess
        # protos; the *WithAccess endpoint sources the gateway-admin flag server-side.
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        response = self._app_catalog().GetAllApplicationModulesWithAccess(
            pb2.GetAllAppModulesRequest(gateway_id=self.gateway_id)
        )
        return web.Response(list(response.modules))


class ApplicationInterfaceViewSet(web.mixins.DestroyModelMixin, SdkResourceViewSet):
    """Application interfaces resource — wired to the raw ApplicationCatalog
    stub. Reads / create / update return the ``ApplicationInterfaceWithAccess``
    proto (renderer flattens it; the re-fetch sources the access flags
    server-side).

    A gateway-level catalog entry. Create / update build the proto in the
    portal (``_build_application_interface``, mirroring the SDK), massage the
    input metadata (``_update_input_metadata``, portal-only JSON massaging),
    register / update, then re-fetch via ``GetApplicationInterfaceWithAccess``.
    """

    request: AiravataRequest
    lookup_field = "app_interface_id"

    def _app_catalog(self) -> ApplicationCatalogServiceStub:
        from airavata.services.application_catalog_service_pb2_grpc import (
            ApplicationCatalogServiceStub,
        )

        return ApplicationCatalogServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> ac_pb2.ApplicationInterfaceWithAccess:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        try:
            return self._app_catalog().GetApplicationInterfaceWithAccess(
                pb2.GetApplicationInterfaceRequest(app_interface_id=lookup_value)
            )
        except Exception:
            # If it failed to load, check to see if it exists at all
            all_interfaces = (
                self._app_catalog()
                .GetAllApplicationInterfaces(
                    pb2.GetAllApplicationInterfacesRequest(gateway_id=self.gateway_id)
                )
                .application_interfaces
            )
            interface_ids = [i.application_interface_id for i in all_interfaces]
            if lookup_value not in interface_ids:
                raise Http404("Application interface does not exist") from None
            else:
                raise  # re-raise

    @override
    def _list_results(
        self, limit: int = -1, offset: int = 0
    ) -> list[ac_pb2.ApplicationInterfaceWithAccess]:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        response = self._app_catalog().GetAllApplicationInterfacesWithAccess(
            pb2.GetAllApplicationInterfacesRequest(gateway_id=self.gateway_id)
        )
        return list(response.interfaces)

    @staticmethod
    def _data_type_int(value: object) -> io_pb2.DataType:
        """``DataType`` -> proto enum int (member NAME or proto int; ``None`` /
        ``""`` -> 0). Mirrors the SDK ``_data_type_int``."""
        from airavata.model.application.io import (
            application_io_pb2 as io,
        )

        from django_airavata.apps.api.experiment_builder import proto_enum_value

        return proto_enum_value(io.DataType, value)

    @staticmethod
    def _meta_data_str(value: object) -> str:
        """``meta_data`` -> proto JSON string (str passes through; other values
        ``json.dumps``ed; ``None`` -> ``""``). Mirrors the SDK ``_meta_data_str``."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return ""

    def _proto_input_data_object(
        self, data: dict[str, Any]
    ) -> io_pb2.InputDataObjectType:
        from airavata.model.application.io import (
            application_io_pb2 as io,
        )

        return io.InputDataObjectType(
            name=data.get("name") or "",
            value=data.get("value") or "",
            type=self._data_type_int(data.get("type")),
            application_argument=data.get("application_argument") or "",
            standard_input=bool(data.get("standard_input", False)),
            user_friendly_description=data.get("user_friendly_description") or "",
            meta_data=self._meta_data_str(data.get("meta_data")),
            input_order=data.get("input_order") or 0,
            is_required=bool(data.get("is_required", False)),
            required_to_added_to_command_line=bool(
                data.get("required_to_added_to_command_line", False)
            ),
            data_staged=bool(data.get("data_staged", False)),
            storage_resource_id=data.get("storage_resource_id") or "",
            is_read_only=bool(data.get("is_read_only", False)),
            override_filename=data.get("override_filename") or "",
        )

    def _proto_output_data_object(
        self, data: dict[str, Any]
    ) -> io_pb2.OutputDataObjectType:
        from airavata.model.application.io import (
            application_io_pb2 as io,
        )

        return io.OutputDataObjectType(
            name=data.get("name") or "",
            value=data.get("value") or "",
            type=self._data_type_int(data.get("type")),
            application_argument=data.get("application_argument") or "",
            is_required=bool(data.get("is_required", False)),
            required_to_added_to_command_line=bool(
                data.get("required_to_added_to_command_line", False)
            ),
            data_movement=bool(data.get("data_movement", False)),
            location=data.get("location") or "",
            search_query=data.get("search_query") or "",
            output_streaming=bool(data.get("output_streaming", False)),
            storage_resource_id=data.get("storage_resource_id") or "",
            meta_data=self._meta_data_str(data.get("meta_data")),
        )

    def _build_application_interface(
        self,
        data: dict[str, Any],
        base: app_interface_pb2.ApplicationInterfaceDescription | None = None,
    ) -> app_interface_pb2.ApplicationInterfaceDescription:
        """Build an ``ApplicationInterfaceDescription`` proto from the
        (snake_case) request body. ``base`` (the update path) seeds the proto;
        nested input/output lists are replaced wholesale when present. Mirrors
        the SDK ``research_resources._build_application_interface``."""
        from airavata.model.appcatalog.appinterface import (
            app_interface_pb2 as ai_pb2,
        )

        ai = ai_pb2.ApplicationInterfaceDescription()
        if base is not None:
            ai.CopyFrom(base)
        if "application_interface_id" in data:
            ai.application_interface_id = data["application_interface_id"] or ""
        if "application_name" in data:
            ai.application_name = data["application_name"] or ""
        if "application_description" in data:
            ai.application_description = data["application_description"] or ""
        if "application_modules" in data:
            ai.application_modules[:] = list(data["application_modules"] or [])
        if "archive_working_directory" in data:
            ai.archive_working_directory = bool(data["archive_working_directory"])
        if "application_inputs" in data:
            del ai.application_inputs[:]
            ai.application_inputs.extend(
                self._proto_input_data_object(i)
                for i in (data["application_inputs"] or [])
            )
        if "application_outputs" in data:
            del ai.application_outputs[:]
            ai.application_outputs.extend(
                self._proto_output_data_object(o)
                for o in (data["application_outputs"] or [])
            )
        return ai

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        # Build the proto, massage input metadata, register, then re-fetch
        # (the re-fetch sources the access flags server-side).
        application_interface = self._build_application_interface(self._body())
        self._update_input_metadata(application_interface)
        app_interface_id = (
            self._app_catalog()
            .RegisterApplicationInterface(
                pb2.RegisterApplicationInterfaceRequest(
                    gateway_id=self.gateway_id,
                    application_interface=application_interface,
                )
            )
            .app_interface_id
        )
        result = self._app_catalog().GetApplicationInterfaceWithAccess(
            pb2.GetApplicationInterfaceRequest(app_interface_id=app_interface_id)
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        app_interface_id = self.kwargs[self.lookup_field]
        base = self._app_catalog().GetApplicationInterface(
            pb2.GetApplicationInterfaceRequest(app_interface_id=app_interface_id)
        )
        application_interface = self._build_application_interface(
            self._body(), base=base
        )
        application_interface.application_interface_id = app_interface_id
        self._update_input_metadata(application_interface)
        self._app_catalog().UpdateApplicationInterface(
            pb2.UpdateApplicationInterfaceRequest(
                app_interface_id=app_interface_id,
                application_interface=application_interface,
            )
        )
        result = self._app_catalog().GetApplicationInterfaceWithAccess(
            pb2.GetApplicationInterfaceRequest(app_interface_id=app_interface_id)
        )
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def perform_destroy(self, instance: ac_pb2.ApplicationInterfaceWithAccess) -> None:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        self._app_catalog().DeleteApplicationInterface(
            pb2.DeleteApplicationInterfaceRequest(
                app_interface_id=instance.application_interface.application_interface_id
            )
        )

    def _update_input_metadata(
        self, app_interface: app_interface_pb2.ApplicationInterfaceDescription
    ) -> None:
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
    def compute_resources(
        self, request: AiravataRequest, app_interface_id: str
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        compute_resources = dict(
            self._app_catalog()
            .GetAvailableComputeResources(
                pb2.GetAvailableComputeResourcesRequest(
                    app_interface_id=app_interface_id
                )
            )
            .compute_resource_names
        )
        return web.Response(compute_resources)


class ApplicationDeploymentViewSet(APIBackedViewSet):
    """Application deployments resource — wired to the raw ApplicationCatalog
    stub. Reads / create / update return the ``ApplicationDeploymentWithAccess``
    proto (renderer flattens it; the re-fetch sources the access flags
    server-side).

    Create / update build the proto in the portal
    (``_build_application_deployment``, mirroring the SDK), register / update,
    then re-fetch via ``GetApplicationDeploymentWithAccess``. ``_has_write``
    stays for the module+profile read list, which the *ForModuleAndProfile
    endpoint doesn't compute.

    The ``queues`` action renders the compute resource's ``BatchQueue`` protos
    directly via ``to_jsonable`` (after overlaying this deployment's defaults).
    """

    request: AiravataRequest
    lookup_field = "app_deployment_id"

    def _has_write(self, request: AiravataRequest, app_deployment_id: str) -> bool:
        """Per-deployment sharing-registry WRITE lookup (legacy
        ``user_has_access``)."""
        from django_airavata.apps.api import serializers

        return serializers.user_has_access(request, app_deployment_id, "WRITE")

    def _app_catalog(self) -> ApplicationCatalogServiceStub:
        from airavata.services.application_catalog_service_pb2_grpc import (
            ApplicationCatalogServiceStub,
        )

        return ApplicationCatalogServiceStub(self.request.airavata_channel)

    def _deployment(
        self, app_deployment_id: str
    ) -> app_deployment_pb2.ApplicationDeploymentDescription:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        return self._app_catalog().GetApplicationDeployment(
            pb2.GetApplicationDeploymentRequest(app_deployment_id=app_deployment_id)
        )

    def _deployment_with_access(
        self,
        deployment: app_deployment_pb2.ApplicationDeploymentDescription,
        request: AiravataRequest,
    ) -> ac_pb2.ApplicationDeploymentWithAccess:
        # Per-deployment sharing WRITE flag the *ForModuleAndProfile endpoint
        # doesn't compute; build the WithAccess proto in the portal.
        from airavata.model.commons import (
            commons_pb2,
        )
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        return pb2.ApplicationDeploymentWithAccess(
            application_deployment=deployment,
            access=commons_pb2.AccessFlags(
                is_owner=False,
                user_has_write_access=self._has_write(
                    request, deployment.app_deployment_id
                ),
            ),
        )

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

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
            deployments = (
                self._app_catalog()
                .GetDeploymentsForModuleAndProfile(
                    pb2.GetDeploymentsForModuleAndProfileRequest(
                        app_module_id=app_module_id,
                        group_resource_profile_id=group_resource_profile_id,
                    )
                )
                .application_deployments
            )
            return web.Response(
                [self._deployment_with_access(d, request) for d in deployments]
            )
        deployments = (
            self._app_catalog()
            .GetAccessibleApplicationDeploymentsWithAccess(
                pb2.GetAccessibleApplicationDeploymentsRequest(
                    gateway_id=self.gateway_id
                )
            )
            .deployments
        )
        return web.Response(list(deployments))

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        return web.Response(
            self._app_catalog().GetApplicationDeploymentWithAccess(
                pb2.GetApplicationDeploymentRequest(
                    app_deployment_id=self.kwargs[self.lookup_field]
                )
            )
        )

    @staticmethod
    def _proto_command_object(
        data: dict[str, Any],
    ) -> app_deployment_pb2.CommandObject:
        from airavata.model.appcatalog.appdeployment import (
            app_deployment_pb2,
        )

        return app_deployment_pb2.CommandObject(
            command=data.get("command") or "",
            command_order=data.get("command_order") or 0,
        )

    @staticmethod
    def _proto_set_env_paths(
        data: dict[str, Any],
    ) -> app_deployment_pb2.SetEnvPaths:
        from airavata.model.appcatalog.appdeployment import (
            app_deployment_pb2,
        )

        return app_deployment_pb2.SetEnvPaths(
            name=data.get("name") or "",
            value=data.get("value") or "",
            env_path_order=data.get("env_path_order") or 0,
        )

    @staticmethod
    def _parallelism_int(value: object) -> parallelism_pb2.ApplicationParallelismType:
        """``parallelism`` -> proto ``ApplicationParallelismType`` int (member
        NAME or proto int; ``None`` / ``""`` -> 0)."""
        from airavata.model.parallelism import (
            parallelism_pb2,
        )

        from django_airavata.apps.api.experiment_builder import proto_enum_value

        return proto_enum_value(parallelism_pb2.ApplicationParallelismType, value)

    def _build_application_deployment(
        self, data: dict[str, Any]
    ) -> app_deployment_pb2.ApplicationDeploymentDescription:
        """Build an ``ApplicationDeploymentDescription`` proto from the
        (snake_case) request body. Mirrors the SDK
        ``research_resources._build_application_deployment`` field-for-field."""
        from airavata.model.appcatalog.appdeployment import (
            app_deployment_pb2,
        )

        return app_deployment_pb2.ApplicationDeploymentDescription(
            app_module_id=data.get("app_module_id") or "",
            compute_host_id=data.get("compute_host_id") or "",
            executable_path=data.get("executable_path") or "",
            parallelism=self._parallelism_int(data.get("parallelism")),
            app_deployment_description=data.get("app_deployment_description") or "",
            module_load_cmds=[
                self._proto_command_object(c)
                for c in (data.get("module_load_cmds") or [])
            ],
            lib_prepend_paths=[
                self._proto_set_env_paths(p)
                for p in (data.get("lib_prepend_paths") or [])
            ],
            lib_append_paths=[
                self._proto_set_env_paths(p)
                for p in (data.get("lib_append_paths") or [])
            ],
            set_environment=[
                self._proto_set_env_paths(p)
                for p in (data.get("set_environment") or [])
            ],
            pre_job_commands=[
                self._proto_command_object(c)
                for c in (data.get("pre_job_commands") or [])
            ],
            post_job_commands=[
                self._proto_command_object(c)
                for c in (data.get("post_job_commands") or [])
            ],
            default_queue_name=data.get("default_queue_name") or "",
            default_node_count=data.get("default_node_count") or 0,
            default_cpu_count=data.get("default_cpu_count") or 0,
            default_walltime=data.get("default_walltime") or 0,
            editable_by_user=bool(data.get("editable_by_user", False)),
        )

    def _body(self) -> dict[str, Any]:
        return self.request.data if isinstance(self.request.data, dict) else {}

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        # Build the proto, register, then re-fetch the WithAccess proto — the
        # server now supplies the access flags (the SDK's hardcoded has_write=True
        # is vestigial; the creator always has write).
        deployment = self._build_application_deployment(self._body())
        app_deployment_id = (
            self._app_catalog()
            .RegisterApplicationDeployment(
                pb2.RegisterApplicationDeploymentRequest(
                    gateway_id=self.gateway_id, application_deployment=deployment
                )
            )
            .app_deployment_id
        )
        result = self._app_catalog().GetApplicationDeploymentWithAccess(
            pb2.GetApplicationDeploymentRequest(app_deployment_id=app_deployment_id)
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        # The proto is rebuilt wholesale from the body (path id forced; update is
        # full-replace), pushed, then re-fetched as the WithAccess proto.
        app_deployment_id = self.kwargs[self.lookup_field]
        deployment = self._build_application_deployment(self._body())
        deployment.app_deployment_id = app_deployment_id
        self._app_catalog().UpdateApplicationDeployment(
            pb2.UpdateApplicationDeploymentRequest(
                app_deployment_id=app_deployment_id, application_deployment=deployment
            )
        )
        result = self._app_catalog().GetApplicationDeploymentWithAccess(
            pb2.GetApplicationDeploymentRequest(app_deployment_id=app_deployment_id)
        )
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def perform_destroy(
        self, instance: app_deployment_pb2.ApplicationDeploymentDescription
    ) -> None:
        from airavata.services import (
            application_catalog_service_pb2 as pb2,
        )

        self._app_catalog().DeleteApplicationDeployment(
            pb2.DeleteApplicationDeploymentRequest(
                app_deployment_id=instance.app_deployment_id
            )
        )

    @override
    def get_instance(
        self, lookup_value: str
    ) -> app_deployment_pb2.ApplicationDeploymentDescription:
        return self._deployment(lookup_value)

    @web.action(detail=True)
    def queues(self, request: AiravataRequest, app_deployment_id: str) -> web.Response:
        """Return queues for this deployment with defaults overridden by deployment defaults if they exist"""
        from airavata.services import resource_service_pb2 as rpb2
        from airavata.services.resource_service_pb2_grpc import (
            ResourceServiceStub,
        )

        from django_airavata.apps.api.proto_render import to_jsonable

        app_deployment = self._deployment(app_deployment_id)
        compute_resource = ResourceServiceStub(
            request.airavata_channel
        ).GetComputeResource(
            rpb2.GetComputeResourceRequest(
                compute_resource_id=app_deployment.compute_host_id
            )
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

    request: AiravataRequest
    lookup_field = "compute_resource_id"

    def _resource(self) -> ResourceServiceStub:
        from airavata.services.resource_service_pb2_grpc import (
            ResourceServiceStub,
        )

        return ResourceServiceStub(self.request.airavata_channel)

    def _compute_resource(
        self, compute_resource_id: str
    ) -> compute_resource_pb2.ComputeResourceDescription:
        from airavata.services import resource_service_pb2 as pb2

        return self._resource().GetComputeResource(
            pb2.GetComputeResourceRequest(compute_resource_id=compute_resource_id)
        )

    def _compute_resource_names(self) -> dict[str, str]:
        from airavata.services import resource_service_pb2 as pb2

        return dict(
            self._resource()
            .GetAllComputeResourceNames(pb2.GetAllComputeResourceNamesRequest())
            .compute_resource_names
        )

    @override
    def get_instance(
        self, lookup_value: str
    ) -> compute_resource_pb2.ComputeResourceDescription:
        return self._compute_resource(lookup_value)

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return web.Response(self.get_object())

    @web.action(detail=False)
    def all_names(self, request: HttpRequest) -> web.Response:
        """Return a map of compute resource names keyed by resource id."""
        return web.Response(self._compute_resource_names())

    @web.action(detail=False)
    def all_names_list(self, request: HttpRequest) -> web.Response:
        """Return a list of compute resource names keyed by resource id."""
        all_names = self._compute_resource_names()
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
    def queues(self, request: HttpRequest, compute_resource_id: str) -> web.Response:
        """Return the resource's batch-queue names (a plain string list)."""
        details = self._compute_resource(compute_resource_id)
        return web.Response([queue.queue_name for queue in details.batch_queues])


def _data_product_has_write(
    request: AiravataRequest, data_product: rc.DataProductModel
) -> bool:
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
    """Data product resource. The read fetches the bare ``DataProductModel`` via
    the raw stub, then builds the ``DataProductWithAccess`` proto in the portal
    (renderer flattens it): ``is_owner`` is owner==caller and
    ``user_has_write_access`` is computed via :func:`_data_product_has_write`
    (the server can't derive the portal-specific shared-dir rule).

    The PUT write body carries ``file_content_text`` (snake_case); the legacy
    ``fileContentText`` wire key is still accepted for compatibility.
    """

    request: AiravataRequest
    permission_classes = [web.IsAuthenticated, DataProductSharedDirPermission]

    def _data_product(self) -> DataProductServiceStub:
        from airavata.services.data_product_service_pb2_grpc import (
            DataProductServiceStub,
        )

        return DataProductServiceStub(self.request.airavata_channel)

    def _get_data_product(self, data_product_uri: str) -> rc.DataProductModel:
        from airavata.services import data_product_service_pb2 as pb2

        return self._data_product().GetDataProduct(
            pb2.GetDataProductRequest(product_uri=data_product_uri)
        )

    def get(self, request: AiravataRequest) -> web.Response:
        from airavata.model.commons import (
            commons_pb2,
        )
        from airavata.services import experiment_service_pb2 as pb2

        data_product_uri = request.query_params["product-uri"]
        data_product = self._get_data_product(data_product_uri)
        owner = data_product.owner_name
        is_owner = bool(owner) and owner == request.user.username
        return web.Response(
            pb2.DataProductWithAccess(
                data_product=data_product,
                access=commons_pb2.AccessFlags(
                    is_owner=is_owner,
                    user_has_write_access=_data_product_has_write(
                        request, data_product
                    ),
                ),
            )
        )

    def put(self, request: AiravataRequest) -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        data_product_uri = request.query_params["product-uri"]
        data_product = self._get_data_product(data_product_uri)
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
            _user_storage_stub(request).UploadFile(
                fs_pb2.UploadFileRequest(
                    storage_resource_id="",
                    path=file_path,
                    content=file_content.encode("utf-8"),
                    name=data_product.product_name or os.path.basename(file_path),
                    content_type="",
                )
            )
            return self.get(request=request)
        else:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)


@web.api_view(http_method_names=["POST"])
def upload_input_file(request: AiravataRequest) -> JsonResponse:
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
def tus_upload_finish(request: AiravataRequest) -> JsonResponse:
    uploadURL = request.POST["uploadURL"]

    def save_upload(
        file_path: str, file_name: str, file_type: str
    ) -> rc.DataProductModel:
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
        log.error(
            "Failed to finish tus upload", exc_info=True, extra={"request": request}
        )
        return exceptions.generic_json_exception_response(e, status=400)


@web.api_view()
def download(request: AiravataRequest) -> FileResponse:
    """Stream the bytes of a data product's first replica.

    Resolves ``?data-product-uri=`` via the research registry and streams the
    file from the storage facade.
    """
    from airavata.services import file_service_pb2 as fs_pb2

    data_product_uri = request.GET.get("data-product-uri", "")
    try:
        data_product = _get_data_product_proto(request, data_product_uri)
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
    resp = _user_storage_stub(request).DownloadFile(
        fs_pb2.DownloadFileRequest(storage_resource_id="", path=file_path)
    )
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
def delete_file(request: AiravataRequest) -> HttpResponse:
    # TODO check that user has write access to this file using sharing API
    from airavata.services import file_service_pb2 as fs_pb2

    data_product_uri = request.GET.get("data-product-uri", "")
    data_product = None
    try:
        data_product = _get_data_product_proto(request, data_product_uri)
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
        _user_storage_stub(request).DeleteFile(
            fs_pb2.DeleteFileRequest(storage_resource_id="", path=file_path)
        )
        return HttpResponse(status=204)
    except ObjectDoesNotExist as e:
        raise Http404(str(e)) from e


class UserProfileViewSet(
    web.mixins.RetrieveModelMixin, web.mixins.ListModelMixin, GenericAPIBackedViewSet
):
    """User profiles resource (read-only) — raw ``UserProfile`` protos (no
    envelope) from the user-profile stub."""

    request: AiravataRequest

    def _user_profiles(self) -> UserProfileServiceStub:
        from airavata.services.user_profile_service_pb2_grpc import (
            UserProfileServiceStub,
        )

        return UserProfileServiceStub(self.request.airavata_channel)

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        from airavata.services import user_profile_service_pb2 as pb2

        response = self._user_profiles().GetAllUserProfilesInGateway(
            pb2.GetAllUserProfilesInGatewayRequest(
                gateway_id=self.gateway_id, offset=0, limit=-1
            )
        )
        return web.Response(list(response.user_profiles))

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        # Look up by the authenticated user, not the URL lookup value.
        from airavata.services import user_profile_service_pb2 as pb2

        return web.Response(
            self._user_profiles().GetUserProfileById(
                pb2.GetUserProfileByIdRequest(
                    user_id=request.user.username, gateway_id=self.gateway_id
                )
            )
        )


class GroupResourceProfileViewSet(APIBackedViewSet):
    """Group resource profiles. SDK returns ``WithAccess[GroupResourceProfile]``.

    ``user_has_write_access`` is a composite the SDK can't derive: WRITE sharing
    on the profile id AND READ access to every credential token (the default
    token plus each compute-preference resource-specific token). The ViewSet
    computes it in ``_compute_has_write`` and passes it in as ``has_write``. The
    list endpoint is unpaginated, matching the pre-migration contract.
    """

    request: AiravataRequest
    lookup_field = "group_resource_profile_id"

    def _grp_profile(self) -> GroupResourceProfileServiceStub:
        from airavata.services.group_resource_profile_service_pb2_grpc import (
            GroupResourceProfileServiceStub,
        )

        return GroupResourceProfileServiceStub(self.request.airavata_channel)

    def _with_access(
        self, profile: group_resource_profile_pb2.GroupResourceProfile
    ) -> grp_pb2.GroupResourceProfileWithAccess:
        # Gateway-catalog: no owner; user_has_write_access is the portal-computed
        # composite the server can't derive (see _compute_has_write).
        from airavata.model.commons import (
            commons_pb2,
        )
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        return pb2.GroupResourceProfileWithAccess(
            group_resource_profile=profile,
            access=commons_pb2.AccessFlags(
                is_owner=False, user_has_write_access=self._compute_has_write(profile)
            ),
        )

    # get_object()/destroy still uses this.
    @override
    def get_list(
        self,
    ) -> builtins.list[group_resource_profile_pb2.GroupResourceProfile]:
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        return list(
            self._grp_profile()
            .GetGroupResourceList(pb2.GetGroupResourceListRequest())
            .group_resource_profiles
        )

    @override
    def get_instance(
        self, lookup_value: str
    ) -> group_resource_profile_pb2.GroupResourceProfile:
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        return self._grp_profile().GetGroupResourceProfile(
            pb2.GetGroupResourceProfileRequest(group_resource_profile_id=lookup_value)
        )

    def _compute_has_write(
        self, profile: group_resource_profile_pb2.GroupResourceProfile
    ) -> bool:
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

        def check_token(token: str) -> bool:
            return not token or user_has_access(request, token, "READ")

        return all(map(check_token, tokens))

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        # Build the WithAccess proto per profile with the composite write flag.
        return web.Response([self._with_access(p) for p in self.get_list()])

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        profile = self.get_instance(self.kwargs[self.lookup_field])
        if profile is None:
            raise Http404
        return web.Response(self._with_access(profile))

    def _build_group_compute_resource_preference(
        self, data: dict[str, Any]
    ) -> group_resource_profile_pb2.GroupComputeResourcePreference:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        from django_airavata.apps.api.experiment_builder import proto_enum_value

        sp = data.get("specific_preferences")
        resource_type = proto_enum_value(grp.ResourceType, data.get("resource_type"))
        msg = grp.GroupComputeResourcePreference(
            compute_resource_id=data.get("compute_resource_id", "") or "",
            group_resource_profile_id=data.get("group_resource_profile_id", "") or "",
            override_by_airavata=bool(data.get("overrideby_airavata", False)),
            login_user_name=data.get("login_user_name", "") or "",
            scratch_location=data.get("scratch_location", "") or "",
            resource_specific_credential_store_token=data.get(
                "resource_specific_credential_store_token", ""
            )
            or "",
            resource_type=resource_type,
        )
        # Resolve the oneof: prefer an explicit specific_preferences, else infer
        # from the flattened allocation_project_number / resource_type / aws fields.
        slurm_data = None
        aws_data = None
        if isinstance(sp, dict):
            if "slurm" in sp and isinstance(sp["slurm"], dict):
                slurm_data = dict(sp["slurm"])
            elif "aws" in sp and isinstance(sp["aws"], dict):
                aws_data = dict(sp["aws"])
            elif "region" in sp or "preferred_ami_id" in sp:
                aws_data = dict(sp)
            elif sp:
                slurm_data = dict(sp)
        if slurm_data is None and aws_data is None:
            if resource_type == grp.ResourceType.AWS or "region" in data:
                aws_data = {}
            elif (
                "allocation_project_number" in data
                or resource_type == grp.ResourceType.SLURM
            ):
                slurm_data = {}
        if "allocation_project_number" in data and slurm_data is not None:
            slurm_data.setdefault(
                "allocation_project_number", data["allocation_project_number"]
            )
        if slurm_data is not None:
            msg.specific_preferences.CopyFrom(
                grp.EnvironmentSpecificPreferences(
                    slurm=self._build_slurm_pref(slurm_data)
                )
            )
        elif aws_data is not None:
            msg.specific_preferences.CopyFrom(
                grp.EnvironmentSpecificPreferences(aws=self._build_aws_pref(aws_data))
            )
        return msg

    @staticmethod
    def _build_ssh_provisioner_config(
        c: dict[str, Any],
    ) -> group_resource_profile_pb2.GroupAccountSSHProvisionerConfig:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.GroupAccountSSHProvisionerConfig(
            resource_id=c.get("resource_id", "") or "",
            group_resource_profile_id=c.get("group_resource_profile_id", "") or "",
            config_name=c.get("config_name", "") or "",
            config_value=c.get("config_value", "") or "",
        )

    @staticmethod
    def _build_reservation(
        r: dict[str, Any],
    ) -> group_resource_profile_pb2.ComputeResourceReservation:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.ComputeResourceReservation(
            reservation_id=r.get("reservation_id", "") or "",
            reservation_name=r.get("reservation_name", "") or "",
            queue_names=list(r.get("queue_names", []) or []),
            start_time=r.get("start_time", 0) or 0,
            end_time=r.get("end_time", 0) or 0,
        )

    def _build_slurm_pref(
        self, s: dict[str, Any]
    ) -> group_resource_profile_pb2.SlurmComputeResourcePreference:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.SlurmComputeResourcePreference(
            allocation_project_number=s.get("allocation_project_number", "") or "",
            preferred_batch_queue=s.get("preferred_batch_queue", "") or "",
            quality_of_service=s.get("quality_of_service", "") or "",
            usage_reporting_gateway_id=s.get("usage_reporting_gateway_id", "") or "",
            ssh_account_provisioner=s.get("ssh_account_provisioner", "") or "",
            group_ssh_account_provisioner_configs=[
                self._build_ssh_provisioner_config(c)
                for c in (s.get("group_ssh_account_provisioner_configs", []) or [])
            ],
            ssh_account_provisioner_additional_info=s.get(
                "ssh_account_provisioner_additional_info", ""
            )
            or "",
            reservations=[
                self._build_reservation(r) for r in (s.get("reservations", []) or [])
            ],
        )

    @staticmethod
    def _build_aws_pref(
        a: dict[str, Any],
    ) -> group_resource_profile_pb2.AwsComputeResourcePreference:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.AwsComputeResourcePreference(
            region=a.get("region", "") or "",
            preferred_ami_id=a.get("preferred_ami_id", "") or "",
            preferred_instance_type=a.get("preferred_instance_type", "") or "",
        )

    @staticmethod
    def _build_compute_resource_policy(
        d: dict[str, Any],
    ) -> group_resource_profile_pb2.ComputeResourcePolicy:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.ComputeResourcePolicy(
            resource_policy_id=d.get("resource_policy_id", "") or "",
            compute_resource_id=d.get("compute_resource_id", "") or "",
            group_resource_profile_id=d.get("group_resource_profile_id", "") or "",
            allowed_batch_queues=list(d.get("allowed_batch_queues", []) or []),
        )

    @staticmethod
    def _build_batch_queue_resource_policy(
        d: dict[str, Any],
    ) -> group_resource_profile_pb2.BatchQueueResourcePolicy:
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.BatchQueueResourcePolicy(
            resource_policy_id=d.get("resource_policy_id", "") or "",
            compute_resource_id=d.get("compute_resource_id", "") or "",
            group_resource_profile_id=d.get("group_resource_profile_id", "") or "",
            queuename=d.get("queuename", "") or "",
            max_allowed_nodes=d.get("max_allowed_nodes", 0) or 0,
            max_allowed_cores=d.get("max_allowed_cores", 0) or 0,
            max_allowed_walltime=d.get("max_allowed_walltime", 0) or 0,
        )

    def _build_group_resource_profile(
        self, data: dict[str, Any]
    ) -> group_resource_profile_pb2.GroupResourceProfile:
        """Build a ``GroupResourceProfile`` proto from the (snake_case) request
        body. ``gateway_id`` is forced from this gateway. Mirrors the SDK
        ``compute_resources.build_group_resource_profile`` field-for-field."""
        from airavata.model.appcatalog.groupresourceprofile import (
            group_resource_profile_pb2 as grp,
        )

        return grp.GroupResourceProfile(
            gateway_id=self.gateway_id or "",
            group_resource_profile_id=data.get("group_resource_profile_id", "") or "",
            group_resource_profile_name=data.get("group_resource_profile_name", "")
            or "",
            compute_preferences=[
                self._build_group_compute_resource_preference(p)
                for p in (data.get("compute_preferences", []) or [])
            ],
            compute_resource_policies=[
                self._build_compute_resource_policy(p)
                for p in (data.get("compute_resource_policies", []) or [])
            ],
            batch_queue_resource_policies=[
                self._build_batch_queue_resource_policy(p)
                for p in (data.get("batch_queue_resource_policies", []) or [])
            ],
            default_credential_store_token=data.get(
                "default_credential_store_token", ""
            )
            or "",
        )

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        data = request.data if isinstance(request.data, dict) else {}
        profile = self._build_group_resource_profile(data)
        # CreateGroupResourceProfile returns the persisted profile (server-minted
        # id + tokens); re-fetch to resolve the composite write flag against it.
        created = self._grp_profile().CreateGroupResourceProfile(
            pb2.CreateGroupResourceProfileRequest(group_resource_profile=profile)
        )
        profile = self.get_instance(created.group_resource_profile_id)
        return web.Response(
            self._with_access(profile), status=web.status.HTTP_201_CREATED
        )

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        group_resource_profile_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        profile = self._build_group_resource_profile(data)
        profile.group_resource_profile_id = group_resource_profile_id
        # The server reconciles the child prefs/policies + updates and returns the
        # reconciled profile; rebuild the portal composite write flag (WRITE +
        # per-credential READ, which the server can't derive) on it, like create/read.
        result = self._grp_profile().UpdateGroupResourceProfileReconciled(
            pb2.UpdateGroupResourceProfileRequest(
                group_resource_profile_id=group_resource_profile_id,
                group_resource_profile=profile,
            )
        )
        return web.Response(self._with_access(result.group_resource_profile))

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def destroy(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            group_resource_profile_service_pb2 as pb2,
        )

        group_resource_profile_id = self.kwargs[self.lookup_field]
        self._grp_profile().RemoveGroupResourceProfile(
            pb2.RemoveGroupResourceProfileRequest(
                group_resource_profile_id=group_resource_profile_id
            )
        )
        return web.Response(status=web.status.HTTP_204_NO_CONTENT)


class SharedEntityViewSet(
    web.mixins.RetrieveModelMixin, web.mixins.UpdateModelMixin, GenericAPIBackedViewSet
):
    """Shared-entities resource — wired to the raw SharingService stub.

    Reads (``retrieve`` / ``all``) call ``GetSharedEntity`` / ``GetAllSharedEntity``
    (each a single server call returning a composed ``SharedEntity`` proto: the
    owner + per-user ``UserProfile`` protos + per-group ``GroupWithAccess``
    envelopes, plus ``is_owner`` / ``has_sharing_permission``). The view projects
    that proto onto a dict matching the read contract — the renderer flattens each
    nested ``UserProfile`` proto and each ``GroupWithAccess`` proto (its
    ``GroupAccessFlags`` merged onto the group as siblings, identical to the SDK
    ``WithGroupAccess`` envelope), so the JSON the frontend reads is unchanged.

    Write model (``update`` / ``partial_update`` / ``merge``): the body's
    NAME-keyed desired permission maps are sent to ``SetEntitySharing`` in a single
    call — the server reads the current direct grants and computes the grant/revoke
    diff (implied-permission expansion + owner preservation) itself.
    ``_normalize_permission`` accepts either the legacy integer or the member-NAME
    ``permission_type`` (portal-only input shaping).
    """

    request: AiravataRequest
    lookup_field = "entity_id"

    def _sharing(self) -> SharingServiceStub:
        from airavata.services.sharing_service_pb2_grpc import (
            SharingServiceStub,
        )

        return SharingServiceStub(self.request.airavata_channel)

    @staticmethod
    def _shared_entity(se: sharing_pb2.SharedEntity) -> dict[str, Any]:
        """Project a proto ``SharedEntity`` onto the read-contract dict.

        Each ``user.user`` is the raw ``UserProfile`` proto and each
        ``group.group`` is the raw ``GroupWithAccess`` proto; the renderer recurses
        the dict and flattens both (the ``GroupAccessFlags`` merge onto the group as
        siblings — same shape the SDK ``WithGroupAccess`` envelope produced)."""
        return {
            "entity_id": se.entity_id,
            "owner": se.owner,
            "user_permissions": [
                {"user": up.user, "permission_type": up.permission_type}
                for up in se.user_permissions
            ],
            "group_permissions": [
                {"group": gp.group, "permission_type": gp.permission_type}
                for gp in se.group_permissions
            ],
            "is_owner": se.is_owner,
            "has_sharing_permission": se.has_sharing_permission,
        }

    def _get_shared_entity(self, entity_id: str) -> sharing_pb2.SharedEntity:
        from airavata.services import sharing_service_pb2 as pb2

        return self._sharing().GetSharedEntity(
            pb2.GetSharedEntityRequest(entity_id=entity_id)
        )

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        entity_id = self.kwargs[self.lookup_field]
        return web.Response(self._shared_entity(self._get_shared_entity(entity_id)))

    @web.action(methods=["get"], detail=True)
    def all(
        self, request: AiravataRequest, entity_id: str | None = None
    ) -> web.Response:
        """Load direct plus indirectly (inherited) shared permissions."""
        from airavata.services import sharing_service_pb2 as pb2

        se = self._sharing().GetAllSharedEntity(
            pb2.GetSharedEntityRequest(entity_id=entity_id)
        )
        return web.Response(self._shared_entity(se))

    @classmethod
    def _normalize_permission(cls, value: int | str) -> str:
        """Coerce a body ``permission_type`` to the member NAME string.

        Accepts either a legacy ``ResourcePermissionType`` integer (resolved via
        the proto enum's own ``Name()``, so it tracks the proto numbering) or the
        new member NAME, so the write path is stable across the cutover.
        """
        if isinstance(value, int):
            from airavata.model.group.group_manager_pb2 import (
                ResourcePermissionType,
            )

            return ResourcePermissionType.Name(value)
        return value

    @classmethod
    def _permission_map(
        cls, permissions: list[dict[str, Any]], id_field: str
    ) -> dict[str, str]:
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

    def _existing_permission_maps(
        self, entity_id: str
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Return ``(existing_user_map, existing_group_map)`` from the server.

        Reads the *directly* granted permissions (the only editable ones) off the
        raw ``SharedEntity`` proto and reduces them to ``{id -> permission_name}``
        maps — the ``existing`` state ``merge`` overlays the body onto. (``group``
        is a ``GroupWithAccess`` proto, so the id is under ``group.group.id``.)
        """
        existing = self._get_shared_entity(entity_id)
        existing_users = {
            up.user.airavata_internal_user_id: up.permission_type
            for up in existing.user_permissions
        }
        existing_groups = {
            gp.group.group.id: gp.permission_type for gp in existing.group_permissions
        }
        return existing_users, existing_groups

    def _apply(
        self,
        entity_id: str,
        new_user_map: dict[str, Any],
        new_group_map: dict[str, Any],
    ) -> None:
        from airavata.services import sharing_service_pb2 as pb2

        # SetEntitySharing reads the current grants server-side, so the portal no
        # longer fetches "existing" to diff — it just sends the desired state.
        self._sharing().SetEntitySharing(
            pb2.SetEntitySharingRequest(
                resource_id=entity_id,
                user_permissions=new_user_map or {},
                group_permissions=new_group_map or {},
            )
        )

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
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

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @web.action(methods=["put"], detail=True)
    def merge(
        self, request: AiravataRequest, entity_id: str | None = None
    ) -> web.Response:
        """Merge the request body's grants on top of the existing settings.

        Unlike ``update`` (which replaces the sharing settings), ``merge`` adds
        the body's permissions to the existing ones, so the effective "new"
        state is ``existing | body`` (body wins on conflicting ids — it appears
        last, matching the old serializer's list concatenation + dict build).
        """
        if entity_id is None:
            raise Http404
        body = request.data if isinstance(request.data, dict) else {}

        existing_users, existing_groups = self._existing_permission_maps(entity_id)
        body_user_map = self._permission_map(
            body.get("user_permissions", []), "airavata_internal_user_id"
        )
        body_group_map = self._permission_map(body.get("group_permissions", []), "id")
        # Merge: existing first, body overrides on conflict (body is "last").
        # The existing maps are still needed here to build the merged desired
        # state; the server diffs that against the current grants itself.
        merged_users = {**existing_users, **body_user_map}
        merged_groups = {**existing_groups, **body_group_map}

        self._apply(entity_id, merged_users, merged_groups)
        return web.Response(self._shared_entity(self._get_shared_entity(entity_id)))


class CredentialSummaryViewSet(
    web.mixins.RetrieveModelMixin,
    web.mixins.ListModelMixin,
    web.mixins.DestroyModelMixin,
    GenericAPIBackedViewSet,
):
    """Credential-summaries resource — wired to the raw CredentialService stub.

    Reads return the ``CredentialSummaryWithAccess`` proto (renderer flattens
    it). ``retrieve`` uses ``GetCredentialSummaryWithAccess``, where the server
    supplies the access flags directly. The list paths
    (``list``/``ssh``/``password``) fetch the bare summaries via
    ``GetAllCredentialSummaries`` and build the WithAccess envelope in the
    portal: ``is_owner`` is always False (a credential has no owner) and
    ``user_has_write_access`` is the per-token sharing WRITE lookup (matching the
    SDK helper). ``list`` (no type) concatenates the SSH and PASSWD typed lists.

    Credentials are created via the typed ``create_ssh``/``create_password``
    actions (the generic create/update verbs are not exposed); each builds the
    request, calls the register RPC, then re-fetches via
    ``GetCredentialSummaryWithAccess`` so the shape matches the read path.
    ``destroy`` dispatches on the summary ``SummaryType`` (``DeleteSSHPubKey`` /
    ``DeletePWDCredential``).
    """

    request: AiravataRequest

    def _credentials(self) -> CredentialServiceStub:
        from airavata.services.credential_service_pb2_grpc import (
            CredentialServiceStub,
        )

        return CredentialServiceStub(self.request.airavata_channel)

    def _with_access(
        self, summary: credential_store_pb2.CredentialSummary
    ) -> cred_pb2.CredentialSummaryWithAccess:
        # Credential is ownerless; user_has_write_access is the per-token sharing
        # WRITE lookup (the server can't fold this into the bare summary list).
        from airavata.model.commons import (
            commons_pb2,
        )
        from airavata.services import credential_service_pb2 as pb2

        return pb2.CredentialSummaryWithAccess(
            credential_summary=summary,
            access=commons_pb2.AccessFlags(
                is_owner=False,
                user_has_write_access=serializers.user_has_access(
                    self.request, summary.token, "WRITE"
                ),
            ),
        )

    def _all_summaries(
        self, summary_type: credential_store_pb2.SummaryType
    ) -> builtins.list[credential_store_pb2.CredentialSummary]:
        from airavata.services import credential_service_pb2 as pb2

        response = self._credentials().GetAllCredentialSummaries(
            pb2.GetAllCredentialSummariesRequest(
                gateway_id=self.gateway_id, type=summary_type
            )
        )
        return list(response.credential_summaries)

    # get_object()/destroy uses this — bare summary carries .type / .token for
    # the type-dispatched delete.
    @override
    def get_instance(self, lookup_value: str) -> credential_store_pb2.CredentialSummary:
        from airavata.services import credential_service_pb2 as pb2

        return self._credentials().GetCredentialSummary(
            pb2.GetCredentialSummaryRequest(
                token_id=lookup_value, gateway_id=self.gateway_id
            )
        )

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        pb2 = serializers._credential_store_pb2()
        summaries = self._all_summaries(pb2.SummaryType.SSH) + self._all_summaries(
            pb2.SummaryType.PASSWD
        )
        return web.Response([self._with_access(s) for s in summaries])

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import credential_service_pb2 as pb2

        lookup_value = self.kwargs[self.lookup_field or "pk"]
        return web.Response(
            self._credentials().GetCredentialSummaryWithAccess(
                pb2.GetCredentialSummaryRequest(
                    token_id=lookup_value, gateway_id=self.gateway_id
                )
            )
        )

    @web.action(detail=False)
    def ssh(self, request: AiravataRequest) -> web.Response:
        pb2 = serializers._credential_store_pb2()
        return web.Response(
            [self._with_access(s) for s in self._all_summaries(pb2.SummaryType.SSH)]
        )

    @web.action(detail=False)
    def password(self, request: AiravataRequest) -> web.Response:
        pb2 = serializers._credential_store_pb2()
        return web.Response(
            [self._with_access(s) for s in self._all_summaries(pb2.SummaryType.PASSWD)]
        )

    def _get_with_access(self, token_id: str) -> cred_pb2.CredentialSummaryWithAccess:
        from airavata.services import credential_service_pb2 as pb2

        return self._credentials().GetCredentialSummaryWithAccess(
            pb2.GetCredentialSummaryRequest(
                token_id=token_id, gateway_id=self.gateway_id
            )
        )

    @web.action(methods=["post"], detail=False)
    def create_ssh(self, request: AiravataRequest) -> web.Response:
        from airavata.services import credential_service_pb2 as pb2

        if "description" not in request.data:
            raise web.ParseError("'description' is required in request")
        # gateway_id / username come from the request context; only description
        # is read from the body (mirrors the SDK create_ssh_credential helper).
        token = (
            self._credentials()
            .GenerateAndRegisterSSHKeys(
                pb2.GenerateAndRegisterSSHKeysRequest(
                    gateway_id=self.gateway_id,
                    username=self.username,
                    description=request.data.get("description") or "",
                )
            )
            .token
        )
        return web.Response(self._get_with_access(token))

    @web.action(methods=["post"], detail=False)
    def create_password(self, request: AiravataRequest) -> web.Response:
        from airavata.services import credential_service_pb2 as pb2

        if (
            "username" not in request.data
            or "password" not in request.data
            or "description" not in request.data
        ):
            raise web.ParseError(
                "'username', 'password' and 'description' are all required in request"
            )
        # gateway_id / portal_user_name come from the request context; the body's
        # username is the login_user_name (mirrors create_password_credential).
        cs = serializers._credential_store_pb2()
        password_credential = cs.PasswordCredential(
            gateway_id=self.gateway_id or "",
            portal_user_name=self.username or "",
            login_user_name=request.data.get("username") or "",
            password=request.data.get("password") or "",
            description=request.data.get("description") or "",
        )
        token = (
            self._credentials()
            .RegisterPwdCredential(
                pb2.RegisterPwdCredentialRequest(
                    gateway_id=self.gateway_id, password_credential=password_credential
                )
            )
            .token
        )
        return web.Response(self._get_with_access(token))

    @override
    def perform_destroy(self, instance: credential_store_pb2.CredentialSummary) -> None:
        # get_object yields the bare CredentialSummary; dispatch on SummaryType.
        from airavata.services import credential_service_pb2 as pb2

        cs = serializers._credential_store_pb2()
        if instance.type == cs.SummaryType.SSH:
            self._credentials().DeleteSSHPubKey(
                pb2.DeleteSSHPubKeyRequest(
                    token_id=instance.token, gateway_id=self.gateway_id
                )
            )
        elif instance.type == cs.SummaryType.PASSWD:
            self._credentials().DeletePWDCredential(
                pb2.DeletePWDCredentialRequest(
                    token_id=instance.token, gateway_id=self.gateway_id
                )
            )


class CurrentGatewayResourceProfile(web.APIView):
    """Current gateway resource profile. The read fetches the bare
    ``GatewayResourceProfile`` proto via the raw stub, then builds the
    ``GatewayResourceProfileWithAccess`` proto in the portal (renderer flattens
    it).

    A gateway-level resource: ``is_owner`` is always False and
    ``user_has_write_access`` is the gateway-admin flag the view computes (the
    server can't derive it).
    """

    request: AiravataRequest

    def _gw_profile(self) -> GatewayResourceProfileServiceStub:
        from airavata.services.gateway_resource_profile_service_pb2_grpc import (
            GatewayResourceProfileServiceStub,
        )

        return GatewayResourceProfileServiceStub(self.request.airavata_channel)

    @staticmethod
    def _build_compute_resource_preference(
        data: dict[str, Any],
    ) -> gateway_profile_pb2.ComputeResourcePreference:
        # Mirrors the SDK compute_resources._build_compute_resource_preference; the
        # preferred_job/data protocol enums were dropped from the proto (#660 drift),
        # so they are intentionally omitted.
        from airavata.model.appcatalog.gatewayprofile import (
            gateway_profile_pb2,
        )

        return gateway_profile_pb2.ComputeResourcePreference(
            compute_resource_id=data.get("compute_resource_id") or "",
            override_by_airavata=bool(data.get("overrideby_airavata", False)),
            login_user_name=data.get("login_user_name") or "",
            preferred_batch_queue=data.get("preferred_batch_queue") or "",
            scratch_location=data.get("scratch_location") or "",
            allocation_project_number=data.get("allocation_project_number") or "",
            resource_specific_credential_store_token=data.get(
                "resource_specific_credential_store_token"
            )
            or "",
            usage_reporting_gateway_id=data.get("usage_reporting_gateway_id") or "",
            quality_of_service=data.get("quality_of_service") or "",
            reservation=data.get("reservation") or "",
            reservation_start_time=data.get("reservation_start_time") or 0,
            reservation_end_time=data.get("reservation_end_time") or 0,
            ssh_account_provisioner=data.get("ssh_account_provisioner") or "",
            ssh_account_provisioner_config=dict(
                data.get("ssh_account_provisioner_config") or {}
            ),
            ssh_account_provisioner_additional_info=data.get(
                "ssh_account_provisioner_additional_info"
            )
            or "",
        )

    @staticmethod
    def _build_storage_preference(
        data: dict[str, Any],
    ) -> gateway_profile_pb2.StoragePreference:
        from airavata.model.appcatalog.gatewayprofile import (
            gateway_profile_pb2,
        )

        return gateway_profile_pb2.StoragePreference(
            storage_resource_id=data.get("storage_resource_id") or "",
            login_user_name=data.get("login_user_name") or "",
            file_system_root_location=data.get("file_system_root_location") or "",
            resource_specific_credential_store_token=data.get(
                "resource_specific_credential_store_token"
            )
            or "",
        )

    def _build_gateway_resource_profile(
        self, data: dict[str, Any]
    ) -> gateway_profile_pb2.GatewayResourceProfile:
        """Build a ``GatewayResourceProfile`` proto from the request body. Mirrors
        the SDK ``compute_resources.build_gateway_resource_profile``."""
        from airavata.model.appcatalog.gatewayprofile import (
            gateway_profile_pb2,
        )

        return gateway_profile_pb2.GatewayResourceProfile(
            gateway_id=data.get("gateway_id") or "",
            credential_store_token=data.get("credential_store_token") or "",
            compute_resource_preferences=[
                self._build_compute_resource_preference(c)
                for c in (data.get("compute_resource_preferences") or [])
            ],
            storage_preferences=[
                self._build_storage_preference(s)
                for s in (data.get("storage_preferences") or [])
            ],
            identity_server_tenant=data.get("identity_server_tenant") or "",
            identity_server_pwd_cred_token=data.get("identity_server_pwd_cred_token")
            or "",
        )

    def _read_with_access(
        self, request: AiravataRequest
    ) -> gw_pb2.GatewayResourceProfileWithAccess:
        # Bare profile + the gateway-admin write flag the server can't derive.
        from airavata.model.commons import (
            commons_pb2,
        )
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        profile = self._gw_profile().GetGatewayResourceProfile(
            pb2.GetGatewayResourceProfileRequest(gateway_id=settings.GATEWAY_ID)
        )
        return pb2.GatewayResourceProfileWithAccess(
            gateway_resource_profile=profile,
            access=commons_pb2.AccessFlags(
                is_owner=False,
                user_has_write_access=getattr(request, "is_gateway_admin", False),
            ),
        )

    def get(self, request: AiravataRequest) -> web.Response:
        return web.Response(self._read_with_access(request))

    def put(self, request: AiravataRequest) -> web.Response:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        data = request.data if isinstance(request.data, dict) else {}
        profile = self._build_gateway_resource_profile(data)
        self._gw_profile().UpdateGatewayResourceProfile(
            pb2.UpdateGatewayResourceProfileRequest(
                gateway_id=settings.GATEWAY_ID, gateway_resource_profile=profile
            )
        )
        return web.Response(
            self._read_with_access(request), status=web.status.HTTP_201_CREATED
        )


class ExperimentArchiveView(web.APIView):
    def get(
        self, request: HttpRequest, experiment_id: str | None = None
    ) -> web.Response:
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

    request: AiravataRequest
    lookup_field = "storage_resource_id"

    def _resource(self) -> ResourceServiceStub:
        from airavata.services.resource_service_pb2_grpc import (
            ResourceServiceStub,
        )

        return ResourceServiceStub(self.request.airavata_channel)

    @override
    def get_instance(
        self, lookup_value: str
    ) -> storage_resource_pb2.StorageResourceDescription:
        from airavata.services import resource_service_pb2 as pb2

        return self._resource().GetStorageResource(
            pb2.GetStorageResourceRequest(storage_resource_id=lookup_value)
        )

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return web.Response(self.get_instance(self.kwargs[self.lookup_field]))

    @web.action(detail=False)
    def all_names(self, request: AiravataRequest) -> web.Response:
        from airavata.services import resource_service_pb2 as pb2

        return web.Response(
            dict(
                self._resource()
                .GetAllStorageResourceNames(pb2.GetAllStorageResourceNamesRequest())
                .storage_resource_names
            )
        )


class StoragePreferenceViewSet(SdkResourceViewSet):
    """Gateway storage preferences — wired to the raw GatewayResourceProfile
    stub. Reads / create / update return the bare ``StoragePreference`` proto (no
    envelope); ``GATEWAY_ID`` threads into every request. Create / update
    ``AddStoragePreference`` / ``UpdateStoragePreference`` then re-fetch via
    ``GetStoragePreference``. The list endpoint is unpaginated, matching the
    pre-migration contract."""

    request: AiravataRequest
    lookup_field = "storage_resource_id"

    def _gw_profile(self) -> GatewayResourceProfileServiceStub:
        from airavata.services.gateway_resource_profile_service_pb2_grpc import (
            GatewayResourceProfileServiceStub,
        )

        return GatewayResourceProfileServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> gateway_profile_pb2.StoragePreference:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        return self._gw_profile().GetStoragePreference(
            pb2.GetStoragePreferenceRequest(
                gateway_id=self.gateway_id, storage_resource_id=lookup_value
            )
        )

    @override
    def _list_results(
        self, limit: int = -1, offset: int = 0
    ) -> list[gateway_profile_pb2.StoragePreference]:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        response = self._gw_profile().GetAllStoragePreferences(
            pb2.GetAllStoragePreferencesRequest(gateway_id=self.gateway_id)
        )
        return list(response.storage_preferences)

    def _build_storage_preference(
        self, data: dict[str, Any]
    ) -> gateway_profile_pb2.StoragePreference:
        """Build a ``StoragePreference`` proto from the (snake_case) request body.

        Mirrors the SDK ``compute_resources._build_storage_preference``
        field-for-field."""
        from airavata.model.appcatalog.gatewayprofile import (
            gateway_profile_pb2,
        )

        return gateway_profile_pb2.StoragePreference(
            storage_resource_id=data.get("storage_resource_id") or "",
            login_user_name=data.get("login_user_name") or "",
            file_system_root_location=data.get("file_system_root_location") or "",
            resource_specific_credential_store_token=data.get(
                "resource_specific_credential_store_token"
            )
            or "",
        )

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        pref = self._build_storage_preference(self._body())
        self._gw_profile().AddStoragePreference(
            pb2.AddStoragePreferenceRequest(
                gateway_id=self.gateway_id,
                storage_resource_id=pref.storage_resource_id,
                storage_preference=pref,
            )
        )
        result = self._gw_profile().GetStoragePreference(
            pb2.GetStoragePreferenceRequest(
                gateway_id=self.gateway_id,
                storage_resource_id=pref.storage_resource_id,
            )
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        storage_resource_id = self.kwargs[self.lookup_field]
        data = dict(self._body())
        data["storage_resource_id"] = storage_resource_id  # path id overrides body
        pref = self._build_storage_preference(data)
        self._gw_profile().UpdateStoragePreference(
            pb2.UpdateStoragePreferenceRequest(
                gateway_id=self.gateway_id,
                storage_resource_id=storage_resource_id,
                storage_preference=pref,
            )
        )
        result = self._gw_profile().GetStoragePreference(
            pb2.GetStoragePreferenceRequest(
                gateway_id=self.gateway_id, storage_resource_id=storage_resource_id
            )
        )
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    def destroy(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import (
            gateway_resource_profile_service_pb2 as pb2,
        )

        self._gw_profile().DeleteStoragePreference(
            pb2.DeleteStoragePreferenceRequest(
                gateway_id=settings.GATEWAY_ID,
                storage_resource_id=self.kwargs[self.lookup_field],
            )
        )
        return web.Response(status=web.status.HTTP_204_NO_CONTENT)


class ParserViewSet(SdkResourceViewSet):
    """Parsers resource (gateway-level catalog) — wired to the raw ParserService
    stub. Reads / create / update return the bare ``Parser`` proto. Create and
    update both ``SaveParser`` then re-fetch via ``GetParser`` so read and write
    paths emit the same shape; ``gateway_id`` is forced to this gateway."""

    request: AiravataRequest
    lookup_field = "parser_id"

    def _parser(self) -> ParserServiceStub:
        from airavata.services.parser_service_pb2_grpc import (
            ParserServiceStub,
        )

        return ParserServiceStub(self.request.airavata_channel)

    @override
    def get_instance(self, lookup_value: str) -> parser_model_pb2.Parser:
        from airavata.services import parser_service_pb2 as pb2

        return self._parser().GetParser(
            pb2.GetParserRequest(parser_id=lookup_value, gateway_id=self.gateway_id)
        )

    @override
    def _list_results(
        self, limit: int = -1, offset: int = 0
    ) -> list[parser_model_pb2.Parser]:
        from airavata.services import parser_service_pb2 as pb2

        response = self._parser().ListAllParsers(
            pb2.ListAllParsersRequest(gateway_id=self.gateway_id)
        )
        return list(response.parsers)

    def _build_parser(self, data: dict[str, Any]) -> parser_model_pb2.Parser:
        """Build a ``Parser`` proto from the (snake_case) request body.

        ``gateway_id`` is forced to this gateway; mirrors the SDK
        ``research_resources._build_parser`` field-for-field."""
        from airavata.model.appcatalog.parser import (
            parser_pb2,
        )

        from django_airavata.apps.api.experiment_builder import proto_enum_value

        def io_type(value: object) -> parser_model_pb2.IOType:
            return proto_enum_value(parser_pb2.IOType, value)

        return parser_pb2.Parser(
            id=data.get("id") or "",
            image_name=data.get("image_name") or "",
            output_dir_path=data.get("output_dir_path") or "",
            input_dir_path=data.get("input_dir_path") or "",
            execution_command=data.get("execution_command") or "",
            gateway_id=self.gateway_id or "",
            input_files=[
                parser_pb2.ParserInput(
                    id=i.get("id") or "",
                    name=i.get("name") or "",
                    required_input=bool(i.get("required_input", False)),
                    parser_id=i.get("parser_id") or "",
                    type=io_type(i.get("type")),
                )
                for i in (data.get("input_files") or [])
            ],
            output_files=[
                parser_pb2.ParserOutput(
                    id=o.get("id") or "",
                    name=o.get("name") or "",
                    required_output=bool(o.get("required_output", False)),
                    parser_id=o.get("parser_id") or "",
                    type=io_type(o.get("type")),
                )
                for o in (data.get("output_files") or [])
            ],
        )

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import parser_service_pb2 as pb2

        parser = self._build_parser(self._body())
        parser_id = (
            self._parser().SaveParser(pb2.SaveParserRequest(parser=parser)).parser_id
        )
        result = self._parser().GetParser(
            pb2.GetParserRequest(parser_id=parser_id, gateway_id=self.gateway_id)
        )
        return web.Response(result, status=web.status.HTTP_201_CREATED)

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import parser_service_pb2 as pb2

        parser_id = self.kwargs[self.lookup_field]
        data = dict(self._body())
        data["id"] = parser_id  # the path id overrides any body value
        parser = self._build_parser(data)
        self._parser().SaveParser(pb2.SaveParserRequest(parser=parser))
        result = self._parser().GetParser(
            pb2.GetParserRequest(parser_id=parser_id, gateway_id=self.gateway_id)
        )
        return web.Response(result)

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)


def _user_storage_path(
    path: str | None,
    experiment_id: str | None = None,
    request: AiravataRequest | None = None,
) -> str:
    """Resolve a portal user-storage path to the absolute facade path.

    A bare relative path is relative to the user's storage root (``~/``); with
    *experiment_id* it is relative to that experiment's data directory (resolved
    via the raw experiment stub) — callers passing *experiment_id* pass *request*.
    """
    rel = (path or "").lstrip("/")
    if experiment_id:
        assert request is not None
        from airavata.services import experiment_service_pb2 as exp_pb2
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        experiment = ExperimentServiceStub(request.airavata_channel).GetExperiment(
            exp_pb2.GetExperimentRequest(experiment_id=experiment_id)
        )
        data_dir = (
            experiment.user_configuration_data.experiment_data_dir
            if experiment.HasField("user_configuration_data")
            else None
        ) or ""
        # The experiment data dir is user-storage-relative. The SDK launch
        # persists it with a leading '/' that the staging write side strips and
        # anchors under the storage root; strip it here too and anchor under
        # '~/' — otherwise list_dir/dir_exists resolve against the SFTP chroot
        # root (outside it) and show "no files".
        base = data_dir.strip("/")
        full = base + ("/" + rel if rel else "")
        if full.startswith("~/"):
            return full
        return "~/" + full
    if rel.startswith("~"):
        return rel
    return "~/" + rel


class UserStoragePathView(web.APIView):
    """User-storage browse/listing over the raw user-storage stub.

    The per-entry path-permission flags (``user_has_write_access`` for files,
    ``user_has_write_access`` / ``is_shared_dir`` for directories) are
    ``GATEWAY_DATA_SHARED_DIRECTORIES`` / ``is_gateway_admin`` decisions, not
    backend fields, so they are layered on the rendered proto here.

    The write paths (upload / tus / file-content replace / delete) stay in the
    portal — HTTP concerns, not part of the read contract.
    """

    request: AiravataRequest
    permission_classes = (web.IsAuthenticated, UserStorageSharedDirPermission)

    def _storage(self) -> UserStorageServiceStub:
        return _user_storage_stub(self.request)

    def _dir_exists(self, resolved: str) -> bool:
        from airavata.services import file_service_pb2 as fs_pb2

        return (
            self._storage()
            .DirExists(fs_pb2.DirExistsRequest(storage_resource_id="", path=resolved))
            .exists
        )

    def get(self, request: AiravataRequest, path: str = "/") -> web.Response:
        # AIRAVATA-3460 Allow passing path as a query parameter instead
        path = request.query_params.get("path", path)
        experiment_id = request.query_params.get("experiment-id")
        return self._create_response(request, path, experiment_id=experiment_id)

    def post(self, request: AiravataRequest, path: str = "/") -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        resolved = _user_storage_path(path, experiment_id, request)
        if not self._dir_exists(resolved):
            self._storage().CreateDir(
                fs_pb2.CreateDirRequest(storage_resource_id="", path=resolved)
            )

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

            def save_file(
                file_path: str, file_name: str, file_type: str
            ) -> rc.DataProductModel:
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
    def put(self, request: AiravataRequest, path: str = "/") -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        path = request.POST.get("path", path)
        # Replace the file if the request has a file upload.
        if "file" in request.FILES:
            self.delete(request=request, path=path)
            dir_path, _file_name = os.path.split(path)
            self.post(request=request, path=dir_path)
        # Replace only the file content if the request body has the `fileContentText`
        elif request.data and "fileContentText" in request.data:
            self._storage().UploadFile(
                fs_pb2.UploadFileRequest(
                    storage_resource_id="",
                    path=_user_storage_path(path, request=request),
                    content=request.data["fileContentText"].encode("utf-8"),
                    name=os.path.basename(path),
                    content_type="",
                )
            )
        else:
            return web.Response(status=web.status.HTTP_400_BAD_REQUEST)

        return self._create_response(request=request, path=path)

    def delete(self, request: AiravataRequest, path: str = "/") -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        path = request.data.get("path", path)
        experiment_id = request.data.get("experiment-id")
        resolved = _user_storage_path(path, experiment_id, request)
        if self._dir_exists(resolved):
            self._storage().DeleteDir(
                fs_pb2.DeleteDirRequest(storage_resource_id="", path=resolved)
            )
        else:
            self._storage().DeleteFile(
                fs_pb2.DeleteFileRequest(storage_resource_id="", path=resolved)
            )

        return web.Response(status=204)

    # Per-entry path-permission flags (mirrors the legacy serializer fields)

    def _dir_write_access(self, request: AiravataRequest, path: str) -> bool:
        """WRITE flag for a directory entry: gateway-admin on a shared path,
        ``True`` otherwise (mirrors ``UserHasWriteAccessToPathSerializer``)."""
        if view_utils.is_shared_path(path):
            return request.is_gateway_admin
        return True

    def _user_has_write_access(self, request: AiravataRequest, path: str) -> bool:
        """Top-level ``user_has_write_access`` (mirrors the legacy base serializer).

        ``True`` for non-shared paths; the gateway-admin flag for shared paths.
        """
        if view_utils.is_shared_path(path):
            return request.is_gateway_admin
        return True

    def _create_response(
        self,
        request: AiravataRequest,
        path: str,
        uploaded: rc.DataProductModel | None = None,
        experiment_id: str | None = None,
    ) -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        from django_airavata.apps.api.proto_render import to_jsonable

        resolved = _user_storage_path(path, experiment_id, request)
        top_write_access = self._user_has_write_access(request, path)
        data: dict[str, Any]
        if self._dir_exists(resolved):
            listing = self._storage().ListDir(
                fs_pb2.ListDirRequest(storage_resource_id="", path=resolved)
            )
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
            rendered = to_jsonable(
                self._storage().GetFileMetadata(
                    fs_pb2.GetFileMetadataRequest(storage_resource_id="", path=resolved)
                )
            )
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

    def _split_path(self, path: str) -> list[str]:
        head, tail = os.path.split(path)
        if head != path:
            return [*self._split_path(head), tail]
        elif tail != "":
            return [tail]
        else:
            return []


class ExperimentStoragePathView(web.APIView):
    """Experiment data-dir browse/listing over the raw user-storage stub.

    Entry ``path`` is rewritten relative to the experiment data dir (the legacy
    ``ListExperimentDir`` exposed relative paths). File entries carry
    ``user_has_write_access`` — always ``True`` since an experiment data dir is
    never a gateway-shared path.
    """

    def get(
        self,
        request: AiravataRequest,
        experiment_id: str | None = None,
        path: str = "",
    ) -> web.Response:
        return self._create_response(request, experiment_id, path)

    def _create_response(
        self,
        request: AiravataRequest,
        experiment_id: str | None,
        path: str,
    ) -> web.Response:
        from airavata.services import file_service_pb2 as fs_pb2

        from django_airavata.apps.api.proto_render import to_jsonable

        storage = _user_storage_stub(request)
        resolved = _user_storage_path(path, experiment_id, request)
        dir_exists = storage.DirExists(
            fs_pb2.DirExistsRequest(storage_resource_id="", path=resolved)
        ).exists
        if not dir_exists:
            raise Http404(f"Path '{path}' does not exist for {experiment_id}")

        base = resolved.rstrip("/")

        def rel(entry_path: str) -> str:
            # Expose the path relative to the experiment data dir, as the legacy
            # list_experiment_dir did (resolved is the absolute experiment path).
            if entry_path.startswith(base + "/"):
                return entry_path[len(base) + 1 :]
            return os.path.basename(entry_path)

        def rel_path(entry_path: str) -> str:
            r = rel(entry_path)
            return os.path.join(path, r) if path else r

        listing = storage.ListDir(
            fs_pb2.ListDirRequest(storage_resource_id="", path=resolved)
        )
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
        data: dict[str, Any] = {
            "is_dir": True,
            "directories": directories,
            "files": files,
            "parts": self._split_path(path),
        }
        return web.Response(data)

    def _split_path(self, path: str) -> list[str]:
        head, tail = os.path.split(path)
        if head != "":
            return [*self._split_path(head), tail]
        elif tail != "":
            return [tail]
        else:
            return []


class WorkspacePreferencesView(web.APIView):
    def get(self, request: AiravataRequest) -> web.Response:
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

    request: AiravataRequest
    lookup_field = "notification_id"

    def _notifications(self) -> NotificationServiceStub:
        from airavata.services.notification_service_pb2_grpc import (
            NotificationServiceStub,
        )

        return NotificationServiceStub(self.request.airavata_channel)

    # APIBackedViewSet integration — still used by the destroy mixin

    @override
    def get_instance(self, lookup_value: str) -> workspace_pb2.Notification:
        from airavata.services import notification_service_pb2 as pb2

        return self._notifications().GetNotification(
            pb2.GetNotificationRequest(
                gateway_id=self.gateway_id, notification_id=lookup_value
            )
        )

    @override
    def get_list(self) -> builtins.list[workspace_pb2.Notification]:
        from airavata.services import notification_service_pb2 as pb2

        return list(
            self._notifications()
            .GetAllNotifications(
                pb2.GetAllNotificationsRequest(gateway_id=self.gateway_id)
            )
            .notifications
        )

    # Portal-only ``show_in_dashboard`` extension (Django ``NotificationExtension``)

    def _show_in_dashboard(self, notification_id: str) -> bool:
        """Resolve the ``show_in_dashboard`` extension flag for one notification."""
        return helpers.show_in_dashboard_map(self.gateway_id).get(
            notification_id, False
        )

    def _show_in_dashboard_map(
        self, notification_ids: Iterable[str]
    ) -> dict[str, bool]:
        """Build ``{notification_id: show_in_dashboard}`` from the cache map."""
        flags = helpers.show_in_dashboard_map(self.gateway_id)
        return {nid: flags.get(nid, False) for nid in notification_ids}

    def _render(
        self,
        with_access: notif_pb2.NotificationWithAccess,
        show_in_dashboard: bool,
    ) -> dict[str, Any]:
        """Flatten a ``WithAccess[Notification]`` and merge the portal-only flag.

        ``to_jsonable`` renders the proto to snake_case JSON merged with the
        access scalars; ``show_in_dashboard`` (the Django extension flag) is
        merged on top here because it is not a proto / SDK field.
        """
        from django_airavata.apps.api.proto_render import to_jsonable

        data = to_jsonable(with_access)
        data["show_in_dashboard"] = bool(show_in_dashboard)
        return data

    def _update_notification_extension(
        self, request: AiravataRequest, notification_id: str
    ) -> None:
        """Persist the portal-only ``show_in_dashboard`` extension flag.

        Mirrors the legacy ``NotificationSerializer.update_notification_extension``
        — only acts when the request body carries ``show_in_dashboard`` (the
        request body is already snake_case)."""
        if "show_in_dashboard" not in request.data:
            return
        helpers.set_show_in_dashboard(
            self.gateway_id, notification_id, request.data["show_in_dashboard"]
        )

    @staticmethod
    def _to_epoch_ms(value: object) -> int:
        """Timestamp -> epoch-millis int. ``None`` / ``""`` / ``0`` / bool -> 0;
        int as-is; ISO-8601 string -> epoch millis."""
        if not value or isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        s = str(value)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return int(dt.timestamp() * 1000)

    def _build_notification(
        self,
        data: dict[str, Any],
        base: workspace_pb2.Notification | None = None,
    ) -> workspace_pb2.Notification:
        """Build a ``Notification`` proto from the (snake_case) request body.

        ``base`` (the update path) seeds the proto so absent keys keep the base
        value; ``gateway_id`` is forced to this gateway. Mirrors the SDK
        ``research_resources._build_notification`` field-for-field."""
        from airavata.model.workspace import (
            workspace_pb2,
        )

        from django_airavata.apps.api.experiment_builder import proto_enum_value

        n = workspace_pb2.Notification()
        if base is not None:
            n.CopyFrom(base)
        n.gateway_id = self.gateway_id or ""
        if "title" in data:
            n.title = data["title"] or ""
        if "notification_message" in data:
            n.notification_message = data["notification_message"] or ""
        if "creation_time" in data:
            n.creation_time = self._to_epoch_ms(data["creation_time"])
        if "published_time" in data:
            n.published_time = self._to_epoch_ms(data["published_time"])
        if "expiration_time" in data:
            n.expiration_time = self._to_epoch_ms(data["expiration_time"])
        if "priority" in data:
            n.priority = proto_enum_value(
                workspace_pb2.NotificationPriority, data["priority"]
            )
        return n

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        from airavata.services import notification_service_pb2 as pb2

        results = list(
            self._notifications()
            .GetAllNotificationsWithAccess(
                pb2.GetAllNotificationsRequest(gateway_id=self.gateway_id)
            )
            .notifications
        )
        dashboard_map = self._show_in_dashboard_map(
            r.notification.notification_id for r in results
        )
        data = [
            self._render(r, dashboard_map.get(r.notification.notification_id, False))
            for r in results
        ]
        return web.Response(data)

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import notification_service_pb2 as pb2

        notification_id = self.kwargs[self.lookup_field]
        result = self._notifications().GetNotificationWithAccess(
            pb2.GetNotificationRequest(
                gateway_id=self.gateway_id, notification_id=notification_id
            )
        )
        return web.Response(
            self._render(result, self._show_in_dashboard(notification_id))
        )

    @override
    def create(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import notification_service_pb2 as pb2

        # request.data is already snake_case
        data = request.data if isinstance(request.data, dict) else {}
        show_in_dashboard = bool(data.get("show_in_dashboard", False))
        notification = self._build_notification(data)
        notification_id = (
            self._notifications()
            .CreateNotification(
                pb2.CreateNotificationRequest(notification=notification)
            )
            .notification_id
        )
        result = self._notifications().GetNotificationWithAccess(
            pb2.GetNotificationRequest(
                gateway_id=self.gateway_id, notification_id=notification_id
            )
        )
        self._update_notification_extension(
            request, result.notification.notification_id
        )
        return web.Response(
            self._render(result, show_in_dashboard), status=web.status.HTTP_201_CREATED
        )

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        from airavata.services import notification_service_pb2 as pb2

        notification_id = self.kwargs[self.lookup_field]
        data = request.data if isinstance(request.data, dict) else {}
        show_in_dashboard = bool(
            data.get("show_in_dashboard", self._show_in_dashboard(notification_id))
        )
        # Read-modify-write: seed from the stored notification, edit the supplied
        # fields, re-pin the id (UpdateNotification is full-replace), matching the
        # SDK ``update_notification`` helper.
        base = self._notifications().GetNotification(
            pb2.GetNotificationRequest(
                gateway_id=self.gateway_id, notification_id=notification_id
            )
        )
        notification = self._build_notification(data, base=base)
        notification.notification_id = notification_id
        self._notifications().UpdateNotification(
            pb2.UpdateNotificationRequest(notification=notification)
        )
        result = self._notifications().GetNotificationWithAccess(
            pb2.GetNotificationRequest(
                gateway_id=self.gateway_id, notification_id=notification_id
            )
        )
        self._update_notification_extension(request, notification_id)
        return web.Response(self._render(result, show_in_dashboard))

    @override
    def partial_update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return self.update(request, *args, **kwargs)

    @override
    def perform_destroy(self, instance: workspace_pb2.Notification) -> None:
        from airavata.services import notification_service_pb2 as pb2

        self._notifications().DeleteNotification(
            pb2.DeleteNotificationRequest(
                gateway_id=self.gateway_id, notification_id=instance.notification_id
            )
        )


class AckNotificationViewSet(web.APIView):
    def get(self, request: AiravataRequest) -> HttpResponse:
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

    request: AiravataRequest
    pagination_class = APIResultPagination
    permission_classes = (
        web.IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    def _iam_admin(self) -> IamAdminServiceStub:
        from airavata.services.iam_admin_service_pb2_grpc import (
            IamAdminServiceStub,
        )

        return IamAdminServiceStub(self.request.airavata_channel)

    @staticmethod
    def _iam_user_state_flags(state: int) -> tuple[bool, bool]:
        # (enabled, email_verified): enabled iff ACTIVE; email_verified iff
        # CONFIRMED or ACTIVE.
        from airavata.model.user import (
            user_profile_pb2,
        )

        Status = user_profile_pb2.Status
        return state == Status.ACTIVE, state in (Status.CONFIRMED, Status.ACTIVE)

    def _group_mgr(self) -> GroupManagerServiceStub:
        from airavata.services.group_manager_service_pb2_grpc import (
            GroupManagerServiceStub,
        )

        return GroupManagerServiceStub(self.request.airavata_channel)

    def _user_profiles(self) -> UserProfileServiceStub:
        from airavata.services.user_profile_service_pb2_grpc import (
            UserProfileServiceStub,
        )

        return UserProfileServiceStub(self.request.airavata_channel)

    # Composed-part resolvers (the parts the owning IAM service can't compute)

    def _does_user_exist(self, user_id: str) -> bool:
        from airavata.services import user_profile_service_pb2 as up_pb2

        return (
            self._user_profiles()
            .DoesUserExist(
                up_pb2.DoesUserExistRequest(
                    user_name=user_id, gateway_id=self.gateway_id
                )
            )
            .exists
        )

    def _user_profile_exists(self, user_profile: user_profile_pb2.UserProfile) -> bool:
        return self._does_user_exist(user_profile.user_id)

    def _user_groups(
        self, user_profile: user_profile_pb2.UserProfile, exists: bool
    ) -> builtins.list[gm_pb2.GroupWithAccess]:
        """The GroupWithAccess protos the user belongs to (read/output path); only
        resolved when the airavata user profile exists. The server computes the six
        access flags, so the renderer flattens these identically to the retired
        ``_envelope.WithGroupAccess`` — no portal-side wrap_groups fan-out. (The write
        path reads the bare-GroupModel roster via ``_convert_user_profile``.)"""
        if not exists:
            return []
        from airavata.services import group_manager_service_pb2 as gm_pb2

        return list(
            self._group_mgr()
            .GetAllGroupsUserBelongsWithAccess(
                gm_pb2.GetAllGroupsUserBelongsRequest(
                    user_name=user_profile.airavata_internal_user_id
                )
            )
            .groups
        )

    def _external_idp_user_info(self, user_id: str) -> dict[str, Any]:
        # TODO(Phase C): external IDP claims were mirrored into the local Django
        # UserProfile.idp_userinfo, which no longer exists. Expose them via a
        # backend RPC / the Keycloak identity broker if this admin column is
        # still needed.
        return {}

    def _user_profile_invalid_fields(self, user_id: str) -> builtins.list[Any]:
        # TODO(Phase C): profile validity was computed from the local Django
        # UserProfile, which no longer exists. Profile validity is Keycloak's
        # concern now; surface it via a backend RPC if this admin column is
        # still needed.
        return []

    def _build_iam_user(
        self,
        user_profile: user_profile_pb2.UserProfile,
        request: AiravataRequest,
        *,
        exists: bool | None = None,
        groups: builtins.list[gm_pb2.GroupWithAccess] | None = None,
    ) -> dict[str, Any]:
        """Compose the IAMUser JSON shape from a proto ``UserProfile`` + the
        composed parts (``DoesUserExist`` result, the user's groups as raw
        ``GroupWithAccess`` protos rendered proto-direct, gateway-admin flag, the
        two admin lookups). The snake_case keys match the retired SDK ``IAMUser``
        pydantic, so the frontend JSON is unchanged.
        """
        from django_airavata.apps.api.proto_render import to_jsonable

        if exists is None:
            exists = self._user_profile_exists(user_profile)
        if groups is None:
            groups = self._user_groups(user_profile, exists)
        enabled, email_verified = self._iam_user_state_flags(user_profile.state)
        return {
            "airavata_internal_user_id": user_profile.airavata_internal_user_id,
            "user_id": user_profile.user_id,
            "gateway_id": user_profile.gateway_id,
            "email": user_profile.emails[0] if user_profile.emails else "",
            "first_name": user_profile.first_name,
            "last_name": user_profile.last_name,
            "enabled": enabled,
            "email_verified": email_verified,
            "creation_time": user_profile.creation_time,
            "airavata_user_profile_exists": exists,
            "user_has_write_access": request.is_gateway_admin,
            "groups": to_jsonable(groups),
            "external_idp_user_info": self._external_idp_user_info(
                user_profile.user_id
            ),
            "user_profile_invalid_fields": self._user_profile_invalid_fields(
                user_profile.user_id
            ),
        }

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        search = request.GET.get("search", None)

        view = self

        class IAMUsersResultIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> list[user_profile_pb2.UserProfile]:
                from airavata.services import (
                    iam_admin_service_pb2 as ia_pb2,
                )

                return list(
                    view._iam_admin()
                    .GetUsers(
                        ia_pb2.GetIamUsersRequest(
                            offset=offset, limit=limit, search=search or ""
                        )
                    )
                    .users
                )

        queryset = IAMUsersResultIterator(query_params=request.query_params.copy())
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._build_iam_user(u, request) for u in page]
            return self.get_paginated_response(data)
        data = [self._build_iam_user(u, request) for u in queryset.get_results()]
        return web.Response(data)

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        user_id = self.kwargs[self.lookup_field]
        user_profile = iam_admin_client.get_user(user_id)
        return web.Response(self._build_iam_user(user_profile, request))

    # APIResultIterator / write-path plumbing (serializer-backed)

    @override
    def get_list(self) -> APIResultIterator:
        search = self.request.GET.get("search", None)

        convert_user_profile = self._convert_user_profile

        class IAMUsersResultIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> Iterator[dict[str, Any]]:
                return map(
                    convert_user_profile,
                    iam_admin_client.get_users(offset, limit, search),
                )

        return IAMUsersResultIterator(query_params=self.request.query_params.copy())

    @override
    def get_instance(self, lookup_value: str) -> dict[str, Any]:
        return self._convert_user_profile(iam_admin_client.get_user(lookup_value))

    @override
    def update(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
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

    def _apply_group_diff(self, instance: dict[str, Any], data: dict[str, Any]) -> None:
        from airavata.services import (
            group_manager_service_pb2 as gm_pb2,
        )
        from airavata.services import (
            user_profile_service_pb2 as up_pb2,
        )

        added_group_ids, removed_group_ids = serializers.iam_user_group_diff(
            instance["groups"], data
        )
        group_mgr = self._group_mgr()
        user_id = instance["airavataInternalUserId"]
        added_groups = []
        for group_id in added_group_ids:
            group = group_mgr.GetGroup(gm_pb2.GetGroupRequest(group_id=group_id))
            group_mgr.AddUsersToGroup(
                gm_pb2.AddUsersToGroupRequest(group_id=group_id, user_ids=[user_id])
            )
            added_groups.append(group)
        if len(added_groups) > 0:
            user_profile = self._user_profiles().GetUserProfileById(
                up_pb2.GetUserProfileByIdRequest(
                    user_id=data["userId"], gateway_id=settings.GATEWAY_ID
                )
            )
            signals.user_added_to_group.send(
                sender=self.__class__,
                user=user_profile,
                groups=added_groups,
                request=self.request,
            )
        for group_id in removed_group_ids:
            group_mgr.RemoveUsersFromGroup(
                gm_pb2.RemoveUsersFromGroupRequest(
                    group_id=group_id, user_ids=[user_id]
                )
            )

    @override
    def perform_destroy(self, instance: dict[str, Any]) -> None:
        iam_admin_client.delete_user(instance["userId"])

    @web.action(methods=["post"], detail=True)
    def enable(
        self, request: AiravataRequest, user_id: str | None = None
    ) -> web.Response:
        if user_id is None:
            raise Http404
        iam_admin_client.enable_user(user_id)
        user_profile = iam_admin_client.get_user(user_id)
        return web.Response(self._build_iam_user(user_profile, request))

    @web.action(methods=["put"], detail=False)
    def update_username(self, request: AiravataRequest) -> web.Response:
        try:
            old_username, new_username = serializers.parse_update_username(request.data)
        except serializers.ValidationError as e:
            return web.Response(e.detail, status=web.status.HTTP_400_BAD_REQUEST)
        iam_admin_client.update_username(old_username, new_username)
        # The username is updated in Keycloak (the source of truth); there is no
        # longer a Django UserProfile mirror to keep in sync.
        user_profile = iam_admin_client.get_user(new_username)
        return web.Response(self._build_iam_user(user_profile, request))

    def _convert_user_profile(
        self, user_profile: user_profile_pb2.UserProfile
    ) -> dict[str, Any]:
        # iam_admin_client returns a protobuf UserProfile; read proto fields
        # directly and build the dict the IAMUserProfile serializer consumes on
        # the write path (the read/output path composes the SDK IAMUser via
        # _build_iam_user).
        from airavata.model.user import (
            user_profile_pb2,
        )

        Status = user_profile_pb2.Status
        airavata_user_profile_exists = self._does_user_exist(user_profile.user_id)
        groups = []
        if airavata_user_profile_exists:
            from airavata.services import (
                group_manager_service_pb2 as gm_pb2,
            )

            # Bare GroupModel roster (the group-diff reads .id); the read/output
            # path renders the with-access variant via _user_groups instead.
            groups = list(
                self._group_mgr()
                .GetAllGroupsUserBelongs(
                    gm_pb2.GetAllGroupsUserBelongsRequest(
                        user_name=user_profile.airavata_internal_user_id
                    )
                )
                .groups
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
    """Experiment-statistics resource. The raw stub returns the
    ``ExperimentStatistics`` proto wholesale; the view nests it under ``results``
    in a pagination envelope keyed on the proto's ``all_experiment_count``."""

    # TODO: restrict to only Admins or Read Only Admins group members

    request: AiravataRequest

    def _experiments(self) -> ExperimentServiceStub:
        from airavata.services.experiment_service_pb2_grpc import (
            ExperimentServiceStub,
        )

        return ExperimentServiceStub(self.request.airavata_channel)

    def get(self, request: AiravataRequest) -> web.Response:
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

        from airavata.services import experiment_service_pb2 as pb2

        stats = self._experiments().GetExperimentStatistics(
            pb2.GetExperimentStatisticsRequest(
                gateway_id=settings.GATEWAY_ID,
                from_time=from_time,
                to_time=to_time,
                user_name=username or "",
                application_name=application_name or "",
                resource_host_name=resource_hostname or "",
                limit=limit,
                offset=offset,
            )
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


class UnverifiedEmailUser(BaseModel):
    """A strict subset of ``IAMUser``: proto-derived scalars plus the
    portal-supplied ``user_has_write_access`` (the gateway-admin flag).

    The shape (relocated from the retired ``iam_resources.UnverifiedEmailUser``
    pydantic model) is the read contract; the renderer recurses it field-by-field.
    """

    model_config = ConfigDict(extra="forbid")

    user_id: str
    gateway_id: str
    email: str
    first_name: str
    last_name: str
    enabled: bool
    email_verified: bool
    creation_time: int
    user_has_write_access: bool


class UnverifiedEmailUserViewSet(
    web.mixins.ListModelMixin, web.mixins.RetrieveModelMixin, GenericAPIBackedViewSet
):
    """Users whose email is not yet verified — a pydantic ``UnverifiedEmailUser``
    (a strict subset of ``IAMUser``). The ViewSet supplies
    ``request.is_gateway_admin``."""

    request: AiravataRequest
    pagination_class = APIResultPagination
    permission_classes = (
        web.IsAuthenticated,
        IsInAdminsGroupPermission,
    )
    lookup_field = "user_id"

    @staticmethod
    def _state_flags(state: int) -> tuple[bool, bool]:
        """``(enabled, email_verified)``: enabled iff ACTIVE; email_verified iff
        CONFIRMED or ACTIVE (relocated from ``iam_resources._iam_user_state_flags``).
        """
        from airavata.model.user import (
            user_profile_pb2,
        )

        Status = user_profile_pb2.Status
        enabled = state == Status.ACTIVE
        email_verified = state in (Status.CONFIRMED, Status.ACTIVE)
        return enabled, email_verified

    def _build_unverified(
        self,
        user_profile: user_profile_pb2.UserProfile,
        request: AiravataRequest,
    ) -> UnverifiedEmailUser:
        # Pure projection of an already-fetched IAM ``UserProfile`` proto onto the
        # read contract; user_has_write_access is the request-scoped admin flag.
        enabled, email_verified = self._state_flags(user_profile.state)
        return UnverifiedEmailUser(
            user_id=user_profile.user_id,
            gateway_id=user_profile.gateway_id,
            email=user_profile.emails[0] if user_profile.emails else "",
            first_name=user_profile.first_name,
            last_name=user_profile.last_name,
            enabled=enabled,
            email_verified=email_verified,
            creation_time=user_profile.creation_time,
            user_has_write_access=request.is_gateway_admin,
        )

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        view = self

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> list[user_profile_pb2.UserProfile]:
                return view._get_unverified_email_user_profiles(limit, offset)

        queryset = UnverifiedEmailUsersResultIterator()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._build_unverified(u, request) for u in page]
            return self.get_paginated_response(data)
        data = [self._build_unverified(u, request) for u in queryset.get_results()]
        return web.Response(data)

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        user_id = self.kwargs[self.lookup_field]
        users = self._get_unverified_email_user_profiles(limit=1, username=user_id)
        if len(users) == 0:
            raise Http404(f"No unverified email record found for user {user_id}")
        return web.Response(self._build_unverified(users[0], request))

    @override
    def get_list(self) -> APIResultIterator:
        get_users = self._get_unverified_email_user_profiles

        class UnverifiedEmailUsersResultIterator(APIResultIterator):
            @override
            def get_results(
                self, limit: int = -1, offset: int = 0
            ) -> list[user_profile_pb2.UserProfile]:
                return get_users(limit, offset)

        return UnverifiedEmailUsersResultIterator()

    @override
    def get_instance(self, lookup_value: str) -> user_profile_pb2.UserProfile:
        users = self._get_unverified_email_user_profiles(limit=1, username=lookup_value)
        if len(users) == 0:
            raise Http404(f"No unverified email record found for user {lookup_value}")
        else:
            return users[0]

    def _get_unverified_email_user_profiles(
        self,
        limit: int = -1,
        offset: int = 0,
        username: str | None = None,
    ) -> builtins.list[user_profile_pb2.UserProfile]:
        # TODO(Phase C): self-registration email verification is now owned by
        # Keycloak (the local EmailVerification model was removed with the Django
        # account surface). Surface unverified-email users via a backend RPC /
        # Keycloak admin query if this admin view is still needed.
        return []


class LogRecordConsumer(web.APIView):
    def post(self, request: AiravataRequest) -> web.Response:
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
    def get(self, request: HttpRequest) -> web.Response:
        return web.Response(
            serializers.settings_data(
                settings.FILE_UPLOAD_MAX_FILE_SIZE,
                settings.TUS_ENDPOINT,
                settings.PGA_URL,
            )
        )


class APIServerStatusCheckView(web.APIView):
    def get(self, request: AiravataRequest) -> web.Response:
        from airavata.services import project_service_pb2 as pb2
        from airavata.services.project_service_pb2_grpc import (
            ProjectServiceStub,
        )

        try:
            ProjectServiceStub(request.airavata_channel).GetUserProjects(
                pb2.GetUserProjectsRequest(
                    gateway_id=settings.GATEWAY_ID,
                    user_name=request.user.username,
                    limit=1,
                    offset=0,
                )
            )
            data = {"apiServerUp": True}
        except Exception as e:
            log.debug(f"API server status check failed: {e!s}")
            data = {"apiServerUp": False}
        return web.Response(data)


@web.api_view()
def notebook_output_view(request: AiravataRequest) -> HttpResponse:
    provider_id = request.GET["provider-id"]
    experiment_id = request.GET["experiment-id"]
    experiment_output_name = request.GET["experiment-output-name"]
    data = output_views.generate_data(
        request, provider_id, experiment_output_name, experiment_id
    )
    return HttpResponse(data["output"])


@web.api_view()
def html_output_view(request: AiravataRequest) -> JsonResponse:
    data = _generate_output_view_data(request)
    return JsonResponse(data)


@web.api_view()
def image_output_view(request: AiravataRequest) -> JsonResponse:
    data = _generate_output_view_data(request)
    # data should contain 'image' as a file-like object or raw bytes with the
    # file data and 'mime-type' with the images mimetype
    data["image"] = base64.b64encode(data["image"]).decode("utf-8")
    return JsonResponse(data)


@web.api_view()
def link_output_view(request: AiravataRequest) -> JsonResponse:
    data = _generate_output_view_data(request)
    return JsonResponse(data)


def _generate_output_view_data(request: AiravataRequest) -> dict[str, Any]:
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
    request: AiravataRequest

    @override
    def get_list(self) -> builtins.list[queue_settings.QueueSettingsCalculator]:
        return queue_settings.get_all()

    @override
    def get_instance(
        self, lookup_value: str
    ) -> queue_settings.QueueSettingsCalculator | None:
        calcs = queue_settings.get_all()
        calc = [calc for calc in calcs if calc.id == lookup_value]
        if len(calc) == 0:
            return None
        return calc[0]

    @override
    def list(self, request: AiravataRequest, *args: Any, **kwargs: Any) -> web.Response:
        return web.Response(
            [serializers.queue_settings_calculator_data(c) for c in self.get_list()]
        )

    @override
    def retrieve(
        self, request: AiravataRequest, *args: Any, **kwargs: Any
    ) -> web.Response:
        return web.Response(
            serializers.queue_settings_calculator_data(self.get_object())
        )

    @web.action(methods=["post"], detail=True)
    def calculate(
        self, request: AiravataRequest, pk: str | None = None
    ) -> web.Response:
        if pk is None:
            raise Http404
        data = request.data if isinstance(request.data, dict) else {}
        result: dict[str, Any] = {}
        # Build the proto ExperimentModel from the request; ignore a malformed
        # body (likely a late-initialization partial) and return empty settings.
        try:
            experiment_model = experiment_builder.build_experiment(
                gateway_id=self.gateway_id, user_name=self.username, data=data
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
