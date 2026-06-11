"""Proto-direct contract snapshot for the full-experiment family.

Replaces the abandoned ``test_full_experiment_parity.py`` (which validated the
legacy camelCase DRF contract).  The proto-direct contract is:

* the SDK ``get_full_experiment`` returns a composed pydantic ``FullExperiment``
  carrying the component protos / ``WithAccess`` envelopes WHOLESALE: the
  experiment (``WithAccess[ExperimentModel]`` — the whole process/task/job tree
  included), the project (``WithAccess[Project]`` or ``None``), the application
  module (``WithAccess[ApplicationModule]`` or ``None``), the compute resource
  (the raw ``ComputeResourceDescription`` proto or ``None``), the input/output
  data products (``WithAccess[DataProductModel]``), the flat job list
  (``JobModel`` protos) and the portal-computed ``output_views`` map;
* the portal's generic ``to_jsonable`` renderer flattens the whole tree to
  **snake_case** JSON by recursing the model field-by-field:
  ``MessageToDict(preserving_proto_field_name=True,
  always_print_fields_with_no_presence=True)`` for every nested proto (enums as
  member NAMES, int64 timestamps as epoch-millis STRINGS) with each envelope's
  access flags merged on top.

This test builds a representative full-experiment composite (an experiment with
a nested process → task → job tree, a referenced project, application module,
compute resource, input/output data products and jobs), runs it through
``get_full_experiment`` (stubbing the chained sharing call and the request-bound
resolvers) + ``to_jsonable``, and asserts the resulting JSON shape: snake_case
keys only, enums as NAMES, timestamps as epoch-millis strings, NO camelCase, NO
hyperlinks.
"""

from django.test import SimpleTestCase

from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appdeployment import (  # noqa: E501
    app_deployment_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.appcatalog.appinterface import (  # noqa: E501
    app_interface_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource import (  # noqa: E501
    compute_resource_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.application.io import (
    application_io_pb2 as io,
)
from airavata_sdk.generated.org.apache.airavata.model.data.replica import (
    replica_catalog_pb2 as rc,
)
from airavata_sdk.generated.org.apache.airavata.model.experiment import (
    experiment_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.job import job_pb2
from airavata_sdk.generated.org.apache.airavata.model.process import (
    process_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.scheduling import (
    scheduling_pb2,
)
from airavata_sdk.generated.org.apache.airavata.model.status import status_pb2
from airavata_sdk.generated.org.apache.airavata.model.task import task_pb2
from airavata_sdk.generated.org.apache.airavata.model.workspace import (
    workspace_pb2,
)
from airavata_sdk.helpers.research_resources import get_full_experiment
from django_airavata.apps.api.proto_render import to_jsonable


# ---------------------------------------------------------------------------
# Representative composite protos
# ---------------------------------------------------------------------------

def _make_experiment():
    job = job_pb2.JobModel(
        job_id="job-1", task_id="task-1", process_id="proc-1", job_name="J",
        creation_time=1705320000000,
        job_statuses=[status_pb2.JobStatus(
            job_state=status_pb2.JobState.ACTIVE,
            time_of_state_change=1705320001000, reason="r", status_id="js-1")])
    task = task_pb2.TaskModel(
        task_id="task-1", task_type=task_pb2.TaskTypes.JOB_SUBMISSION,
        parent_process_id="proc-1", creation_time=1705320000000,
        task_statuses=[status_pb2.TaskStatus(
            state=status_pb2.TaskState.TASK_STATE_COMPLETED,
            time_of_state_change=1705320002000, reason="ok",
            status_id="ts-1")],
        jobs=[job])
    process = process_pb2.ProcessModel(
        process_id="proc-1", experiment_id="exp-contract-1",
        creation_time=1705320000000,
        process_statuses=[status_pb2.ProcessStatus(
            state=status_pb2.ProcessState.PROCESS_STATE_COMPLETED,
            time_of_state_change=1705320003000, reason="done",
            status_id="ps-1", process_id="proc-1")],
        tasks=[task])
    ucd = experiment_pb2.UserConfigurationDataModel(
        airavata_auto_schedule=False,
        computational_resource_scheduling=(
            scheduling_pb2.ComputationalResourceSchedulingModel(
                resource_host_id="comp-1", total_cpu_count=4, node_count=1,
                queue_name="normal", wall_time_limit=30)))
    return experiment_pb2.ExperimentModel(
        experiment_id="exp-contract-1", project_id="proj-contract-1",
        gateway_id="default",
        experiment_type=experiment_pb2.ExperimentType.SINGLE_APPLICATION,
        user_name="alice", experiment_name="Contract Experiment",
        creation_time=1705320000000, description="desc",
        execution_id="iface-1", email_addresses=["a@x.org"],
        user_configuration_data=ucd,
        experiment_inputs=[io.InputDataObjectType(
            name="in1", value="airavata-dp://in", type=io.DataType.URI,
            input_order=1, is_required=True)],
        experiment_outputs=[io.OutputDataObjectType(
            name="out1", value="airavata-dp://out", type=io.DataType.URI)],
        experiment_status=[status_pb2.ExperimentStatus(
            state=status_pb2.ExperimentState.EXPERIMENT_STATE_EXECUTING,
            time_of_state_change=1705320004000, reason="running",
            status_id="es-1")],
        processes=[process])


def _make_project():
    return workspace_pb2.Project(
        project_id="proj-contract-1", owner="alice", gateway_id="default",
        name="Contract Project", description="p", creation_time=1705320000000)


def _make_app_interface():
    return app_interface_pb2.ApplicationInterfaceDescription(
        application_interface_id="iface-1", application_name="App",
        application_modules=["mod-1"])


def _make_app_module():
    return app_deployment_pb2.ApplicationModule(
        app_module_id="mod-1", app_module_name="mod",
        app_module_version="1.0", app_module_description="m")


def _make_compute_resource():
    return compute_resource_pb2.ComputeResourceDescription(
        compute_resource_id="comp-1", host_name="hpc.example.org",
        resource_description="HPC", enabled=True)


def _make_data_product(uri, owner_name):
    return rc.DataProductModel(
        product_uri=uri, gateway_id="default", owner_name=owner_name,
        product_name=uri.split("://")[-1],
        data_product_type=rc.DataProductType.FILE,
        creation_time=1705320000000, last_modified_time=1705320005000,
        replica_locations=[rc.DataReplicaLocationModel(
            replica_name="gw copy",
            replica_location_category=(
                rc.ReplicaLocationCategory.GATEWAY_DATA_STORE),
            replica_persistent_type=rc.ReplicaPersistentType.TRANSIENT,
            storage_resource_id="store-1",
            file_path="/data/" + uri.split("://")[-1])])


def _make_job():
    return job_pb2.JobModel(
        job_id="job-1", task_id="task-1", process_id="proc-1", job_name="J",
        creation_time=1705320000000)


# ---------------------------------------------------------------------------
# Stub client
# ---------------------------------------------------------------------------

class _FakeResearch:
    def __init__(self):
        self._experiment = _make_experiment()
        self._project = _make_project()
        self._app_interface = _make_app_interface()
        self._app_module = _make_app_module()
        self._data_products = {
            "airavata-dp://in": _make_data_product("airavata-dp://in", "alice"),
            "airavata-dp://out": _make_data_product("airavata-dp://out", "bob"),
        }
        self._jobs = [_make_job()]

    def get_experiment(self, experiment_id):
        return self._experiment

    def get_project(self, project_id):
        return self._project

    def get_application_interface(self, app_interface_id):
        return self._app_interface

    def get_application_module(self, app_module_id):
        return self._app_module

    def get_data_product(self, uri):
        return self._data_products[uri]

    def get_job_details(self, experiment_id):
        return self._jobs


class _FakeCompute:
    def get_compute_resource(self, compute_resource_id):
        return _make_compute_resource()


class _FakeSharing:
    def __init__(self, has_access=True):
        self._has_access = has_access
        self.calls = []

    def user_has_access(self, resource_id, user_id, permission_type):
        self.calls.append((resource_id, user_id, permission_type))
        return self._has_access


class _FakeClient:
    def __init__(self, username="alice", sharing_has_access=True):
        self.research = _FakeResearch()
        self.compute = _FakeCompute()
        self.sharing = _FakeSharing(sharing_has_access)
        self.gateway_id = "default"
        self.username = username


def _dp_write(_dp):
    return True


def _output_views(_experiment, _app_interface):
    return {"out1": ["view-provider-a"]}


class FullExperimentContractSnapshotTest(SimpleTestCase):

    def _render(self, *, username="alice", sharing_has_access=True,
                project_has_read=True, module_has_write=True,
                dp_write=_dp_write, output_views=_output_views):
        client = _FakeClient(
            username=username, sharing_has_access=sharing_has_access)
        result = get_full_experiment(
            client, "exp-contract-1",
            project_has_read=project_has_read,
            module_has_write=module_has_write,
            data_product_write_fn=dp_write,
            output_views_fn=output_views,
        )
        return to_jsonable(result)

    # ------------------------------------------------------------------
    # Top-level composed shape
    # ------------------------------------------------------------------

    def test_top_level_key_set(self):
        rendered = self._render()
        self.assertEqual(set(rendered.keys()), {
            "experiment_id", "experiment", "project", "application_module",
            "compute_resource", "input_data_products", "output_data_products",
            "job_details", "output_views",
        })

    def test_top_level_experiment_id(self):
        self.assertEqual(self._render()["experiment_id"], "exp-contract-1")

    def test_output_views_passed_through(self):
        self.assertEqual(
            self._render()["output_views"], {"out1": ["view-provider-a"]})

    # ------------------------------------------------------------------
    # Nested experiment (WithAccess[ExperimentModel] flattened)
    # ------------------------------------------------------------------

    def test_experiment_scalars_and_flags(self):
        exp = self._render()["experiment"]
        self.assertEqual(exp["experiment_id"], "exp-contract-1")
        self.assertEqual(exp["project_id"], "proj-contract-1")
        self.assertEqual(exp["user_name"], "alice")
        # WithAccess flags merged on top.
        self.assertFalse(exp["is_owner"])  # experiment carries no owner flag
        self.assertTrue(exp["user_has_write_access"])  # chained sharing -> True

    def test_experiment_enum_is_name(self):
        exp = self._render()["experiment"]
        self.assertEqual(exp["experiment_type"], "SINGLE_APPLICATION")
        self.assertEqual(
            exp["experiment_status"][0]["state"],
            "EXPERIMENT_STATE_EXECUTING")

    def test_experiment_timestamp_is_epoch_millis_string(self):
        exp = self._render()["experiment"]
        self.assertIsInstance(exp["creation_time"], str)
        self.assertEqual(exp["creation_time"], "1705320000000")

    def test_experiment_tree_serialized(self):
        exp = self._render()["experiment"]
        proc = exp["processes"][0]
        self.assertEqual(proc["process_id"], "proc-1")
        task = proc["tasks"][0]
        self.assertEqual(task["task_type"], "JOB_SUBMISSION")
        self.assertEqual(
            task["task_statuses"][0]["state"], "TASK_STATE_COMPLETED")
        job = task["jobs"][0]
        self.assertEqual(job["job_id"], "job-1")
        self.assertEqual(job["job_statuses"][0]["job_state"], "ACTIVE")

    # ------------------------------------------------------------------
    # Nested project (WithAccess[Project] flattened)
    # ------------------------------------------------------------------

    def test_project_flattened_with_flags(self):
        proj = self._render()["project"]
        self.assertEqual(proj["project_id"], "proj-contract-1")
        self.assertEqual(proj["owner"], "alice")
        # is_owner SDK-trivial (owner == username); write from chained sharing.
        self.assertTrue(proj["is_owner"])
        self.assertTrue(proj["user_has_write_access"])

    def test_project_omitted_without_read(self):
        self.assertIsNone(self._render(project_has_read=False)["project"])

    # ------------------------------------------------------------------
    # Nested application module (WithAccess[ApplicationModule] flattened)
    # ------------------------------------------------------------------

    def test_application_module_flattened_with_flags(self):
        mod = self._render()["application_module"]
        self.assertEqual(mod["app_module_id"], "mod-1")
        # gateway-catalog: no ownership, write flag is module_has_write.
        self.assertFalse(mod["is_owner"])
        self.assertTrue(mod["user_has_write_access"])

    def test_application_module_write_flag_reflects_module_has_write(self):
        mod = self._render(module_has_write=False)["application_module"]
        self.assertFalse(mod["user_has_write_access"])

    # ------------------------------------------------------------------
    # Nested compute resource (raw proto flattened)
    # ------------------------------------------------------------------

    def test_compute_resource_flattened(self):
        cr = self._render()["compute_resource"]
        self.assertEqual(cr["compute_resource_id"], "comp-1")
        self.assertEqual(cr["host_name"], "hpc.example.org")
        # raw proto, no access flags merged.
        self.assertNotIn("is_owner", cr)
        self.assertNotIn("user_has_write_access", cr)

    # ------------------------------------------------------------------
    # Data products (WithAccess[DataProductModel] flattened)
    # ------------------------------------------------------------------

    def test_data_products_flattened_with_flags(self):
        rendered = self._render()
        ins = rendered["input_data_products"]
        outs = rendered["output_data_products"]
        self.assertEqual([d["product_uri"] for d in ins], ["airavata-dp://in"])
        self.assertEqual(
            [d["product_uri"] for d in outs], ["airavata-dp://out"])
        # is_owner SDK-trivial (owner_name == username "alice").
        self.assertTrue(ins[0]["is_owner"])    # owner_name="alice"
        self.assertFalse(outs[0]["is_owner"])  # owner_name="bob"
        # write flag is the resolver result (stub returns True).
        self.assertTrue(ins[0]["user_has_write_access"])
        self.assertTrue(outs[0]["user_has_write_access"])

    def test_data_product_enums_are_names(self):
        dp = self._render()["input_data_products"][0]
        self.assertEqual(dp["data_product_type"], "FILE")
        rl = dp["replica_locations"][0]
        self.assertEqual(rl["replica_location_category"], "GATEWAY_DATA_STORE")
        self.assertEqual(rl["replica_persistent_type"], "TRANSIENT")

    def test_data_product_timestamp_is_epoch_millis_string(self):
        dp = self._render()["input_data_products"][0]
        self.assertEqual(dp["creation_time"], "1705320000000")
        self.assertEqual(dp["last_modified_time"], "1705320005000")

    def test_data_product_dropped_legacy_keys_absent(self):
        dp = self._render()["input_data_products"][0]
        # The proto-direct data-product contract dropped these legacy aliases.
        for legacy in ("download_url", "is_input_file_upload", "modified_time",
                       "filesize"):
            self.assertNotIn(legacy, dp)

    # ------------------------------------------------------------------
    # Jobs (raw JobModel protos flattened)
    # ------------------------------------------------------------------

    def test_jobs_flattened(self):
        jobs = self._render()["job_details"]
        self.assertEqual([j["job_id"] for j in jobs], ["job-1"])
        # raw proto, no access flags.
        self.assertNotIn("user_has_write_access", jobs[0])

    # ------------------------------------------------------------------
    # snake_case-only / no-camelCase / no-hyperlinks (whole tree)
    # ------------------------------------------------------------------

    def _all_keys(self, obj):
        keys = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.append(k)
                keys.extend(self._all_keys(v))
        elif isinstance(obj, list):
            for x in obj:
                keys.extend(self._all_keys(x))
        return keys

    def test_no_camelcase_keys_anywhere(self):
        for key in self._all_keys(self._render()):
            self.assertEqual(
                key, key.lower(),
                f"key {key!r} is not lowercase/snake_case")

    def test_no_hyperlink_keys_anywhere(self):
        keys = set(self._all_keys(self._render()))
        for hyperlink in ("url", "full_experiment", "shared_entity",
                          "experiments", "application_interface",
                          "application_deployments"):
            self.assertNotIn(hyperlink, keys)

    def test_no_legacy_camel_keys(self):
        keys = set(self._all_keys(self._render()))
        for legacy in ("experimentId", "projectId", "creationTime",
                       "userHasWriteAccess", "isOwner", "downloadURL",
                       "computeResource", "applicationModule",
                       "inputDataProducts", "outputViews"):
            self.assertNotIn(legacy, keys)

    # ------------------------------------------------------------------
    # Chained sharing call (experiment + project WRITE lookups)
    # ------------------------------------------------------------------

    def test_chained_sharing_calls_use_write(self):
        client = _FakeClient()
        get_full_experiment(
            client, "exp-contract-1",
            project_has_read=True, module_has_write=True,
            data_product_write_fn=_dp_write, output_views_fn=_output_views)
        # One WRITE lookup for the experiment, one for the project.
        perms = [c[2] for c in client.sharing.calls]
        self.assertEqual(perms, ["WRITE", "WRITE"])
        resources = {c[0] for c in client.sharing.calls}
        self.assertEqual(resources, {"exp-contract-1", "proj-contract-1"})
