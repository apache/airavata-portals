from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from django.conf import settings
from django.core.cache import cache

from django_airavata.request import AiravataRequest

if TYPE_CHECKING:
    from airavata.services import user_profile_service_pb2

logger = logging.getLogger(__name__)


def _most_recent_writable_project_id(request: AiravataRequest) -> str | None:
    """Id of the caller's most-recent WRITE-accessible project, or None.

    GetMostRecentWritableProject does the newest-first WRITE scan server-side and
    raises NOT_FOUND when the caller has no writable project.
    """
    import grpc
    from airavata.services import project_service_pb2 as pb2
    from airavata.services.project_service_pb2_grpc import (
        ProjectServiceStub,
    )

    try:
        result = ProjectServiceStub(
            request.airavata_channel
        ).GetMostRecentWritableProject(
            pb2.GetUserProjectsRequest(
                gateway_id=settings.GATEWAY_ID, user_name=request.user.username
            )
        )
        return result.project.project_id or None
    except grpc.RpcError as e:
        # ``.code()`` is declared on ``grpc.Call``, not ``grpc.RpcError``, in the
        # grpc stubs; the concrete error is always a ``Call`` at runtime.
        if cast("grpc.Call", e).code() == grpc.StatusCode.NOT_FOUND:
            return None
        raise


def _accessible_group_resource_profile_ids(request: AiravataRequest) -> list[str]:
    from airavata.services import (
        group_resource_profile_service_pb2 as pb2,
    )
    from airavata.services.group_resource_profile_service_pb2_grpc import (
        GroupResourceProfileServiceStub,
    )

    response = GroupResourceProfileServiceStub(
        request.airavata_channel
    ).GetGroupResourceList(pb2.GetGroupResourceListRequest())
    return [g.group_resource_profile_id for g in response.group_resource_profiles]


# Per-gateway notification "show in dashboard" flags live in the cache, not the
# DB (was the api_notificationextension table): {notification_id: bool}. Portal-
# only UI state with no proto/SDK equivalent; cache eviction just resets the flag
# to its False default until an admin sets it again.
def _notif_dashboard_key(gateway_id: str) -> str:
    return f"notif_show_in_dashboard:{gateway_id}"


def show_in_dashboard_map(gateway_id: str) -> dict[str, bool]:
    """Return ``{notification_id: show_in_dashboard}`` for the gateway."""
    return cache.get(_notif_dashboard_key(gateway_id), {})


def set_show_in_dashboard(gateway_id: str, notification_id: str, value: object) -> None:
    """Set (or clear) the show_in_dashboard flag for one notification."""
    flags = show_in_dashboard_map(gateway_id)
    flags[notification_id] = bool(value)
    cache.set(_notif_dashboard_key(gateway_id), flags)


# Per-user workspace preferences (most-recent project/group/compute + per-app
# favorites) live server-side in iam-service, reached through UserProfileService
# over ``request.airavata_channel``. The values are seeded/repaired on read
# against the raw gRPC catalogs (first writeable project, accessible group
# resource profiles).
class WorkspacePreferences:
    """Server-backed workspace preferences.

    Seeded from GetUserPreferences; mutate the ``most_recent_*`` attributes or
    the ``application_favorites`` map and call ``save()`` to persist through
    UpdateUserPreferences.
    """

    def __init__(
        self,
        request: AiravataRequest,
        prefs: user_profile_service_pb2.UserPreferences,
    ) -> None:
        self._request = request
        self.most_recent_project_id: str | None = prefs.most_recent_project_id or None
        self.most_recent_group_resource_profile_id: str | None = (
            prefs.most_recent_group_resource_profile_id or None
        )
        self.most_recent_compute_resource_id: str | None = (
            prefs.most_recent_compute_resource_id or None
        )
        self.application_favorites: dict[str, bool] = dict(prefs.application_favorites)

    def save(self) -> None:
        from airavata.services import user_profile_service_pb2 as pb2
        from airavata.services.user_profile_service_pb2_grpc import (
            UserProfileServiceStub,
        )

        UserProfileServiceStub(self._request.airavata_channel).UpdateUserPreferences(
            pb2.UserPreferences(
                most_recent_project_id=self.most_recent_project_id or "",
                most_recent_group_resource_profile_id=self.most_recent_group_resource_profile_id
                or "",
                most_recent_compute_resource_id=self.most_recent_compute_resource_id
                or "",
                application_favorites=self.application_favorites,
            )
        )


class WorkspacePreferencesHelper:
    """Read/write a user's workspace preferences via UserProfileService.

    ``get`` loads the caller's stored preferences, then seeds/repairs the
    most-recent project + group resource profile using the raw gRPC catalogs.
    """

    def get(self, request: AiravataRequest) -> WorkspacePreferences:
        from airavata.services.user_profile_service_pb2_grpc import (
            UserProfileServiceStub,
        )
        from google.protobuf import empty_pb2

        prefs = UserProfileServiceStub(request.airavata_channel).GetUserPreferences(
            empty_pb2.Empty()  # ty: ignore[unresolved-attribute]  # protobuf ships no .pyi for google well-known types
        )
        workspace_preferences = WorkspacePreferences(request, prefs)
        self._check(request, workspace_preferences)
        return workspace_preferences

    def _check(self, request: AiravataRequest, prefs: WorkspacePreferences) -> None:
        "Validate preference values and update as needed."
        if not prefs.most_recent_project_id or not self._can_write(
            request, prefs.most_recent_project_id
        ):
            most_recent_project_id = _most_recent_writable_project_id(request)
            if most_recent_project_id is not None:
                logger.info(
                    f"_check: updating most_recent_project_id to {most_recent_project_id}"
                )
                prefs.most_recent_project_id = most_recent_project_id
                prefs.save()
            else:
                logger.warning(
                    "_check: no writeable projects found, unsetting most_recent_project_id"
                )
                prefs.most_recent_project_id = None
                prefs.save()
        group_resource_profile_ids = _accessible_group_resource_profile_ids(request)
        if (
            not prefs.most_recent_group_resource_profile_id
            or prefs.most_recent_group_resource_profile_id
            not in group_resource_profile_ids
        ):
            first_grp_id = (
                group_resource_profile_ids[0]
                if len(group_resource_profile_ids) > 0
                else None
            )
            logger.warning(
                f"_check: updating "
                f"most_recent_group_resource_profile_id to "
                f"{first_grp_id}"
            )
            prefs.most_recent_group_resource_profile_id = first_grp_id
            prefs.save()

    def _can_write(self, request: AiravataRequest, entity_id: str) -> bool:
        from django_airavata.apps.api import serializers

        return serializers.user_has_access(request, entity_id, "WRITE")
