"""Map gRPC ``FileMetadataResponse`` messages to the plain-dict shape the user
storage serializers read.

The user-storage file/directory serializers consume dicts keyed the way the
legacy ``user_storage.listdir`` produced; these helpers convert the gRPC
``FileMetadataResponse`` into that dict shape. (All the Thrift-attribute-shape
read adapters that once lived here are gone — every serializer is proto-native.)
"""


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
