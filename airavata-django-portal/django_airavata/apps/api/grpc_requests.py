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

from airavata.model.appcatalog.computeresource.ttypes import (
    JobSubmissionProtocol as _ThriftJobSubmissionProtocol,
)
from airavata.model.appcatalog.parallelism.ttypes import (
    ApplicationParallelismType as _ThriftParallelismType,
)
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    ResourceType as _ThriftResourceType,
)
from airavata.model.appcatalog.parser.ttypes import IOType as _ThriftIOType
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
)
from airavata.model.experiment.ttypes import (
    ExperimentType as _ThriftExperimentType,
)
from airavata.model.workspace.ttypes import (
    NotificationPriority as _ThriftNotificationPriority,
)

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
    # proto3 prefixes only members that would otherwise collide in the file —
    # in practice just the zero *_UNKNOWN sentinel — so real members usually
    # stay bare. Re-apply the prefix only when it yields a valid proto member
    # (the mirror of the read-side _thrift_enum_prefixed, which strips it only
    # when present).
    if prefix and (prefix + name) in proto_enum.keys():
        name = prefix + name
    return proto_enum.Value(name)


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


def notification(t):
    """Thrift ``Notification`` -> proto ``Notification`` request message."""
    return _workspace_pb2().Notification(
        notification_id=t.notificationId or '',
        gateway_id=t.gatewayId or '',
        title=t.title or '',
        notification_message=t.notificationMessage or '',
        creation_time=t.creationTime or 0,
        published_time=t.publishedTime or 0,
        expiration_time=t.expirationTime or 0,
        priority=_proto_enum(
            _workspace_pb2().NotificationPriority, _ThriftNotificationPriority,
            t.priority, 'NOTIFICATION_PRIORITY_'),
    )


def _parser_input(t):
    """Thrift ``ParserInput`` -> proto ``ParserInput``."""
    pp = _pb2("appcatalog.parser.parser_pb2")
    return pp.ParserInput(
        id=t.id or '',
        name=t.name or '',
        required_input=bool(t.requiredInput),
        parser_id=t.parserId or '',
        type=_proto_enum(pp.IOType, _ThriftIOType, t.type, 'IO_TYPE_'),
    )


def _parser_output(t):
    """Thrift ``ParserOutput`` -> proto ``ParserOutput``."""
    pp = _pb2("appcatalog.parser.parser_pb2")
    return pp.ParserOutput(
        id=t.id or '',
        name=t.name or '',
        required_output=bool(t.requiredOutput),
        parser_id=t.parserId or '',
        type=_proto_enum(pp.IOType, _ThriftIOType, t.type, 'IO_TYPE_'),
    )


def parser(t):
    """Thrift ``Parser`` -> proto ``Parser`` request message."""
    return _pb2("appcatalog.parser.parser_pb2").Parser(
        id=t.id or '',
        image_name=t.imageName or '',
        output_dir_path=t.outputDirPath or '',
        input_dir_path=t.inputDirPath or '',
        execution_command=t.executionCommand or '',
        input_files=[_parser_input(i) for i in (t.inputFiles or [])],
        output_files=[_parser_output(o) for o in (t.outputFiles or [])],
        gateway_id=t.gatewayId or '',
    )


# proto-name -> Thrift protocol value maps (mirror grpc_adapters); inverted
# below to go Thrift value -> proto value, preserving the divergent name pairs
# (Thrift CLOUD <-> proto JSP_CLOUD; Thrift LOCAL <-> proto
# DATA_MOVEMENT_PROTOCOL_LOCAL).
_JOB_SUBMISSION_PROTOCOL_REV = {
    _ThriftJobSubmissionProtocol.LOCAL: 'LOCAL',
    _ThriftJobSubmissionProtocol.SSH: 'SSH',
    _ThriftJobSubmissionProtocol.GLOBUS: 'GLOBUS',
    _ThriftJobSubmissionProtocol.UNICORE: 'UNICORE',
    _ThriftJobSubmissionProtocol.CLOUD: 'JSP_CLOUD',
    _ThriftJobSubmissionProtocol.SSH_FORK: 'SSH_FORK',
    _ThriftJobSubmissionProtocol.LOCAL_FORK: 'LOCAL_FORK',
}
_DATA_MOVEMENT_PROTOCOL_REV = {
    _ThriftDataMovementProtocol.LOCAL: 'DATA_MOVEMENT_PROTOCOL_LOCAL',
    _ThriftDataMovementProtocol.SCP: 'SCP',
    _ThriftDataMovementProtocol.SFTP: 'SFTP',
    _ThriftDataMovementProtocol.UNICORE_STORAGE_SERVICE: 'UNICORE_STORAGE_SERVICE',
}


def _proto_enum_rev(proto_enum, rev_map, value):
    """Thrift enum value -> proto enum value via an EXPLICIT inverse name map
    (for protocol enums whose proto/Thrift member names diverge). None/unmapped
    -> 0 (proto *_UNKNOWN)."""
    if value is None:
        return 0
    name = rev_map.get(value)
    return proto_enum.Value(name) if name is not None else 0


def _compute_resource_preference(t):
    """Thrift ``ComputeResourcePreference`` -> proto message."""
    gp = _pb2("appcatalog.gatewayprofile.gateway_profile_pb2")
    cr = _pb2("appcatalog.computeresource.compute_resource_pb2")
    dm = _pb2("data.movement.data_movement_pb2")
    return gp.ComputeResourcePreference(
        compute_resource_id=t.computeResourceId or '',
        override_by_airavata=bool(t.overridebyAiravata),
        login_user_name=t.loginUserName or '',
        preferred_job_submission_protocol=_proto_enum_rev(
            cr.JobSubmissionProtocol, _JOB_SUBMISSION_PROTOCOL_REV,
            t.preferredJobSubmissionProtocol),
        preferred_data_movement_protocol=_proto_enum_rev(
            dm.DataMovementProtocol, _DATA_MOVEMENT_PROTOCOL_REV,
            t.preferredDataMovementProtocol),
        preferred_batch_queue=t.preferredBatchQueue or '',
        scratch_location=t.scratchLocation or '',
        allocation_project_number=t.allocationProjectNumber or '',
        resource_specific_credential_store_token=t.resourceSpecificCredentialStoreToken or '',
        usage_reporting_gateway_id=t.usageReportingGatewayId or '',
        quality_of_service=t.qualityOfService or '',
        reservation=t.reservation or '',
        reservation_start_time=t.reservationStartTime or 0,
        reservation_end_time=t.reservationEndTime or 0,
        ssh_account_provisioner=t.sshAccountProvisioner or '',
        ssh_account_provisioner_config=dict(t.sshAccountProvisionerConfig or {}),
        ssh_account_provisioner_additional_info=t.sshAccountProvisionerAdditionalInfo or '',
    )


def storage_preference(t):
    """Thrift ``StoragePreference`` -> proto ``StoragePreference``."""
    return _pb2("appcatalog.gatewayprofile.gateway_profile_pb2").StoragePreference(
        storage_resource_id=t.storageResourceId or '',
        login_user_name=t.loginUserName or '',
        file_system_root_location=t.fileSystemRootLocation or '',
        resource_specific_credential_store_token=t.resourceSpecificCredentialStoreToken or '',
    )


def gateway_resource_profile(t):
    """Thrift ``GatewayResourceProfile`` -> proto message."""
    return _pb2("appcatalog.gatewayprofile.gateway_profile_pb2").GatewayResourceProfile(
        gateway_id=t.gatewayID or '',
        credential_store_token=t.credentialStoreToken or '',
        compute_resource_preferences=[
            _compute_resource_preference(p)
            for p in (t.computeResourcePreferences or [])],
        storage_preferences=[
            storage_preference(p) for p in (t.storagePreferences or [])],
        identity_server_tenant=t.identityServerTenant or '',
        identity_server_pwd_cred_token=t.identityServerPwdCredToken or '',
    )


# --- Experiment tree (write direction) -------------------------------------
# Reverse of grpc_adapters.experiment. The write path carries only what the
# user submitted; status/errors/processes/workflow are server-managed.


def _computational_resource_scheduling(t):
    """Thrift ``ComputationalResourceSchedulingModel`` -> proto message."""
    return _pb2("scheduling.scheduling_pb2").ComputationalResourceSchedulingModel(
        resource_host_id=t.resourceHostId or '',
        total_cpu_count=t.totalCPUCount or 0,
        node_count=t.nodeCount or 0,
        number_of_threads=t.numberOfThreads or 0,
        queue_name=t.queueName or '',
        wall_time_limit=t.wallTimeLimit or 0,
        total_physical_memory=t.totalPhysicalMemory or 0,
        chessis_number=t.chessisNumber or '',
        static_working_dir=t.staticWorkingDir or '',
        override_login_user_name=t.overrideLoginUserName or '',
        override_scratch_location=t.overrideScratchLocation or '',
        override_allocation_project_number=t.overrideAllocationProjectNumber or '',
        m_group_count=t.mGroupCount or 0,
    )


def _user_configuration_data(t):
    """Thrift ``UserConfigurationDataModel`` -> proto message."""
    ucd = _pb2("experiment.experiment_pb2").UserConfigurationDataModel(
        airavata_auto_schedule=bool(t.airavataAutoSchedule),
        override_manual_scheduled_params=bool(t.overrideManualScheduledParams),
        share_experiment_publicly=bool(t.shareExperimentPublicly),
        throttle_resources=bool(t.throttleResources),
        user_dn=t.userDN or '',
        generate_cert=bool(t.generateCert),
        input_storage_resource_id=t.inputStorageResourceId or '',
        output_storage_resource_id=t.outputStorageResourceId or '',
        experiment_data_dir=t.experimentDataDir or '',
        use_user_cr_pref=bool(t.useUserCRPref),
        group_resource_profile_id=t.groupResourceProfileId or '',
        auto_scheduled_comp_resource_scheduling_list=[
            _computational_resource_scheduling(s)
            for s in (t.autoScheduledCompResourceSchedulingList or [])],
    )
    if t.computationalResourceScheduling is not None:
        ucd.computational_resource_scheduling.CopyFrom(
            _computational_resource_scheduling(t.computationalResourceScheduling))
    return ucd


def experiment(t):
    """Thrift ``ExperimentModel`` -> proto ``ExperimentModel`` request message.

    Only the user-submitted fields are populated; experiment_status, errors and
    processes are server-managed (left empty), workflow omitted.
    """
    exp_pb = _pb2("experiment.experiment_pb2")
    e = exp_pb.ExperimentModel(
        experiment_id=t.experimentId or '',
        project_id=t.projectId or '',
        gateway_id=t.gatewayId or '',
        experiment_type=_proto_enum(
            exp_pb.ExperimentType, _ThriftExperimentType, t.experimentType,
            'EXPERIMENT_TYPE_'),
        user_name=t.userName or '',
        experiment_name=t.experimentName or '',
        description=t.description or '',
        execution_id=t.executionId or '',
        enable_email_notification=bool(t.enableEmailNotification),
        email_addresses=list(t.emailAddresses or []),
        experiment_inputs=[
            _input_data_object(i) for i in (t.experimentInputs or [])],
        experiment_outputs=[
            _output_data_object(o) for o in (t.experimentOutputs or [])],
    )
    if t.userConfigurationData is not None:
        e.user_configuration_data.CopyFrom(
            _user_configuration_data(t.userConfigurationData))
    return e


# --- Group resource profile (write direction) ------------------------------
# Reverse of grpc_adapters.group_resource_profile. Reuses the _proto_enum_rev
# protocol maps defined above.


def _grp_pb2():
    return _pb2("appcatalog.groupresourceprofile.group_resource_profile_pb2")


def _reverse_compute_resource_reservation(t):
    return _grp_pb2().ComputeResourceReservation(
        reservation_id=t.reservationId or '',
        reservation_name=t.reservationName or '',
        queue_names=list(t.queueNames or []),
        start_time=t.startTime or 0,
        end_time=t.endTime or 0,
    )


def _reverse_group_account_ssh_provisioner_config(t):
    return _grp_pb2().GroupAccountSSHProvisionerConfig(
        resource_id=t.resourceId or '',
        group_resource_profile_id=t.groupResourceProfileId or '',
        config_name=t.configName or '',
        config_value=t.configValue or '',
    )


def _reverse_slurm_compute_resource_preference(t):
    return _grp_pb2().SlurmComputeResourcePreference(
        allocation_project_number=t.allocationProjectNumber or '',
        preferred_batch_queue=t.preferredBatchQueue or '',
        quality_of_service=t.qualityOfService or '',
        usage_reporting_gateway_id=t.usageReportingGatewayId or '',
        ssh_account_provisioner=t.sshAccountProvisioner or '',
        group_ssh_account_provisioner_configs=[
            _reverse_group_account_ssh_provisioner_config(c)
            for c in (t.groupSSHAccountProvisionerConfigs or [])],
        ssh_account_provisioner_additional_info=(
            t.sshAccountProvisionerAdditionalInfo or ''),
        reservations=[
            _reverse_compute_resource_reservation(r)
            for r in (t.reservations or [])],
    )


def _reverse_aws_compute_resource_preference(t):
    return _grp_pb2().AwsComputeResourcePreference(
        region=t.region or '',
        preferred_ami_id=t.preferredAmiId or '',
        preferred_instance_type=t.preferredInstanceType or '',
    )


def _reverse_group_compute_resource_preference(t):
    grp = _grp_pb2()
    cr = _pb2("appcatalog.computeresource.compute_resource_pb2")
    dm = _pb2("data.movement.data_movement_pb2")
    msg = grp.GroupComputeResourcePreference(
        compute_resource_id=t.computeResourceId or '',
        group_resource_profile_id=t.groupResourceProfileId or '',
        override_by_airavata=bool(t.overridebyAiravata),
        login_user_name=t.loginUserName or '',
        scratch_location=t.scratchLocation or '',
        preferred_job_submission_protocol=_proto_enum_rev(
            cr.JobSubmissionProtocol, _JOB_SUBMISSION_PROTOCOL_REV,
            t.preferredJobSubmissionProtocol),
        preferred_data_movement_protocol=_proto_enum_rev(
            dm.DataMovementProtocol, _DATA_MOVEMENT_PROTOCOL_REV,
            t.preferredDataMovementProtocol),
        resource_specific_credential_store_token=(
            t.resourceSpecificCredentialStoreToken or ''),
        resource_type=_proto_enum(
            grp.ResourceType, _ThriftResourceType, t.resourceType),
    )
    sp = getattr(t, 'specificPreferences', None)
    if sp is not None:
        if t.resourceType == _ThriftResourceType.AWS and getattr(sp, 'aws', None):
            msg.specific_preferences.CopyFrom(grp.EnvironmentSpecificPreferences(
                aws=_reverse_aws_compute_resource_preference(sp.aws)))
        elif getattr(sp, 'slurm', None):
            msg.specific_preferences.CopyFrom(grp.EnvironmentSpecificPreferences(
                slurm=_reverse_slurm_compute_resource_preference(sp.slurm)))
    return msg


def _reverse_compute_resource_policy(t):
    return _grp_pb2().ComputeResourcePolicy(
        resource_policy_id=t.resourcePolicyId or '',
        compute_resource_id=t.computeResourceId or '',
        group_resource_profile_id=t.groupResourceProfileId or '',
        allowed_batch_queues=list(t.allowedBatchQueues or []),
    )


def _reverse_batch_queue_resource_policy(t):
    return _grp_pb2().BatchQueueResourcePolicy(
        resource_policy_id=t.resourcePolicyId or '',
        compute_resource_id=t.computeResourceId or '',
        group_resource_profile_id=t.groupResourceProfileId or '',
        queuename=t.queuename or '',
        max_allowed_nodes=t.maxAllowedNodes or 0,
        max_allowed_cores=t.maxAllowedCores or 0,
        max_allowed_walltime=t.maxAllowedWalltime or 0,
    )


def group_resource_profile(t):
    """Thrift ``GroupResourceProfile`` -> proto message."""
    return _grp_pb2().GroupResourceProfile(
        gateway_id=t.gatewayId or '',
        group_resource_profile_id=t.groupResourceProfileId or '',
        group_resource_profile_name=t.groupResourceProfileName or '',
        compute_preferences=[
            _reverse_group_compute_resource_preference(p)
            for p in (t.computePreferences or [])],
        compute_resource_policies=[
            _reverse_compute_resource_policy(p)
            for p in (t.computeResourcePolicies or [])],
        batch_queue_resource_policies=[
            _reverse_batch_queue_resource_policy(p)
            for p in (t.batchQueueResourcePolicies or [])],
        creation_time=t.creationTime or 0,
        updated_time=t.updatedTime or 0,
        default_credential_store_token=t.defaultCredentialStoreToken or '',
    )


def group(t):
    """Thrift ``GroupModel`` -> proto ``GroupModel`` request message."""
    return _pb2("group.group_manager_pb2").GroupModel(
        id=t.id or '',
        name=t.name or '',
        owner_id=t.ownerId or '',
        description=t.description or '',
        members=list(t.members or []),
        admins=list(t.admins or []),
    )
