import copy
import datetime
import json
import logging
import re

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from django_airavata.app_config import AiravataAppConfig
from django_airavata.commons.dynamic_apps.context_processors import (
    custom_app_registry,
)

logger = logging.getLogger(__name__)


# Per-user notification read-state lives in the cache (was the
# api_user_notifications table): {notification_id: is_read}. Pure UX state; cache
# eviction just re-marks notifications unread.
def _notif_read_key(username):
    return f"notif_read:{username}"


def notification_read_state(username):
    return cache.get(_notif_read_key(username), {})


def mark_notification_read(username, notification_id):
    state = notification_read_state(username)
    state[notification_id] = True
    cache.set(_notif_read_key(username), state)


def user(request):
    """Provide ``{{ user }}`` to templates without ``django.contrib.auth``.

    Replaces ``django.contrib.auth.context_processors.auth`` (the auth app is no
    longer installed). ``request.user`` is the KeycloakUser / AnonymousUser set
    by the auth middleware. No ``perms`` is exposed — the portal authorizes via
    gateway-admin flags (``request.is_gateway_admin``), not Django permissions.
    """
    return {"user": getattr(request, "user", None)}


# proto NotificationPriority value -> the Thrift NotificationPriority integer the
# frontend dashboard expects (proto LOW=1/NORMAL=2/HIGH=3 vs Thrift 0/1/2). Built
# lazily so this module stays importable without the gRPC SDK on the path.
_notification_priority_proto_to_thrift = None


def _notification_priority(value):
    global _notification_priority_proto_to_thrift
    if _notification_priority_proto_to_thrift is None:
        from airavata_sdk.generated.org.apache.airavata.model.workspace import (
            workspace_pb2,
        )

        proto = workspace_pb2.NotificationPriority
        # Historical Thrift NotificationPriority integers (LOW/NORMAL/HIGH =
        # 0/1/2) the dashboard expects; proto assigns 1/2/3 (0 = UNKNOWN).
        thrift_ints = {"LOW": 0, "NORMAL": 1, "HIGH": 2}
        _notification_priority_proto_to_thrift = {
            v.number: thrift_ints[v.name]
            for v in proto.DESCRIPTOR.values
            if v.name in thrift_ints
        }
    return _notification_priority_proto_to_thrift.get(value)


def get_notifications(request):
    if request.user.is_authenticated and getattr(request, "authz_token", None):
        unread_notifications = 0
        try:
            notifications = list(
                request.airavata.research.get_all_notifications(settings.GATEWAY_ID)
            )
        except Exception:
            logger.warning("Failed to load notifications")
            notifications = []
        # naive UTC (matches the naive datetimes from fromtimestamp below);
        # replaces deprecated utcnow() without making this tz-aware
        current_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        valid_notifications = []
        for notification in notifications:
            notification_data = {
                "notificationId": notification.notification_id,
                "gatewayId": notification.gateway_id,
                "title": notification.title,
                "notificationMessage": notification.notification_message,
                "creationTime": notification.creation_time,
                "publishedTime": notification.published_time,
                "expirationTime": notification.expiration_time,
                "priority": _notification_priority(notification.priority),
            }
            expirationTime = datetime.datetime.fromtimestamp(
                notification.expiration_time / 1000
            )
            publishedTime = datetime.datetime.fromtimestamp(
                notification.published_time / 1000
            )

            if expirationTime > current_time and publishedTime < current_time:
                notification_data["url"] = (
                    request.build_absolute_uri(
                        reverse("django_airavata_api:ack-notifications")
                    )
                    + "?id="
                    + str(notification.notification_id)
                )

                is_read = notification_read_state(request.user.username).get(
                    notification.notification_id, False
                )
                notification_data["is_read"] = is_read
                if not is_read:
                    unread_notifications += 1
                valid_notifications.append(notification_data)

        return {
            "notifications": json.dumps(valid_notifications),
            "unread_notifications": unread_notifications,
        }
    else:
        return {"notifications": json.dumps([])}


def user_session_data(request):
    data = {}
    if request.user.is_authenticated:
        data["username"] = request.user.username
        data["airavataInternalUserId"] = (
            request.user.username + "@" + settings.GATEWAY_ID
        )
        # is_gateway_admin may not be set if a failure occurs during login
        data["isGatewayAdmin"] = getattr(request, "is_gateway_admin", False)
    return {
        "user_session_data": json.dumps(data),
        # Keycloak account console for the "User Settings" link in base.html.
        "KEYCLOAK_ACCOUNT_CONSOLE_URL": getattr(
            settings, "KEYCLOAK_ACCOUNT_CONSOLE_URL", ""
        ),
    }


def airavata_app_registry(request):
    """Put airavata django apps into the context."""
    airavata_apps = [
        app
        for app in apps.get_app_configs()
        if isinstance(app, AiravataAppConfig)
        and (getattr(app, "enabled", None) is None or app.enabled(request))
        and app.label not in settings.HIDDEN_AIRAVATA_APPS
    ]
    # Sort by app_order then by verbose_name (case-insensitive)
    airavata_apps.sort(key=lambda app: f"{app.app_order:09}-{app.verbose_name.lower()}")
    current_app = _get_current_app(request, airavata_apps)

    return {
        "airavata_apps": airavata_apps,
        "current_airavata_app": current_app,
        "airavata_app_nav": (
            _get_app_nav(request, current_app) if current_app else None
        ),
    }


def _get_current_app(request, apps):
    current_app = [
        app
        for app in apps
        if request.resolver_match
        and app.url_app_name == request.resolver_match.app_name
    ]
    return current_app[0] if len(current_app) > 0 else None


def _get_app_nav(request, current_app):
    if hasattr(current_app, "nav"):
        # Copy and filter current_app's nav items
        nav = [
            item
            for item in copy.copy(current_app.nav)
            if "enabled" not in item or item["enabled"](request)
        ]
        # convert "/djangoapp/path/in/app" to "path/in/app"
        app_path = "/".join(request.path.split("/")[2:])
        for nav_item in nav:
            if "active_prefixes" in nav_item:
                if re.match("|".join(nav_item["active_prefixes"]), app_path):
                    nav_item["active"] = True
                else:
                    nav_item["active"] = False
            else:
                # 'active_prefixes' is optional, and if not specified, assume
                # current item is active
                nav_item["active"] = True
    else:
        # Default to the home view in the app
        nav = [
            {
                "label": current_app.verbose_name,
                "icon": "fa " + current_app.fa_icon_class,
                "url": current_app.url_home,
            }
        ]
    return nav


def google_analytics_tracking_id(request):
    """Put the Google Analytics tracking id into context."""
    return {"ga_tracking_id": getattr(settings, "GOOGLE_ANALYTICS_TRACKING_ID", None)}


def _safe_reverse(name):
    """Reverse a named URL, returning ``#`` if it can't be resolved."""
    try:
        return reverse(name)
    except Exception:
        return "#"


def shell_data(request):
    """Assemble the page-shell data the Vue app shell (AppShell.vue) renders.

    The shell is a lightweight client: this composes the brand, primary nav,
    app switcher, user menu, and unread notifications into one JSON-serializable
    dict (rendered into base.html via ``json_script``). No business logic — it
    reuses the registries the other context processors already build.
    """
    chrome = getattr(settings, "PORTAL_CHROME", {}) or {}
    # The sidebar brand shows the platform name; gateways may override it via
    # PORTAL_CHROME["title"]. (PORTAL_TITLE remains the full HTML <title>.)
    title = chrome.get("title") or "Airavata"

    app_registry = airavata_app_registry(request)
    custom_registry = custom_app_registry(request)
    current_airavata_app = app_registry.get("current_airavata_app")
    current_custom_app = custom_registry.get("current_custom_app")

    def _items_for_app(app, is_current):
        items = []
        for nav in _get_app_nav(request, app) or []:
            items.append(
                {
                    "label": nav.get("label"),
                    "icon": nav.get("icon"),
                    "url": _safe_reverse(nav.get("url")),
                    # _get_app_nav defaults items without `active_prefixes` to
                    # active, so only trust the flag for the current app.
                    "active": is_current and bool(nav.get("active")),
                }
            )
        return items

    # Grouped navigation: every app is a section header with all of its nav items
    # shown beneath it (replacing the collapsed app-switcher). Only the current
    # app's matching item is flagged active.
    nav_groups = []
    for app in app_registry.get("airavata_apps") or []:
        is_current = app is current_airavata_app
        items = _items_for_app(app, is_current)
        if items:
            nav_groups.append(
                {
                    "label": app.verbose_name,
                    "icon": "fa " + app.fa_icon_class,
                    "current": is_current,
                    "items": items,
                }
            )
    for app in custom_registry.get("custom_apps") or []:
        is_current = (
            current_custom_app is not None and app.label == current_custom_app.label
        )
        items = _items_for_app(app, is_current)
        if items:
            nav_groups.append(
                {
                    "label": app.verbose_name,
                    "icon": "fa " + app.fa_icon_class,
                    "current": is_current,
                    "items": items,
                }
            )

    data = {
        "title": title,
        "logoUrl": chrome.get("logo_url")
            or static_logo_url(),
        "logoBackgroundColor": chrome.get("logo_background_color"),
        "menuLinks": chrome.get("user_menu_links") or [],
        "navGroups": nav_groups,
    }

    if request.user.is_authenticated:
        data["user"] = {
            "first_name": getattr(request.user, "first_name", ""),
            "last_name": getattr(request.user, "last_name", ""),
            "username": getattr(request.user, "username", ""),
            "email": getattr(request.user, "email", ""),
        }
        data["accountUrl"] = getattr(settings, "KEYCLOAK_ACCOUNT_CONSOLE_URL", "")
        data["logoutUrl"] = _safe_reverse("django_airavata_auth:logout")
        notifications = get_notifications(request)
        data["notices"] = json.loads(notifications.get("notifications") or "[]")
        data["unreadCount"] = notifications.get("unread_notifications", 0)

    return {"shell_data": data}


def static_logo_url():
    """Default portal logo served from static files."""
    from django.templatetags.static import static

    try:
        return static("images/airavata-logo.png")
    except Exception:
        return None
