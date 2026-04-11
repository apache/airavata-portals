from django.urls import re_path

from . import views

app_name = "django_airavata_workspace"
urlpatterns = [
    # Project list (workspace landing page)
    re_path(r"^$", views.projects_list, name="projects"),
    # Project overview dashboard
    re_path(r"^projects/(?P<project_id>[^/]+)/$", views.project_overview, name="project_overview"),
    # Project-scoped experiments
    re_path(
        r"^projects/(?P<project_id>[^/]+)/experiments$",
        views.experiments_list,
        name="experiments",
    ),
    re_path(
        r"^projects/(?P<project_id>[^/]+)/experiments/(?P<experiment_id>[^/]+)/edit$",
        views.edit_experiment,
        name="edit_experiment",
    ),
    re_path(
        r"^projects/(?P<project_id>[^/]+)/experiments/(?P<experiment_id>[^/]+)/$",
        views.view_experiment,
        name="view_experiment",
    ),
    # Project-scoped datasets
    re_path(
        r"^projects/(?P<project_id>[^/]+)/datasets$",
        views.datasets,
        name="datasets",
    ),
    # Project edit
    re_path(r"^projects/(?P<project_id>[^/]+)/edit$", views.edit_project, name="edit_project"),
    # Applications (gateway-wide)
    re_path(
        r"^applications/(?P<app_module_id>[^/]+)/create_experiment$",
        views.create_experiment,
        name="create_experiment",
    ),
    re_path(r"^applications$", views.applications, name="applications"),
    # Resources
    re_path(r"^storage", views.user_storage, name="storage"),
    re_path(r"^compute", views.compute_resources, name="compute"),
]
