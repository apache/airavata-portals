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

from airavata.model.appcatalog.computeresource.ttypes import (
    JobSubmissionProtocol as _ThriftJobSubmissionProtocol,
)
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    ResourceType as _ThriftResourceType,
)
from airavata.model.appcatalog.parallelism.ttypes import (
    ApplicationParallelismType as _ThriftParallelismType,
)
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.credential.store.ttypes import SummaryType as _ThriftSummaryType
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
)


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


def _thrift_enum_mapped(pb, field, proto_name_to_thrift):
    """Bridge a proto enum field to a Thrift value via an EXPLICIT name map.

    Needed when the proto and Thrift enum member NAMES diverge — proto3 prefixes
    members whose bare name would collide in the file (e.g. proto
    ``DATA_MOVEMENT_PROTOCOL_LOCAL`` vs Thrift ``LOCAL``), and some members exist
    on only one side (e.g. proto-only ``GRID_FTP``). Unmapped members — including
    the zero ``*_UNKNOWN`` sentinel and proto-only values — return None (the
    serializer fields are nullable for these).
    """
    enum_descriptor = pb.DESCRIPTOR.fields_by_name[field].enum_type
    proto_name = enum_descriptor.values_by_number[getattr(pb, field)].name
    return proto_name_to_thrift.get(proto_name)


# proto DataMovementProtocol member name -> Thrift DataMovementProtocol value.
# Names diverge (proto prefixes LOCAL; proto-only GRID_FTP has no Thrift value).
_DATA_MOVEMENT_PROTOCOL = {
    'DATA_MOVEMENT_PROTOCOL_LOCAL': _ThriftDataMovementProtocol.LOCAL,
    'SCP': _ThriftDataMovementProtocol.SCP,
    'SFTP': _ThriftDataMovementProtocol.SFTP,
    'UNICORE_STORAGE_SERVICE': _ThriftDataMovementProtocol.UNICORE_STORAGE_SERVICE,
}


def _data_movement_interface(pb):
    """gRPC ``DataMovementInterface`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        dataMovementInterfaceId=pb.data_movement_interface_id,
        dataMovementProtocol=_thrift_enum_mapped(
            pb, 'data_movement_protocol', _DATA_MOVEMENT_PROTOCOL),
        priorityOrder=pb.priority_order,
        creationTime=pb.creation_time or None,
        updateTime=pb.update_time or None,
        storageResourceId=pb.storage_resource_id,
    )


def storage_resource(pb):
    """gRPC ``StorageResourceDescription`` -> ``StorageResourceSerializer`` shape."""
    return SimpleNamespace(
        storageResourceId=pb.storage_resource_id,
        hostName=pb.host_name,
        storageResourceDescription=pb.storage_resource_description,
        enabled=pb.enabled,
        dataMovementInterfaces=[
            _data_movement_interface(d) for d in pb.data_movement_interfaces],
        # top-level creation/update use UTCPosixTimestampDateTimeField (not
        # nullable, divides by 1000) -> keep the int.
        creationTime=pb.creation_time,
        updateTime=pb.update_time,
    )


# proto JobSubmissionProtocol member name -> Thrift JobSubmissionProtocol value.
# Mostly aligned, but proto JSP_CLOUD maps to Thrift CLOUD (name divergence).
_JOB_SUBMISSION_PROTOCOL = {
    'LOCAL': _ThriftJobSubmissionProtocol.LOCAL,
    'SSH': _ThriftJobSubmissionProtocol.SSH,
    'GLOBUS': _ThriftJobSubmissionProtocol.GLOBUS,
    'UNICORE': _ThriftJobSubmissionProtocol.UNICORE,
    'JSP_CLOUD': _ThriftJobSubmissionProtocol.CLOUD,
    'SSH_FORK': _ThriftJobSubmissionProtocol.SSH_FORK,
    'LOCAL_FORK': _ThriftJobSubmissionProtocol.LOCAL_FORK,
}

# proto FileSystems int value -> Thrift FileSystems int value (built lazily by
# name; the proto map key is a bare int32 with no enum descriptor to read).
_file_systems_proto_to_thrift = None


def _file_systems(pb_map):
    """proto ``file_systems`` map<int32, string> -> {Thrift FileSystems int: path}.

    The proto map key is a bare int32 holding a proto ``FileSystems`` value;
    convert each to the Thrift ``FileSystems`` int (by name — proto HOME=1 vs
    Thrift HOME=0) so the serializer's ``DictField`` renders the same '0'..'4'
    keys the Thrift i32-keyed map produced. Keys stay plain ints (not IntEnum)
    so ``DictField``'s ``str(key)`` yields the digit, as Thrift's map did.
    Unknown keys (e.g. the proto-only zero sentinel) are dropped.
    """
    global _file_systems_proto_to_thrift
    if _file_systems_proto_to_thrift is None:
        from airavata.model.appcatalog.computeresource.ttypes import FileSystems
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource import (  # noqa: E501
            compute_resource_pb2,
        )
        proto_fs = compute_resource_pb2.FileSystems
        _file_systems_proto_to_thrift = {
            proto_fs.Value(name): int(getattr(FileSystems, name))
            for name in proto_fs.keys() if hasattr(FileSystems, name)
        }
    return {
        _file_systems_proto_to_thrift[k]: v
        for k, v in pb_map.items() if k in _file_systems_proto_to_thrift
    }


def _batch_queue(pb):
    """gRPC ``BatchQueue`` -> ``BatchQueueSerializer`` shape (all scalars)."""
    return SimpleNamespace(
        queueName=pb.queue_name,
        queueDescription=pb.queue_description,
        maxRunTime=pb.max_run_time,
        maxNodes=pb.max_nodes,
        maxProcessors=pb.max_processors,
        maxJobsInQueue=pb.max_jobs_in_queue,
        maxMemory=pb.max_memory,
        cpuPerNode=pb.cpu_per_node,
        defaultNodeCount=pb.default_node_count,
        defaultCPUCount=pb.default_cpu_count,
        defaultWalltime=pb.default_walltime,
        queueSpecificMacros=pb.queue_specific_macros,
        isDefaultQueue=pb.is_default_queue,
    )


def _job_submission_interface(pb):
    """gRPC ``JobSubmissionInterface`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobSubmissionInterfaceId=pb.job_submission_interface_id,
        jobSubmissionProtocol=_thrift_enum_mapped(
            pb, 'job_submission_protocol', _JOB_SUBMISSION_PROTOCOL),
        priorityOrder=pb.priority_order,
    )


def compute_resource(pb):
    """gRPC ``ComputeResourceDescription`` -> ``ComputeResourceDescriptionSerializer`` shape.

    The deepest read model: recursively adapts batch queues, the file-systems
    map, and the job-submission and data-movement interface lists.
    """
    return SimpleNamespace(
        computeResourceId=pb.compute_resource_id,
        hostName=pb.host_name,
        hostAliases=list(pb.host_aliases),
        ipAddresses=list(pb.ip_addresses),
        resourceDescription=pb.resource_description,
        enabled=pb.enabled,
        batchQueues=[_batch_queue(q) for q in pb.batch_queues],
        fileSystems=_file_systems(pb.file_systems),
        jobSubmissionInterfaces=[
            _job_submission_interface(j) for j in pb.job_submission_interfaces],
        dataMovementInterfaces=[
            _data_movement_interface(d) for d in pb.data_movement_interfaces],
        maxMemoryPerNode=pb.max_memory_per_node,
        gatewayUsageReporting=pb.gateway_usage_reporting,
        gatewayUsageModuleLoadCommand=pb.gateway_usage_module_load_command,
        gatewayUsageExecutable=pb.gateway_usage_executable,
        cpusPerNode=pb.cpus_per_node,
        defaultNodeCount=pb.default_node_count,
        defaultCPUCount=pb.default_cpu_count,
        defaultWalltime=pb.default_walltime,
    )


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


# proto ResourceType member name -> Thrift ResourceType value (names align,
# ints differ: proto SLURM=1 vs Thrift SLURM=0).
_RESOURCE_TYPE = {
    'SLURM': _ThriftResourceType.SLURM,
    'AWS': _ThriftResourceType.AWS,
}


def _compute_resource_reservation(pb):
    """gRPC ``ComputeResourceReservation`` -> ``ComputeResourceReservationSerializer`` shape."""
    return SimpleNamespace(
        reservationId=pb.reservation_id,
        reservationName=pb.reservation_name,
        queueNames=list(pb.queue_names),
        # serializer overrides start/end with nullable UTC fields.
        startTime=pb.start_time or None,
        endTime=pb.end_time or None,
    )


def _group_account_ssh_provisioner_config(pb):
    """gRPC ``GroupAccountSSHProvisionerConfig`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        resourceId=pb.resource_id,
        groupResourceProfileId=pb.group_resource_profile_id,
        configName=pb.config_name,
        configValue=pb.config_value,
    )


def _slurm_compute_resource_preference(pb):
    """gRPC ``SlurmComputeResourcePreference`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        allocationProjectNumber=pb.allocation_project_number,
        preferredBatchQueue=pb.preferred_batch_queue,
        qualityOfService=pb.quality_of_service,
        usageReportingGatewayId=pb.usage_reporting_gateway_id,
        sshAccountProvisioner=pb.ssh_account_provisioner,
        groupSSHAccountProvisionerConfigs=[
            _group_account_ssh_provisioner_config(c)
            for c in pb.group_ssh_account_provisioner_configs],
        sshAccountProvisionerAdditionalInfo=pb.ssh_account_provisioner_additional_info,
        reservations=[_compute_resource_reservation(r) for r in pb.reservations],
    )


def _aws_compute_resource_preference(pb):
    """gRPC ``AwsComputeResourcePreference`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        region=pb.region,
        preferredAmiId=pb.preferred_ami_id,
        preferredInstanceType=pb.preferred_instance_type,
    )


def _environment_specific_preferences(pb):
    """proto oneof ``EnvironmentSpecificPreferences`` -> {slurm, aws} (one set)."""
    which = pb.WhichOneof('preferences')
    return SimpleNamespace(
        slurm=(_slurm_compute_resource_preference(pb.slurm)
               if which == 'slurm' else None),
        aws=(_aws_compute_resource_preference(pb.aws)
             if which == 'aws' else None),
    )


def _group_compute_resource_preference(pb):
    """gRPC ``GroupComputeResourcePreference`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        computeResourceId=pb.compute_resource_id,
        groupResourceProfileId=pb.group_resource_profile_id,
        overridebyAiravata=pb.override_by_airavata,
        loginUserName=pb.login_user_name,
        scratchLocation=pb.scratch_location,
        # rendered as raw ints; bridge by name (incl. the JSP_CLOUD/LOCAL
        # divergences) to the Thrift integer the frontend expects.
        preferredJobSubmissionProtocol=_thrift_enum_mapped(
            pb, 'preferred_job_submission_protocol', _JOB_SUBMISSION_PROTOCOL),
        preferredDataMovementProtocol=_thrift_enum_mapped(
            pb, 'preferred_data_movement_protocol', _DATA_MOVEMENT_PROTOCOL),
        # empty token -> None so the serializer's userHasWriteAccess token READ
        # check (``token is None or ...``) skips unset tokens.
        resourceSpecificCredentialStoreToken=(
            pb.resource_specific_credential_store_token or None),
        resourceType=_thrift_enum_mapped(pb, 'resource_type', _RESOURCE_TYPE),
        specificPreferences=(
            _environment_specific_preferences(pb.specific_preferences)
            if pb.HasField('specific_preferences') else None),
    )


def _compute_resource_policy(pb):
    """gRPC ``ComputeResourcePolicy`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        resourcePolicyId=pb.resource_policy_id,
        computeResourceId=pb.compute_resource_id,
        groupResourceProfileId=pb.group_resource_profile_id,
        allowedBatchQueues=list(pb.allowed_batch_queues),
    )


def _batch_queue_resource_policy(pb):
    """gRPC ``BatchQueueResourcePolicy`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        resourcePolicyId=pb.resource_policy_id,
        computeResourceId=pb.compute_resource_id,
        groupResourceProfileId=pb.group_resource_profile_id,
        queuename=pb.queuename,
        maxAllowedNodes=pb.max_allowed_nodes,
        maxAllowedCores=pb.max_allowed_cores,
        maxAllowedWalltime=pb.max_allowed_walltime,
    )


def group_resource_profile(pb):
    """gRPC ``GroupResourceProfile`` -> ``GroupResourceProfileSerializer`` shape.

    Recursively adapts the compute preferences (each carrying a slurm/aws
    union of specific preferences with reservations) and the compute /
    batch-queue resource policies.
    """
    return SimpleNamespace(
        gatewayId=pb.gateway_id,
        groupResourceProfileId=pb.group_resource_profile_id,
        groupResourceProfileName=pb.group_resource_profile_name,
        computePreferences=[
            _group_compute_resource_preference(p) for p in pb.compute_preferences],
        computeResourcePolicies=[
            _compute_resource_policy(p) for p in pb.compute_resource_policies],
        batchQueueResourcePolicies=[
            _batch_queue_resource_policy(p) for p in pb.batch_queue_resource_policies],
        creationTime=pb.creation_time or None,
        updatedTime=pb.updated_time or None,
        defaultCredentialStoreToken=pb.default_credential_store_token or None,
    )
