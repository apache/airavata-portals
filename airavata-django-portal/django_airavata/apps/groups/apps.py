from django_airavata.app_config import AiravataAppConfig


class GroupsConfig(AiravataAppConfig):
    name = "django_airavata.apps.groups"
    label = "django_airavata_groups"
    verbose_name = "Resources"
    app_order = 10
    url_home = "storage"
    fa_icon_class = "fa-server"
    app_description = """
        Manage storage, compute, credentials, and sharing.
    """
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
        {
            "label": "Sharing",
            "icon": "fa fa-users",
            "url": "django_airavata_groups:manage",
            "active_prefixes": ["sharing"],
        },
    ]
