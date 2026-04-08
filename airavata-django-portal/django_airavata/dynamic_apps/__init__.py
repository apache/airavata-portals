import logging
from importlib import import_module
from importlib.metadata import entry_points

# AppConfig instances from custom Django apps
CUSTOM_DJANGO_APPS = []

logger = logging.getLogger(__name__)


def load(installed_apps, entry_point_group="airavata.djangoapp"):
    for entry_point in entry_points(group=entry_point_group):
        custom_app_class = entry_point.load()
        custom_app_instance = custom_app_class(entry_point.name, import_module(entry_point.module))
        CUSTOM_DJANGO_APPS.append(custom_app_instance)
        # Create path to AppConfig class (otherwise the ready() method doesn't get
        # called)
        logger.info(f"adding dynamic Django app {entry_point.name}")
        installed_apps.append(f"{entry_point.module}.{entry_point.attr}")


def merge_setting_dict(default, custom_setting):
    # FIXME: only handles dict settings, doesn't handle lists
    if isinstance(custom_setting, dict):
        for k in custom_setting:
            if k not in default:
                default[k] = custom_setting[k]
            else:
                raise Exception(f"Custom django app setting conflicts with key {k} in {default}")


def merge_settings(settings_module):
    for custom_django_app in CUSTOM_DJANGO_APPS:
        if hasattr(custom_django_app, "merge_settings"):
            custom_django_app.merge_settings(settings_module)
        elif hasattr(custom_django_app, "settings"):
            # This approach is deprecated, use 'merge_settings' instead
            # Merge settings from custom Django apps
            # NOTE: only handles DJANGO_VITE additions
            print(f"{type(custom_django_app).__name__}.settings attr is deprecated, use merge_settings instead")
            s = custom_django_app.settings
            merge_setting_dict(
                settings_module.DJANGO_VITE,
                getattr(s, "DJANGO_VITE", {}),
            )
