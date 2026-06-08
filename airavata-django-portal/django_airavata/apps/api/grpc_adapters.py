"""Adapters from gRPC protobuf messages to the attribute shape the existing
DRF serializers read.

Track D: while ``apps/api`` views are repointed from the Thrift API to the gRPC
facade (``request.airavata``), the portal keeps its REST contract with the Vue
frontend unchanged by reusing the existing serializers. Those serializers were
generated from the Thrift models, so they read Thrift attribute names
(``projectID``, ``creationTime``, ...). These adapters expose the corresponding
protobuf fields (``project_id``, ``creation_time``, ...) under those Thrift names,
so serializer output is identical by construction. They are removed once the
serializers are made protobuf-native.
"""

from types import SimpleNamespace

from airavata.model.appcatalog.parallelism.ttypes import (
    ApplicationParallelismType as _ThriftParallelismType,
)
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.credential.store.ttypes import SummaryType as _ThriftSummaryType


def _thrift_enum(pb, field, thrift_enum):
    """Map a protobuf enum field to the Thrift enum value of the SAME name.

    proto and Thrift enums frequently assign different integers to the same
    member name (e.g. ``SummaryType.SSH`` is 1 in proto but 0 in Thrift), so the
    bridge must go by NAME, never by raw integer — otherwise an adapter would
    silently mislabel one enum member as another.
    """
    enum_descriptor = pb.DESCRIPTOR.fields_by_name[field].enum_type
    name = enum_descriptor.values_by_number[getattr(pb, field)].name
    return getattr(thrift_enum, name)


def proto_summary_type(thrift_summary_type):
    """Thrift ``SummaryType`` -> proto ``SummaryType`` enum value (by name).

    The credential facade's request messages take the proto enum value, so views
    that still speak in Thrift ``SummaryType`` (e.g. for delete dispatch) convert
    through here. Imported lazily so this module stays importable without the
    gRPC SDK on the path (the SDK is required only once ``request.airavata`` is
    actually used).
    """
    from airavata_sdk.generated.org.apache.airavata.model.credential.store import (
        credential_store_pb2,
    )
    return credential_store_pb2.SummaryType.Value(
        _ThriftSummaryType(thrift_summary_type).name)


def project(pb):
    """gRPC ``Project`` protobuf -> ``ProjectSerializer`` (Thrift ``Project``) shape."""
    return SimpleNamespace(
        projectID=pb.project_id,
        owner=pb.owner,
        gatewayId=pb.gateway_id,
        name=pb.name,
        description=pb.description,
        # int64 epoch millis, like the Thrift field; 0 (unset) -> None for the
        # serializer's allow_null creationTime.
        creationTime=pb.creation_time or None,
        sharedUsers=list(pb.shared_users),
        sharedGroups=list(pb.shared_groups),
    )


def application_module(pb):
    """gRPC ``ApplicationModule`` protobuf -> ``ApplicationModuleSerializer`` shape."""
    return SimpleNamespace(
        appModuleId=pb.app_module_id,
        appModuleName=pb.app_module_name,
        appModuleVersion=pb.app_module_version,
        appModuleDescription=pb.app_module_description,
    )


def experiment_summary(pb):
    """gRPC ``ExperimentSummaryModel`` protobuf -> ``ExperimentSummarySerializer`` shape."""
    return SimpleNamespace(
        experimentId=pb.experiment_id,
        projectId=pb.project_id,
        gatewayId=pb.gateway_id,
        creationTime=pb.creation_time or None,
        userName=pb.user_name,
        name=pb.name,
        description=pb.description,
        executionId=pb.execution_id,
        resourceHostId=pb.resource_host_id,
        experimentStatus=pb.experiment_status,
        statusUpdateTime=pb.status_update_time or None,
    )


def credential_summary(pb):
    """gRPC ``CredentialSummary`` protobuf -> ``CredentialSummarySerializer`` shape."""
    return SimpleNamespace(
        # proto/Thrift SummaryType have different ints per name -> bridge by name
        # so the serializer's ThriftEnumField labels it correctly and
        # perform_destroy's ``instance.type == SummaryType.SSH`` (Thrift) holds.
        type=_thrift_enum(pb, 'type', _ThriftSummaryType),
        gatewayId=pb.gateway_id,
        username=pb.username,
        publicKey=pb.public_key,
        # int64 epoch millis, like the Thrift field; the serializer's
        # UTCPosixTimestampDateTimeField divides by 1000, so keep it an int.
        persistedTime=pb.persisted_time,
        token=pb.token,
        description=pb.description,
    )


def _input_data_object(pb):
    """gRPC ``InputDataObjectType`` -> ``InputDataObjectTypeSerializer`` shape."""
    return SimpleNamespace(
        name=pb.name,
        value=pb.value,
        # DataType proto/Thrift ints differ per name -> bridge by name; the
        # serializer's EnumChoiceField(DataType) reads ``.name`` off the member.
        type=_thrift_enum(pb, 'type', _ThriftDataType),
        applicationArgument=pb.application_argument,
        standardInput=pb.standard_input,
        userFriendlyDescription=pb.user_friendly_description,
        # JSON string; empty -> None so StoredJSONField renders null like Thrift.
        metaData=pb.meta_data or None,
        inputOrder=pb.input_order,
        isRequired=pb.is_required,
        requiredToAddedToCommandLine=pb.required_to_added_to_command_line,
        dataStaged=pb.data_staged,
        storageResourceId=pb.storage_resource_id,
        isReadOnly=pb.is_read_only,
        overrideFilename=pb.override_filename,
    )


def _output_data_object(pb):
    """gRPC ``OutputDataObjectType`` -> ``OutputDataObjectTypeSerializer`` shape."""
    return SimpleNamespace(
        name=pb.name,
        value=pb.value,
        type=_thrift_enum(pb, 'type', _ThriftDataType),
        applicationArgument=pb.application_argument,
        isRequired=pb.is_required,
        requiredToAddedToCommandLine=pb.required_to_added_to_command_line,
        dataMovement=pb.data_movement,
        location=pb.location,
        searchQuery=pb.search_query,
        outputStreaming=pb.output_streaming,
        storageResourceId=pb.storage_resource_id,
        metaData=pb.meta_data or None,
    )


def application_interface(pb):
    """gRPC ``ApplicationInterfaceDescription`` -> ``ApplicationInterfaceDescriptionSerializer`` shape.

    Recursively adapts the nested ``applicationInputs``/``applicationOutputs``
    repeated messages.
    """
    return SimpleNamespace(
        applicationInterfaceId=pb.application_interface_id,
        applicationName=pb.application_name,
        applicationDescription=pb.application_description,
        applicationModules=list(pb.application_modules),
        applicationInputs=[_input_data_object(i) for i in pb.application_inputs],
        applicationOutputs=[_output_data_object(o) for o in pb.application_outputs],
        archiveWorkingDirectory=pb.archive_working_directory,
        hasOptionalFileInputs=pb.has_optional_file_inputs,
    )


def _command_object(pb):
    """gRPC ``CommandObject`` -> ``CommandObjectSerializer`` shape."""
    return SimpleNamespace(command=pb.command, commandOrder=pb.command_order)


def _set_env_paths(pb):
    """gRPC ``SetEnvPaths`` -> ``SetEnvPathsSerializer`` shape."""
    return SimpleNamespace(
        name=pb.name, value=pb.value, envPathOrder=pb.env_path_order)


def application_deployment(pb):
    """gRPC ``ApplicationDeploymentDescription`` -> ``ApplicationDeploymentDescriptionSerializer`` shape.

    Recursively adapts the nested command/env-path lists. ``parallelism`` is an
    enum with the proto/Thrift integer mismatch (proto SERIAL=1 vs Thrift
    SERIAL=0) -> bridged by name. The queue-default cluster maps the proto-zero
    "unset" sentinels back to None so the serializer renders null as Thrift did.
    """
    return SimpleNamespace(
        appDeploymentId=pb.app_deployment_id,
        appModuleId=pb.app_module_id,
        computeHostId=pb.compute_host_id,
        executablePath=pb.executable_path,
        parallelism=_thrift_enum(pb, 'parallelism', _ThriftParallelismType),
        appDeploymentDescription=pb.app_deployment_description,
        moduleLoadCmds=[_command_object(c) for c in pb.module_load_cmds],
        libPrependPaths=[_set_env_paths(p) for p in pb.lib_prepend_paths],
        libAppendPaths=[_set_env_paths(p) for p in pb.lib_append_paths],
        setEnvironment=[_set_env_paths(p) for p in pb.set_environment],
        preJobCommands=[_command_object(c) for c in pb.pre_job_commands],
        postJobCommands=[_command_object(c) for c in pb.post_job_commands],
        defaultQueueName=pb.default_queue_name or None,
        defaultNodeCount=pb.default_node_count or None,
        defaultCPUCount=pb.default_cpu_count or None,
        defaultWalltime=pb.default_walltime or None,
        editableByUser=pb.editable_by_user,
    )
