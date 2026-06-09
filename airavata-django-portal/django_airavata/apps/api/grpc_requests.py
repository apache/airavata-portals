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
from airavata.model.appcatalog.groupresourceprofile.ttypes import (
    ResourceType as _ThriftResourceType,
)
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
)

_GEN = "airavata_sdk.generated.org.apache.airavata.model"


def _pb2(path):
    return importlib.import_module(f"{_GEN}.{path}")


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


def _proto_enum_rev(proto_enum, rev_map, value):
    """Thrift enum value -> proto enum value via an EXPLICIT inverse name map
    (for protocol enums whose proto/Thrift member names diverge). None/unmapped
    -> 0 (proto *_UNKNOWN)."""
    if value is None:
        return 0
    name = rev_map.get(value)
    return proto_enum.Value(name) if name is not None else 0


# Thrift protocol value -> proto member name, preserving the divergent name pairs
# (Thrift CLOUD <-> proto JSP_CLOUD; Thrift LOCAL <-> proto
# DATA_MOVEMENT_PROTOCOL_LOCAL). Used by the group-resource-profile write path.
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


def data_product_for_upload(*, gateway_id, owner_name, product_name, file_path,
                            storage_resource_id, content_type=None, product_size=0):
    """Build a proto ``DataProductModel`` to register for a freshly uploaded file.

    The gRPC ``storage.upload_file`` only transfers the bytes and returns a
    minimal ``DataProductModel``; the portal registers the full data product via
    ``research.register_data_product`` so the file gets a canonical product URI.
    Mirrors the legacy ``user_storage._create_data_product`` shape: a single
    GATEWAY_DATA_STORE / TRANSIENT replica pointing at ``file_path``, with the
    content type recorded under ``mime-type`` metadata.
    """
    rc = _pb2("data.replica.replica_catalog_pb2")
    product_metadata = {"mime-type": content_type} if content_type else {}
    return rc.DataProductModel(
        gateway_id=gateway_id,
        owner_name=owner_name,
        product_name=product_name,
        data_product_type=rc.DataProductType.FILE,
        product_size=product_size or 0,
        product_metadata=product_metadata,
        replica_locations=[rc.DataReplicaLocationModel(
            replica_name="{} gateway data store copy".format(product_name),
            replica_location_category=rc.ReplicaLocationCategory.GATEWAY_DATA_STORE,
            replica_persistent_type=rc.ReplicaPersistentType.TRANSIENT,
            storage_resource_id=storage_resource_id or '',
            file_path=file_path,
        )],
    )
