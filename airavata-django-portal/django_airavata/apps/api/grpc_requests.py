"""Adapters from the Thrift-shaped objects the DRF serializers produce to the
gRPC protobuf request messages the facade expects.

Track D (D3 writes): the ``apps/api`` serializers were generated from the Thrift
models, so ``serializer.save()`` yields a Thrift model instance (Thrift attribute
names: ``projectID``, ``gatewayId``, ...). These adapters convert that instance
into the corresponding protobuf message (``project_id``, ``gateway_id``, ...) so
the gRPC facade can send it. They are the write-direction mirror of
``grpc_adapters`` and are removed once the serializers are made protobuf-native.

proto3 scalar fields cannot hold ``None``, so optional Thrift values that may be
``None`` are coerced to the proto default (``''``/``0``/``[]``).
"""

import importlib

from airavata.model.appcatalog.parallelism.ttypes import (
    ApplicationParallelismType as _ThriftParallelismType,
)
from airavata.model.application.io.ttypes import DataType as _ThriftDataType

_GEN = "airavata_sdk.generated.org.apache.airavata.model"


def _pb2(path):
    return importlib.import_module(f"{_GEN}.{path}")


def _workspace_pb2():
    return _pb2("workspace.workspace_pb2")


def _proto_enum(proto_enum, thrift_enum, value, prefix=''):
    """Thrift enum value -> proto enum value, by name (mirror of the read-side
    ``grpc_adapters`` enum bridges).

    proto and Thrift enums assign different integers to the same member name, so
    the bridge goes by NAME. ``prefix`` re-applies a proto-only member prefix
    (e.g. ``EXPERIMENT_STATE_``). ``None`` -> 0 (the proto default / zero
    sentinel).
    """
    if value is None:
        return 0
    name = thrift_enum(value).name
    return proto_enum.Value(prefix + name)


def project(t):
    """Thrift ``Project`` -> proto ``Project`` request message."""
    return _workspace_pb2().Project(
        project_id=t.projectID or '',
        owner=t.owner or '',
        gateway_id=t.gatewayId or '',
        name=t.name or '',
        description=t.description or '',
        creation_time=t.creationTime or 0,
        shared_users=list(t.sharedUsers or []),
        shared_groups=list(t.sharedGroups or []),
    )


def password_credential(gateway_id, portal_user_name, login_user_name,
                         password, description):
    """Build a proto ``PasswordCredential`` from the create-password request."""
    return _pb2("credential.store.credential_store_pb2").PasswordCredential(
        gateway_id=gateway_id or '',
        portal_user_name=portal_user_name or '',
        login_user_name=login_user_name or '',
        password=password or '',
        description=description or '',
    )


def application_module(t):
    """Thrift ``ApplicationModule`` -> proto ``ApplicationModule``."""
    return _pb2("appcatalog.appdeployment.app_deployment_pb2").ApplicationModule(
        app_module_id=t.appModuleId or '',
        app_module_name=t.appModuleName or '',
        app_module_version=t.appModuleVersion or '',
        app_module_description=t.appModuleDescription or '',
    )


def _input_data_object(t):
    io = _pb2("application.io.application_io_pb2")
    return io.InputDataObjectType(
        name=t.name or '',
        value=t.value or '',
        type=_proto_enum(io.DataType, _ThriftDataType, t.type),
        application_argument=t.applicationArgument or '',
        standard_input=bool(t.standardInput),
        user_friendly_description=t.userFriendlyDescription or '',
        # StoredJSONField.to_internal_value json.dumps()es metaData to a string.
        meta_data=t.metaData or '',
        input_order=t.inputOrder or 0,
        is_required=bool(t.isRequired),
        required_to_added_to_command_line=bool(t.requiredToAddedToCommandLine),
        data_staged=bool(t.dataStaged),
        storage_resource_id=t.storageResourceId or '',
        is_read_only=bool(t.isReadOnly),
        override_filename=t.overrideFilename or '',
    )


def _output_data_object(t):
    io = _pb2("application.io.application_io_pb2")
    return io.OutputDataObjectType(
        name=t.name or '',
        value=t.value or '',
        type=_proto_enum(io.DataType, _ThriftDataType, t.type),
        application_argument=t.applicationArgument or '',
        is_required=bool(t.isRequired),
        required_to_added_to_command_line=bool(t.requiredToAddedToCommandLine),
        data_movement=bool(t.dataMovement),
        location=t.location or '',
        search_query=t.searchQuery or '',
        output_streaming=bool(t.outputStreaming),
        storage_resource_id=t.storageResourceId or '',
        meta_data=t.metaData or '',
    )


def application_interface(t):
    """Thrift ``ApplicationInterfaceDescription`` -> proto message."""
    return _pb2("appcatalog.appinterface.app_interface_pb2").ApplicationInterfaceDescription(
        application_interface_id=t.applicationInterfaceId or '',
        application_name=t.applicationName or '',
        application_description=t.applicationDescription or '',
        application_modules=list(t.applicationModules or []),
        application_inputs=[_input_data_object(i) for i in (t.applicationInputs or [])],
        application_outputs=[_output_data_object(o) for o in (t.applicationOutputs or [])],
        archive_working_directory=bool(t.archiveWorkingDirectory),
        has_optional_file_inputs=bool(t.hasOptionalFileInputs),
    )


def _command_object(t):
    return _pb2("appcatalog.appdeployment.app_deployment_pb2").CommandObject(
        command=t.command or '',
        command_order=t.commandOrder or 0,
    )


def _set_env_paths(t):
    return _pb2("appcatalog.appdeployment.app_deployment_pb2").SetEnvPaths(
        name=t.name or '',
        value=t.value or '',
        env_path_order=t.envPathOrder or 0,
    )


def application_deployment(t):
    """Thrift ``ApplicationDeploymentDescription`` -> proto message."""
    dep = _pb2("appcatalog.appdeployment.app_deployment_pb2")
    return dep.ApplicationDeploymentDescription(
        app_deployment_id=t.appDeploymentId or '',
        app_module_id=t.appModuleId or '',
        compute_host_id=t.computeHostId or '',
        executable_path=t.executablePath or '',
        parallelism=_proto_enum(
            _pb2("parallelism.parallelism_pb2").ApplicationParallelismType,
            _ThriftParallelismType, t.parallelism),
        app_deployment_description=t.appDeploymentDescription or '',
        module_load_cmds=[_command_object(c) for c in (t.moduleLoadCmds or [])],
        lib_prepend_paths=[_set_env_paths(p) for p in (t.libPrependPaths or [])],
        lib_append_paths=[_set_env_paths(p) for p in (t.libAppendPaths or [])],
        set_environment=[_set_env_paths(p) for p in (t.setEnvironment or [])],
        pre_job_commands=[_command_object(c) for c in (t.preJobCommands or [])],
        post_job_commands=[_command_object(c) for c in (t.postJobCommands or [])],
        default_queue_name=t.defaultQueueName or '',
        default_node_count=t.defaultNodeCount or 0,
        default_cpu_count=t.defaultCPUCount or 0,
        default_walltime=t.defaultWalltime or 0,
        editable_by_user=bool(t.editableByUser),
    )
