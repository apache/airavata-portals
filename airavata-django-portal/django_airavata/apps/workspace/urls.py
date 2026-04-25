from django.urls import re_path
from django.views.generic import RedirectView

from . import views

app_name = "django_airavata_workspace"
urlpatterns = [
    # Redirect bare /workspace/ to /workspace/home
    re_path(r"^$", RedirectView.as_view(url="home", permanent=False)),
    # Home dashboard
    re_path(r"^home$", views.dashboard, name="home"),
    # Project list
    re_path(r"^projects$", views.projects_list, name="projects"),
    # Top-level datasets list (public catalog + user's private datasets)
    re_path(r"^datasets$", views.datasets_list, name="datasets"),
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
        RedirectView.as_view(url="/workspace/launch", permanent=True),
        name="edit_experiment_redirect",
    ),
    re_path(
        r"^projects/(?P<project_id>[^/]+)/experiments/(?P<experiment_id>[^/]+)/$",
        views.view_experiment,
        name="view_experiment",
    ),
    # Project-scoped artifacts (experiment outputs)
    re_path(
        r"^projects/(?P<project_id>[^/]+)/artifacts$",
        views.artifacts,
        name="artifacts",
    ),
    # Project edit
    re_path(r"^projects/(?P<project_id>[^/]+)/edit$", views.edit_project, name="edit_project"),
    # Generic experiment launcher (Task 5)
    re_path(r"^launch$", views.launch, name="launch"),
    # Applications (gateway-wide) — app management surface stays. Only the
    # per-app create_experiment URL redirects to the new generic launcher.
    re_path(r"^applications/new$", views.new_application, name="new_application"),
    re_path(
        r"^applications/(?P<app_module_id>[^/]+)/create_experiment$",
        RedirectView.as_view(url="/workspace/launch", permanent=True),
        name="create_experiment_redirect",
    ),
    re_path(
        r"^applications/(?P<app_module_id>[^/]+)/$",
        views.edit_application,
        name="application_editor",
    ),
    re_path(r"^applications$", views.applications, name="applications"),
    # Resources — storage
    re_path(
        r"^storage/(?P<storage_resource_id>[^/]+)/tree(?:/(?P<path>.*))?$",
        views.storage_tree,
        name="storage_tree",
    ),
    re_path(
        r"^storage/(?P<storage_resource_id>[^/]+)/$",
        views.storage_detail,
        name="storage_detail",
    ),
    re_path(r"^storage$", views.user_storage, name="storage"),
    re_path(r"^compute", views.compute_resources, name="compute"),
]

