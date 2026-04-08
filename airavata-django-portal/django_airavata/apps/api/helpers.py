import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from django_airavata.proto_compat import ResourcePermissionType

from . import models

logger = logging.getLogger(__name__)


class WorkspacePreferencesHelper:
    def get(self, request: Any) -> models.WorkspacePreferences:
        try:
            workspace_preferences = models.WorkspacePreferences.objects.get(username=request.user.username)
            self._check(request, workspace_preferences)
        except ObjectDoesNotExist:
            workspace_preferences = self._create_default(request)
            workspace_preferences.save()
        return workspace_preferences

    def _create_default(self, request: Any) -> models.WorkspacePreferences:
        workspace_preferences = models.WorkspacePreferences.create(request.user.username)
        most_recent_project = self._get_most_recent_project(request)
        workspace_preferences.most_recent_project_id = most_recent_project.projectID
        first_grp = self._get_first_group_resource_profile(request)
        workspace_preferences.most_recent_group_resource_profile_id = (
            first_grp.groupResourceProfileId if first_grp else None
        )
        return workspace_preferences

    def _get_most_recent_project(self, request: Any) -> Any:
        "Return most recent writeable project."
        projects = request.airavata_client.research.get_user_projects(settings.GATEWAY_ID, request.user.username, -1, 0)
        for project in projects:
            if self._can_write(request, project.projectID):
                return project
        return None

    def _get_first_group_resource_profile(self, request: Any) -> Any:
        "Return first accessible group resource profile"

        group_resource_profiles = request.airavata_client.compute.get_group_resource_list(settings.GATEWAY_ID)
        if len(group_resource_profiles) > 0:
            return group_resource_profiles[0]
        else:
            return None

    def _check(self, request: Any, prefs: models.WorkspacePreferences) -> None:
        "Validate preference values and update as needed."
        if not prefs.most_recent_project_id or not self._can_write(request, prefs.most_recent_project_id):
            most_recent_project = self._get_most_recent_project(request)
            if most_recent_project is not None:
                logger.info(f"_check: updating most_recent_project_id to {most_recent_project.projectID}")
                prefs.most_recent_project_id = most_recent_project.projectID
                prefs.save()
            else:
                logger.warning("_check: no writeable projects found, unsetting most_recent_project_id")
                prefs.most_recent_project_id = None
                prefs.save()
        group_resource_profiles = request.airavata_client.compute.get_group_resource_list(settings.GATEWAY_ID)
        group_resource_profile_ids = list(map(lambda g: g.groupResourceProfileId, group_resource_profiles))
        if (
            not prefs.most_recent_group_resource_profile_id
            or prefs.most_recent_group_resource_profile_id not in group_resource_profile_ids
        ):
            first_grp_id = group_resource_profile_ids[0] if len(group_resource_profile_ids) > 0 else None
            logger.warn(f"_check: updating most_recent_group_resource_profile_id to {first_grp_id}")
            prefs.most_recent_group_resource_profile_id = first_grp_id
            prefs.save()

    def _can_write(self, request: Any, entity_id: str) -> bool:
        return request.airavata_client.sharing.user_has_access(entity_id, ResourcePermissionType.WRITE)

    def _can_read(self, request: Any, entity_id: str) -> bool:
        return request.airavata_client.sharing.user_has_access(entity_id, ResourcePermissionType.READ)
