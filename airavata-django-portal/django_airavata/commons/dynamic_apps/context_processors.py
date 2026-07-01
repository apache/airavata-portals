from __future__ import annotations

import logging
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

from django_airavata.commons import dynamic_apps

if TYPE_CHECKING:
    from django.http import HttpRequest

    from django_airavata.commons.dynamic_apps import DynamicAppConfig

logger = logging.getLogger(__name__)


def custom_app_registry(request: HttpRequest) -> dict[str, Any]:
    """Put custom Django apps into the context."""
    custom_apps = dynamic_apps.CUSTOM_DJANGO_APPS.copy()
    custom_apps = [
        _enhance_custom_app_config(app)
        for app in custom_apps
        if (getattr(app, "enabled", None) is None or app.enabled(request))
    ]
    custom_apps.sort(key=lambda app: app.verbose_name.lower())
    current_custom_app = _get_current_app(request, custom_apps)
    return {
        # 'custom_apps': list(map(_app_to_dict, custom_apps)),
        "custom_apps": custom_apps,
        "current_custom_app": current_custom_app,
    }


def _enhance_custom_app_config(app: DynamicAppConfig) -> DynamicAppConfig:
    """As necessary add default values for properties to custom AppConfigs."""
    app.url_app_name = _get_url_app_name(app)
    app.url_home = _get_url_home(app)
    app.fa_icon_class = _get_fa_icon_class(app)
    app.app_description = _get_app_description(app)
    return app


def _get_url_app_name(app_config: DynamicAppConfig) -> str | None:
    """Return the urls namespace for the given AppConfig instance."""
    urls = _get_app_urls(app_config)
    return getattr(urls, "app_name", None)


def _get_url_home(app_config: DynamicAppConfig) -> str | None:
    """Get named URL of home page of app."""
    if hasattr(app_config, "url_home"):
        return app_config.url_home
    else:
        return _get_default_url_home(app_config)


def _get_default_url_home(app_config: DynamicAppConfig) -> str | None:
    """Return first url pattern as a default."""
    urls = _get_app_urls(app_config)
    app_name = _get_url_app_name(app_config)
    logger.warning(f"Custom Django app {app_config.label} has no URL namespace defined")
    first_named_url = None
    for urlpattern in urls.urlpatterns:
        if hasattr(urlpattern, "name"):
            first_named_url = urlpattern.name
            break
    if not first_named_url:
        raise Exception(f"{urls} has no named urls, can't figure out default home URL")
    if app_name:
        return app_name + ":" + first_named_url
    else:
        return first_named_url


def _get_fa_icon_class(app_config: DynamicAppConfig) -> str:
    """Return Font Awesome icon class to use for app."""
    if hasattr(app_config, "fa_icon_class"):
        return app_config.fa_icon_class
    else:
        return "fa-circle"


def _get_app_description(app_config: DynamicAppConfig) -> str | None:
    """Return brief description of app."""
    return getattr(app_config, "app_description", None)


def _get_app_urls(app_config: DynamicAppConfig) -> ModuleType:
    return import_module(".urls", app_config.name)


def _get_current_app(
    request: HttpRequest, apps: list[DynamicAppConfig]
) -> DynamicAppConfig | None:
    current_app = [
        app
        for app in apps
        if request.resolver_match
        and app.url_app_name == request.resolver_match.app_name
    ]
    return current_app[0] if len(current_app) > 0 else None
