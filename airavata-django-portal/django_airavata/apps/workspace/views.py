import json
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.module_loading import import_string
from rest_framework.renderers import JSONRenderer

from django_airavata.apps.api import models
from django_airavata.apps.api import user_storage as user_storage_sdk
from django_airavata.apps.api.views import (
    ApplicationModuleViewSet,
    ExperimentSearchViewSet,
    FullExperimentViewSet,
    ProjectViewSet,
)
from django_airavata.proto_compat import DataType

logger = logging.getLogger(__name__)

# Map bundle names to Vite entry point paths
ENTRY_POINTS = {
    "experiment-list": "static/django_airavata_workspace/js/entry-experiment-list.js",
    "applications": "static/django_airavata_workspace/js/entry-applications.js",
    "project-list": "static/django_airavata_workspace/js/entry-project-list.js",
    "project-overview": "static/django_airavata_workspace/js/entry-project-overview.js",
    "edit-project": "static/django_airavata_workspace/js/entry-edit-project.js",
    "create-experiment": "static/django_airavata_workspace/js/entry-create-experiment.js",
    "edit-experiment": "static/django_airavata_workspace/js/entry-edit-experiment.js",
    "view-experiment": "static/django_airavata_workspace/js/entry-view-experiment.js",
    "user-storage": "static/django_airavata_workspace/js/entry-user-storage.js",
    "compute": "static/django_airavata_workspace/js/entry-compute.js",
    "datasets": "static/django_airavata_workspace/js/entry-datasets.js",
    "datasets-list": "static/django_airavata_workspace/js/entry-datasets-list.js",
    "credentials": "static/django_airavata_workspace/js/entry-credentials.js",
    "gateway-settings": "static/django_airavata_workspace/js/entry-gateway-settings.js",
    "storage-detail": "static/django_airavata_workspace/js/entry-storage-detail.js",
    "storage-tree": "static/django_airavata_workspace/js/entry-storage-tree.js",
    "compute-detail": "static/django_airavata_workspace/js/entry-compute-detail.js",
    "application-editor": "static/django_airavata_workspace/js/entry-application-editor.js",
    "dashboard": "static/django_airavata_workspace/js/entry-dashboard.js",
}


@login_required
def dashboard(request):
    request.active_nav_item = "home"
    return render(
        request,
        "django_airavata_workspace/dashboard.html",
        {
            "bundle_name": "dashboard",
            "entry_point": ENTRY_POINTS["dashboard"],
        },
    )


@login_required
def projects_list(request):
    request.active_nav_item = "projects"

    response = ProjectViewSet.as_view({"get": "list"})(request)
    if response.status_code != 200:
        logger.warning("Failed to load projects list: %s", response.data.get("detail", "unknown error"))
        projects_json = "[]"
    else:
        projects_json = JSONRenderer().render(response.data).decode("utf-8")

    # Auto-create default project on first visit with zero projects
    projects_data = json.loads(projects_json)
    results = projects_data.get("results", projects_data) if isinstance(projects_data, dict) else projects_data
    if len(results) == 0:
        from django_airavata.apps.api.helpers import WorkspacePreferencesHelper

        prefs = WorkspacePreferencesHelper().get(request)
        if not prefs.default_project_created:
            _create_default_project(request)
            prefs.default_project_created = True
            prefs.save()
            # Re-fetch projects after creation
            response = ProjectViewSet.as_view({"get": "list"})(request)
            if response.status_code == 200:
                projects_json = JSONRenderer().render(response.data).decode("utf-8")

    return render(
        request,
        "django_airavata_workspace/projects_list.html",
        {"bundle_name": "project-list", "entry_point": ENTRY_POINTS["project-list"], "projects_data": projects_json},
    )


def _create_default_project(request):
    """Create a default project for the current user."""
    from airavata_sdk.generated.org.apache.airavata.model.workspace.workspace_pb2 import (
        Project as ProjectProto,
    )

    username = request.user.username
    gateway_id = settings.GATEWAY_ID
    project = ProjectProto(
        owner=username,
        gateway_id=gateway_id,
        name=f"{username}-default",
        description=f"Default project for {username}",
    )
    project_id = request.airavata_client.research.create_project(gateway_id, project)
    logger.info("Created default project %s for user %s", project_id, username)
    return project_id


@login_required
def applications(request):
    request.active_nav_item = "applications"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "applications",
            "entry_point": ENTRY_POINTS["applications"],
        },
    )


@login_required
def new_application(request):
    request.active_nav_item = "applications"
    return render(
        request,
        "django_airavata_workspace/application_editor.html",
        {
            "bundle_name": "application-editor",
            "entry_point": ENTRY_POINTS["application-editor"],
        },
    )


@login_required
def edit_application(request, app_module_id):
    request.active_nav_item = "applications"
    return render(
        request,
        "django_airavata_workspace/application_editor.html",
        {
            "bundle_name": "application-editor",
            "entry_point": ENTRY_POINTS["application-editor"],
            "app_module_id": app_module_id,
        },
    )


@login_required
def edit_project(request, project_id):
    request.active_nav_item = "projects"

    return render(
        request,
        "django_airavata_workspace/edit_project.html",
        {"bundle_name": "edit-project", "entry_point": ENTRY_POINTS["edit-project"], "project_id": project_id},
    )


@login_required
def project_overview(request, project_id):
    request.active_nav_item = "projects"

    project = request.airavata_client.research.get_project(project_id)

    breadcrumbs = [
        {"label": "Projects", "url": "/workspace/projects"},
        {"label": project.name, "url": None},
    ]

    return render(
        request,
        "django_airavata_workspace/project_overview.html",
        {
            "bundle_name": "project-overview",
            "entry_point": ENTRY_POINTS["project-overview"],
            "project_id": project_id,
            "project_name": project.name,
            "breadcrumbs_json": json.dumps(breadcrumbs),
        },
    )


@login_required
def create_experiment(request, app_module_id):
    request.active_nav_item = "applications"

    # User input files can be passed as query parameters
    # <input name>=<path/to/user_file>
    # and also as data product URIs
    # <input name>=<data product URI>
    app_interface = ApplicationModuleViewSet.as_view({"get": "application_interface"})(
        request, app_module_id=app_module_id
    )
    if app_interface.status_code != 200:
        raise Exception("Failed to load application module data: {}".format(app_interface.data["detail"]))
    user_input_values = {}
    for app_input in app_interface.data.get("application_inputs", []):
        if app_input["type"] == DataType.URI and app_input["name"] in request.GET:
            user_file_value = request.GET[app_input["name"]]
            try:
                user_file_url = urlparse(user_file_value)
                if user_file_url.scheme == "airavata-dp":
                    dp_uri = user_file_value
                    try:
                        data_product = request.airavata_client.research.get_data_product(dp_uri)
                        if user_storage_sdk.exists(request, data_product):
                            user_input_values[app_input["name"]] = dp_uri
                    except Exception:
                        logger.exception(f"Failed checking data product uri: {dp_uri}", extra={"request": request})
            except ValueError:
                logger.exception(f"Invalid user file value: {user_file_value}", extra={"request": request})
        elif app_input["type"] == DataType.STRING and app_input["name"] in request.GET:
            name = app_input["name"]
            user_input_values[name] = request.GET[name]
    context = {
        "bundle_name": "create-experiment",
        "entry_point": ENTRY_POINTS["create-experiment"],
        "app_module_id": app_module_id,
        "user_input_values": json.dumps(user_input_values),
    }
    if "experiment-data-dir" in request.GET:
        context["experiment_data_dir"] = request.GET["experiment-data-dir"]

    template_path = "django_airavata_workspace/create_experiment.html"
    # Apply a custom application template if it exists
    custom_template_path, custom_context = get_custom_template(request, app_module_id)
    if custom_template_path is not None:
        logger.debug(f"Applying custom application template {custom_template_path}")
        template_path = custom_template_path
        context.update(custom_context)

    return render(request, template_path, context)


@login_required
def edit_experiment(request, project_id, experiment_id):
    request.active_nav_item = "projects"

    project = request.airavata_client.research.get_project(project_id)
    experiment = request.airavata_client.research.get_experiment(experiment_id)
    applicationInterface = request.airavata_client.research.get_application_interface(experiment.execution_id)
    app_module_id = applicationInterface.application_modules[0]

    breadcrumbs = [
        {"label": "Projects", "url": "/workspace/projects"},
        {"label": project.name, "url": f"/workspace/projects/{project_id}/"},
        {"label": "Experiments", "url": f"/workspace/projects/{project_id}/experiments"},
        {"label": "Edit Experiment", "url": None},
    ]

    context = {
        "bundle_name": "edit-experiment",
        "entry_point": ENTRY_POINTS["edit-experiment"],
        "experiment_id": experiment_id,
        "app_module_id": app_module_id,
        "project_id": project_id,
        "breadcrumbs_json": json.dumps(breadcrumbs),
    }
    template_path = "django_airavata_workspace/edit_experiment.html"
    custom_template_path, custom_context = get_custom_template(request, app_module_id)
    if custom_template_path is not None:
        logger.debug(f"Applying custom application template {custom_template_path}")
        template_path = custom_template_path
        context.update(custom_context)

    return render(request, template_path, context)


def get_custom_template(request, app_module_id):
    template_path = None
    context = {}
    query = models.ApplicationTemplate.objects.filter(application_module_id=app_module_id)
    if query.exists():
        application_template = query.get()
        template_path = application_template.template_path
        for context_processor in application_template.context_processors.all():
            context_processor = import_string(context_processor.callable_path)
            context.update(context_processor(request))
    return template_path, context


@login_required
def view_experiment(request, project_id, experiment_id):
    request.active_nav_item = "projects"

    project = request.airavata_client.research.get_project(project_id)
    launching = json.loads(request.GET.get("launching", "false"))
    response = FullExperimentViewSet.as_view({"get": "retrieve"})(request, experiment_id=experiment_id)
    if response.status_code != 200:
        raise Exception("Failed to load experiment data: {}".format(response.data["detail"]))
    full_experiment_json = JSONRenderer().render(response.data).decode("utf-8")

    breadcrumbs = [
        {"label": "Projects", "url": "/workspace/projects"},
        {"label": project.name, "url": f"/workspace/projects/{project_id}/"},
        {"label": "Experiments", "url": f"/workspace/projects/{project_id}/experiments"},
        {"label": "Experiment", "url": None},
    ]

    return render(
        request,
        "django_airavata_workspace/view_experiment.html",
        {
            "bundle_name": "view-experiment",
            "entry_point": ENTRY_POINTS["view-experiment"],
            "full_experiment_data": full_experiment_json,
            "launching": json.dumps(launching),
            "project_id": project_id,
            "breadcrumbs_json": json.dumps(breadcrumbs),
        },
    )


@login_required
def user_storage(request):
    request.active_nav_item = "storage"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "user-storage",
            "entry_point": ENTRY_POINTS["user-storage"],
        },
    )


@login_required
def compute_resources(request):
    request.active_nav_item = "compute"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "compute",
            "entry_point": ENTRY_POINTS["compute"],
        },
    )


@login_required
def storage_detail(request, storage_resource_id):
    request.active_nav_item = "storage"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "storage-detail",
            "entry_point": ENTRY_POINTS["storage-detail"],
            "storage_resource_id": storage_resource_id,
        },
    )


@login_required
def storage_tree(request, storage_resource_id, path=""):
    request.active_nav_item = "storage"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "storage-tree",
            "entry_point": ENTRY_POINTS["storage-tree"],
            "storage_resource_id": storage_resource_id,
            "storage_path": path or "",
        },
    )


@login_required
def compute_detail(request, compute_resource_id):
    request.active_nav_item = "compute"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "compute-detail",
            "entry_point": ENTRY_POINTS["compute-detail"],
            "compute_resource_id": compute_resource_id,
        },
    )


@login_required
def credentials(request):
    request.active_nav_item = "credentials"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "credentials",
            "entry_point": ENTRY_POINTS["credentials"],
        },
    )


@login_required
def gateway_settings(request):
    request.active_nav_item = "settings"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "gateway-settings",
            "entry_point": ENTRY_POINTS["gateway-settings"],
            "gateway_id": settings.GATEWAY_ID,
            "portal_title": getattr(settings, "PORTAL_TITLE", "Airavata Portal"),
            "is_gateway_admin": getattr(request, "is_gateway_admin", False),
        },
    )


@login_required
def artifacts(request, project_id):
    request.active_nav_item = "projects"

    project = request.airavata_client.research.get_project(project_id)

    breadcrumbs = [
        {"label": "Projects", "url": "/workspace/projects"},
        {"label": project.name, "url": f"/workspace/projects/{project_id}/"},
        {"label": "Artifacts", "url": None},
    ]

    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "datasets",
            "entry_point": ENTRY_POINTS.get("datasets", ""),
            "project_id": project_id,
            "breadcrumbs_json": json.dumps(breadcrumbs),
        },
    )


@login_required
def datasets_list(request):
    request.active_nav_item = "datasets"
    return render(
        request,
        "django_airavata_workspace/datasets_list.html",
        {
            "bundle_name": "datasets-list",
            "entry_point": ENTRY_POINTS["datasets-list"],
        },
    )


@login_required
def launch(request):
    request.active_nav_item = "launch"
    return render(request, "django_airavata_workspace/launch.html", {
        "feature_flag": getattr(settings, "FEATURE_GENERIC_LAUNCHER", False),
    })


@login_required
def experiments_list(request, project_id):
    request.active_nav_item = "projects"

    project = request.airavata_client.research.get_project(project_id)

    response = ExperimentSearchViewSet.as_view({"get": "list"})(request)
    if response.status_code != 200:
        logger.warning("Failed to load experiments list: %s", response.data.get("detail", "unknown error"))
        experiments_json = "[]"
    else:
        experiments_json = JSONRenderer().render(response.data).decode("utf-8")

    breadcrumbs = [
        {"label": "Projects", "url": "/workspace/projects"},
        {"label": project.name, "url": f"/workspace/projects/{project_id}/"},
        {"label": "Experiments", "url": None},
    ]

    return render(
        request,
        "django_airavata_workspace/experiments_list.html",
        {
            "bundle_name": "experiment-list",
            "entry_point": ENTRY_POINTS["experiment-list"],
            "experiments_data": experiments_json,
            "project_id": project_id,
            "breadcrumbs_json": json.dumps(breadcrumbs),
        },
    )
