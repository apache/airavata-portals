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
