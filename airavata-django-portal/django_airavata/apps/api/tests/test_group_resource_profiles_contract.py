"""Proto-direct contract snapshot for the group-resource-profile family.

Replaces the abandoned ``test_group_resource_profile_parity.py`` (which validated
the legacy camelCase + Thrift-int DRF contract).  The proto-direct contract is:

* the SDK ``get_group_resource_profile`` returns a
  ``WithAccess[GroupResourceProfile]`` — the raw
  ``group_resource_profile_pb2.GroupResourceProfile`` proto unioned with the
  caller's access flags (``is_owner`` always ``False`` — the profile has no
  owner; ``user_has_write_access`` is the composite ``userHasWriteAccess``
  boolean the ViewSet resolves and passes in: WRITE on the profile AND READ on
  every credential token);
* the portal's generic ``to_jsonable`` renderer flattens that to **snake_case**
  JSON: ``MessageToDict(preserving_proto_field_name=True,
  always_print_fields_with_no_presence=True)`` merged with the two scalars.

This test builds a representative ``GroupResourceProfile`` proto (a SLURM compute
preference with nested provisioner configs + reservations, an AWS compute
preference, an unset-oneof compute preference, plus the two policy lists), runs it
through ``get_group_resource_profile`` + the renderer, and asserts the resulting
JSON shape: snake_case keys only, the three enums as member NAMES (``"SSH"`` /
``"SFTP"`` / ``"SLURM"`` — NOT the legacy Thrift integers), the
``specific_preferences`` SLURM/AWS oneof rendered natively (an unset oneof leaves
the field ABSENT — no legacy ``{"slurm": ..., "aws": None}`` mirroring, no
flattened ``allocation_project_number``), int64 timestamps as epoch-millis
STRINGS, the proto field name ``override_by_airavata`` (NOT the legacy
``overrideby_airavata``), no camelCase, and no ``url`` hyperlink.

The chained-sharing call the project family makes does NOT apply here — the
composite write flag is resolved by the ViewSet and passed straight into the SDK
function (no sharing lookup to stub).
"""

from django.test import SimpleTestCase

from airavata_sdk.generated.org.apache.airavata.model.appcatalog.groupresourceprofile import (  # noqa: E501
    group_resource_profile_pb2 as grp,
)
from airavata_sdk.helpers._envelope import WithAccess
from airavata_sdk.helpers.compute_resources import get_group_resource_profile
from django_airavata.apps.api.proto_render import to_jsonable


# ---------------------------------------------------------------------------
# Stub client — returns a fixed proto from the raw compute facade
# ---------------------------------------------------------------------------

class _FakeCompute:
    def __init__(self, profile):
        self._profile = profile
        self.calls = []

    def get_group_resource_profile(self, group_resource_profile_id):
        self.calls.append(group_resource_profile_id)
        return self._profile


class _FakeClient:
    def __init__(self, profile, username="alice"):
        self.compute = _FakeCompute(profile)
        self.gateway_id = "default"
        self.username = username


def _make_slurm_pref():
    slurm = grp.SlurmComputeResourcePreference(
        allocation_project_number="alloc-1",
        preferred_batch_queue="normal",
        ssh_account_provisioner="prov",
        group_ssh_account_provisioner_configs=[
            grp.GroupAccountSSHProvisionerConfig(
                resource_id="r1", config_name="cn", config_value="cv")],
        reservations=[
            grp.ComputeResourceReservation(
                reservation_id="rid", queue_names=["q1"],
                start_time=1705320000000, end_time=0)],
    )
    return grp.GroupComputeResourcePreference(
        compute_resource_id="cr-slurm",
        group_resource_profile_id="grp-1",
        override_by_airavata=True,
        login_user_name="alice",
        scratch_location="/scratch",
        # proto SSH / SFTP — rendered as member NAMES, not Thrift ints.
        preferred_job_submission_protocol=2,   # SSH
        preferred_data_movement_protocol=3,    # SFTP
        resource_type=grp.ResourceType.SLURM,
        specific_preferences=grp.EnvironmentSpecificPreferences(slurm=slurm),
    )


def _make_aws_pref():
    return grp.GroupComputeResourcePreference(
        compute_resource_id="cr-aws",
        resource_type=grp.ResourceType.AWS,
        specific_preferences=grp.EnvironmentSpecificPreferences(
            aws=grp.AwsComputeResourcePreference(
                region="us-east-1", preferred_ami_id="ami-1",
                preferred_instance_type="t2.micro")),
    )


def _make_unset_oneof_pref():
    # No specific_preferences -> the oneof stays ABSENT in the JSON.
    return grp.GroupComputeResourcePreference(compute_resource_id="cr-none")


def _make_profile():
    return grp.GroupResourceProfile(
        gateway_id="default",
        group_resource_profile_id="grp-1",
        group_resource_profile_name="Test GRP",
        compute_preferences=[
            _make_slurm_pref(), _make_aws_pref(), _make_unset_oneof_pref()],
        compute_resource_policies=[
            grp.ComputeResourcePolicy(
                resource_policy_id="rp-1", compute_resource_id="cr-slurm",
                allowed_batch_queues=["normal", "long"])],
        batch_queue_resource_policies=[
            grp.BatchQueueResourcePolicy(
                resource_policy_id="bq-1", compute_resource_id="cr-slurm",
                queuename="normal", max_allowed_nodes=10,
                max_allowed_cores=100, max_allowed_walltime=60)],
        creation_time=1705320000000,
        updated_time=1705323600000,
        default_credential_store_token="def-tok",
    )


# The exact snake_case JSON the proto-direct group-resource-profile read endpoint
# emits.  (dict ``==`` is order-independent; MessageToDict orders set fields
# first then defaults, which is irrelevant to equality.)
_EXPECTED_SLURM_PREF = {
    "compute_resource_id": "cr-slurm",
    "group_resource_profile_id": "grp-1",
    # the proto field name — NOT the legacy ``overrideby_airavata``.
    "override_by_airavata": True,
    "login_user_name": "alice",
    "scratch_location": "/scratch",
    # enums as member NAMES (proto-direct), NOT Thrift integers.
    "preferred_job_submission_protocol": "SSH",
    "preferred_data_movement_protocol": "SFTP",
    "resource_type": "SLURM",
    "resource_specific_credential_store_token": "",
    # the oneof renders natively as {"slurm": {...}} — no legacy aws=None mirror,
    # no flattened allocation_project_number at the compute-pref top level.
    "specific_preferences": {
        "slurm": {
            "allocation_project_number": "alloc-1",
            "preferred_batch_queue": "normal",
            "quality_of_service": "",
            "usage_reporting_gateway_id": "",
            "ssh_account_provisioner": "prov",
            "group_ssh_account_provisioner_configs": [
                {
                    "resource_id": "r1",
                    "group_resource_profile_id": "",
                    "config_name": "cn",
                    "config_value": "cv",
                }
            ],
            "ssh_account_provisioner_additional_info": "",
            "reservations": [
                {
                    "reservation_id": "rid",
                    "reservation_name": "",
                    "queue_names": ["q1"],
                    # int64 epoch-millis as STRINGS (0 stays "0", not None).
                    "start_time": "1705320000000",
                    "end_time": "0",
                }
            ],
        }
    },
}

_EXPECTED_AWS_PREF = {
    "compute_resource_id": "cr-aws",
    "group_resource_profile_id": "",
    "override_by_airavata": False,
    "login_user_name": "",
    "scratch_location": "",
    "preferred_job_submission_protocol": "JOB_SUBMISSION_PROTOCOL_UNKNOWN",
    "preferred_data_movement_protocol": "DATA_MOVEMENT_PROTOCOL_UNKNOWN",
    "resource_type": "AWS",
    "resource_specific_credential_store_token": "",
    "specific_preferences": {
        "aws": {
            "region": "us-east-1",
            "preferred_ami_id": "ami-1",
            "preferred_instance_type": "t2.micro",
        }
    },
}

_EXPECTED_UNSET_PREF = {
    "compute_resource_id": "cr-none",
    "group_resource_profile_id": "",
    "override_by_airavata": False,
    "login_user_name": "",
    "scratch_location": "",
    "preferred_job_submission_protocol": "JOB_SUBMISSION_PROTOCOL_UNKNOWN",
    "preferred_data_movement_protocol": "DATA_MOVEMENT_PROTOCOL_UNKNOWN",
    "resource_type": "RESOURCE_TYPE_UNKNOWN",
    "resource_specific_credential_store_token": "",
    # specific_preferences is ABSENT — the unset oneof is not emitted.
}

_EXPECTED_SNAPSHOT = {
    "gateway_id": "default",
    "group_resource_profile_id": "grp-1",
    "group_resource_profile_name": "Test GRP",
    "compute_preferences": [
        _EXPECTED_SLURM_PREF, _EXPECTED_AWS_PREF, _EXPECTED_UNSET_PREF],
    "compute_resource_policies": [
        {
            "resource_policy_id": "rp-1",
            "compute_resource_id": "cr-slurm",
            "group_resource_profile_id": "",
            "allowed_batch_queues": ["normal", "long"],
        }
    ],
    "batch_queue_resource_policies": [
        {
            "resource_policy_id": "bq-1",
            "compute_resource_id": "cr-slurm",
            "group_resource_profile_id": "",
            "queuename": "normal",
            "max_allowed_nodes": 10,
            "max_allowed_cores": 100,
            "max_allowed_walltime": 60,
        }
    ],
    # int64 epoch-millis rendered as STRINGS.
    "creation_time": "1705320000000",
    "updated_time": "1705323600000",
    # empty-string -> None coercion is dropped; the proto value passes through.
    "default_credential_store_token": "def-tok",
    # access flags merged on top of the proto by to_jsonable.
    "is_owner": False,
    "user_has_write_access": True,
}


class GroupResourceProfileContractSnapshotTest(SimpleTestCase):

    def _render(self, has_write=True):
        client = _FakeClient(_make_profile())
        result = get_group_resource_profile(
            client, "grp-1", has_write=has_write)
        return to_jsonable(result)

    # ------------------------------------------------------------------
    # SDK return shape
    # ------------------------------------------------------------------

    def test_sdk_returns_withaccess_carrying_the_proto(self):
        profile = _make_profile()
        client = _FakeClient(profile)
        result = get_group_resource_profile(client, "grp-1", has_write=True)
        self.assertIsInstance(result, WithAccess)
        # the proto flows through wholesale — no field copied out.
        self.assertIs(result.message, profile)
        self.assertFalse(result.is_owner)
        self.assertTrue(result.user_has_write_access)
        self.assertEqual(client.compute.calls, ["grp-1"])

    # ------------------------------------------------------------------
    # Full snapshot
    # ------------------------------------------------------------------

    def test_full_snapshot_matches(self):
        self.assertEqual(self._render(), _EXPECTED_SNAPSHOT)

    def test_exact_top_level_key_set(self):
        self.assertEqual(
            set(self._render().keys()), set(_EXPECTED_SNAPSHOT.keys()))

    def test_exact_slurm_pref_key_set(self):
        cp = self._render()["compute_preferences"][0]
        self.assertEqual(set(cp.keys()), set(_EXPECTED_SLURM_PREF.keys()))

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
                    self.assertNotIn(
                        "ID", key,
                        f"key {key!r} carries a camelCase 'ID' fragment")
                    _check(value)
            elif isinstance(obj, list):
                for item in obj:
                    _check(item)

        _check(self._render())

    def test_no_camelcase_keys(self):
        rendered = self._render()
        cp = rendered["compute_preferences"][0]
        for legacy in (
            "gatewayId", "gatewayID", "groupResourceProfileId",
            "groupResourceProfileName", "computePreferences",
            "computeResourcePolicies", "batchQueueResourcePolicies",
            "creationTime", "updatedTime", "defaultCredentialStoreToken",
            "userHasWriteAccess", "isOwner", "url",
        ):
            self.assertNotIn(legacy, rendered)
        for legacy in (
            "computeResourceId", "overridebyAiravata", "overrideByAiravata",
            "loginUserName", "scratchLocation",
            "preferredJobSubmissionProtocol", "preferredDataMovementProtocol",
            "resourceType", "specificPreferences",
            "resourceSpecificCredentialStoreToken",
        ):
            self.assertNotIn(legacy, cp)

    # ------------------------------------------------------------------
    # Enum NAMES (the three proto enums)
    # ------------------------------------------------------------------

    def test_protocol_and_resource_type_enums_render_as_member_names(self):
        cp = self._render()["compute_preferences"][0]
        self.assertEqual(cp["preferred_job_submission_protocol"], "SSH")
        self.assertEqual(cp["preferred_data_movement_protocol"], "SFTP")
        self.assertEqual(cp["resource_type"], "SLURM")
        # not the legacy Thrift integers.
        self.assertNotIn(cp["preferred_job_submission_protocol"], (1, "1"))
        self.assertNotIn(cp["resource_type"], (0, "0"))

    def test_unknown_enums_render_as_sentinel_names(self):
        cp = self._render()["compute_preferences"][2]
        self.assertEqual(
            cp["preferred_job_submission_protocol"],
            "JOB_SUBMISSION_PROTOCOL_UNKNOWN")
        self.assertEqual(
            cp["preferred_data_movement_protocol"],
            "DATA_MOVEMENT_PROTOCOL_UNKNOWN")
        self.assertEqual(cp["resource_type"], "RESOURCE_TYPE_UNKNOWN")

    # ------------------------------------------------------------------
    # specific_preferences oneof
    # ------------------------------------------------------------------

    def test_slurm_oneof_renders_natively(self):
        cp = self._render()["compute_preferences"][0]
        sp = cp["specific_preferences"]
        # only the active branch is present — no legacy {"slurm", "aws"} mirror.
        self.assertEqual(set(sp.keys()), {"slurm"})
        self.assertEqual(
            sp["slurm"]["allocation_project_number"], "alloc-1")
        # the SLURM allocation_project_number is NOT flattened to the top level.
        self.assertNotIn("allocation_project_number", cp)

    def test_aws_oneof_renders_natively(self):
        cp = self._render()["compute_preferences"][1]
        sp = cp["specific_preferences"]
        # only the active branch — the bare-AWS unwrap is dropped.
        self.assertEqual(set(sp.keys()), {"aws"})
        self.assertEqual(sp["aws"]["region"], "us-east-1")

    def test_unset_oneof_is_absent(self):
        cp = self._render()["compute_preferences"][2]
        self.assertNotIn("specific_preferences", cp)

    def test_slurm_provisioner_acronym_key_is_proto_snake_case(self):
        slurm = self._render()["compute_preferences"][0][
            "specific_preferences"]["slurm"]
        # proto-direct emits the plain snake_case proto field name, NOT the
        # legacy upper-acronym ``groupSSHAccountProvisionerConfigs``.
        self.assertIn("group_ssh_account_provisioner_configs", slurm)
        self.assertNotIn("groupSSHAccountProvisionerConfigs", slurm)

    # ------------------------------------------------------------------
    # Specific field-handling guarantees
    # ------------------------------------------------------------------

    def test_override_uses_proto_field_name(self):
        cp = self._render()["compute_preferences"][0]
        self.assertIn("override_by_airavata", cp)
        self.assertNotIn("overrideby_airavata", cp)
        self.assertIs(cp["override_by_airavata"], True)

    def test_timestamps_are_epoch_millis_strings(self):
        rendered = self._render()
        self.assertEqual(rendered["creation_time"], "1705320000000")
        self.assertEqual(rendered["updated_time"], "1705323600000")
        # reservation 0-end_time stays "0" (always_print + int64->string).
        res = rendered["compute_preferences"][0][
            "specific_preferences"]["slurm"]["reservations"][0]
        self.assertEqual(res["start_time"], "1705320000000")
        self.assertEqual(res["end_time"], "0")

    def test_default_token_passes_through_not_nulled(self):
        # the legacy empty-string -> None coercion is dropped.
        self.assertEqual(
            self._render()["default_credential_store_token"], "def-tok")

    def test_batch_queue_zero_int_preserved(self):
        profile = grp.GroupResourceProfile(
            group_resource_profile_id="grp-1",
            batch_queue_resource_policies=[
                grp.BatchQueueResourcePolicy(
                    resource_policy_id="bq-0", max_allowed_nodes=0)])
        client = _FakeClient(profile)
        rendered = to_jsonable(
            get_group_resource_profile(client, "grp-1", has_write=False))
        bqp = rendered["batch_queue_resource_policies"][0]
        self.assertEqual(bqp["max_allowed_nodes"], 0)

    # ------------------------------------------------------------------
    # Access flags
    # ------------------------------------------------------------------

    def test_is_owner_always_false(self):
        self.assertFalse(self._render()["is_owner"])

    def test_user_has_write_access_reflects_passed_flag(self):
        self.assertTrue(self._render(has_write=True)["user_has_write_access"])
        self.assertFalse(self._render(has_write=False)["user_has_write_access"])

    # ------------------------------------------------------------------
    # Stable shape on an empty profile
    # ------------------------------------------------------------------

    def test_empty_profile_has_stable_shape(self):
        profile = grp.GroupResourceProfile(group_resource_profile_id="grp-empty")
        client = _FakeClient(profile)
        rendered = to_jsonable(
            get_group_resource_profile(client, "grp-empty", has_write=False))
        self.assertEqual(rendered["compute_preferences"], [])
        self.assertEqual(rendered["compute_resource_policies"], [])
        self.assertEqual(rendered["batch_queue_resource_policies"], [])
        self.assertEqual(rendered["gateway_id"], "")
        self.assertEqual(rendered["creation_time"], "0")
        self.assertEqual(rendered["default_credential_store_token"], "")
        self.assertFalse(rendered["is_owner"])
        self.assertFalse(rendered["user_has_write_access"])
