"""Proto-direct contract snapshot for the data-product family.

The data-product read endpoint (``DataProductView.get``) returns the SDK
``get_data_product`` result — a ``WithAccess[DataProductModel]``: the raw
``replica_catalog_pb2.DataProductModel`` proto unioned with the caller's access
flags (``is_owner`` = the product is owned by the caller; ``user_has_write_access``
= the boolean the view resolves via ``_data_product_has_write`` and passes in).
The global ``ProtoJSONRenderer`` (``to_jsonable``) flattens that to snake_case JSON.

This test builds a representative ``DataProductModel`` (a FILE product with a
nested GATEWAY_DATA_STORE / TRANSIENT replica and ``mime-type`` metadata), runs it
through ``get_data_product`` + the renderer, and asserts the resulting JSON shape:
snake_case keys only, ``data_product_type`` / replica enums as member NAMES
(``"FILE"`` / ``"GATEWAY_DATA_STORE"`` / ``"TRANSIENT"`` — not Thrift integers),
``product_metadata`` rendered as a native JSON object, int64 timestamp fields as
decimal STRINGS (``product_size`` is int32 -> a JSON number), no camelCase keys,
and the two access scalars merged on top.
"""

from django.test import SimpleTestCase

from airavata_sdk.generated.org.apache.airavata.model.data.replica import (
    replica_catalog_pb2 as rc,
)
from airavata_sdk.helpers._envelope import WithAccess
from airavata_sdk.helpers.research_resources import get_data_product
from django_airavata.apps.api.proto_render import to_jsonable

_PRODUCT_URI = "airavata-dp://gateway/alice/file.txt"


# ---------------------------------------------------------------------------
# Stub client — returns a fixed proto from the raw research facade
# ---------------------------------------------------------------------------

class _FakeResearch:
    def __init__(self, product):
        self._product = product
        self.calls = []

    def get_data_product(self, product_uri):
        self.calls.append(product_uri)
        return self._product


class _FakeClient:
    def __init__(self, product, username="alice"):
        self.research = _FakeResearch(product)
        self.gateway_id = "default"
        self.username = username


def _make_replica():
    return rc.DataReplicaLocationModel(
        replica_id="rep-1",
        product_uri=_PRODUCT_URI,
        replica_name="gateway data store copy",
        replica_location_category=rc.ReplicaLocationCategory.GATEWAY_DATA_STORE,
        replica_persistent_type=rc.ReplicaPersistentType.TRANSIENT,
        storage_resource_id="storage-1",
        file_path="/data/alice/file.txt",
        creation_time=1705320000000,
        last_modified_time=1705323600000,
    )


def _make_product():
    return rc.DataProductModel(
        product_uri=_PRODUCT_URI,
        gateway_id="default",
        product_name="file.txt",
        owner_name="alice",
        data_product_type=rc.DataProductType.FILE,
        product_size=2048,
        creation_time=1705320000000,
        last_modified_time=1705323600000,
        product_metadata={"mime-type": "text/plain"},
        replica_locations=[_make_replica()],
    )


# The exact snake_case JSON the proto-direct data-product read endpoint emits.
_EXPECTED_REPLICA = {
    "replica_id": "rep-1",
    "product_uri": _PRODUCT_URI,
    "replica_name": "gateway data store copy",
    "replica_description": "",
    # int64 epoch-millis as STRINGS (0 stays "0").
    "creation_time": "1705320000000",
    "last_modified_time": "1705323600000",
    "valid_until_time": "0",
    # enums as member NAMES, not Thrift integers.
    "replica_location_category": "GATEWAY_DATA_STORE",
    "replica_persistent_type": "TRANSIENT",
    "storage_resource_id": "storage-1",
    "file_path": "/data/alice/file.txt",
    # map<string,string> always rendered (empty -> {}).
    "replica_metadata": {},
}

_EXPECTED_SNAPSHOT = {
    "product_uri": _PRODUCT_URI,
    "gateway_id": "default",
    "parent_product_uri": "",
    "product_name": "file.txt",
    "product_description": "",
    "owner_name": "alice",
    "data_product_type": "FILE",
    # product_size is int32 -> rendered as a JSON number.
    "product_size": 2048,
    # int64 timestamps as STRINGS.
    "creation_time": "1705320000000",
    "last_modified_time": "1705323600000",
    # map<string,string> rendered as a native JSON object.
    "product_metadata": {"mime-type": "text/plain"},
    "replica_locations": [_EXPECTED_REPLICA],
    # access flags merged on top of the proto by to_jsonable.
    "is_owner": True,
    "user_has_write_access": True,
}


class DataProductContractSnapshotTest(SimpleTestCase):

    def _render(self, has_write=True, username="alice"):
        client = _FakeClient(_make_product(), username=username)
        result = get_data_product(client, _PRODUCT_URI, has_write=has_write)
        return to_jsonable(result)

    # ------------------------------------------------------------------
    # SDK return shape
    # ------------------------------------------------------------------

    def test_sdk_returns_withaccess_carrying_the_proto(self):
        product = _make_product()
        client = _FakeClient(product)
        result = get_data_product(client, _PRODUCT_URI, has_write=True)
        self.assertIsInstance(result, WithAccess)
        # the proto flows through wholesale — no field copied out.
        self.assertIs(result.message, product)
        self.assertTrue(result.is_owner)
        self.assertTrue(result.user_has_write_access)
        self.assertEqual(client.research.calls, [_PRODUCT_URI])

    # ------------------------------------------------------------------
    # Full snapshot
    # ------------------------------------------------------------------

    def test_full_snapshot_matches(self):
        self.assertEqual(self._render(), _EXPECTED_SNAPSHOT)

    def test_exact_top_level_key_set(self):
        self.assertEqual(
            set(self._render().keys()), set(_EXPECTED_SNAPSHOT.keys()))

    def test_exact_replica_key_set(self):
        replica = self._render()["replica_locations"][0]
        self.assertEqual(set(replica.keys()), set(_EXPECTED_REPLICA.keys()))

    # ------------------------------------------------------------------
    # snake_case-only assertions (no camelCase keys anywhere)
    # ------------------------------------------------------------------

    def test_keys_are_snake_case(self):
        def _check(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    self.assertEqual(
                        key, key.lower(),
                        f"key {key!r} is not lowercase/snake_case")
                    _check(value)
            elif isinstance(obj, list):
                for item in obj:
                    _check(item)

        _check(self._render())

    def test_no_camelcase_keys(self):
        rendered = self._render()
        for legacy in (
            "productUri", "productURI", "gatewayId", "gatewayID",
            "parentProductUri", "productName", "productDescription",
            "ownerName", "dataProductType", "productSize", "creationTime",
            "lastModifiedTime", "productMetadata", "replicaLocations",
            "userHasWriteAccess", "isOwner", "url",
        ):
            self.assertNotIn(legacy, rendered)
        replica = rendered["replica_locations"][0]
        for legacy in (
            "replicaId", "productUri", "replicaName", "replicaDescription",
            "creationTime", "lastModifiedTime", "validUntilTime",
            "replicaLocationCategory", "replicaPersistentType",
            "storageResourceId", "filePath",
        ):
            self.assertNotIn(legacy, replica)

    # ------------------------------------------------------------------
    # Enum NAMES
    # ------------------------------------------------------------------

    def test_data_product_type_renders_as_member_name(self):
        self.assertEqual(self._render()["data_product_type"], "FILE")

    def test_replica_enums_render_as_member_names(self):
        replica = self._render()["replica_locations"][0]
        self.assertEqual(
            replica["replica_location_category"], "GATEWAY_DATA_STORE")
        self.assertEqual(replica["replica_persistent_type"], "TRANSIENT")

    def test_unknown_type_renders_as_sentinel_name(self):
        product = rc.DataProductModel(product_uri=_PRODUCT_URI)
        client = _FakeClient(product)
        rendered = to_jsonable(
            get_data_product(client, _PRODUCT_URI, has_write=False))
        self.assertEqual(
            rendered["data_product_type"], "DATA_PRODUCT_TYPE_UNKNOWN")

    # ------------------------------------------------------------------
    # int64 / metadata field handling
    # ------------------------------------------------------------------

    def test_int64_timestamps_are_strings_size_is_int(self):
        rendered = self._render()
        # product_size is int32 -> a JSON number; the int64 timestamps are STRINGS.
        self.assertEqual(rendered["product_size"], 2048)
        self.assertEqual(rendered["creation_time"], "1705320000000")
        self.assertEqual(rendered["last_modified_time"], "1705323600000")
        replica = rendered["replica_locations"][0]
        self.assertEqual(replica["creation_time"], "1705320000000")
        self.assertEqual(replica["valid_until_time"], "0")

    def test_product_metadata_is_native_object(self):
        self.assertEqual(
            self._render()["product_metadata"], {"mime-type": "text/plain"})

    # ------------------------------------------------------------------
    # Access flags
    # ------------------------------------------------------------------

    def test_is_owner_reflects_owner_name_match(self):
        self.assertTrue(self._render(username="alice")["is_owner"])
        self.assertFalse(self._render(username="bob")["is_owner"])

    def test_user_has_write_access_reflects_passed_flag(self):
        self.assertTrue(self._render(has_write=True)["user_has_write_access"])
        self.assertFalse(self._render(has_write=False)["user_has_write_access"])

    # ------------------------------------------------------------------
    # Stable shape on a bare product
    # ------------------------------------------------------------------

    def test_empty_product_has_stable_shape(self):
        product = rc.DataProductModel(product_uri="airavata-dp://empty")
        client = _FakeClient(product)
        rendered = to_jsonable(
            get_data_product(client, "airavata-dp://empty", has_write=False))
        self.assertEqual(rendered["replica_locations"], [])
        self.assertEqual(rendered["gateway_id"], "")
        self.assertEqual(rendered["product_size"], 0)
        self.assertEqual(rendered["creation_time"], "0")
        # no owner_name -> not owned.
        self.assertFalse(rendered["is_owner"])
        self.assertFalse(rendered["user_has_write_access"])
