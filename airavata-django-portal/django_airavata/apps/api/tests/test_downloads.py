"""Unit tests for the directory-zip download paths rewired off the SDK storage
facade onto the raw UserStorageService stub (ListDir / DownloadFile) and the raw
ExperimentService stub (GetExperiment for the archive name)."""

import io
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from airavata.services import file_service_pb2
from django.test import RequestFactory, SimpleTestCase

from django_airavata.apps.api import downloads


class _FakeStorageStub:
    """Records ListDir / DownloadFile and returns canned listings/bytes."""

    def __init__(self):
        self.calls = []
        # one file at root, one subdir holding one file
        self._listings = {
            "/base": file_service_pb2.ListDirResponse(
                files=[
                    file_service_pb2.FileMetadataResponse(
                        name="a.txt", path="/base/a.txt", size=3
                    )
                ],
                directories=[file_service_pb2.FileMetadataResponse(name="sub")],
            ),
            "/base/sub": file_service_pb2.ListDirResponse(
                files=[
                    file_service_pb2.FileMetadataResponse(
                        name="b.txt", path="/base/sub/b.txt", size=3
                    )
                ],
                directories=[],
            ),
        }
        self._content = {"/base/a.txt": b"AAA", "/base/sub/b.txt": b"BBB"}

    def ListDir(self, req):
        self.calls.append(("ListDir", req.storage_resource_id, req.path))
        return self._listings[req.path]

    def DownloadFile(self, req):
        self.calls.append(("DownloadFile", req.storage_resource_id, req.path))
        return file_service_pb2.DownloadFileResponse(content=self._content[req.path])


class ZipEntriesTests(SimpleTestCase):
    def test_recurses_directories_yielding_relative_archive_names(self):
        stub = _FakeStorageStub()
        entries = list(downloads._zip_entries(stub, "/base"))
        # archive names are relative to the requested dir; recursion descends
        self.assertEqual(
            sorted(name for name, _path, _size in entries),
            ["a.txt", "sub/b.txt"],
        )
        # ListDir is issued with an empty storage_resource_id over the resolved path
        list_calls = [c for c in stub.calls if c[0] == "ListDir"]
        self.assertEqual(list_calls[0], ("ListDir", "", "/base"))
        self.assertIn(("ListDir", "", "/base/sub"), list_calls)


class ZipResponseTests(SimpleTestCase):
    def test_builds_zip_from_downloadfile_content(self):
        stub = _FakeStorageStub()
        entries = list(downloads._zip_entries(stub, "/base"))
        response = downloads._zip_response(stub, "out.zip", entries)
        self.assertEqual(
            response["Content-Disposition"], "attachment; filename=out.zip"
        )
        buf = io.BytesIO(b"".join(response.streaming_content))
        with zipfile.ZipFile(buf) as zf:
            self.assertEqual(zf.read("a.txt"), b"AAA")
            self.assertEqual(zf.read("sub/b.txt"), b"BBB")
        # bytes came from the raw DownloadFile RPC (empty storage_resource_id)
        dl = [c for c in stub.calls if c[0] == "DownloadFile"]
        self.assertEqual(
            sorted(path for _rpc, _srid, path in dl),
            ["/base/a.txt", "/base/sub/b.txt"],
        )


class DownloadDirViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_download_dir_threads_raw_user_storage_stub(self):
        stub = _FakeStorageStub()
        request = self.factory.get("/sdk/download-dir/?path=/base")
        request.user = MagicMock(username="alice")
        request.airavata_channel = object()
        with (
            patch.object(downloads, "_user_storage_stub", return_value=stub),
            patch.object(downloads, "_user_storage_path", return_value="/base"),
        ):
            response = downloads.download_dir(request)
        buf = io.BytesIO(b"".join(response.streaming_content))
        with zipfile.ZipFile(buf) as zf:
            self.assertEqual(set(zf.namelist()), {"a.txt", "sub/b.txt"})

    def test_download_experiment_dir_names_archive_from_get_experiment(self):
        stub = _FakeStorageStub()
        exp_stub = SimpleNamespace(
            GetExperiment=lambda req: SimpleNamespace(experiment_name="My Exp")
        )
        request = self.factory.get("/sdk/download-experiment-dir/?path=/base")
        request.user = MagicMock(username="alice")
        request.airavata_channel = object()
        with (
            patch.object(downloads, "_user_storage_stub", return_value=stub),
            patch.object(downloads, "_user_storage_path", return_value="/base"),
            patch(
                "airavata.services.experiment_service_pb2_grpc.ExperimentServiceStub",
                return_value=exp_stub,
            ),
        ):
            response = downloads.download_experiment_dir(request, experiment_id="EXP_1")
        # experiment_name flows into the zip filename (get_valid_filename strips space)
        self.assertIn("My_Exp", response["Content-Disposition"])
