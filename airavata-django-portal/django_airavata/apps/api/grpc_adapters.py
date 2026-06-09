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
from airavata.model.data.replica.ttypes import (
    DataProductType as _ThriftDataProductType,
    ReplicaLocationCategory as _ThriftReplicaLocationCategory,
    ReplicaPersistentType as _ThriftReplicaPersistentType,
)
from airavata.model.data.movement.ttypes import (
    DataMovementProtocol as _ThriftDataMovementProtocol,
)
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
