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
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.data.replica.ttypes import (
    DataProductType as _ThriftDataProductType,
    ReplicaLocationCategory as _ThriftReplicaLocationCategory,
    ReplicaPersistentType as _ThriftReplicaPersistentType,
)
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
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
