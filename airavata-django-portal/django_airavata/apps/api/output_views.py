from __future__ import annotations

import collections.abc
import inspect
import json
import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Protocol

from airavata.model.application.io.application_io_pb2 import (
    DataType,
)
from django.conf import settings

if TYPE_CHECKING:
    import io

    from airavata.model.appcatalog.appinterface.app_interface_pb2 import (
        ApplicationInterfaceDescription,
    )
    from airavata.model.application.io.application_io_pb2 import (
        OutputDataObjectType,
    )
    from airavata.model.data.replica.replica_catalog_pb2 import DataProductModel
    from airavata.model.experiment.experiment_pb2 import ExperimentModel

    from django_airavata.request import AiravataRequest


class OutputViewProvider(Protocol):
    """Duck-typed surface of an output-view-provider plugin.

    Plugins are loaded from the ``airavata.output_view_providers`` entry-point
    group (see ``apps.ApiConfig.ready``); they expose ``display_type`` / ``name``
    / ``immediate`` metadata and a ``generate_data`` callable. ``test_output_file``
    is optional (only some providers define it, read via ``getattr``).
    """

    display_type: str
    name: str
    immediate: bool

    def generate_data(
        self,
        request: AiravataRequest,
        experiment_output: OutputDataObjectType,
        experiment: ExperimentModel,
        output_file: io.IOBase | None = ...,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


logger = logging.getLogger(__name__)


def _get_experiment_proto(
    request: AiravataRequest, experiment_id: str
) -> ExperimentModel:
    """Bare ``ExperimentModel`` for *experiment_id* via the raw experiment stub."""
    from airavata.services import experiment_service_pb2 as exp_pb2
    from airavata.services.experiment_service_pb2_grpc import (
        ExperimentServiceStub,
    )

    return ExperimentServiceStub(request.airavata_channel).GetExperiment(
        exp_pb2.GetExperimentRequest(experiment_id=experiment_id)
    )


def _data_product_file_path(data_product: DataProductModel) -> str | None:
    """First replica's file path (``~/``-prefixed when relative), or None.

    The storage stub expects the FULL path, absolute or ``~/``-prefixed (a bare
    relative path NPEs server-side). Mirrors ``view_utils.data_product_file_path``.
    """
    replicas = data_product.replica_locations
    if not replicas:
        return None
    file_path = replicas[0].file_path
    if not file_path:
        return None
    if not (file_path.startswith("/") or file_path.startswith("~/")):
        file_path = "~/" + file_path
    return file_path


def _download_data_product_files(
    request: AiravataRequest, data_product_uris: list[str]
) -> list[io.BytesIO]:
    """For each ``airavata-dp://`` URI, fetch the product, resolve its first
    replica's file path, and download its bytes when the file exists.

    Returns a list of :class:`io.BytesIO` (``.name`` set to the download name or
    the path basename), in input-URI order. The 2N per-URI calls (GetDataProduct
    -> FileExists -> DownloadFile) are byte transport, not business logic. URIs
    with no replica / missing file contribute nothing.
    """
    import io
    import os

    from airavata.services import data_product_service_pb2 as dp_pb2
    from airavata.services import file_service_pb2 as fs_pb2
    from airavata.services.data_product_service_pb2_grpc import (
        DataProductServiceStub,
    )
    from airavata.services.file_service_pb2_grpc import (
        UserStorageServiceStub,
    )

    data_product_stub = DataProductServiceStub(request.airavata_channel)
    storage = UserStorageServiceStub(request.airavata_channel)
    output_files = []
    for uri in data_product_uris:
        data_product = data_product_stub.GetDataProduct(
            dp_pb2.GetDataProductRequest(product_uri=uri)
        )
        path = _data_product_file_path(data_product)
        if (
            path
            and storage.FileExists(
                fs_pb2.FileExistsRequest(storage_resource_id="", path=path)
            ).exists
        ):
            resp = storage.DownloadFile(
                fs_pb2.DownloadFileRequest(storage_resource_id="", path=path)
            )
            output_file = io.BytesIO(resp.content)
            output_file.name = resp.name or os.path.basename(path)
            output_files.append(output_file)
    return output_files


# This is populated by apps.ApiConfig.ready()
OUTPUT_VIEW_PROVIDERS: dict[str, OutputViewProvider] = {}


class DefaultViewProvider:
    display_type = "default"
    immediate = False
    name = "Default"

    def generate_data(
        self,
        request: AiravataRequest,
        experiment_output: OutputDataObjectType,
        experiment: ExperimentModel,
        output_file: io.IOBase | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {}


DEFAULT_VIEW_PROVIDERS: dict[str, OutputViewProvider] = {
    "default": DefaultViewProvider()
}


def get_output_views(
    request: AiravataRequest,
    experiment: ExperimentModel,
    application_interface: ApplicationInterfaceDescription | None = None,
) -> dict[str, list[dict[str, Any]]]:
    output_views: dict[str, list[dict[str, Any]]] = {}
    for output in experiment.experiment_outputs:
        output_views[output.name] = []
        output_view_provider_ids = _get_output_view_providers(
            output, application_interface
        )
        for output_view_provider_id in output_view_provider_ids:
            output_view_provider = None
            if output_view_provider_id in DEFAULT_VIEW_PROVIDERS:
                output_view_provider = DEFAULT_VIEW_PROVIDERS[output_view_provider_id]
            elif output_view_provider_id in OUTPUT_VIEW_PROVIDERS:
                output_view_provider = OUTPUT_VIEW_PROVIDERS[output_view_provider_id]
            else:
                logger.warning(
                    f"Unable to find output view provider with name '{output_view_provider_id}'"
                )
            if output_view_provider is not None:
                view_config: dict[str, Any] = {
                    "provider-id": output_view_provider_id,
                    "display-type": output_view_provider.display_type,
                    "name": getattr(
                        output_view_provider, "name", output_view_provider_id
                    ),
                }
                if getattr(output_view_provider, "immediate", False):
                    # Immediately call generate_data function
                    data = _generate_data(
                        request, output_view_provider, output, experiment
                    )
                    view_config["data"] = data
                else:
                    view_config["data"] = {}
                output_views[output.name].append(view_config)
    return output_views


def _get_output_view_provider(
    output_view_provider_id: str,
) -> OutputViewProvider | None:

    if output_view_provider_id in DEFAULT_VIEW_PROVIDERS:
        return DEFAULT_VIEW_PROVIDERS[output_view_provider_id]
    elif output_view_provider_id in OUTPUT_VIEW_PROVIDERS:
        return OUTPUT_VIEW_PROVIDERS[output_view_provider_id]
    return None


def _get_output_view_providers(
    experiment_output: OutputDataObjectType,
    application_interface: ApplicationInterfaceDescription | None,
) -> list[str]:
    output_view_providers: list[str] = []
    logger.debug(
        "Resolving output view providers for output %s", experiment_output.name
    )
    if experiment_output.meta_data:
        try:
            output_metadata = json.loads(experiment_output.meta_data)
            logger.debug(f"output_metadata={output_metadata}")
            if "output-view-providers" in output_metadata:
                output_view_providers.extend(output_metadata["output-view-providers"])
        except Exception:
            logger.exception(
                f"Failed to parse metadata for output {experiment_output.name}"
            )
    # Add in any output view providers defined on the application interface
    if application_interface is not None:
        app_output_view_providers = _get_application_output_view_providers(
            application_interface, experiment_output.name
        )
        for view_provider in app_output_view_providers:
            if view_provider not in output_view_providers:
                output_view_providers.append(view_provider)
    if "default" not in output_view_providers:
        output_view_providers.insert(0, "default")
    return output_view_providers


def _get_application_output_view_providers(
    application_interface: ApplicationInterfaceDescription, output_name: str
) -> list[str]:
    app_output = [
        o for o in application_interface.application_outputs if o.name == output_name
    ]
    if len(app_output) == 1:
        logger.debug("Found application output definition for %s", output_name)
        app_output = app_output[0]
    else:
        return []
    if app_output.meta_data:
        try:
            output_metadata = json.loads(app_output.meta_data)
            if "output-view-providers" in output_metadata:
                return output_metadata["output-view-providers"]
        except Exception:
            logger.exception(f"Failed to parse metadata for output {app_output.name}")
    return []


def generate_data(
    request: AiravataRequest,
    output_view_provider_id: str,
    experiment_output_name: str,
    experiment_id: str,
    test_mode: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    output_view_provider = _get_output_view_provider(output_view_provider_id)
    # TODO if output_view_provider is None, return 404
    if output_view_provider is None:
        raise Exception(f"No output view provider {output_view_provider_id}")
    experiment = _get_experiment_proto(request, experiment_id)
    experiment_output = [
        o for o in experiment.experiment_outputs if o.name == experiment_output_name
    ]
    # TODO: handle experiment_output not found by name
    experiment_output = experiment_output[0]
    # TODO: add experiment_output_dir
    # convert the extra/interactive arguments to appropriate types
    kwargs = _convert_params_to_type(output_view_provider, kwargs)
    return _generate_data(
        request,
        output_view_provider,
        experiment_output,
        experiment,
        test_mode=test_mode,
        **kwargs,
    )


def _generate_data(
    request: AiravataRequest,
    output_view_provider: OutputViewProvider,
    experiment_output: OutputDataObjectType,
    experiment: ExperimentModel,
    test_mode: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    output_files: list[io.IOBase] = []
    # test_mode can only be used in DEBUG=True mode
    if test_mode and settings.DEBUG:
        test_output_file = getattr(output_view_provider, "test_output_file", None)
        if test_output_file is None:
            raise Exception(f"test_output_file is not set on {output_view_provider}")
        logger.info(f"Using {test_output_file} instead of regular output file")
        # Handle kept open intentionally: stored in output_files and read by the
        # view provider downstream; a context manager would close it too early.
        output_file = open(test_output_file, "rb")  # noqa: SIM115
        output_files.append(output_file)

    elif (
        experiment_output.value
        and experiment_output.type
        in (DataType.URI, DataType.URI_COLLECTION, DataType.STDOUT, DataType.STDERR)
        and experiment_output.value.startswith("airavata-dp")
    ):
        data_product_uris = experiment_output.value.split(",")
        output_files.extend(_download_data_product_files(request, data_product_uris))

    generate_data_func = output_view_provider.generate_data
    method_sig = inspect.signature(generate_data_func)
    if "output_files" in method_sig.parameters:
        generate_data_func = partial(generate_data_func, output_files=output_files)
    # TODO: convert experiment and experiment_output to dict/JSON
    data = generate_data_func(
        request,
        experiment_output,
        experiment,
        output_file=output_files[0] if len(output_files) > 0 else None,
        **kwargs,
    )
    _process_interactive_params(data)
    return data


def _process_interactive_params(data: dict[str, Any]) -> None:
    if "interactive" in data:
        _convert_options(data)
        for param in data["interactive"]:
            if "type" not in param:
                param["type"] = _infer_interactive_param_type(param)
            # integer type implicitly has a step size of 1
            if param["type"] == "integer" and "step" not in param:
                param["step"] = 1


def _convert_options(data: dict[str, Any]) -> None:
    """Convert interactive options to explicit text/value dicts."""
    for param in data["interactive"]:
        if "options" in param and isinstance(param["options"][0], str):
            param["options"] = _convert_options_strings(param["options"])
        elif "options" in param and isinstance(
            param["options"][0], collections.abc.Sequence
        ):
            param["options"] = _convert_options_sequences(param["options"])


def _convert_options_strings(options: list[str]) -> list[dict[str, str]]:
    return [{"text": o, "value": o} for o in options]


def _convert_options_sequences(
    options: list[collections.abc.Sequence[Any]],
) -> list[dict[str, Any]]:
    return [{"text": o[0], "value": o[1]} for o in options]


def _infer_interactive_param_type(param: dict[str, Any]) -> str | None:
    v = param["value"]
    # Boolean test must come first since bools are also integers
    if isinstance(v, bool):
        return "boolean"
    elif isinstance(v, float):
        return "float"
    elif isinstance(v, int):
        return "integer"
    elif isinstance(v, str):
        return "string"


def _convert_params_to_type(
    output_view_provider: OutputViewProvider, params: dict[str, Any]
) -> dict[str, Any]:
    method_sig = inspect.signature(output_view_provider.generate_data)
    method_params = method_sig.parameters
    # Special query parameter _meta holds type information for interactive
    # parameters (will only be present if there are interactive parameters)
    meta = json.loads(params.pop("_meta", "{}"))
    for k, v in params.items():
        meta_type = meta[k]["type"] if k in meta else None
        default_value = None
        if (
            k in method_params
            and method_params[k].default is not inspect.Parameter.empty
            and method_params[k].default is not None
        ):
            default_value = method_params[k].default
        # TODO: handle lists?
        # Handle boolean and numeric values, converting from string
        if meta_type == "boolean" or isinstance(default_value, bool):
            params[k] = v == "true"
        elif meta_type == "float" or isinstance(default_value, float):
            params[k] = float(v)
        elif meta_type == "integer" or isinstance(default_value, int):
            params[k] = int(v)
        elif meta_type == "string" or isinstance(default_value, str):
            params[k] = v
        else:
            logger.warning(
                f"Unrecognized type for parameter {k}: "
                f"meta_type={meta_type}, default_value={default_value}"
            )
    return params
