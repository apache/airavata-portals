import logging

from airavata_sdk.helpers import compute_resources
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Per-gateway notification "show in dashboard" flags live in the cache, not the
# DB (was the api_notificationextension table): {notification_id: bool}. Portal-
# only UI state with no proto/SDK equivalent; cache eviction just resets the flag
# to its False default until an admin sets it again.
def _notif_dashboard_key(gateway_id):
    return f"notif_show_in_dashboard:{gateway_id}"


def show_in_dashboard_map(gateway_id):
    """Return ``{notification_id: show_in_dashboard}`` for the gateway."""
    return cache.get(_notif_dashboard_key(gateway_id), {})


def set_show_in_dashboard(gateway_id, notification_id, value):
    """Set (or clear) the show_in_dashboard flag for one notification."""
    flags = show_in_dashboard_map(gateway_id)
    flags[notification_id] = bool(value)
    cache.set(_notif_dashboard_key(gateway_id), flags)


# Per-user workspace preferences (most-recent project/group/compute + per-app
# favorites) live in the cache, not the DB (was api_workspacepreferences /
# api_applicationpreferences). Pure UX state; cache eviction just reseeds the
# defaults on the next read.
def _prefs_key(username):
    return f"workspace_prefs:{username}"


def _load_prefs(username):
    return cache.get(_prefs_key(username))


def _store_prefs(username, data):
    cache.set(_prefs_key(username), data)


class _ApplicationPreference:
    """Cache-backed stand-in for the old ApplicationPreferences row.

    Exposes the ``application_id`` / ``favorite`` attributes the serializer and
    favorite/unfavorite views read; ``save()`` writes the favorite flag back
    through the owning preferences object.
    """

    def __init__(self, prefs, application_id, favorite):
        self._prefs = prefs
        self.application_id = application_id
        self.favorite = favorite

    def save(self):
        self._prefs._set_favorite(self.application_id, self.favorite)


class _ApplicationPreferencesManager:
    """Mimics the ORM reverse-FK manager (``applicationpreferences_set``)."""

    def __init__(self, prefs):
        self._prefs = prefs

    def all(self):
        return [
            _ApplicationPreference(self._prefs, app_id, favorite)
            for app_id, favorite in self._prefs._favorites.items()
        ]

    def get(self, application_id):
        if application_id not in self._prefs._favorites:
            from django.core.exceptions import ObjectDoesNotExist

            raise ObjectDoesNotExist()
        return _ApplicationPreference(
            self._prefs, application_id, self._prefs._favorites[application_id]
        )

    def create(self, username=None, application_id=None, favorite=False):
        self._prefs._set_favorite(application_id, favorite)
        return _ApplicationPreference(self._prefs, application_id, favorite)


class WorkspacePreferences:
    """Cache-backed stand-in for the old WorkspacePreferences row.

    Preserves the attribute/method surface every call site relies on:
    ``most_recent_*`` mutable attributes, ``save()``, and an
    ``applicationpreferences_set`` reverse-manager.
    """

    def __init__(self, username, data):
        self.username = username
        self.most_recent_project_id = data.get("most_recent_project_id")
        self.most_recent_group_resource_profile_id = data.get(
            "most_recent_group_resource_profile_id"
        )
        self.most_recent_compute_resource_id = data.get(
            "most_recent_compute_resource_id"
        )
        self._favorites = dict(data.get("application_preferences", {}))
        self.applicationpreferences_set = _ApplicationPreferencesManager(self)

    def _as_dict(self):
        return {
            "most_recent_project_id": self.most_recent_project_id,
            "most_recent_group_resource_profile_id": self.most_recent_group_resource_profile_id,
            "most_recent_compute_resource_id": self.most_recent_compute_resource_id,
            "application_preferences": self._favorites,
        }

    def save(self):
        _store_prefs(self.username, self._as_dict())

    def _set_favorite(self, application_id, favorite):
        self._favorites[application_id] = favorite
        self.save()


class WorkspacePreferencesHelper:
    """Read/write a user's workspace preferences.

    The record lives in this portal's cache; the server-side lookups needed to
    seed/validate it (first writeable project, accessible group resource
    profiles) are delegated to the SDK ``compute_resources`` helpers.
    """

    def get(self, request):
        username = request.user.username
        data = _load_prefs(username)
        if data is None:
            workspace_preferences = self._create_default(request, username)
            workspace_preferences.save()
        else:
            workspace_preferences = WorkspacePreferences(username, data)
            self._check(request, workspace_preferences)
        return workspace_preferences

    def _create_default(self, request, username):
        defaults = compute_resources.resolve_workspace_defaults(request.airavata)
        return WorkspacePreferences(
            username,
            {
                "most_recent_project_id": defaults["most_recent_project_id"],
                "most_recent_group_resource_profile_id": defaults[
                    "most_recent_group_resource_profile_id"
                ],
            },
        )

    def _check(self, request, prefs):
        "Validate preference values and update as needed."
        if not prefs.most_recent_project_id or not self._can_write(
            request, prefs.most_recent_project_id
        ):
            most_recent_project_id = compute_resources.most_recent_writeable_project_id(
                request.airavata
            )
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
        group_resource_profile_ids = (
            compute_resources.accessible_group_resource_profile_ids(request.airavata)
        )
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

    def _can_write(self, request, entity_id):
        return compute_resources.user_can_write(request.airavata, entity_id)
