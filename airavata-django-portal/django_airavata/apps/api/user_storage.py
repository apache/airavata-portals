"""Thin compatibility layer over the SDK facade's StorageClient.

Replaces the deleted ``airavata_django_portal_sdk.user_storage`` module.
Every function here accepts ``request`` as its first argument (to mirror the
old API) and delegates to ``request.airavata_client.storage``.
"""

import io
import logging
import os
from typing import Any, BinaryIO

from django.conf import settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers to extract file paths from DataProductModel proto objects
# ---------------------------------------------------------------------------

def _get_replica_filepath(data_product: Any) -> str | None:
    """Return the file_path from the first GATEWAY_DATA_STORE replica location."""
    for replica in data_product.replica_locations:
        if replica.file_path:
            return replica.file_path
    return None


def _get_replica_storage_resource_id(data_product: Any) -> str | None:
    """Return the storage_resource_id from the first replica location."""
    for replica in data_product.replica_locations:
        if replica.storage_resource_id:
            return replica.storage_resource_id
    return None


# ---------------------------------------------------------------------------
# File existence / metadata
# ---------------------------------------------------------------------------

def exists(request: Any, data_product: Any) -> bool:
    """Check whether the file backing *data_product* exists in user storage."""
    path = _get_replica_filepath(data_product)
    if not path:
        return False
    try:
        return request.airavata_client.storage.file_exists(path)
    except Exception:
        return False


def dir_exists(request: Any, path: str, experiment_id: str | None = None) -> bool:
    """Check whether *path* exists as a directory in user storage."""
    if experiment_id:
        return experiment_dir_exists(request, experiment_id, path)
    return request.airavata_client.storage.dir_exists(path)


def experiment_dir_exists(request: Any, experiment_id: str, path: str = "") -> bool:
    """Check whether the experiment output directory exists."""
    try:
        request.airavata_client.storage.list_experiment_dir(experiment_id, path)
        return True
    except Exception:
        return False


def is_input_file(request: Any, data_product: Any) -> bool:
    """Return True if the data product's path is under the inputs directory."""
    path = _get_replica_filepath(data_product)
    if not path:
        return False
    # Input files are stored under a path that contains "/inputs/" or starts with "inputs/"
    normalized = path.replace("\\", "/")
    return "/inputs/" in normalized or normalized.startswith("inputs/")


# ---------------------------------------------------------------------------
# File / directory listing
# ---------------------------------------------------------------------------

def listdir(request: Any, path: str, experiment_id: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """List the contents of *path*, returning (directories, files) dicts."""
    if experiment_id:
        return list_experiment_dir(request, experiment_id, path)
    resp = request.airavata_client.storage.list_dir(path)
    directories = _metadata_list_to_dicts(resp.directories)
    files = _metadata_list_to_dicts(resp.files)
    return directories, files


def list_experiment_dir(request: Any, experiment_id: str, path: str = "") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """List the experiment output directory."""
    resp = request.airavata_client.storage.list_experiment_dir(experiment_id, path)
    directories = _metadata_list_to_dicts(resp.directories)
    files = _metadata_list_to_dicts(resp.files)
    return directories, files


def _metadata_list_to_dicts(items: Any) -> list[dict[str, Any]]:
    """Convert repeated FileMetadataResponse protos to plain dicts."""
    result: list[dict[str, Any]] = []
    for item in items:
        result.append({
            "name": item.name,
            "path": item.path,
            "size": item.size,
            "created_time": item.created_time,
            "modified_time": item.modified_time,
            "data-product-uri": item.data_product_uri,
            "mime_type": item.content_type,
            "hidden": False,
        })
    return result


# ---------------------------------------------------------------------------
# File open / download
# ---------------------------------------------------------------------------

def open_file(request: Any, data_product: Any) -> io.BytesIO:
    """Download the file for *data_product* and return a file-like object."""
    path = _get_replica_filepath(data_product)
    assert path is not None, "data_product has no replica file path"
    resp = request.airavata_client.storage.download_file(path)
    f = io.BytesIO(resp.content)
    f.name = resp.name or os.path.basename(path)
    return f


# ---------------------------------------------------------------------------
# File upload / save
# ---------------------------------------------------------------------------

def save_input_file(request: Any, input_file: BinaryIO, name: str | None = None, content_type: str = "") -> Any:
    """Upload *input_file* to the user's input files directory.

    Returns a DataProductModel proto.
    """
    file_name = name or getattr(input_file, "name", "uploaded_file")
    content = input_file.read()
    resp = request.airavata_client.storage.upload_file(
        path="inputs",
        content=content,
        name=file_name,
        content_type=content_type or "",
    )
    # The upload returns a FileUploadResponse with a data product URI.
    # Fetch and return the full DataProductModel.
    return request.airavata_client.research.get_data_product(resp.uri)


def save(request: Any, path: str, file_obj: BinaryIO, name: str | None = None, content_type: str = "", experiment_id: str | None = None) -> Any:
    """Upload *file_obj* to *path* in user storage.

    Returns a DataProductModel proto.
    """
    file_name = name or getattr(file_obj, "name", "uploaded_file")
    content = file_obj.read()
    resp = request.airavata_client.storage.upload_file(
        path=path,
        content=content,
        name=file_name,
        content_type=content_type or "",
    )
    return request.airavata_client.research.get_data_product(resp.uri)


# ---------------------------------------------------------------------------
# File content update
# ---------------------------------------------------------------------------

def update_data_product_content(request: Any, data_product: Any, fileContentText: str) -> None:
    """Replace the content of the file backing *data_product* with *fileContentText*."""
    path = _get_replica_filepath(data_product)
    assert path is not None, "data_product has no replica file path"
    name = os.path.basename(path)
    request.airavata_client.storage.upload_file(
        path=os.path.dirname(path),
        content=fileContentText.encode("utf-8"),
        name=name,
    )


def update_file_content(request: Any, path: str, fileContentText: str) -> None:
    """Replace the content of the file at *path* with *fileContentText*."""
    name = os.path.basename(path)
    request.airavata_client.storage.upload_file(
        path=os.path.dirname(path),
        content=fileContentText.encode("utf-8"),
        name=name,
    )


# ---------------------------------------------------------------------------
# File / directory creation and deletion
# ---------------------------------------------------------------------------

def create_user_dir(request: Any, path: str, experiment_id: str | None = None) -> tuple[None, str]:
    """Create a directory at *path*. Returns (storage_resource_id, created_path)."""
    resp = request.airavata_client.storage.create_dir(path)
    return None, resp.created_path


def create_symlink(request: Any, source_path: str, dest_path: str) -> None:
    """Create a symlink from *source_path* to *dest_path*."""
    request.airavata_client.storage.create_symlink(source_path, dest_path)


def delete(request: Any, data_product: Any) -> None:
    """Delete the file backing *data_product*."""
    path = _get_replica_filepath(data_product)
    if path:
        request.airavata_client.storage.delete_file(path)


def delete_user_file(request: Any, path: str, experiment_id: str | None = None) -> None:
    """Delete a user file at *path*."""
    request.airavata_client.storage.delete_file(path)


def delete_dir(request: Any, path: str, experiment_id: str | None = None) -> None:
    """Delete a directory at *path*."""
    request.airavata_client.storage.delete_dir(path)


# ---------------------------------------------------------------------------
# File metadata
# ---------------------------------------------------------------------------

def get_file_metadata(request: Any, path: str, experiment_id: str | None = None) -> dict[str, Any]:
    """Get metadata for the file at *path*. Returns a dict."""
    resp = request.airavata_client.storage.get_file_metadata(path)
    return {
        "name": resp.name,
        "path": resp.path,
        "size": resp.size,
        "created_time": resp.created_time,
        "modified_time": resp.modified_time,
        "data-product-uri": resp.data_product_uri,
        "mime_type": resp.content_type,
        "hidden": False,
    }


def get_data_product_metadata(request: Any, data_product: Any = None, data_product_uri: str | None = None) -> dict[str, Any]:
    """Get metadata for a data product. Returns a dict with path, size, etc."""
    if data_product is None and data_product_uri:
        data_product = request.airavata_client.research.get_data_product(data_product_uri)
    path = _get_replica_filepath(data_product)
    if not path:
        return {"path": "", "size": 0, "userHasWriteAccess": False}
    try:
        resp = request.airavata_client.storage.get_file_metadata(path)
        return {
            "name": resp.name,
            "path": resp.path,
            "size": resp.size,
            "created_time": resp.created_time,
            "modified_time": resp.modified_time,
            "data-product-uri": resp.data_product_uri,
            "mime_type": resp.content_type,
            "userHasWriteAccess": True,
        }
    except Exception:
        return {"path": path, "size": 0, "userHasWriteAccess": False}


# ---------------------------------------------------------------------------
# Download URL helpers
# ---------------------------------------------------------------------------

def get_download_url(request: Any, data_product_uri: str | None = None) -> str:
    """Return a URL to download the file for *data_product_uri*."""
    from django.urls import reverse
    from urllib.parse import quote
    return reverse("django_airavata_api:download_file") + f"?data-product-uri={quote(data_product_uri or '')}"


def get_lazy_download_url(request: Any, data_product: Any = None, data_product_uri: str | None = None) -> str | None:
    """Return a download URL. Accepts either a data_product or data_product_uri."""
    if data_product_uri:
        return get_download_url(request, data_product_uri=data_product_uri)
    if data_product:
        return get_download_url(request, data_product_uri=data_product.product_uri)
    return None
