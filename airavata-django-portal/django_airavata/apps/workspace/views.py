from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlparse

from airavata.model.application.io.application_io_pb2 import (
    DataType,
)
from django.conf import settings
from django.shortcuts import render
from django.utils.module_loading import import_string

from django_airavata.apps.api import view_utils
from django_airavata.apps.api.proto_render import ProtoJSONRenderer
from django_airavata.apps.api.views import (
    ApplicationModuleViewSet,
    ExperimentSearchViewSet,
    FullExperimentViewSet,
    ProjectViewSet,
)
from django_airavata.apps.auth.decorators import login_required

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

    from django_airavata.apps.api.web import Response
    from django_airavata.request import AiravataRequest

logger = logging.getLogger(__name__)


@login_required
def experiments_list(request: AiravataRequest) -> HttpResponse:

    response = cast(
        "Response", ExperimentSearchViewSet.as_view({"get": "list"})(request)
    )
    if response.status_code != 200:
        raise Exception(
            "Failed to load experiments list: {}".format(response.data["detail"])
        )
    experiments_json = ProtoJSONRenderer().render(response.data).decode("utf-8")
    return render(
        request,
        "django_airavata_workspace/experiments_list.html",
        {"bundle_name": "experiment-list", "experiments_data": experiments_json},
    )


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "django_airavata_workspace/dashboard.html",
        {
            "bundle_name": "dashboard",
            "sidebar": True,
        },
    )


@login_required
def projects_list(request: AiravataRequest) -> HttpResponse:

    response = cast("Response", ProjectViewSet.as_view({"get": "list"})(request))
    if response.status_code != 200:
        raise Exception(
            "Failed to load projects list: {}".format(response.data["detail"])
        )
    projects_json = ProtoJSONRenderer().render(response.data).decode("utf-8")

    return render(
        request,
        "django_airavata_workspace/projects_list.html",
        {"bundle_name": "project-list", "projects_data": projects_json},
    )


@login_required
def edit_project(request: HttpRequest, project_id: str) -> HttpResponse:

    return render(
        request,
        "django_airavata_workspace/edit_project.html",
        {"bundle_name": "edit-project", "project_id": project_id},
    )


@login_required
def create_experiment(request: AiravataRequest, app_module_id: str) -> HttpResponse:

    # User input files can be passed as query parameters
    # <input name>=<path/to/user_file>
    # and also as data product URIs
    # <input name>=<data product URI>
    app_interface = cast(
        "Response",
        ApplicationModuleViewSet.as_view({"get": "application_interface"})(
            request, app_module_id=app_module_id
        ),
    )
    if app_interface.status_code != 200:
        raise Exception(
            "Failed to load application module data: {}".format(
                app_interface.data["detail"]
            )
        )
    user_input_values = {}
    # The `application_interface` action returns a proto-direct
    # ApplicationInterfaceWithAccess, so read the ApplicationInterfaceDescription
    # proto and its inputs directly (rather than subscripting a serialized dict).
    # app_input.type stays the proto DataType enum; compare against its named members.
    application_interface = app_interface.data.application_interface
    for app_input in application_interface.application_inputs:
        if app_input.type == DataType.URI and app_input.name in request.GET:
            user_file_value = request.GET[app_input.name]
            try:
                user_file_url = urlparse(user_file_value)
                if user_file_url.scheme == "airavata-dp":
                    dp_uri = user_file_value
                    try:
                        from airavata.services import (
                            data_product_service_pb2 as dp_pb2,
                        )
                        from airavata.services import (
                            file_service_pb2 as fs_pb2,
                        )
                        from airavata.services.data_product_service_pb2_grpc import (
                            DataProductServiceStub,
                        )
                        from airavata.services.file_service_pb2_grpc import (
                            UserStorageServiceStub,
                        )

                        data_product = DataProductServiceStub(
                            request.airavata_channel
                        ).GetDataProduct(
                            dp_pb2.GetDataProductRequest(product_uri=dp_uri)
                        )
                        file_path = view_utils.data_product_file_path(data_product)
                        if (
                            file_path
                            and UserStorageServiceStub(request.airavata_channel)
                            .FileExists(
                                fs_pb2.FileExistsRequest(
                                    storage_resource_id="", path=file_path
                                )
                            )
                            .exists
                        ):
                            user_input_values[app_input.name] = dp_uri
                    except Exception:
                        logger.exception(
                            f"Failed checking data product uri: {dp_uri}",
                            extra={"request": request},
                        )
            except ValueError:
                logger.exception(
                    f"Invalid user file value: {user_file_value}",
                    extra={"request": request},
                )
        elif app_input.type == DataType.STRING and app_input.name in request.GET:
            name = app_input.name
            user_input_values[name] = request.GET[name]
    context = {
        "bundle_name": "create-experiment",
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
def edit_experiment(request: AiravataRequest, experiment_id: str) -> HttpResponse:
    from airavata.services import (
        application_catalog_service_pb2 as ac_pb2,
    )
    from airavata.services import (
        experiment_service_pb2 as exp_pb2,
    )
    from airavata.services.application_catalog_service_pb2_grpc import (
        ApplicationCatalogServiceStub,
    )
    from airavata.services.experiment_service_pb2_grpc import (
        ExperimentServiceStub,
    )

    experiment = ExperimentServiceStub(request.airavata_channel).GetExperiment(
        exp_pb2.GetExperimentRequest(experiment_id=experiment_id)
    )
    applicationInterface = ApplicationCatalogServiceStub(
        request.airavata_channel
    ).GetApplicationInterface(
        ac_pb2.GetApplicationInterfaceRequest(app_interface_id=experiment.execution_id)
    )
    app_module_id = applicationInterface.application_modules[0]
    context = {
        "bundle_name": "edit-experiment",
        "experiment_id": experiment_id,
        "app_module_id": app_module_id,
    }
    template_path = "django_airavata_workspace/edit_experiment.html"
    # Apply a custom application template if it exists
    custom_template_path, custom_context = get_custom_template(request, app_module_id)
    if custom_template_path is not None:
        logger.debug(f"Applying custom application template {custom_template_path}")
        template_path = custom_template_path
        context.update(custom_context)

    return render(request, template_path, context)


def get_custom_template(
    request: AiravataRequest, app_module_id: str
) -> tuple[str | None, dict[str, Any]]:
    template_path = None
    context: dict[str, Any] = {}
    config = settings.PORTAL_APPLICATION_TEMPLATES.get(app_module_id)
    if config:
        template_path = config.get("template_path")
        for callable_path in config.get("context_processors", []):
            context_processor = import_string(callable_path)
            context.update(context_processor(request))
    return template_path, context


@login_required
def view_experiment(request: AiravataRequest, experiment_id: str) -> HttpResponse:

    launching = json.loads(request.GET.get("launching", "false"))
    response = cast(
        "Response",
        FullExperimentViewSet.as_view({"get": "retrieve"})(
            request, experiment_id=experiment_id
        ),
    )
    if response.status_code != 200:
        raise Exception(
            "Failed to load experiment data: {}".format(response.data["detail"])
        )
    full_experiment_json = ProtoJSONRenderer().render(response.data).decode("utf-8")

    return render(
        request,
        "django_airavata_workspace/view_experiment.html",
        {
            "bundle_name": "view-experiment",
            "full_experiment_data": full_experiment_json,
            "launching": json.dumps(launching),
        },
    )


@login_required
def user_storage(request: HttpRequest) -> HttpResponse:
    return render(
        request, "django_airavata_workspace/base.html", {"bundle_name": "user-storage"}
    )
