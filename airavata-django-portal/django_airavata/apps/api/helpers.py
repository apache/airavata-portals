import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from . import models

logger = logging.getLogger(__name__)


class WorkspacePreferencesHelper:

    def get(self, request):
        try:
            workspace_preferences = models.WorkspacePreferences.objects.get(
                username=request.user.username)
            self._check(request, workspace_preferences)
        except ObjectDoesNotExist:
            workspace_preferences = self._create_default(request)
            workspace_preferences.save()
        return workspace_preferences

    def _create_default(self, request):
        workspace_preferences = models.WorkspacePreferences.create(
            request.user.username)
        most_recent_project = self._get_most_recent_project(request)
        workspace_preferences.most_recent_project_id = (
            most_recent_project.project_id if most_recent_project else None)
        first_grp = \
            self._get_first_group_resource_profile(request)
        workspace_preferences.most_recent_group_resource_profile_id = \
            first_grp.group_resource_profile_id if first_grp else None
        return workspace_preferences

    def _get_most_recent_project(self, request):
        "Return most recent writeable project."
        projects = request.airavata.research.get_user_projects(
            gateway_id=settings.GATEWAY_ID, user_name=request.user.username,
            limit=-1, offset=0)
        for project in projects:
            if self._can_write(request, project.project_id):
                return project
        return None

    def _get_first_group_resource_profile(self, request):
        "Return first accessible group resource profile"

        group_resource_profiles = \
            request.airavata.compute.get_group_resource_list()
        if len(group_resource_profiles) > 0:
            return group_resource_profiles[0]
        else:
            return None

    def _check(self, request, prefs):
        "Validate preference values and update as needed."
        if (not prefs.most_recent_project_id or
                not self._can_write(request, prefs.most_recent_project_id)):
            most_recent_project = self._get_most_recent_project(request)
            if most_recent_project is not None:
                logger.info("_check: updating most_recent_project_id to {}".format(most_recent_project.project_id))
                prefs.most_recent_project_id = most_recent_project.project_id
                prefs.save()
            else:
                logger.warning("_check: no writeable projects found, unsetting most_recent_project_id")
                prefs.most_recent_project_id = None
                prefs.save()
        group_resource_profiles = \
            request.airavata.compute.get_group_resource_list()
        group_resource_profile_ids = [g.group_resource_profile_id for g in group_resource_profiles]
        if (not prefs.most_recent_group_resource_profile_id or
                prefs.most_recent_group_resource_profile_id not in group_resource_profile_ids):
            first_grp_id = (group_resource_profile_ids[0]
                            if len(group_resource_profile_ids) > 0
                            else None)
            logger.warning(f"_check: updating "
                           f"most_recent_group_resource_profile_id to "
                           f"{first_grp_id}")
            prefs.most_recent_group_resource_profile_id = first_grp_id
            prefs.save()

    def _can_write(self, request, entity_id):
        return request.airavata.sharing.user_has_access(
            resource_id=entity_id, user_id=request.user.username,
            permission_type="WRITE")

    def _can_read(self, request, entity_id):
        return request.airavata.sharing.user_has_access(
            resource_id=entity_id, user_id=request.user.username,
            permission_type="READ")
