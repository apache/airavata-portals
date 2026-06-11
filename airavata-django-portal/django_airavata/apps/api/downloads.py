"""Streaming ZIP downloads of user-storage and experiment-output directories.

Ports the two ``/sdk/download-*`` directory-zip endpoints the file browser links
to (UserStoragePathViewer / ExperimentStoragePathViewer / ExperimentStorageView
Container) off the retired ``airavata_django_portal_sdk`` and onto the gRPC
storage facade (``request.airavata.storage``). Individual-file downloads go
through the ``download``/``download-file`` views instead.
"""
import io
import logging
import os
import zipfile

from django.http import StreamingHttpResponse
from django.utils.text import get_valid_filename

from django_airavata.apps.api.web import api_view

from .views import _user_storage_path

log = logging.getLogger(__name__)


@api_view()
def download_dir(request):
    """Stream a user-storage directory (``?path=``) as a zip archive."""
    path = request.GET.get('path', "")
    base = get_valid_filename(os.path.basename(path))
    filename = (base + ".zip") if base else 'home.zip'
    resolved = _user_storage_path(path, request=request)
    entries = _zip_entries(request.airavata.storage, resolved)
    return _zip_response(request.airavata.storage, filename, entries)


@api_view()
def download_experiment_dir(request, experiment_id=None):
    """Stream an experiment's output directory (``?path=``) as a zip archive."""
    path = request.GET.get('path', "")
    experiment = request.airavata.research.get_experiment(experiment_id)
    exp_name = get_valid_filename(experiment.experiment_name)
    base = get_valid_filename(os.path.basename(path))
    filename = f'{exp_name}_{base}.zip' if base else f'{exp_name}.zip'
    resolved = _user_storage_path(path, experiment_id=experiment_id, request=request)
    entries = _zip_entries(request.airavata.storage, resolved)
    return _zip_response(request.airavata.storage, filename, entries)


def _zip_entries(storage, base_resolved, rel_dir=""):
    """Recurse the directory, yielding ``(archive_name, absolute_path, size)`` per file.

    ``rel_dir`` accumulates the path relative to ``base_resolved`` so archive names
    are relative to the requested directory (mirrors the legacy
    ``user_storage.listdir`` recursion).
    """
    listing = storage.list_dir(_join(base_resolved, rel_dir))
    for f in listing.files:
        yield os.path.join(rel_dir, f.name), f.path, f.size
    for d in listing.directories:
        yield from _zip_entries(storage, base_resolved, os.path.join(rel_dir, d.name))


def _join(base, rel):
    return base if not rel else base.rstrip("/") + "/" + rel


def _zip_response(storage, filename, entries):
    # Files are already fully read into memory (storage.download_file().content),
    # so build the whole archive in a BytesIO with stdlib zipfile and stream the
    # buffer back. NOTE: this buffers the entire zip in memory — fine for dev, but
    # for large directories in production this should be replaced with a true
    # streaming zip (the previous zipstream-new behavior).
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for archive_name, abs_path, size in entries:
            zf.writestr(archive_name, storage.download_file(abs_path).content)
    buf.seek(0)
    response = StreamingHttpResponse(
        _iter_buffer(buf), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


def _iter_buffer(buf):
    """Yield the in-memory archive in buffer-sized chunks."""
    while True:
        chunk = buf.read(io.DEFAULT_BUFFER_SIZE)
        if not chunk:
            break
        yield chunk
