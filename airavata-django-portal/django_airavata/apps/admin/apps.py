from django_airavata.app_config import AiravataAppConfig


class AdminConfig(AiravataAppConfig):
    name = "django_airavata.apps.admin"
    label = "django_airavata_admin"
    verbose_name = "Gateway"
    app_order = 100
    url_home = "gateway_settings"
    fa_icon_class = "fa-cog"
    app_description = """
        Gateway administration and configuration.
    """
    nav = [
        {
            "label": "Settings",
            "icon": "fa fa-cog",
            "url": "gateway_settings",
            "active_prefixes": ["settings"],
        },
        {
            "label": "Manage Users",
            "icon": "fa fa-users-cog",
            "url": "django_airavata_admin:users",
            "active_prefixes": ["users", "extended-user-profile"],
            "enabled": lambda req: getattr(req, "is_gateway_admin", False) or getattr(req, "is_read_only_gateway_admin", False),
        },
        {
            "label": "Notices",
            "icon": "fa fa-bell",
            "url": "django_airavata_admin:notices",
            "active_prefixes": ["notices"],
            "enabled": lambda req: getattr(req, "is_gateway_admin", False) or getattr(req, "is_read_only_gateway_admin", False),
        },
    ]
