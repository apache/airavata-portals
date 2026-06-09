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
    JobManagerCommand as _ThriftJobManagerCommand,
    JobSubmissionProtocol as _ThriftJobSubmissionProtocol,
    MonitorMode as _ThriftMonitorMode,
    ProviderName as _ThriftProviderName,
    ResourceJobManagerType as _ThriftResourceJobManagerType,
)
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    ResourceType as _ThriftResourceType,
)
from airavata.model.appcatalog.parallelism.ttypes import (
    ApplicationParallelismType as _ThriftParallelismType,
)
from airavata.model.appcatalog.parser.ttypes import IOType as _ThriftIOType
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.data.replica.ttypes import (
    DataProductType as _ThriftDataProductType,
    ReplicaLocationCategory as _ThriftReplicaLocationCategory,
    ReplicaPersistentType as _ThriftReplicaPersistentType,
)
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
    SecurityProtocol as _ThriftSecurityProtocol,
)
from airavata.model.experiment.ttypes import (
    ExperimentType as _ThriftExperimentType,
)
from airavata.model.status.ttypes import (
    ExperimentState as _ThriftExperimentState,
    JobState as _ThriftJobState,
    ProcessState as _ThriftProcessState,
    TaskState as _ThriftTaskState,
)
from airavata.model.task.ttypes import TaskTypes as _ThriftTaskTypes
from airavata.model.user.ttypes import Status as _ThriftStatus
from airavata.model.workspace.ttypes import (
    NotificationPriority as _ThriftNotificationPriority,
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


def _thrift_enum_prefixed(pb, field, thrift_enum, proto_prefix):
    """Bridge a proto enum field to a Thrift value by name after stripping a
    proto-only prefix.

    proto3 namespaces enum members that would otherwise collide in the file
    (``EXPERIMENT_STATE_CREATED``) where the Thrift enum uses the bare name
    (``CREATED``). Members absent from Thrift — notably the zero ``*_UNKNOWN``
    sentinel — map to None (the serializer renders these as nullable ints).
    """
    name = pb.DESCRIPTOR.fields_by_name[field].enum_type.values_by_number[
        getattr(pb, field)].name
    if name.startswith(proto_prefix):
        name = name[len(proto_prefix):]
    return getattr(thrift_enum, name, None)


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


def experiment_statistics(pb):
    """gRPC ``ExperimentStatistics`` -> ``ExperimentStatisticsSerializer`` shape.

    A wrapper of per-state counts plus per-state experiment-summary lists, each
    list adapted with :func:`experiment_summary`.
    """
    return SimpleNamespace(
        allExperimentCount=pb.all_experiment_count,
        completedExperimentCount=pb.completed_experiment_count,
        cancelledExperimentCount=pb.cancelled_experiment_count,
        failedExperimentCount=pb.failed_experiment_count,
        createdExperimentCount=pb.created_experiment_count,
        runningExperimentCount=pb.running_experiment_count,
        allExperiments=[experiment_summary(s) for s in pb.all_experiments],
        completedExperiments=[experiment_summary(s) for s in pb.completed_experiments],
        failedExperiments=[experiment_summary(s) for s in pb.failed_experiments],
        cancelledExperiments=[experiment_summary(s) for s in pb.cancelled_experiments],
        createdExperiments=[experiment_summary(s) for s in pb.created_experiments],
        runningExperiments=[experiment_summary(s) for s in pb.running_experiments],
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


def storage_preference(pb):
    """gRPC ``StoragePreference`` -> ``StoragePreferenceSerializer`` shape."""
    return SimpleNamespace(
        storageResourceId=pb.storage_resource_id,
        loginUserName=pb.login_user_name,
        fileSystemRootLocation=pb.file_system_root_location,
        resourceSpecificCredentialStoreToken=pb.resource_specific_credential_store_token,
    )


def _compute_resource_preference(pb):
    """gRPC ``ComputeResourcePreference`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        computeResourceId=pb.compute_resource_id,
        overridebyAiravata=pb.override_by_airavata,
        loginUserName=pb.login_user_name,
        # rendered as raw ints; bridge by name (name-divergent maps).
        preferredJobSubmissionProtocol=_thrift_enum_mapped(
            pb, 'preferred_job_submission_protocol', _JOB_SUBMISSION_PROTOCOL),
        preferredDataMovementProtocol=_thrift_enum_mapped(
            pb, 'preferred_data_movement_protocol', _DATA_MOVEMENT_PROTOCOL),
        preferredBatchQueue=pb.preferred_batch_queue,
        scratchLocation=pb.scratch_location,
        allocationProjectNumber=pb.allocation_project_number,
        resourceSpecificCredentialStoreToken=pb.resource_specific_credential_store_token,
        usageReportingGatewayId=pb.usage_reporting_gateway_id,
        qualityOfService=pb.quality_of_service,
        reservation=pb.reservation,
        reservationStartTime=pb.reservation_start_time or None,
        reservationEndTime=pb.reservation_end_time or None,
        sshAccountProvisioner=pb.ssh_account_provisioner,
        sshAccountProvisionerConfig=dict(pb.ssh_account_provisioner_config),
        sshAccountProvisionerAdditionalInfo=pb.ssh_account_provisioner_additional_info,
    )


def gateway_resource_profile(pb):
    """gRPC ``GatewayResourceProfile`` -> ``GatewayResourceProfileSerializer`` shape."""
    return SimpleNamespace(
        gatewayID=pb.gateway_id,
        credentialStoreToken=pb.credential_store_token,
        computeResourcePreferences=[
            _compute_resource_preference(p) for p in pb.compute_resource_preferences],
        storagePreferences=[storage_preference(p) for p in pb.storage_preferences],
        identityServerTenant=pb.identity_server_tenant,
        identityServerPwdCredToken=pb.identity_server_pwd_cred_token,
    )


# --- Experiment tree -------------------------------------------------------
#
# getExperiment returns the full ExperimentModel including the processes tree
# (process -> tasks -> jobs, each with its status list). The status/type enums
# render as raw integers and are bridged by name with the proto prefix stripped
# (proto EXPERIMENT_STATE_CREATED -> Thrift CREATED). Status timeOfStateChange
# stays an int (ExperimentStatusSerializer/ProcessStatusSerializer use a
# non-nullable UTC field; the nested auto-generated ones render the int);
# model creation/update times map proto-zero -> None (nullable).


def _error_model(pb):
    """gRPC ``ErrorModel`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        errorId=pb.error_id,
        creationTime=pb.creation_time or None,
        actualErrorMessage=pb.actual_error_message,
        userFriendlyMessage=pb.user_friendly_message,
        transientOrPersistent=pb.transient_or_persistent,
        rootCauseErrorIdList=list(pb.root_cause_error_id_list),
    )


def _computational_resource_scheduling(pb):
    """gRPC ``ComputationalResourceSchedulingModel`` -> auto-generated shape."""
    return SimpleNamespace(
        resourceHostId=pb.resource_host_id,
        totalCPUCount=pb.total_cpu_count,
        nodeCount=pb.node_count,
        numberOfThreads=pb.number_of_threads,
        queueName=pb.queue_name,
        wallTimeLimit=pb.wall_time_limit,
        totalPhysicalMemory=pb.total_physical_memory,
        chessisNumber=pb.chessis_number,
        staticWorkingDir=pb.static_working_dir,
        overrideLoginUserName=pb.override_login_user_name,
        overrideScratchLocation=pb.override_scratch_location,
        overrideAllocationProjectNumber=pb.override_allocation_project_number,
        mGroupCount=pb.m_group_count,
    )


def _user_configuration_data(pb):
    """gRPC ``UserConfigurationDataModel`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        airavataAutoSchedule=pb.airavata_auto_schedule,
        overrideManualScheduledParams=pb.override_manual_scheduled_params,
        shareExperimentPublicly=pb.share_experiment_publicly,
        computationalResourceScheduling=(
            _computational_resource_scheduling(pb.computational_resource_scheduling)
            if pb.HasField('computational_resource_scheduling') else None),
        throttleResources=pb.throttle_resources,
        userDN=pb.user_dn,
        generateCert=pb.generate_cert,
        inputStorageResourceId=pb.input_storage_resource_id,
        outputStorageResourceId=pb.output_storage_resource_id,
        experimentDataDir=pb.experiment_data_dir,
        useUserCRPref=pb.use_user_cr_pref,
        groupResourceProfileId=pb.group_resource_profile_id,
        autoScheduledCompResourceSchedulingList=[
            _computational_resource_scheduling(s)
            for s in pb.auto_scheduled_comp_resource_scheduling_list],
    )


def _experiment_status(pb):
    """gRPC ``ExperimentStatus`` -> ``ExperimentStatusSerializer`` shape."""
    return SimpleNamespace(
        state=_thrift_enum_prefixed(
            pb, 'state', _ThriftExperimentState, 'EXPERIMENT_STATE_'),
        timeOfStateChange=pb.time_of_state_change,
        reason=pb.reason,
        statusId=pb.status_id,
    )


def _process_status(pb):
    """gRPC ``ProcessStatus`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        state=_thrift_enum_prefixed(
            pb, 'state', _ThriftProcessState, 'PROCESS_STATE_'),
        timeOfStateChange=pb.time_of_state_change,
        reason=pb.reason,
        statusId=pb.status_id,
        processId=pb.process_id,
    )


def _task_status(pb):
    """gRPC ``TaskStatus`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        state=_thrift_enum_prefixed(
            pb, 'state', _ThriftTaskState, 'TASK_STATE_'),
        timeOfStateChange=pb.time_of_state_change,
        reason=pb.reason,
        statusId=pb.status_id,
    )


def _job_status(pb):
    """gRPC ``JobStatus`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobState=_thrift_enum_prefixed(
            pb, 'job_state', _ThriftJobState, 'JOB_STATE_'),
        timeOfStateChange=pb.time_of_state_change,
        reason=pb.reason,
        statusId=pb.status_id,
    )


def job_model(pb):
    """gRPC ``JobModel`` -> ``JobSerializer`` shape."""
    return SimpleNamespace(
        jobId=pb.job_id,
        taskId=pb.task_id,
        processId=pb.process_id,
        jobDescription=pb.job_description,
        creationTime=pb.creation_time or None,
        jobStatuses=[_job_status(s) for s in pb.job_statuses],
        computeResourceConsumed=pb.compute_resource_consumed,
        jobName=pb.job_name,
        workingDir=pb.working_dir,
        stdOut=pb.std_out,
        stdErr=pb.std_err,
        exitCode=pb.exit_code,
    )


def _task_model(pb):
    """gRPC ``TaskModel`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        taskId=pb.task_id,
        taskType=_thrift_enum_prefixed(
            pb, 'task_type', _ThriftTaskTypes, 'TASK_TYPES_'),
        parentProcessId=pb.parent_process_id,
        creationTime=pb.creation_time or None,
        lastUpdateTime=pb.last_update_time or None,
        taskStatuses=[_task_status(s) for s in pb.task_statuses],
        taskDetail=pb.task_detail,
        subTaskModel=pb.sub_task_model,
        taskErrors=[_error_model(e) for e in pb.task_errors],
        jobs=[job_model(j) for j in pb.jobs],
        maxRetry=pb.max_retry,
        currentRetry=pb.current_retry,
    )


def _process_model(pb):
    """gRPC ``ProcessModel`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        processId=pb.process_id,
        experimentId=pb.experiment_id,
        creationTime=pb.creation_time or None,
        lastUpdateTime=pb.last_update_time or None,
        processStatuses=[_process_status(s) for s in pb.process_statuses],
        processDetail=pb.process_detail,
        applicationInterfaceId=pb.application_interface_id,
        applicationDeploymentId=pb.application_deployment_id,
        computeResourceId=pb.compute_resource_id,
        processInputs=[_input_data_object(i) for i in pb.process_inputs],
        processOutputs=[_output_data_object(o) for o in pb.process_outputs],
        processResourceSchedule=(
            _computational_resource_scheduling(pb.process_resource_schedule)
            if pb.HasField('process_resource_schedule') else None),
        tasks=[_task_model(t) for t in pb.tasks],
        taskDag=pb.task_dag,
        processErrors=[_error_model(e) for e in pb.process_errors],
        gatewayExecutionId=pb.gateway_execution_id,
        enableEmailNotification=pb.enable_email_notification,
        emailAddresses=list(pb.email_addresses),
        inputStorageResourceId=pb.input_storage_resource_id,
        outputStorageResourceId=pb.output_storage_resource_id,
        userDn=pb.user_dn,
        generateCert=pb.generate_cert,
        experimentDataDir=pb.experiment_data_dir,
        userName=pb.user_name,
        useUserCRPref=pb.use_user_cr_pref,
        groupResourceProfileId=pb.group_resource_profile_id,
        # the legacy workflow-engine subsystem is not adapted (rarely populated);
        # an empty list matches the Thrift default for non-workflow processes.
        processWorkflows=[],
    )


def experiment(pb):
    """gRPC ``ExperimentModel`` -> ``ExperimentSerializer`` shape.

    The deepest read model: recursively adapts the user configuration, the
    experiment input/output and status lists, the errors, and the full
    processes -> tasks -> jobs tree.
    """
    return SimpleNamespace(
        experimentId=pb.experiment_id,
        projectId=pb.project_id,
        gatewayId=pb.gateway_id,
        experimentType=_thrift_enum_prefixed(
            pb, 'experiment_type', _ThriftExperimentType, 'EXPERIMENT_TYPE_'),
        userName=pb.user_name,
        experimentName=pb.experiment_name,
        creationTime=pb.creation_time or None,
        description=pb.description,
        executionId=pb.execution_id,
        gatewayExecutionId=pb.gateway_execution_id,
        gatewayInstanceId=pb.gateway_instance_id,
        enableEmailNotification=pb.enable_email_notification,
        emailAddresses=list(pb.email_addresses),
        userConfigurationData=(
            _user_configuration_data(pb.user_configuration_data)
            if pb.HasField('user_configuration_data') else None),
        experimentInputs=[_input_data_object(i) for i in pb.experiment_inputs],
        experimentOutputs=[_output_data_object(o) for o in pb.experiment_outputs],
        experimentStatus=[_experiment_status(s) for s in pb.experiment_status],
        errors=[_error_model(e) for e in pb.errors],
        processes=[_process_model(p) for p in pb.processes],
        # legacy workflow-engine subsystem not adapted (rarely populated).
        workflow=None,
    )


def group(pb):
    """gRPC ``GroupModel`` -> ``GroupSerializer`` shape."""
    return SimpleNamespace(
        id=pb.id,
        name=pb.name,
        ownerId=pb.owner_id,
        description=pb.description or None,
        members=list(pb.members),
        admins=list(pb.admins),
    )


def _data_replica_location(pb):
    """gRPC ``DataReplicaLocationModel`` -> serializer shape."""
    return SimpleNamespace(
        replicaId=pb.replica_id or None,
        productUri=pb.product_uri or None,
        replicaName=pb.replica_name or None,
        replicaDescription=pb.replica_description or None,
        creationTime=pb.creation_time or None,
        lastModifiedTime=pb.last_modified_time or None,
        validUntilTime=pb.valid_until_time or None,
        replicaLocationCategory=_thrift_enum_prefixed(
            pb, 'replica_location_category', _ThriftReplicaLocationCategory,
            'REPLICA_LOCATION_CATEGORY_'),
        replicaPersistentType=_thrift_enum_prefixed(
            pb, 'replica_persistent_type', _ThriftReplicaPersistentType,
            'REPLICA_PERSISTENT_TYPE_'),
        storageResourceId=pb.storage_resource_id or None,
        filePath=pb.file_path or None,
        replicaMetadata=dict(pb.replica_metadata),
    )


def data_product_file_path(data_product):
    """First replica's ``filePath`` from an adapted data product, or None.

    The gRPC ``storage`` facade expects the FULL FILE PATH, absolute or
    ``~/``-prefixed (a bare relative path NPEs server-side, as ``resolvePath``
    expands ``~/`` to the storage root). Replica file paths are typically
    absolute (e.g. ``/storage/tmp/<file>``); a relative one is ``~/``-prefixed.
    Pass an adapted ``DataProductModel`` (``grpc_adapters.data_product``).
    """
    replicas = getattr(data_product, 'replicaLocations', None) or []
    if not replicas:
        return None
    file_path = getattr(replicas[0], 'filePath', None)
    if not file_path:
        return None
    if not (file_path.startswith('/') or file_path.startswith('~/')):
        file_path = '~/' + file_path
    return file_path


def data_product(pb):
    """gRPC ``DataProductModel`` -> ``DataProductSerializer`` shape."""
    return SimpleNamespace(
        productUri=pb.product_uri,
        gatewayId=pb.gateway_id,
        parentProductUri=pb.parent_product_uri or None,
        productName=pb.product_name or None,
        productDescription=pb.product_description or None,
        ownerName=pb.owner_name or None,
        dataProductType=_thrift_enum_prefixed(
            pb, 'data_product_type', _ThriftDataProductType,
            'DATA_PRODUCT_TYPE_'),
        productSize=pb.product_size or None,
        creationTime=pb.creation_time or None,
        # the serializer declares both modifiedTime and lastModifiedTime
        modifiedTime=pb.last_modified_time or None,
        lastModifiedTime=pb.last_modified_time or None,
        productMetadata=dict(pb.product_metadata),
        replicaLocations=[
            _data_replica_location(r) for r in pb.replica_locations],
    )


def user_profile(pb):
    """gRPC ``UserProfile`` -> ``UserProfileSerializer`` shape.

    Note the Thrift attribute quirks the serializer expects: ``State`` (capital),
    ``orginationAffiliation`` (Thrift's spelling), ``labeledURI``. The nested
    ``nsfDemographics``/``customDashboard`` structs are not surfaced in the
    sharing UI, so they render null.
    """
    return SimpleNamespace(
        userModelVersion=pb.user_model_version or None,
        airavataInternalUserId=pb.airavata_internal_user_id,
        userId=pb.user_id,
        gatewayId=pb.gateway_id,
        emails=list(pb.emails),
        firstName=pb.first_name or None,
        lastName=pb.last_name or None,
        middleName=pb.middle_name or None,
        namePrefix=pb.name_prefix or None,
        nameSuffix=pb.name_suffix or None,
        orcidId=pb.orcid_id or None,
        phones=list(pb.phones),
        country=pb.country or None,
        nationality=list(pb.nationality),
        homeOrganization=pb.home_organization or None,
        orginationAffiliation=pb.origination_affiliation or None,
        creationTime=pb.creation_time or None,
        lastAccessTime=pb.last_access_time or None,
        validUntil=pb.valid_until or None,
        State=_thrift_enum_prefixed(pb, 'state', _ThriftStatus, 'STATUS_'),
        comments=pb.comments or None,
        labeledURI=pb.labeled_uri or None,
        gpgKey=pb.gpg_key or None,
        timeZone=pb.time_zone or None,
        nsfDemographics=None,
        customDashboard=None,
    )


def notification(pb):
    """gRPC ``Notification`` -> ``NotificationSerializer`` shape."""
    return SimpleNamespace(
        notificationId=pb.notification_id,
        gatewayId=pb.gateway_id,
        title=pb.title,
        notificationMessage=pb.notification_message,
        creationTime=pb.creation_time or None,
        # publishedTime/expirationTime use non-nullable UTC fields -> keep int.
        publishedTime=pb.published_time,
        expirationTime=pb.expiration_time,
        # priority renders via ThriftEnumField (the NAME), so produce the Thrift
        # member; proto prefixes only the zero UNKNOWN sentinel.
        priority=_thrift_enum_prefixed(
            pb, 'priority', _ThriftNotificationPriority, 'NOTIFICATION_PRIORITY_'),
    )


def _parser_input(pb):
    """gRPC ``ParserInput`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        id=pb.id,
        name=pb.name,
        requiredInput=pb.required_input,
        parserId=pb.parser_id,
        # type (IOType) renders as a raw int; bridge by name (proto FILE/PROPERTY
        # align, only IO_TYPE_UNKNOWN is prefixed).
        type=_thrift_enum_prefixed(pb, 'type', _ThriftIOType, 'IO_TYPE_'),
    )


def _parser_output(pb):
    """gRPC ``ParserOutput`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        id=pb.id,
        name=pb.name,
        requiredOutput=pb.required_output,
        parserId=pb.parser_id,
        type=_thrift_enum_prefixed(pb, 'type', _ThriftIOType, 'IO_TYPE_'),
    )


def parser(pb):
    """gRPC ``Parser`` -> ``ParserSerializer`` shape."""
    return SimpleNamespace(
        id=pb.id,
        imageName=pb.image_name,
        outputDirPath=pb.output_dir_path,
        inputDirPath=pb.input_dir_path,
        executionCommand=pb.execution_command,
        inputFiles=[_parser_input(i) for i in pb.input_files],
        outputFiles=[_parser_output(o) for o in pb.output_files],
        gatewayId=pb.gateway_id,
    )


# --- Per-protocol job-submission / data-movement interface details ----------
# These admin-only detail views render a single protocol's submission/movement
# model via the auto-generated serializer, so the adapter exposes Thrift attribute
# names. SecurityProtocol/ResourceJobManagerType/ProviderName are prefix-aligned
# (proto *_UNKNOWN sentinel -> None). MonitorMode NAMES diverge (proto MONITOR_FORK
# / MONITOR_LOCAL vs Thrift FORK / LOCAL) so it needs an explicit map. The
# ResourceJobManager carries two enum-keyed map<int32,string> fields whose int keys
# hold proto enum values, bridged to the Thrift enum int by name (like _file_systems).

# proto MonitorMode member name -> Thrift MonitorMode value (names diverge for the
# FORK/LOCAL members, which proto prefixes with MONITOR_).
_MONITOR_MODE = {
    'POLL_JOB_MANAGER': _ThriftMonitorMode.POLL_JOB_MANAGER,
    'CLOUD_JOB_MONITOR': _ThriftMonitorMode.CLOUD_JOB_MONITOR,
    'JOB_EMAIL_NOTIFICATION_MONITOR': _ThriftMonitorMode.JOB_EMAIL_NOTIFICATION_MONITOR,
    'XSEDE_AMQP_SUBSCRIBE': _ThriftMonitorMode.XSEDE_AMQP_SUBSCRIBE,
    'MONITOR_FORK': _ThriftMonitorMode.FORK,
    'MONITOR_LOCAL': _ThriftMonitorMode.LOCAL,
}


def _enum_keyed_map(pb_map, proto_enum, thrift_enum):
    """proto map<int32, string> whose int key holds a ``proto_enum`` value ->
    {Thrift enum member: value}, bridging the key by NAME (proto and Thrift assign
    different ints to the same member). The Thrift model declared these as
    enum-keyed maps, so the serializer's ``DictField`` rendered ``str(member)``
    (e.g. ``'JobManagerCommand.SUBMISSION'``) -> keep the Thrift IntEnum member as
    the key to reproduce that exact representation. Unknown keys (e.g. the zero
    sentinel) are dropped.
    """
    result = {}
    for k, v in pb_map.items():
        name = proto_enum.DESCRIPTOR.values_by_number.get(k)
        if name is None:
            continue
        thrift_member = getattr(thrift_enum, name.name, None)
        if thrift_member is not None:
            result[thrift_member] = v
    return result


def _resource_job_manager(pb):
    """gRPC ``ResourceJobManager`` -> auto-generated serializer shape."""
    from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource import (  # noqa: E501
        compute_resource_pb2,
    )
    from airavata_sdk.generated.org.apache.airavata.model.parallelism import (
        parallelism_pb2,
    )
    return SimpleNamespace(
        resourceJobManagerId=pb.resource_job_manager_id or None,
        resourceJobManagerType=_thrift_enum_prefixed(
            pb, 'resource_job_manager_type', _ThriftResourceJobManagerType,
            'RESOURCE_JOB_MANAGER_TYPE_'),
        pushMonitoringEndpoint=pb.push_monitoring_endpoint or None,
        jobManagerBinPath=pb.job_manager_bin_path or None,
        jobManagerCommands=_enum_keyed_map(
            pb.job_manager_commands, compute_resource_pb2.JobManagerCommand,
            _ThriftJobManagerCommand),
        parallelismPrefix=_enum_keyed_map(
            pb.parallelism_prefix, parallelism_pb2.ApplicationParallelismType,
            _ThriftParallelismType),
    )


def local_job_submission(pb):
    """gRPC ``LOCALSubmission`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobSubmissionInterfaceId=pb.job_submission_interface_id,
        resourceJobManager=_resource_job_manager(pb.resource_job_manager),
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
    )


def ssh_job_submission(pb):
    """gRPC ``SSHJobSubmission`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobSubmissionInterfaceId=pb.job_submission_interface_id,
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
        resourceJobManager=_resource_job_manager(pb.resource_job_manager),
        alternativeSSHHostName=pb.alternative_ssh_host_name or None,
        sshPort=pb.ssh_port or None,
        monitorMode=_thrift_enum_mapped(pb, 'monitor_mode', _MONITOR_MODE),
        batchQueueEmailSenders=list(pb.batch_queue_email_senders),
    )


def cloud_job_submission(pb):
    """gRPC ``CloudJobSubmission`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobSubmissionInterfaceId=pb.job_submission_interface_id,
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
        nodeId=pb.node_id or None,
        executableType=pb.executable_type or None,
        providerName=_thrift_enum_prefixed(
            pb, 'provider_name', _ThriftProviderName, 'PROVIDER_NAME_'),
        userAccountName=pb.user_account_name or None,
    )


def unicore_job_submission(pb):
    """gRPC ``UnicoreJobSubmission`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        jobSubmissionInterfaceId=pb.job_submission_interface_id,
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
        unicoreEndPointURL=pb.unicore_end_point_url or None,
    )


def local_data_movement(pb):
    """gRPC ``LOCALDataMovement`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        dataMovementInterfaceId=pb.data_movement_interface_id,
    )


def scp_data_movement(pb):
    """gRPC ``SCPDataMovement`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        dataMovementInterfaceId=pb.data_movement_interface_id,
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
        alternativeSCPHostName=pb.alternative_scp_host_name or None,
        sshPort=pb.ssh_port or None,
    )


def grid_ftp_data_movement(pb):
    """gRPC ``GridFTPDataMovement`` -> auto-generated serializer shape."""
    return SimpleNamespace(
        dataMovementInterfaceId=pb.data_movement_interface_id,
        securityProtocol=_thrift_enum_prefixed(
            pb, 'security_protocol', _ThriftSecurityProtocol,
            'SECURITY_PROTOCOL_'),
        gridFTPEndPoints=list(pb.grid_ftp_end_points),
    )


# --- User storage file/directory listings -----------------------------------
# The storage serializers (UserStorageFileSerializer / UserStorageDirectorySerializer)
# read plain dicts keyed the way the legacy user_storage.listdir produced. The gRPC
# FileMetadataResponse carries name/path/size/modified_time(epoch ms)/content_type/
# data_product_uri; map it to that dict shape. ``relative_path`` overrides the path the
# serializer reports (e.g. experiment-dir listings expose a path relative to the data dir).

def _epoch_millis_to_datetime(value):
    """Epoch milliseconds -> aware UTC datetime, or None when unset (0)."""
    if not value:
        return None
    import datetime
    return datetime.datetime.fromtimestamp(value / 1000, tz=datetime.timezone.utc)


def user_storage_file(pb, relative_path=None):
    """gRPC ``FileMetadataResponse`` (a file) -> UserStorageFileSerializer dict."""
    modified = _epoch_millis_to_datetime(pb.modified_time)
    return {
        'name': pb.name,
        'path': relative_path if relative_path is not None else pb.path,
        'data-product-uri': pb.data_product_uri or None,
        # The adaptor exposes only a modified time; reuse it for created time so
        # the serializer's createdTime/modifiedTime both render (SFTP has no ctime).
        'created_time': modified,
        'modified_time': modified,
        'mime_type': pb.content_type or None,
        'size': pb.size,
        'hidden': False,
    }


def user_storage_directory(pb, relative_path=None):
    """gRPC ``FileMetadataResponse`` (a directory) -> UserStorageDirectorySerializer dict."""
    modified = _epoch_millis_to_datetime(pb.modified_time)
    return {
        'name': pb.name,
        'path': relative_path if relative_path is not None else pb.path,
        'created_time': modified,
        'modified_time': modified,
        'size': pb.size,
        'hidden': False,
    }
