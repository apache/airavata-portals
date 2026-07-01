from __future__ import annotations

import logging
from importlib import import_module
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from django.http import HttpRequest


class DynamicAppConfig(Protocol):
    """A typed view of a custom (dynamic) Django app's ``AppConfig``.

    Dynamic apps are discovered through the ``airavata.djangoapp`` entry point and
    follow the portal convention of exposing these display attributes (the
    ``context_processors`` here fill in defaults for the ones an app omits). It is
    a structural view, not a base class — third-party apps need not inherit from
    anything portal-specific.
    """

    name: str
    label: str
    verbose_name: str
    url_app_name: str | None
    url_home: str | None
    fa_icon_class: str
    app_description: str | None
    enabled: Callable[[HttpRequest], bool]


# AppConfig instances from custom Django apps
CUSTOM_DJANGO_APPS: list[DynamicAppConfig] = []

logger = logging.getLogger(__name__)


def load(
    installed_apps: list[str], entry_point_group: str = "airavata.djangoapp"
) -> None:
    for entry_point in entry_points(group=entry_point_group):
        custom_app_class = entry_point.load()
        custom_app_instance = custom_app_class(
            entry_point.name, import_module(entry_point.module)
        )
        CUSTOM_DJANGO_APPS.append(custom_app_instance)
        # Create path to AppConfig class (otherwise the ready() method doesn't get
        # called)
        logger.info(f"adding dynamic Django app {entry_point.name}")
        installed_apps.append(f"{entry_point.module}.{entry_point.attr}")


def merge_setting_dict(default: dict[str, Any], custom_setting: Any) -> None:
    # FIXME: only handles dict settings, doesn't handle lists
    if isinstance(custom_setting, dict):
        for k in custom_setting:
            if k not in default:
                default[k] = custom_setting[k]
            else:
                raise Exception(
                    f"Custom django app setting conflicts with key {k} in {default}"
                )


def merge_settings(settings_module: ModuleType) -> None:
    for custom_django_app in CUSTOM_DJANGO_APPS:
        # ``merge_settings`` / ``settings`` are optional hooks outside the
        # DynamicAppConfig structural view, so probe them dynamically.
        app_merge_settings = getattr(custom_django_app, "merge_settings", None)
        app_settings = getattr(custom_django_app, "settings", None)
        if app_merge_settings is not None:
            app_merge_settings(settings_module)
        elif app_settings is not None:
            # This approach is deprecated, use 'merge_settings' instead
            # Merge settings from custom Django apps
            # NOTE: only handles VITE_MANIFESTS additions
            print(
                f"{type(custom_django_app).__name__}.settings attr is deprecated, use merge_settings instead"
            )
            merge_setting_dict(
                settings_module.VITE_MANIFESTS,
                getattr(app_settings, "VITE_MANIFESTS", {}),
            )
