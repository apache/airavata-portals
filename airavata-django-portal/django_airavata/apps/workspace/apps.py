from django_airavata.app_config import AiravataAppConfig


class WorkspaceConfig(AiravataAppConfig):
    name = "django_airavata.apps.workspace"
    label = "django_airavata_workspace"
    verbose_name = "Workspace"
    app_order = 0
    url_home = "django_airavata_workspace:projects"
    fa_icon_class = "fa-flask"
    app_description = """
        Launch applications and manage your experiments and projects.
    """
    nav = [
        {
            "label": "Applications",
            "icon": "fa fa-cubes",
            "url": "django_airavata_workspace:applications",
            "active_prefixes": ["applications"],
        },
        {
            "label": "Projects",
            "icon": "fa fa-box",
            "url": "django_airavata_workspace:projects",
            "active_prefixes": ["projects"],
        },
    ]
