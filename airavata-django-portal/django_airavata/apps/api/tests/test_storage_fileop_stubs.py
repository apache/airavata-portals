"""Unit tests for the storage file-op paths rewired off the SDK helpers onto
raw generated gRPC stubs.

These exercise the portal-side proto assembly / path-resolution / orchestration
that surrounds the byte transport — the parts that carry portal logic. The stub
seam is faked: a request carries an ``airavata_channel`` and the
``UserStorageServiceStub`` / ``DataProductServiceStub`` / ``ExperimentServiceStub``
constructors are patched to return recording fakes, so no live channel is needed.
"""

from types import SimpleNamespace
from unittest import mock

from airavata.model.data.replica import (
    replica_catalog_pb2 as rc,
)
from django.test import SimpleTestCase

from django_airavata.apps.api import output_views, views


def _request(username="alice"):
    return SimpleNamespace(
        airavata_channel=object(),
        user=SimpleNamespace(username=username),
    )


class _FakeStorageStub:
    """Records every user-storage RPC and returns canned responses."""

    def __init__(self, channel=None):
        self.calls = []
        self.metadata_path = "/storage/tmp/file.txt"
        self.metadata_size = 1234
        self.default_storage_resource_id = "storage-1"
        self.dir_exists = False
        self.file_exists = True
        self.list_dir_resp = SimpleNamespace(directories=[], files=[])
        self.download_resp = SimpleNamespace(
            name="file.txt", content=b"hello", content_type="text/plain"
        )

    def UploadFile(self, req):
        self.calls.append(("UploadFile", req))
        return SimpleNamespace()

    def DownloadFile(self, req):
        self.calls.append(("DownloadFile", req))
        return self.download_resp

    def DeleteFile(self, req):
        self.calls.append(("DeleteFile", req))
        return SimpleNamespace()

    def DeleteDir(self, req):
        self.calls.append(("DeleteDir", req))
        return SimpleNamespace()

    def CreateDir(self, req):
        self.calls.append(("CreateDir", req))
        return SimpleNamespace()

    def DirExists(self, req):
        self.calls.append(("DirExists", req))
        return SimpleNamespace(exists=self.dir_exists)

    def FileExists(self, req):
        self.calls.append(("FileExists", req))
        return SimpleNamespace(exists=self.file_exists)

    def ListDir(self, req):
        self.calls.append(("ListDir", req))
        return self.list_dir_resp

    def GetFileMetadata(self, req):
        self.calls.append(("GetFileMetadata", req))
        return SimpleNamespace(path=self.metadata_path, size=self.metadata_size)

    def GetDefaultStorageResourceId(self, req):
        self.calls.append(("GetDefaultStorageResourceId", req))
        return SimpleNamespace(storage_resource_id=self.default_storage_resource_id)


class _FakeDataProductStub:
    def __init__(self, channel=None, product=None):
        self.calls = []
        self.product = product or rc.DataProductModel(
            product_uri="airavata-dp://gateway/alice/file.txt",
            product_name="file.txt",
            owner_name="alice",
            replica_locations=[
                rc.DataReplicaLocationModel(file_path="/storage/tmp/file.txt")
            ],
        )
        self.registered_uri = "airavata-dp://gateway/alice/file.txt"

    def GetDataProduct(self, req):
        self.calls.append(("GetDataProduct", req))
        return self.product

    def RegisterDataProduct(self, req):
        self.calls.append(("RegisterDataProduct", req))
        return SimpleNamespace(product_uri=self.registered_uri)


class _FakeUpload:
    def __init__(self, content=b"abc", name="up.txt"):
        self._content = content
        self.name = name

    def read(self):
        return self._content


def _patch_storage(fake):
    return mock.patch(
        "airavata.services.file_service_pb2_grpc.UserStorageServiceStub",
        return_value=fake,
    )


def _patch_data_product(fake):
    return mock.patch(
        "airavata.services.data_product_service_pb2_grpc.DataProductServiceStub",
        return_value=fake,
    )


class BuildUploadDataProductTest(SimpleTestCase):
    def test_assembles_file_product_with_gateway_data_store_replica(self):
        with self.settings(GATEWAY_ID="default"):
            dp = views._build_upload_data_product(
                owner_name="alice",
                product_name="file.txt",
                file_path="/storage/tmp/file.txt",
                storage_resource_id="storage-1",
                content_type="text/plain",
                product_size=2048,
            )
        self.assertEqual(dp.gateway_id, "default")
        self.assertEqual(dp.owner_name, "alice")
        self.assertEqual(dp.product_name, "file.txt")
        self.assertEqual(dp.data_product_type, rc.DataProductType.FILE)
        self.assertEqual(dp.product_size, 2048)
        self.assertEqual(dp.product_metadata["mime-type"], "text/plain")
        self.assertEqual(len(dp.replica_locations), 1)
        replica = dp.replica_locations[0]
        self.assertEqual(replica.file_path, "/storage/tmp/file.txt")
        self.assertEqual(replica.storage_resource_id, "storage-1")
        self.assertEqual(
            replica.replica_location_category,
            rc.ReplicaLocationCategory.GATEWAY_DATA_STORE,
        )
        self.assertEqual(
            replica.replica_persistent_type, rc.ReplicaPersistentType.TRANSIENT
        )

    def test_no_content_type_omits_mime_metadata(self):
        with self.settings(GATEWAY_ID="default"):
            dp = views._build_upload_data_product(
                owner_name="alice",
                product_name="x",
                file_path="/p",
                storage_resource_id="s",
            )
        self.assertNotIn("mime-type", dict(dp.product_metadata))


class UserStoragePathResolveTest(SimpleTestCase):
    def test_bare_relative_path_anchored_under_home(self):
        self.assertEqual(views._user_storage_path("foo/bar"), "~/foo/bar")

    def test_leading_slash_stripped_then_home_anchored(self):
        self.assertEqual(views._user_storage_path("/foo/bar"), "~/foo/bar")

    def test_already_home_relative_passes_through(self):
        self.assertEqual(views._user_storage_path("~/foo"), "~/foo")

    def test_experiment_id_resolves_against_data_dir(self):
        experiment = SimpleNamespace(
            user_configuration_data=SimpleNamespace(
                experiment_data_dir="/exp-data-dir"
            ),
        )
        experiment.HasField = lambda f: f == "user_configuration_data"
        fake_exp_stub = SimpleNamespace(
            GetExperiment=lambda req: experiment,
        )
        with mock.patch(
            "airavata.services.experiment_service_pb2_grpc.ExperimentServiceStub",
            return_value=fake_exp_stub,
        ):
            resolved = views._user_storage_path(
                "sub/file.txt", experiment_id="EXP_1", request=_request()
            )
        self.assertEqual(resolved, "~/exp-data-dir/sub/file.txt")


class StorageUploadAndRegisterTest(SimpleTestCase):
    def test_uploads_bytes_then_registers_product(self):
        storage = _FakeStorageStub()
        data_product = _FakeDataProductStub()
        request = _request()
        with (
            self.settings(GATEWAY_ID="default"),
            _patch_storage(storage),
            _patch_data_product(data_product),
        ):
            result = views._storage_upload_and_register(
                request, "tmp", _FakeUpload(content=b"abc", name="up.txt")
            )
        # bytes were uploaded
        upload = next(c for c in storage.calls if c[0] == "UploadFile")
        self.assertEqual(upload[1].content, b"abc")
        self.assertEqual(upload[1].path, "~/tmp/up.txt")
        # product was registered using the resolved metadata path + default storage
        register = next(c for c in data_product.calls if c[0] == "RegisterDataProduct")
        replica = register[1].data_product.replica_locations[0]
        self.assertEqual(replica.file_path, "/storage/tmp/file.txt")
        self.assertEqual(replica.storage_resource_id, "storage-1")
        # returns the freshly fetched product proto
        self.assertIs(result, data_product.product)


class DownloadDataProductFilesTest(SimpleTestCase):
    def test_downloads_each_existing_file_in_order(self):
        storage = _FakeStorageStub()
        data_product = _FakeDataProductStub()
        request = _request()
        with _patch_storage(storage), _patch_data_product(data_product):
            files = output_views._download_data_product_files(
                request, ["airavata-dp://a", "airavata-dp://b"]
            )
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].read(), b"hello")
        self.assertEqual(files[0].name, "file.txt")

    def test_missing_file_contributes_nothing(self):
        storage = _FakeStorageStub()
        storage.file_exists = False
        data_product = _FakeDataProductStub()
        request = _request()
        with _patch_storage(storage), _patch_data_product(data_product):
            files = output_views._download_data_product_files(
                request, ["airavata-dp://a"]
            )
        self.assertEqual(files, [])

    def test_no_replica_contributes_nothing(self):
        storage = _FakeStorageStub()
        no_replica = rc.DataProductModel(product_uri="airavata-dp://x")
        data_product = _FakeDataProductStub(product=no_replica)
        request = _request()
        with _patch_storage(storage), _patch_data_product(data_product):
            files = output_views._download_data_product_files(
                request, ["airavata-dp://x"]
            )
        self.assertEqual(files, [])


class OutputViewsGetExperimentProtoTest(SimpleTestCase):
    def test_returns_bare_experiment_proto(self):
        experiment = SimpleNamespace(experiment_id="EXP_1")
        fake_exp_stub = SimpleNamespace(GetExperiment=lambda req: experiment)
        request = _request()
        with mock.patch(
            "airavata.services.experiment_service_pb2_grpc.ExperimentServiceStub",
            return_value=fake_exp_stub,
        ):
            result = output_views._get_experiment_proto(request, "EXP_1")
        self.assertIs(result, experiment)


class OutputViewsDataProductFilePathTest(SimpleTestCase):
    def test_relative_path_home_anchored(self):
        dp = rc.DataProductModel(
            replica_locations=[rc.DataReplicaLocationModel(file_path="rel/x")]
        )
        self.assertEqual(output_views._data_product_file_path(dp), "~/rel/x")

    def test_absolute_path_passthrough(self):
        dp = rc.DataProductModel(
            replica_locations=[rc.DataReplicaLocationModel(file_path="/abs/x")]
        )
        self.assertEqual(output_views._data_product_file_path(dp), "/abs/x")

    def test_no_replica_returns_none(self):
        self.assertIsNone(output_views._data_product_file_path(rc.DataProductModel()))
