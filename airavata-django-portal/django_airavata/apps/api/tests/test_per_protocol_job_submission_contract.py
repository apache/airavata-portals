"""Proto-direct contract snapshot for the per-protocol-job-submission family.

Replaces the abandoned ``test_job_submission_parity.py`` (which validated the
legacy camelCase DRF contract with Thrift-integer enums).  The proto-direct
contract is:

* the SDK ``get_{local,ssh,unicore,cloud}_job_submission`` helpers return the
  bare facade proto DIRECTLY — no envelope, no dict transform (these resources
  carry no hyperlink, ownership, or sharing fields);
* the portal's generic ``to_jsonable`` renderer flattens each proto to
  **snake_case** JSON via ``MessageToDict(preserving_proto_field_name=True,
  always_print_fields_with_no_presence=True)``.

This test builds a representative proto for each of the four protocols
(populating nested / enum / repeated / enum-keyed-map fields), runs it through
the SDK helper (with a stub facade) + ``to_jsonable``, and asserts the resulting
JSON shape: snake_case keys only, enums as member NAMES (not Thrift integers),
``ssh_port`` as a number, the ``resource_job_manager`` enum-keyed maps keyed
verbatim by the proto int32 key (rendered as a decimal STRING), and NO camelCase
/ NO upper-acronym (``alternativeSSHHostName`` / ``unicoreEndPointURL``) / NO
hyperlinks.
"""

from django.test import SimpleTestCase

from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource import (  # noqa: E501
    compute_resource_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.data.movement import (
    data_movement_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.parallelism import (
    parallelism_pb2,
)
from airavata_sdk.helpers.compute_resources import (
    get_cloud_job_submission,
    get_local_job_submission,
    get_ssh_job_submission,
    get_unicore_job_submission,
)
from django_airavata.apps.api.proto_render import to_jsonable


# ---------------------------------------------------------------------------
# Stub client — records the facade call, returns a fixed proto
# ---------------------------------------------------------------------------

class _FakeCompute:
    def __init__(self, *, local=None, ssh=None, unicore=None, cloud=None):
        self._local = local
        self._ssh = ssh
        self._unicore = unicore
        self._cloud = cloud
        self.calls = []

    def get_local_job_submission(self, sid):
        self.calls.append(("local", sid))
        return self._local

    def get_ssh_job_submission(self, sid):
        self.calls.append(("ssh", sid))
        return self._ssh

    def get_unicore_job_submission(self, sid):
        self.calls.append(("unicore", sid))
        return self._unicore

    def get_cloud_job_submission(self, sid):
        self.calls.append(("cloud", sid))
        return self._cloud


class _FakeClient:
    def __init__(self, **kwargs):
        self.compute = _FakeCompute(**kwargs)


# ---------------------------------------------------------------------------
# Representative protos
# ---------------------------------------------------------------------------

def _sec(name):
    return data_movement_pb2.SecurityProtocol.Value(name)


def _make_resource_job_manager():
    rjm = compute_resource_pb2.ResourceJobManager(
        resource_job_manager_id="rjm-1",
        resource_job_manager_type=compute_resource_pb2.ResourceJobManagerType.SLURM,
        push_monitoring_endpoint="ep",
        job_manager_bin_path="/bin")
    rjm.job_manager_commands[
        compute_resource_pb2.JobManagerCommand.SUBMISSION] = "sbatch"
    rjm.job_manager_commands[
        compute_resource_pb2.JobManagerCommand.JOB_MONITORING] = "squeue"
    rjm.parallelism_prefix[
        parallelism_pb2.ApplicationParallelismType.MPI] = "mpirun"
    return rjm


def _make_local():
    return compute_resource_pb2.LOCALSubmission(
        job_submission_interface_id="ls-1",
        resource_job_manager=_make_resource_job_manager(),
        security_protocol=_sec("LOCAL"))


def _make_ssh():
    return compute_resource_pb2.SSHJobSubmission(
        job_submission_interface_id="ssh-1",
        security_protocol=_sec("SSH_KEYS"),
        resource_job_manager=_make_resource_job_manager(),
        alternative_ssh_host_name="alt.host",
        ssh_port=22,
        monitor_mode=compute_resource_pb2.MonitorMode.MONITOR_FORK,
        batch_queue_email_senders=["a@x.com", "b@x.com"])


def _make_cloud():
    return compute_resource_pb2.CloudJobSubmission(
        job_submission_interface_id="cl-1",
        security_protocol=_sec("OAUTH"),
        node_id="n1",
        executable_type="exe",
        provider_name=compute_resource_pb2.ProviderName.AWSEC2,
        user_account_name="acct")


def _make_unicore():
    return compute_resource_pb2.UnicoreJobSubmission(
        job_submission_interface_id="u-1",
        security_protocol=_sec("GSI"),
        unicore_end_point_url="https://u")


# ---------------------------------------------------------------------------
# The exact snake_case JSON each proto-direct read endpoint emits.
# ---------------------------------------------------------------------------

# ``ResourceJobManager`` is rendered identically wherever it is nested: enum as
# member NAME, the two enum-keyed maps keyed VERBATIM by the proto int32 enum
# value (rendered as a decimal STRING; SUBMISSION=1 -> "1", JOB_MONITORING=2 ->
# "2", MPI=2 -> "2").
_EXPECTED_RJM = {
    "resource_job_manager_id": "rjm-1",
    "resource_job_manager_type": "SLURM",
    "push_monitoring_endpoint": "ep",
    "job_manager_bin_path": "/bin",
    "job_manager_commands": {"1": "sbatch", "2": "squeue"},
    "parallelism_prefix": {"2": "mpirun"},
}

_EXPECTED_LOCAL = {
    "job_submission_interface_id": "ls-1",
    "security_protocol": "LOCAL",
    "resource_job_manager": _EXPECTED_RJM,
}

_EXPECTED_SSH = {
    "job_submission_interface_id": "ssh-1",
    "security_protocol": "SSH_KEYS",
    "resource_job_manager": _EXPECTED_RJM,
    "alternative_ssh_host_name": "alt.host",
    "ssh_port": 22,
    "monitor_mode": "MONITOR_FORK",
    "batch_queue_email_senders": ["a@x.com", "b@x.com"],
}

_EXPECTED_CLOUD = {
    "job_submission_interface_id": "cl-1",
    "security_protocol": "OAUTH",
    "node_id": "n1",
    "executable_type": "exe",
    "provider_name": "AWSEC2",
    "user_account_name": "acct",
}

_EXPECTED_UNICORE = {
    "job_submission_interface_id": "u-1",
    "security_protocol": "GSI",
    "unicore_end_point_url": "https://u",
}


class JobSubmissionContractSnapshotTest(SimpleTestCase):

    # ------------------------------------------------------------------
    # Full snapshots — SDK helper returns the proto, to_jsonable flattens it
    # ------------------------------------------------------------------

    def test_local_snapshot_matches(self):
        client = _FakeClient(local=_make_local())
        rendered = to_jsonable(get_local_job_submission(client, "ls-1"))
        self.assertEqual(rendered, _EXPECTED_LOCAL)
        self.assertEqual(client.compute.calls, [("local", "ls-1")])

    def test_ssh_snapshot_matches(self):
        client = _FakeClient(ssh=_make_ssh())
        rendered = to_jsonable(get_ssh_job_submission(client, "ssh-1"))
        self.assertEqual(rendered, _EXPECTED_SSH)
        self.assertEqual(client.compute.calls, [("ssh", "ssh-1")])

    def test_cloud_snapshot_matches(self):
        client = _FakeClient(cloud=_make_cloud())
        rendered = to_jsonable(get_cloud_job_submission(client, "cl-1"))
        self.assertEqual(rendered, _EXPECTED_CLOUD)
        self.assertEqual(client.compute.calls, [("cloud", "cl-1")])

    def test_unicore_snapshot_matches(self):
        client = _FakeClient(unicore=_make_unicore())
        rendered = to_jsonable(get_unicore_job_submission(client, "u-1"))
        self.assertEqual(rendered, _EXPECTED_UNICORE)
        self.assertEqual(client.compute.calls, [("unicore", "u-1")])

    # ------------------------------------------------------------------
    # Enums render as member NAMES, not the legacy Thrift integers
    # ------------------------------------------------------------------

    def test_enums_are_member_names_not_thrift_ints(self):
        ssh = to_jsonable(get_ssh_job_submission(
            _FakeClient(ssh=_make_ssh()), "ssh-1"))
        self.assertEqual(ssh["security_protocol"], "SSH_KEYS")
        self.assertEqual(ssh["monitor_mode"], "MONITOR_FORK")
        self.assertEqual(
            ssh["resource_job_manager"]["resource_job_manager_type"], "SLURM")
        cloud = to_jsonable(get_cloud_job_submission(
            _FakeClient(cloud=_make_cloud()), "cl-1"))
        self.assertEqual(cloud["provider_name"], "AWSEC2")
        # Not the historical Thrift integers (1 / 4 / 2 / 1).
        for v in (ssh["security_protocol"], ssh["monitor_mode"],
                  cloud["provider_name"]):
            self.assertIsInstance(v, str)

    # ------------------------------------------------------------------
    # Enum-keyed maps serialize VERBATIM (int32 key as decimal STRING)
    # ------------------------------------------------------------------

    def test_resource_job_manager_maps_keyed_verbatim(self):
        ssh = to_jsonable(get_ssh_job_submission(
            _FakeClient(ssh=_make_ssh()), "ssh-1"))
        rjm = ssh["resource_job_manager"]
        # NOT the legacy composite "JobManagerCommand.SUBMISSION" keys — the
        # proto int32 enum value verbatim ("1" SUBMISSION, "2" JOB_MONITORING).
        self.assertEqual(
            rjm["job_manager_commands"], {"1": "sbatch", "2": "squeue"})
        self.assertEqual(rjm["parallelism_prefix"], {"2": "mpirun"})

    # ------------------------------------------------------------------
    # ssh_port is a number; nested message presence
    # ------------------------------------------------------------------

    def test_ssh_port_is_a_number(self):
        ssh = to_jsonable(get_ssh_job_submission(
            _FakeClient(ssh=_make_ssh()), "ssh-1"))
        self.assertIsInstance(ssh["ssh_port"], int)
        self.assertEqual(ssh["ssh_port"], 22)

    def test_unset_resource_job_manager_is_absent(self):
        """An unset message field (explicit presence) stays ABSENT — the nested
        resource_job_manager is only present when populated."""
        local = compute_resource_pb2.LOCALSubmission(
            job_submission_interface_id="ls-min")
        rendered = to_jsonable(get_local_job_submission(
            _FakeClient(local=local), "ls-min"))
        self.assertNotIn("resource_job_manager", rendered)

    # ------------------------------------------------------------------
    # snake_case-only assertions (no camelCase / acronym / hyperlink keys)
    # ------------------------------------------------------------------

    def _all_keys(self, obj):
        keys = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(k)
                keys |= self._all_keys(v)
        elif isinstance(obj, list):
            for x in obj:
                keys |= self._all_keys(x)
        return keys

    def test_no_camelcase_or_acronym_keys(self):
        ssh = to_jsonable(get_ssh_job_submission(
            _FakeClient(ssh=_make_ssh()), "ssh-1"))
        uni = to_jsonable(get_unicore_job_submission(
            _FakeClient(unicore=_make_unicore()), "u-1"))
        legacy = {
            "jobSubmissionInterfaceId", "securityProtocol", "monitorMode",
            "sshPort", "alternativeSshHostName", "alternativeSSHHostName",
            "resourceJobManager", "batchQueueEmailSenders",
            "unicoreEndPointUrl", "unicoreEndPointURL", "providerName",
        }
        for key in self._all_keys(ssh) | self._all_keys(uni):
            self.assertNotIn(key, legacy, f"legacy key {key!r} leaked")
            # map keys are decimal strings ("0", "1"); scalar field keys are
            # lowercase snake_case (no uppercase fragments).
            if not key.isdigit():
                self.assertEqual(
                    key, key.lower(), f"key {key!r} is not snake_case")

    def test_no_hyperlink_fields(self):
        ssh = to_jsonable(get_ssh_job_submission(
            _FakeClient(ssh=_make_ssh()), "ssh-1"))
        self.assertNotIn("url", ssh)
