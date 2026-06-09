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
from airavata.model.appcatalog.parser.ttypes import IOType as _ThriftIOType
from airavata.model.application.io.ttypes import DataType as _ThriftDataType
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
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
