from django_airavata.app_config import AiravataAppConfig


class ResourcesConfig(AiravataAppConfig):
    """Sidebar nav-only app for the Resources section.

    Storage / Compute / Credentials routes and views live in the workspace
    app (`workspace_views.user_storage` etc.) and in `django_airavata/urls.py`.
    This app exists only to contribute the "Resources" nav section to the
    sidebar. It has no models, no URL patterns, no JS.
    """

    name = "django_airavata.apps.resources"
    label = "django_airavata_resources"
    verbose_name = "Resources"
    app_order = 10
    url_home = "storage"
    fa_icon_class = "fa-server"
    app_description = "Manage storage, compute, and credentials."
    nav = [
        {
            "label": "Storage",
            "icon": "fa fa-folder-open",
            "url": "storage",
            "active_prefixes": ["storage"],
        },
        {
            "label": "Compute",
            "icon": "fa fa-server",
            "url": "compute",
            "active_prefixes": ["compute"],
        },
        {
            "label": "Credentials",
            "icon": "fa fa-key",
            "url": "credentials",
            "active_prefixes": ["credentials"],
        },
    ]
