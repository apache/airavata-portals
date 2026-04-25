import json
from pathlib import Path
from unittest import TestCase

import jsonschema
from django.conf import settings

from django_airavata.apps.api import launcher_serializers


CONTRACTS = Path(settings.BASE_DIR) / "tests" / "contracts"


class ExperimentDraftSerializerTest(TestCase):
    def _valid_draft(self) -> dict:
        return {
            "name": "test-run",
            "project_id": "proj-1",
            "app_id": "namd",
            "interface_name": "run",
            "inputs": {
                "sim_dir": {"storage_id": "my-home", "path": "/home/x/sim"},
                "steps": 1000,
            },
            "outputs": {"trajectory": {"storage_id": "my-home", "path": "/home/x/out.dcd"}},
            "runtime": {
                "compute_resource_id": "bridges-2",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 64,
            },
        }

    def test_valid_draft_passes_schema(self):
        schema = json.loads((CONTRACTS / "experiment-draft.schema.json").read_text())
        jsonschema.validate(self._valid_draft(), schema)

    def test_serializer_accepts_valid_draft(self):
        serializer = launcher_serializers.ExperimentDraftSerializer(data=self._valid_draft())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_rejects_missing_runtime(self):
        draft = self._valid_draft()
        del draft["runtime"]
        serializer = launcher_serializers.ExperimentDraftSerializer(data=draft)
        self.assertFalse(serializer.is_valid())
        self.assertIn("runtime", serializer.errors)

    def test_serializer_rejects_bad_walltime(self):
        draft = self._valid_draft()
        draft["runtime"]["walltime"] = "not-a-time"
        serializer = launcher_serializers.ExperimentDraftSerializer(data=draft)
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_malformed_file_input(self):
        draft = self._valid_draft()
        draft["inputs"]["sim_dir"] = {"storage_id": "my-home"}  # missing 'path'
        serializer = launcher_serializers.ExperimentDraftSerializer(data=draft)
        self.assertFalse(serializer.is_valid())

    def test_serializer_rejects_non_scalar_non_dict_input(self):
        draft = self._valid_draft()
        draft["inputs"]["steps"] = [1, 2, 3]  # neither scalar nor {storage_id, path}
        serializer = launcher_serializers.ExperimentDraftSerializer(data=draft)
        self.assertFalse(serializer.is_valid())


class PreviewResponseSchemaTest(TestCase):
    def test_valid_response(self):
        schema = json.loads((CONTRACTS / "preview-response.schema.json").read_text())
        jsonschema.validate(
            {"invocation_command": "bash run.sh", "script_contents": "#!/bin/bash\n", "warnings": []},
            schema,
        )
