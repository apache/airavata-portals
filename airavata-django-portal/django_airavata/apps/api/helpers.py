import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

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
        workspace_preferences.most_recent_project_id = most_recent_project.project_id if most_recent_project else None
        return workspace_preferences

    def _get_most_recent_project(self, request: Any) -> Any:
        "Return most recent writeable project."
        projects = request.airavata_client.research.get_user_projects(settings.GATEWAY_ID, request.user.username, -1, 0)
        for project in projects:
            if self._can_write(request, project.project_id):
                return project
        return None

    def _check(self, request: Any, prefs: models.WorkspacePreferences) -> None:
        "Validate preference values and update as needed."
        if not prefs.most_recent_project_id or not self._can_write(request, prefs.most_recent_project_id):
            most_recent_project = self._get_most_recent_project(request)
            if most_recent_project is not None:
                logger.info(f"_check: updating most_recent_project_id to {most_recent_project.project_id}")
                prefs.most_recent_project_id = most_recent_project.project_id
                prefs.save()
            else:
                logger.warning("_check: no writeable projects found, unsetting most_recent_project_id")
                prefs.most_recent_project_id = None
                prefs.save()

    def _can_write(self, request: Any, entity_id: str) -> bool:
        user_id = request.user.username + "@" + settings.GATEWAY_ID
        return request.airavata_client.sharing.user_has_access(entity_id, user_id, "WRITE")

    def _can_read(self, request: Any, entity_id: str) -> bool:
        user_id = request.user.username + "@" + settings.GATEWAY_ID
        return request.airavata_client.sharing.user_has_access(entity_id, user_id, "READ")
