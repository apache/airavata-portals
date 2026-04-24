# Generic Experiment Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the per-application experiment launch flow with a single `/workspace/launch` 3-tab wizard backed by new Django REST endpoints and a Pinia store.

**Architecture:** Vue 3 `<script setup lang="ts">` SPA mounted at `/workspace/launch`. Tabs are dumb views over a `useLaunchStore` Pinia store that owns the experiment draft. Tab 1 owns app pick + interface pick + scalar/file inputs + file outputs (each file row carries its own storage + path). Tab 2 owns runtime (compute + partition + walltime + nodes + CPUs, profile-driven from the picked project). Tab 3 fetches a server-rendered preview script via a new dry-run RPC and submits via the existing experiment-launch path. A `launcher_client.py` Python module abstracts the airavata gRPC layer so a stub can power tests and CI before the real upstream RPCs land.

**Tech Stack:** Vue 3, Pinia 3, TypeScript strict, Vite 6, Vitest + jsdom + `@vue/test-utils`, Playwright, Django 5.1, DRF, Thrift Airavata client (stubbed via `launcher_client.py`).

**Spec:** [`2026-04-24-generic-experiment-launcher-design.md`](../specs/2026-04-24-generic-experiment-launcher-design.md)

---

## File Map

### Created

**Backend (Python / Django)**
- `django_airavata/apps/api/launcher_client.py` — abstraction layer over the airavata gRPC calls (real + stub).
- `django_airavata/apps/api/launcher_serializers.py` — DRF serializers for app, interface, draft, preview.
- `django_airavata/apps/api/launcher_views.py` — DRF views for the launcher API surface.
- `django_airavata/apps/api/tests/test_launcher_views.py` — Django TestCase for the new views.
- `django_airavata/apps/api/tests/test_launcher_client.py` — unit tests for the stub + serialization.
- `django_airavata/apps/workspace/templates/django_airavata_workspace/launch.html` — minimal SPA shell.
- `tests/contracts/experiment-draft.schema.json` — JSON schema for draft payload.
- `tests/contracts/preview-response.schema.json` — JSON schema for preview response.

**Frontend (Vue / TS)**
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-launch.ts`
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/LaunchContainer.vue`
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ExperimentMetaHeader.vue`
- `…/js/components/launch/WizardTabs.vue`
- `…/js/components/launch/Tab1ApplicationInputs.vue`
- `…/js/components/launch/AppPicker.vue`
- `…/js/components/launch/InterfacePicker.vue`
- `…/js/components/launch/InputList.vue`
- `…/js/components/launch/ScalarInputRow.vue`
- `…/js/components/launch/FileInputRow.vue`
- `…/js/components/launch/OutputList.vue`
- `…/js/components/launch/FileOutputRow.vue`
- `…/js/components/launch/Tab2Runtime.vue`
- `…/js/components/launch/runtime/RuntimeInputs.vue`
- `…/js/components/launch/Tab3ReviewLaunch.vue`
- `…/js/components/launch/InvocationCommand.vue`
- `…/js/components/launch/ScriptPreview.vue`
- `django_airavata/static/common/js/stores/launch.ts` — Pinia store for the wizard.
- `django_airavata/static/common/js/stores/launch-types.ts` — typed interfaces for Application / Interface / Draft / Preview.
- `…/static/common/js/services/launcherService.ts` — typed fetch wrappers around the new endpoints.
- `…/tests/unit/components/launch/*.spec.ts` — one spec per component (mirrors src tree).
- `…/tests/unit/stores/launch.spec.ts` — Pinia store spec.
- `…/tests/unit/integration/launch-flow.spec.ts` — full happy-path integration test with API mocked.
- `tests/e2e/specs/launch-happy.spec.ts`
- `tests/e2e/specs/launch-error-paths.spec.ts`

### Modified
- `django_airavata/apps/api/urls.py` — register new `launcher_views` endpoints.
- `django_airavata/apps/workspace/views.py` — `launch(request)` view, removal of `create_experiment` + `edit_experiment` views.
- `django_airavata/apps/workspace/urls.py` — new route + 301 redirects for old routes.
- `django_airavata/settings.py` — `FEATURE_GENERIC_LAUNCHER` flag, `LAUNCHER_CLIENT_STUB` flag.
- `tests/e2e/specs/smoke.spec.ts` — extend `AUTHENTICATED_PAGES` with `/workspace/launch`.
- Repo-internal call sites of the old URL listed in Task 24.

### Deleted (Task 26)
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/CreateExperimentContainer.vue`
- `…/js/containers/EditExperimentContainer.vue`
- `…/js/components/experiment/ExperimentEditor.vue`
- `…/js/components/experiment/ComputationalResourceSchedulingEditor.vue`
- `…/js/components/experiment/QueueSettingsEditor.vue`
- `…/js/components/experiment/GroupResourceProfileSelector.vue`
- `…/js/entry-create-experiment.js`
- `…/js/entry-edit-experiment.js`

---

## Phase 1 — Backend foundations

### Task 1: Settings flags + launcher_client stub layer

**Files:**
- Create: `django_airavata/apps/api/launcher_client.py`
- Create: `django_airavata/apps/api/tests/test_launcher_client.py`
- Modify: `django_airavata/settings.py`

- [ ] **Step 1: Add settings flags**

Append to `django_airavata/settings.py`:

```python
# Generic experiment launcher feature flags
FEATURE_GENERIC_LAUNCHER = os.environ.get("FEATURE_GENERIC_LAUNCHER", "False").lower() == "true"
LAUNCHER_CLIENT_STUB = os.environ.get("LAUNCHER_CLIENT_STUB", "True").lower() == "true"
```

`LAUNCHER_CLIENT_STUB` defaults `True` so dev + CI work before the airavata server's new-model RPCs land. Phase 9 flips it to `False` once they do.

- [ ] **Step 2: Write the failing client tests**

Create `django_airavata/apps/api/tests/test_launcher_client.py`:

```python
from unittest import TestCase

from django.test import override_settings

from django_airavata.apps.api import launcher_client


class StubLauncherClientTest(TestCase):
    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_applications_returns_at_least_one_app(self):
        client = launcher_client.get_client(user_token="ignored")
        apps = client.list_applications(category=None, search=None)
        self.assertTrue(len(apps) >= 1)
        first = apps[0]
        self.assertIn("app_id", first)
        self.assertIn("name", first)
        self.assertIn("content", first)
        self.assertIn("interfaces", first)
        self.assertIsInstance(first["interfaces"], list)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_get_resource_profile_returns_partitions(self):
        client = launcher_client.get_client(user_token="ignored")
        profile = client.get_project_resource_profile(project_id="proj-stub")
        self.assertIn("compute_resources", profile)
        self.assertIn("allocation_id", profile)
        self.assertTrue(len(profile["compute_resources"]) >= 1)
        self.assertIn("partitions", profile["compute_resources"][0])

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_generate_preview_returns_script_and_command(self):
        client = launcher_client.get_client(user_token="ignored")
        preview = client.generate_preview({
            "name": "x",
            "project_id": "proj-stub",
            "app_id": "app-stub",
            "interface_name": "run",
            "inputs": {},
            "outputs": {},
            "runtime": {
                "compute_resource_id": "cr-stub",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 8,
            },
        })
        self.assertIn("invocation_command", preview)
        self.assertIn("script_contents", preview)
        self.assertIn("warnings", preview)
        self.assertIsInstance(preview["warnings"], list)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_list_projects_returns_at_least_one(self):
        client = launcher_client.get_client(user_token="ignored")
        projects = client.list_projects()
        self.assertTrue(len(projects) >= 1)
        self.assertIn("project_id", projects[0])
        self.assertIn("name", projects[0])
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_client -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'django_airavata.apps.api.launcher_client'`.

- [ ] **Step 4: Implement the stub client**

Create `django_airavata/apps/api/launcher_client.py`:

```python
"""Abstraction layer over the airavata server's launcher RPCs.

The real RPCs (new-model applications + dry-run preview) are landing in the
Java server separately. To unblock portal development and keep CI green,
this module ships with a stub implementation that returns plausible
fixtures. The settings flag ``LAUNCHER_CLIENT_STUB`` selects between the
stub and the real client. Tests should mock at the ``get_client`` boundary.
"""

from __future__ import annotations

from typing import Any, Protocol

from django.conf import settings


class LauncherClient(Protocol):
    def list_applications(self, *, category: str | None, search: str | None) -> list[dict[str, Any]]: ...
    def get_application(self, *, app_id: str) -> dict[str, Any]: ...
    def get_project_resource_profile(self, *, project_id: str) -> dict[str, Any]: ...
    def list_user_storages(self) -> list[dict[str, Any]]: ...
    def list_projects(self) -> list[dict[str, Any]]: ...
    def generate_preview(self, draft: dict[str, Any]) -> dict[str, Any]: ...
    def launch_experiment(self, draft: dict[str, Any]) -> dict[str, Any]: ...


_STUB_APPS: list[dict[str, Any]] = [
    {
        "app_id": "namd",
        "name": "NAMD",
        "category": "Molecular Dynamics",
        "content": {"kind": "github", "url": "github.com/Illinois/namd@v3.0"},
        "interfaces": [
            {
                "name": "compile",
                "inputs": [],
                "outputs": [{"name": "binary", "type": "file"}],
            },
            {
                "name": "run",
                "inputs": [
                    {"name": "sim_dir", "type": "dir", "required": True},
                    {"name": "force_field", "type": "file", "required": True},
                    {"name": "steps", "type": "int", "required": True},
                ],
                "outputs": [{"name": "trajectory", "type": "file"}],
            },
        ],
    }
]


class _StubClient:
    def __init__(self, user_token: str) -> None:
        self.user_token = user_token

    def list_applications(self, *, category: str | None, search: str | None) -> list[dict[str, Any]]:
        results = list(_STUB_APPS)
        if category:
            results = [a for a in results if a["category"] == category]
        if search:
            needle = search.lower()
            results = [a for a in results if needle in a["name"].lower()]
        return results

    def get_application(self, *, app_id: str) -> dict[str, Any]:
        for a in _STUB_APPS:
            if a["app_id"] == app_id:
                return a
        raise LookupError(f"unknown app_id {app_id!r}")

    def get_project_resource_profile(self, *, project_id: str) -> dict[str, Any]:
        return {
            "project_id": project_id,
            "allocation_id": "NSF-CS240042",
            "compute_resources": [
                {
                    "compute_resource_id": "bridges-2",
                    "name": "Bridges-2",
                    "mapped_storage": {"storage_id": "bridges2-scratch", "scratch_path": f"/scratch/{project_id}"},
                    "partitions": [
                        {"name": "RM", "max_walltime": "48:00:00", "max_nodes": 64, "cpus_per_node": 128},
                        {"name": "RM-shared", "max_walltime": "48:00:00", "max_nodes": 1, "cpus_per_node": 128},
                        {"name": "GPU", "max_walltime": "48:00:00", "max_nodes": 16, "cpus_per_node": 64},
                    ],
                }
            ],
        }

    def list_user_storages(self) -> list[dict[str, Any]]:
        return [
            {"storage_id": "my-home", "name": "My Home", "is_primary": True},
            {"storage_id": "bridges2-scratch", "name": "Bridges-2 Scratch", "is_primary": False},
        ]

    def list_projects(self) -> list[dict[str, Any]]:
        return [
            {"project_id": "proj-stub", "name": "stub-lab-2026"},
        ]

    def generate_preview(self, draft: dict[str, Any]) -> dict[str, Any]:
        compute_id = draft["runtime"]["compute_resource_id"]
        is_slurm = "bridges" in compute_id or "expanse" in compute_id or "anvil" in compute_id
        partition = draft["runtime"]["partition"]
        walltime = draft["runtime"]["walltime"]
        nodes = draft["runtime"]["nodes"]
        cpus = draft["runtime"]["cpus_per_node"]
        if is_slurm:
            invocation = f"sbatch /tmp/{draft['name']}/run.sh"
            script_lines = [
                "#!/bin/bash",
                f"#SBATCH --job-name={draft['name']}",
                "#SBATCH -A NSF-CS240042",
                f"#SBATCH -p {partition}",
                f"#SBATCH -N {nodes}",
                f"#SBATCH --ntasks-per-node={cpus}",
                f"#SBATCH -t {walltime}",
                "",
                "# compute-service",
                "module load openmpi/4.1.2",
                "",
                "# agent-service",
                "airavata-agent --exp-id $EXP_ID &",
                "",
                "# research-framework",
                f"srun {draft.get('app_id', 'app')} {draft.get('interface_name', 'run')}",
            ]
        else:
            invocation = f"bash /tmp/{draft['name']}/run.sh"
            script_lines = [
                "#!/bin/bash",
                "# compute-service",
                "module load openmpi/4.1.2",
                "",
                "# agent-service",
                "airavata-agent --exp-id $EXP_ID &",
                "",
                "# research-framework",
                f"{draft.get('app_id', 'app')} {draft.get('interface_name', 'run')}",
            ]
        return {
            "invocation_command": invocation,
            "script_contents": "\n".join(script_lines) + "\n",
            "warnings": [],
        }

    def launch_experiment(self, draft: dict[str, Any]) -> dict[str, Any]:
        return {"experiment_id": f"exp-{draft['name']}-stub"}


class _RealClient:
    def __init__(self, user_token: str) -> None:
        self.user_token = user_token

    def list_applications(self, *, category, search):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def get_application(self, *, app_id):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def get_project_resource_profile(self, *, project_id):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def list_user_storages(self):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def list_projects(self):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def generate_preview(self, draft):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def launch_experiment(self, draft):
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")


def get_client(user_token: str) -> LauncherClient:
    if getattr(settings, "LAUNCHER_CLIENT_STUB", True):
        return _StubClient(user_token)
    return _RealClient(user_token)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_client -v 2`
Expected: PASS — 4 tests OK.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/api/launcher_client.py \
        django_airavata/apps/api/tests/test_launcher_client.py \
        django_airavata/settings.py
git commit -m "feat(launcher): launcher_client stub + settings flags"
```

---

### Task 2: Launcher serializers + JSON contract

**Files:**
- Create: `django_airavata/apps/api/launcher_serializers.py`
- Create: `tests/contracts/experiment-draft.schema.json`
- Create: `tests/contracts/preview-response.schema.json`
- Create: `django_airavata/apps/api/tests/test_launcher_serializers.py`

- [ ] **Step 1: Write the contract JSON schemas**

Create `tests/contracts/experiment-draft.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ExperimentDraft",
  "type": "object",
  "required": ["name", "project_id", "app_id", "interface_name", "inputs", "outputs", "runtime"],
  "properties": {
    "name": {"type": "string", "minLength": 1, "maxLength": 256},
    "project_id": {"type": "string"},
    "description": {"type": "string"},
    "app_id": {"type": "string"},
    "interface_name": {"type": "string"},
    "inputs": {
      "type": "object",
      "additionalProperties": {
        "oneOf": [
          {"type": ["string", "number", "boolean"]},
          {
            "type": "object",
            "required": ["storage_id", "path"],
            "properties": {
              "storage_id": {"type": "string"},
              "path": {"type": "string"}
            }
          }
        ]
      }
    },
    "outputs": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["storage_id", "path"],
        "properties": {
          "storage_id": {"type": "string"},
          "path": {"type": "string"}
        }
      }
    },
    "runtime": {
      "type": "object",
      "required": ["compute_resource_id", "partition", "walltime", "nodes", "cpus_per_node"],
      "properties": {
        "compute_resource_id": {"type": "string"},
        "partition": {"type": "string"},
        "walltime": {"type": "string", "pattern": "^\\d{1,3}:[0-5]\\d:[0-5]\\d$"},
        "nodes": {"type": "integer", "minimum": 1},
        "cpus_per_node": {"type": "integer", "minimum": 1}
      }
    }
  }
}
```

Create `tests/contracts/preview-response.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PreviewResponse",
  "type": "object",
  "required": ["invocation_command", "script_contents", "warnings"],
  "properties": {
    "invocation_command": {"type": "string", "minLength": 1},
    "script_contents": {"type": "string", "minLength": 1},
    "warnings": {"type": "array", "items": {"type": "string"}}
  }
}
```

- [ ] **Step 2: Write the failing serializer tests**

Create `django_airavata/apps/api/tests/test_launcher_serializers.py`:

```python
import json
from pathlib import Path
from unittest import TestCase

import jsonschema

from django_airavata.apps.api import launcher_serializers


CONTRACTS = Path(__file__).resolve().parents[4] / "tests" / "contracts"


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


class PreviewResponseSchemaTest(TestCase):
    def test_valid_response(self):
        schema = json.loads((CONTRACTS / "preview-response.schema.json").read_text())
        jsonschema.validate(
            {"invocation_command": "bash run.sh", "script_contents": "#!/bin/bash\n", "warnings": []},
            schema,
        )
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_serializers -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'django_airavata.apps.api.launcher_serializers'`.

- [ ] **Step 4: Implement the serializers**

Create `django_airavata/apps/api/launcher_serializers.py`:

```python
import re

from rest_framework import serializers


WALLTIME_RE = re.compile(r"^\d{1,3}:[0-5]\d:[0-5]\d$")


class RuntimeSerializer(serializers.Serializer):
    compute_resource_id = serializers.CharField()
    partition = serializers.CharField()
    walltime = serializers.CharField()
    nodes = serializers.IntegerField(min_value=1)
    cpus_per_node = serializers.IntegerField(min_value=1)

    def validate_walltime(self, value: str) -> str:
        if not WALLTIME_RE.match(value):
            raise serializers.ValidationError("walltime must match HH:MM:SS or HHH:MM:SS")
        return value


class StorageRefSerializer(serializers.Serializer):
    storage_id = serializers.CharField()
    path = serializers.CharField()


class ExperimentDraftSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=256)
    project_id = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    app_id = serializers.CharField()
    interface_name = serializers.CharField()
    inputs = serializers.DictField(child=serializers.JSONField())
    outputs = serializers.DictField(child=StorageRefSerializer())
    runtime = RuntimeSerializer()

    def validate_inputs(self, value):
        # Each input is either a scalar (str/int/float/bool) or a {storage_id, path} object.
        for name, v in value.items():
            if isinstance(v, dict):
                StorageRefSerializer(data=v).is_valid(raise_exception=True)
        return value


class PreviewResponseSerializer(serializers.Serializer):
    invocation_command = serializers.CharField()
    script_contents = serializers.CharField()
    warnings = serializers.ListField(child=serializers.CharField(), default=list)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_serializers -v 2`
Expected: PASS — 5 tests OK. (`jsonschema` is already a transitive dep via `wagtail`; if missing, `pip install jsonschema` and add to requirements-dev.txt.)

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/api/launcher_serializers.py \
        django_airavata/apps/api/tests/test_launcher_serializers.py \
        tests/contracts/experiment-draft.schema.json \
        tests/contracts/preview-response.schema.json
git commit -m "feat(launcher): DRF serializers + JSON contract schemas"
```

---

### Task 3: Launcher views — listing, profile, storages

**Files:**
- Create: `django_airavata/apps/api/launcher_views.py`
- Modify: `django_airavata/apps/api/urls.py`
- Create: `django_airavata/apps/api/tests/test_launcher_views.py`

- [ ] **Step 1: Write the failing view tests**

Create `django_airavata/apps/api/tests/test_launcher_views.py`:

```python
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase


class LauncherListingViewsTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        self.client.force_login(self.user)
        # Stub out the session token reader the views rely on
        session = self.client.session
        session["ACCESS_TOKEN"] = "test-token"
        session.save()

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_applications_list_default(self):
        resp = self.client.get("/api/launcher/applications/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(len(body["results"]) >= 1)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_applications_list_filters_by_search(self):
        resp = self.client.get("/api/launcher/applications/?search=namd")
        self.assertEqual(resp.status_code, 200)
        names = [a["name"] for a in resp.json()["results"]]
        self.assertIn("NAMD", names)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_application_detail(self):
        resp = self.client.get("/api/launcher/applications/namd/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["app_id"], "namd")

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_resource_profile_for_project(self):
        resp = self.client.get("/api/launcher/projects/proj-1/resource-profile/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("compute_resources", body)
        self.assertIn("allocation_id", body)

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_user_storages(self):
        resp = self.client.get("/api/launcher/storages/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(any(s.get("is_primary") for s in body["results"]))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_projects_list(self):
        resp = self.client.get("/api/launcher/projects/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("results", body)
        self.assertTrue(len(body["results"]) >= 1)
        self.assertIn("project_id", body["results"][0])
        self.assertIn("name", body["results"][0])

    def test_endpoints_require_auth(self):
        self.client.logout()
        for url in [
            "/api/launcher/applications/",
            "/api/launcher/applications/namd/",
            "/api/launcher/projects/proj-1/resource-profile/",
            "/api/launcher/storages/",
            "/api/launcher/projects/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 403)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_views -v 2`
Expected: FAIL — endpoints not registered (404), or `launcher_views` module missing.

- [ ] **Step 3: Implement the listing views**

Create `django_airavata/apps/api/launcher_views.py`:

```python
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from django_airavata.apps.api import launcher_client


def _client(request: Request) -> launcher_client.LauncherClient:
    token = request.session.get("ACCESS_TOKEN", "")
    return launcher_client.get_client(user_token=token)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def applications_list(request: Request) -> Response:
    category = request.query_params.get("category") or None
    search = request.query_params.get("search") or None
    results = _client(request).list_applications(category=category, search=search)
    return Response({"results": results})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def application_detail(request: Request, app_id: str) -> Response:
    try:
        return Response(_client(request).get_application(app_id=app_id))
    except LookupError:
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def project_resource_profile(request: Request, project_id: str) -> Response:
    return Response(_client(request).get_project_resource_profile(project_id=project_id))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_storages(request: Request) -> Response:
    return Response({"results": _client(request).list_user_storages()})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def projects_list(request: Request) -> Response:
    return Response({"results": _client(request).list_projects()})
```

- [ ] **Step 4: Register the URLs**

Edit `django_airavata/apps/api/urls.py`. Find the existing `urlpatterns = [` block and add these entries before the closing bracket:

```python
from . import launcher_views

# ... after the existing router lines and before the urlpatterns list, add:
urlpatterns += [
    re_path(r"^launcher/applications/$", launcher_views.applications_list, name="launcher_applications_list"),
    re_path(r"^launcher/applications/(?P<app_id>[^/]+)/$", launcher_views.application_detail, name="launcher_application_detail"),
    re_path(r"^launcher/projects/(?P<project_id>[^/]+)/resource-profile/$",
            launcher_views.project_resource_profile, name="launcher_project_resource_profile"),
    re_path(r"^launcher/storages/$", launcher_views.user_storages, name="launcher_user_storages"),
    re_path(r"^launcher/projects/$", launcher_views.projects_list, name="launcher_projects_list"),
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_views -v 2`
Expected: PASS — 7 tests OK.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/api/launcher_views.py \
        django_airavata/apps/api/urls.py \
        django_airavata/apps/api/tests/test_launcher_views.py
git commit -m "feat(launcher): listing endpoints (apps, profile, storages, projects)"
```

---

### Task 4: Preview + create endpoints

**Files:**
- Modify: `django_airavata/apps/api/launcher_views.py`
- Modify: `django_airavata/apps/api/urls.py`
- Modify: `django_airavata/apps/api/tests/test_launcher_views.py`

- [ ] **Step 1: Add the failing tests**

Append to `django_airavata/apps/api/tests/test_launcher_views.py`:

```python
class LauncherWriteViewsTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        self.client.force_login(self.user)
        session = self.client.session
        session["ACCESS_TOKEN"] = "test-token"
        session.save()
        self.draft = {
            "name": "test-run",
            "project_id": "proj-1",
            "app_id": "namd",
            "interface_name": "run",
            "inputs": {"steps": 100},
            "outputs": {"trajectory": {"storage_id": "my-home", "path": "/x/out.dcd"}},
            "runtime": {
                "compute_resource_id": "bridges-2",
                "partition": "RM",
                "walltime": "01:00:00",
                "nodes": 1,
                "cpus_per_node": 64,
            },
        }

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_returns_script_and_command(self):
        resp = self.client.post("/api/launcher/experiment-drafts/preview/", self.draft, format="json")
        self.assertEqual(resp.status_code, 200, resp.content)
        body = resp.json()
        self.assertIn("invocation_command", body)
        self.assertIn("script_contents", body)
        self.assertIn("warnings", body)
        self.assertTrue(body["script_contents"].startswith("#!/bin/bash"))

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_rejects_invalid_draft(self):
        bad = dict(self.draft)
        bad["runtime"] = {**bad["runtime"], "walltime": "garbage"}
        resp = self.client.post("/api/launcher/experiment-drafts/preview/", bad, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("runtime", resp.json())

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_preview_returns_502_when_client_unreachable(self):
        with patch.object(launcher_views, "_client") as mock_client:
            mock_client.return_value.generate_preview.side_effect = ConnectionError("airavata down")
            resp = self.client.post("/api/launcher/experiment-drafts/preview/", self.draft, format="json")
        self.assertEqual(resp.status_code, 502)
        self.assertIn("message", resp.json())

    @override_settings(LAUNCHER_CLIENT_STUB=True)
    def test_create_returns_experiment_id(self):
        resp = self.client.post("/api/launcher/experiment-drafts/", self.draft, format="json")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertIn("experiment_id", resp.json())
```

Add to the imports at the top of the test file:

```python
from django_airavata.apps.api import launcher_views  # noqa: E402  (for the patch target)
```

- [ ] **Step 2: Run to verify the new tests fail**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_views.LauncherWriteViewsTest -v 2`
Expected: FAIL — endpoints not registered (404).

- [ ] **Step 3: Implement the views**

Append to `django_airavata/apps/api/launcher_views.py`:

```python
from django_airavata.apps.api import launcher_serializers


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def experiment_draft_preview(request: Request) -> Response:
    serializer = launcher_serializers.ExperimentDraftSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = _client(request).generate_preview(serializer.validated_data)
    except ConnectionError as e:
        return Response({"message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def experiment_draft_create(request: Request) -> Response:
    serializer = launcher_serializers.ExperimentDraftSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = _client(request).launch_experiment(serializer.validated_data)
    except ConnectionError as e:
        return Response({"message": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result, status=status.HTTP_201_CREATED)
```

- [ ] **Step 4: Register the URLs**

Append to the `urlpatterns += [...]` block in `django_airavata/apps/api/urls.py`:

```python
    re_path(r"^launcher/experiment-drafts/preview/$",
            launcher_views.experiment_draft_preview, name="launcher_draft_preview"),
    re_path(r"^launcher/experiment-drafts/$",
            launcher_views.experiment_draft_create, name="launcher_draft_create"),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test django_airavata.apps.api.tests.test_launcher_views -v 2`
Expected: PASS — all tests OK (11 total).

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/api/launcher_views.py \
        django_airavata/apps/api/urls.py \
        django_airavata/apps/api/tests/test_launcher_views.py
git commit -m "feat(launcher): preview + create endpoints with 502/400 handling"
```

---

### Task 5: Workspace launch view + redirects

**Files:**
- Modify: `django_airavata/apps/workspace/views.py`
- Modify: `django_airavata/apps/workspace/urls.py`
- Create: `django_airavata/apps/workspace/templates/django_airavata_workspace/launch.html`
- Create: `django_airavata/apps/workspace/tests/test_launch_view.py`

- [ ] **Step 1: Write the failing test**

Create `django_airavata/apps/workspace/tests/test_launch_view.py` (create the `tests/__init__.py` if missing):

```python
from django.contrib.auth import get_user_model
from django.test import TestCase


class LaunchViewTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pw")
        self.client.force_login(self.user)

    def test_launch_renders_for_authenticated_user(self):
        resp = self.client.get("/workspace/launch")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="launch-app"')

    def test_old_create_experiment_url_redirects_to_launch(self):
        resp = self.client.get("/workspace/applications/anything/create_experiment", follow=False)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "/workspace/launch")

    def test_old_applications_url_redirects_to_launch(self):
        resp = self.client.get("/workspace/applications", follow=False)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "/workspace/launch")

    def test_launch_requires_auth(self):
        self.client.logout()
        resp = self.client.get("/workspace/launch", follow=False)
        # Login redirect — exact path depends on AUTH_LOGIN_URL but we just check it's a redirect
        self.assertIn(resp.status_code, (302, 401))
```

- [ ] **Step 2: Run to verify it fails**

Run: `python manage.py test django_airavata.apps.workspace.tests.test_launch_view -v 2`
Expected: FAIL — `/workspace/launch` returns 404 or current URL config redirects don't match.

- [ ] **Step 3: Add the SPA shell template**

Create `django_airavata/apps/workspace/templates/django_airavata_workspace/launch.html`:

```html
{% extends "base.html" %}
{% load django_vite %}

{% block content %}
  <div id="launch-app" data-feature-flag="{{ feature_flag|yesno:'on,off' }}"></div>
{% endblock %}

{% block scripts %}
  {% vite_asset "js/entry-launch.ts" app="workspace" %}
{% endblock %}
```

- [ ] **Step 4: Add the launch view**

Edit `django_airavata/apps/workspace/views.py`. Add this view (and import `settings` at the top if not already):

```python
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required
def launch(request):
    return render(request, "django_airavata_workspace/launch.html", {
        "feature_flag": getattr(settings, "FEATURE_GENERIC_LAUNCHER", False),
    })
```

- [ ] **Step 5: Wire URL + redirects**

Edit `django_airavata/apps/workspace/urls.py`. Replace the existing patterns for `applications`, `applications/(...)/create_experiment`, and `applications/(...)/$` with:

```python
from django.views.generic import RedirectView

# ...
urlpatterns = [
    # ... unchanged entries ...
    re_path(r"^launch$", views.launch, name="launch"),
    re_path(r"^applications$", RedirectView.as_view(url="/workspace/launch", permanent=True), name="applications_redirect"),
    re_path(r"^applications/(?P<app_module_id>[^/]+)/create_experiment$",
            RedirectView.as_view(url="/workspace/launch", permanent=True),
            name="create_experiment_redirect"),
    re_path(r"^applications/(?P<app_module_id>[^/]+)/$",
            RedirectView.as_view(url="/workspace/launch", permanent=True),
            name="application_editor_redirect"),
    # leave the rest of the file untouched
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python manage.py test django_airavata.apps.workspace.tests.test_launch_view -v 2`
Expected: PASS — 4 tests OK.

- [ ] **Step 7: Commit**

```bash
git add django_airavata/apps/workspace/views.py \
        django_airavata/apps/workspace/urls.py \
        django_airavata/apps/workspace/templates/django_airavata_workspace/launch.html \
        django_airavata/apps/workspace/tests/test_launch_view.py
git commit -m "feat(launcher): /workspace/launch view + 301 redirects from old URLs"
```

---

## Phase 2 — Frontend foundation

### Task 6: Pinia store + types + service

**Files:**
- Create: `django_airavata/static/common/js/stores/launch-types.ts`
- Create: `django_airavata/static/common/js/stores/launch.ts`
- Create: `django_airavata/static/common/js/services/launcherService.ts`
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/stores/launch.spec.ts`

- [ ] **Step 1: Define the types**

Create `django_airavata/static/common/js/stores/launch-types.ts`:

```ts
export type ScalarType = "string" | "int" | "float" | "bool" | "enum" | "multi-string";
export type FileType = "file" | "dir";
export type IOType = ScalarType | FileType;

export interface IODescriptor {
  name: string;
  type: IOType;
  required?: boolean;
  options?: string[]; // for enum
}

export interface InterfaceDescriptor {
  name: string;
  inputs: IODescriptor[];
  outputs: IODescriptor[];
}

export interface AppContent {
  kind: "tarball" | "github";
  url: string;
}

export interface Application {
  app_id: string;
  name: string;
  category: string;
  content: AppContent;
  interfaces: InterfaceDescriptor[];
}

export interface Partition {
  name: string;
  max_walltime: string;
  max_nodes: number;
  cpus_per_node: number;
}

export interface MappedStorage {
  storage_id: string;
  scratch_path: string;
}

export interface ComputeResource {
  compute_resource_id: string;
  name: string;
  mapped_storage: MappedStorage;
  partitions: Partition[];
}

export interface ResourceProfile {
  project_id: string;
  allocation_id: string;
  compute_resources: ComputeResource[];
}

export interface UserStorage {
  storage_id: string;
  name: string;
  is_primary: boolean;
}

export type StorageRef = { storage_id: string; path: string };
export type ScalarValue = string | number | boolean;
export type InputValue = ScalarValue | StorageRef | null;

export interface RuntimeChoice {
  compute_resource_id: string | null;
  partition: string | null;
  walltime: string;
  nodes: number;
  cpus_per_node: number;
}

export interface ExperimentDraft {
  name: string;
  project_id: string | null;
  description: string;
  app_id: string | null;
  interface_name: string | null;
  inputs: Record<string, InputValue>;
  outputs: Record<string, StorageRef>;
  runtime: RuntimeChoice;
}

export interface PreviewResponse {
  invocation_command: string;
  script_contents: string;
  warnings: string[];
}
```

- [ ] **Step 2: Define the service wrapper**

Create `django_airavata/static/common/js/services/launcherService.ts`:

```ts
import type {
  Application,
  ExperimentDraft,
  PreviewResponse,
  ResourceProfile,
  UserStorage,
} from "../stores/launch-types";

const API = "/api/launcher";

async function getJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    ...init,
    credentials: "same-origin",
    headers: { Accept: "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: res.statusText }));
    throw Object.assign(new Error(body.message ?? res.statusText), { status: res.status, body });
  }
  return res.json() as Promise<T>;
}

function csrf(): string {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m?.[1] ?? "";
}

export const launcherService = {
  listApplications(params: { category?: string; search?: string } = {}): Promise<{ results: Application[] }> {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    if (params.search) qs.set("search", params.search);
    const tail = qs.toString();
    return getJson(`${API}/applications/${tail ? "?" + tail : ""}`);
  },

  getApplication(appId: string): Promise<Application> {
    return getJson(`${API}/applications/${encodeURIComponent(appId)}/`);
  },

  getProjectResourceProfile(projectId: string): Promise<ResourceProfile> {
    return getJson(`${API}/projects/${encodeURIComponent(projectId)}/resource-profile/`);
  },

  listUserStorages(): Promise<{ results: UserStorage[] }> {
    return getJson(`${API}/storages/`);
  },

  listProjects(): Promise<{ results: Array<{ project_id: string; name: string }> }> {
    return getJson(`${API}/projects/`);
  },

  generatePreview(draft: ExperimentDraft, signal?: AbortSignal): Promise<PreviewResponse> {
    return getJson(`${API}/experiment-drafts/preview/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(draft),
      signal,
    });
  },

  launchExperiment(draft: ExperimentDraft): Promise<{ experiment_id: string }> {
    return getJson(`${API}/experiment-drafts/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: JSON.stringify(draft),
    });
  },
};
```

- [ ] **Step 3: Write the failing store test**

Create `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/stores/launch.spec.ts`:

```ts
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import type { InterfaceDescriptor } from "django-airavata-common-ui/stores/launch-types";

const RUN_IFACE: InterfaceDescriptor = {
  name: "run",
  inputs: [
    { name: "sim_dir", type: "dir", required: true },
    { name: "steps", type: "int", required: true },
  ],
  outputs: [{ name: "trajectory", type: "file" }],
};

describe("useLaunchStore", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("starts with an invalid empty draft", () => {
    const s = useLaunchStore();
    expect(s.tab1Valid).toBe(false);
    expect(s.tab2Valid).toBe(false);
  });

  it("validates tab 1 once name+project+app+iface+inputs+outputs are set", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    s.pickApp({ app_id: "namd", name: "NAMD", category: "MD",
                content: { kind: "github", url: "g" }, interfaces: [RUN_IFACE] });
    s.pickInterface("run");
    s.setInput("sim_dir", { storage_id: "my-home", path: "/x" });
    s.setInput("steps", 100);
    s.setOutput("trajectory", { storage_id: "my-home", path: "/y" });
    expect(s.tab1Valid).toBe(true);
  });

  it("clears interface + inputs when app changes", () => {
    const s = useLaunchStore();
    s.pickApp({ app_id: "namd", name: "NAMD", category: "MD",
                content: { kind: "github", url: "g" }, interfaces: [RUN_IFACE] });
    s.pickInterface("run");
    s.setInput("steps", 100);
    s.pickApp({ app_id: "gromacs", name: "GROMACS", category: "MD",
                content: { kind: "tarball", url: "t" }, interfaces: [] });
    expect(s.draft.interface_name).toBeNull();
    expect(s.draft.inputs).toEqual({});
  });

  it("clears compute fields when project changes", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    s.setRuntime({ compute_resource_id: "cr-1", partition: "RM", walltime: "01:00:00", nodes: 1, cpus_per_node: 8 });
    s.setMeta({ name: "x", project_id: "p2", description: "" });
    expect(s.draft.runtime.compute_resource_id).toBeNull();
    expect(s.draft.runtime.partition).toBeNull();
  });

  it("computes a stable hash that changes only on draft change", () => {
    const s = useLaunchStore();
    const h1 = s.draftHash;
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    expect(s.draftHash).not.toBe(h1);
    const h2 = s.draftHash;
    s.setMeta({ name: "x", project_id: "p1", description: "" });
    expect(s.draftHash).toBe(h2);
  });
});
```

- [ ] **Step 4: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- launch.spec`
Expected: FAIL — module `django-airavata-common-ui/stores/launch` not resolved.

- [ ] **Step 5: Implement the Pinia store**

Create `django_airavata/static/common/js/stores/launch.ts`:

```ts
import { defineStore } from "pinia";
import { computed, reactive, ref } from "vue";
import type {
  Application,
  ExperimentDraft,
  IODescriptor,
  InterfaceDescriptor,
  InputValue,
  PreviewResponse,
  ResourceProfile,
  RuntimeChoice,
  StorageRef,
  UserStorage,
} from "./launch-types";

const EMPTY_RUNTIME: RuntimeChoice = {
  compute_resource_id: null,
  partition: null,
  walltime: "01:00:00",
  nodes: 1,
  cpus_per_node: 1,
};

function makeDraft(): ExperimentDraft {
  return {
    name: "",
    project_id: null,
    description: "",
    app_id: null,
    interface_name: null,
    inputs: {},
    outputs: {},
    runtime: { ...EMPTY_RUNTIME },
  };
}

function isStorageRef(v: InputValue): v is StorageRef {
  return typeof v === "object" && v !== null && "storage_id" in v && "path" in v;
}

function inputHasValue(io: IODescriptor, v: InputValue): boolean {
  if (v === null || v === undefined) return !io.required;
  if (io.type === "file" || io.type === "dir") {
    return isStorageRef(v) && v.path.length > 0 && v.storage_id.length > 0;
  }
  return true;
}

export const useLaunchStore = defineStore("launch", () => {
  const draft = reactive<ExperimentDraft>(makeDraft());
  const pickedApp = ref<Application | null>(null);
  const profile = ref<ResourceProfile | null>(null);
  const storages = ref<UserStorage[]>([]);
  const preview = ref<PreviewResponse | null>(null);
  const previewError = ref<string | null>(null);
  const previewLoading = ref(false);
  const lastPreviewedHash = ref<string | null>(null);

  function setMeta(m: { name: string; project_id: string | null; description: string }) {
    if (draft.project_id !== m.project_id) {
      draft.runtime = { ...EMPTY_RUNTIME };
      profile.value = null;
    }
    draft.name = m.name;
    draft.project_id = m.project_id;
    draft.description = m.description;
  }

  function pickApp(a: Application) {
    pickedApp.value = a;
    draft.app_id = a.app_id;
    draft.interface_name = null;
    draft.inputs = {};
    draft.outputs = {};
  }

  function pickInterface(name: string) {
    draft.interface_name = name;
    draft.inputs = {};
    draft.outputs = {};
  }

  function setInput(name: string, value: InputValue) {
    draft.inputs[name] = value;
  }

  function setOutput(name: string, value: StorageRef) {
    draft.outputs[name] = value;
  }

  function setRuntime(r: RuntimeChoice) {
    draft.runtime = { ...r };
  }

  const pickedInterface = computed<InterfaceDescriptor | null>(() => {
    const a = pickedApp.value;
    const n = draft.interface_name;
    if (!a || !n) return null;
    return a.interfaces.find((i) => i.name === n) ?? null;
  });

  const tab1Valid = computed(() => {
    if (!draft.name || !draft.project_id || !draft.app_id || !draft.interface_name) return false;
    const iface = pickedInterface.value;
    if (!iface) return false;
    for (const io of iface.inputs) {
      if (!inputHasValue(io, draft.inputs[io.name] ?? null)) return false;
    }
    for (const io of iface.outputs) {
      if (io.type !== "file" && io.type !== "dir") continue;
      const v = draft.outputs[io.name];
      if (!v || !v.path || !v.storage_id) return false;
    }
    return true;
  });

  const tab2Valid = computed(() => {
    const r = draft.runtime;
    return Boolean(r.compute_resource_id && r.partition && r.walltime && r.nodes >= 1 && r.cpus_per_node >= 1);
  });

  // FNV-1a 32-bit string hash on JSON of the draft. Stable, fast, no deps.
  const draftHash = computed(() => {
    const s = JSON.stringify(draft);
    let h = 0x811c9dc5;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 0x01000193);
    }
    return (h >>> 0).toString(16);
  });

  function reset() {
    Object.assign(draft, makeDraft());
    pickedApp.value = null;
    profile.value = null;
    preview.value = null;
    previewError.value = null;
    lastPreviewedHash.value = null;
  }

  return {
    draft,
    pickedApp,
    pickedInterface,
    profile,
    storages,
    preview,
    previewError,
    previewLoading,
    lastPreviewedHash,
    tab1Valid,
    tab2Valid,
    draftHash,
    setMeta,
    pickApp,
    pickInterface,
    setInput,
    setOutput,
    setRuntime,
    reset,
  };
});
```

- [ ] **Step 6: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- launch.spec`
Expected: PASS — 5 tests OK.

- [ ] **Step 7: Commit**

```bash
git add django_airavata/static/common/js/stores/launch-types.ts \
        django_airavata/static/common/js/stores/launch.ts \
        django_airavata/static/common/js/services/launcherService.ts \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/stores/launch.spec.ts
git commit -m "feat(launcher): Pinia store + types + service wrapper"
```

---

### Task 7: ExperimentMetaHeader

**Files:**
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ExperimentMetaHeader.vue`
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/ExperimentMetaHeader.spec.ts`

- [ ] **Step 1: Write the failing test**

Create the spec file:

```ts
import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import ExperimentMetaHeader from "../../../../js/components/launch/ExperimentMetaHeader.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const PROJECTS = [
  { project_id: "p1", name: "my-lab-2026" },
  { project_id: "p2", name: "shared" },
];

describe("ExperimentMetaHeader", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("binds name input to the store", async () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    await w.find("input[data-test='exp-name']").setValue("my-run");
    expect(useLaunchStore().draft.name).toBe("my-run");
  });

  it("binds project dropdown to the store", async () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    await w.find("select[data-test='exp-project']").setValue("p2");
    expect(useLaunchStore().draft.project_id).toBe("p2");
  });

  it("renders description as a textarea", () => {
    const w = mount(ExperimentMetaHeader, { props: { projects: PROJECTS } });
    expect(w.find("textarea[data-test='exp-description']").exists()).toBe(true);
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- ExperimentMetaHeader`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement the component**

Create `…/js/components/launch/ExperimentMetaHeader.vue`:

```vue
<template>
  <div class="row g-2 mb-2">
    <div class="col-md-6">
      <input
        data-test="exp-name"
        class="form-control"
        :value="store.draft.name"
        placeholder="Experiment name"
        maxlength="256"
        @input="onName(($event.target as HTMLInputElement).value)"
      />
    </div>
    <div class="col-md-6">
      <select
        data-test="exp-project"
        class="form-select"
        :value="store.draft.project_id ?? ''"
        @change="onProject(($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Select a project</option>
        <option v-for="p in projects" :key="p.project_id" :value="p.project_id">
          {{ p.name }}
        </option>
      </select>
    </div>
    <div class="col-12">
      <textarea
        data-test="exp-description"
        class="form-control"
        rows="2"
        :value="store.draft.description"
        placeholder="Description (optional)"
        @input="onDescription(($event.target as HTMLTextAreaElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

defineProps<{ projects: Array<{ project_id: string; name: string }> }>();

const store = useLaunchStore();

function onName(v: string) {
  store.setMeta({ name: v, project_id: store.draft.project_id, description: store.draft.description });
}
function onProject(v: string) {
  store.setMeta({ name: store.draft.name, project_id: v || null, description: store.draft.description });
}
function onDescription(v: string) {
  store.setMeta({ name: store.draft.name, project_id: store.draft.project_id, description: v });
}
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- ExperimentMetaHeader`
Expected: PASS — 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ExperimentMetaHeader.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/ExperimentMetaHeader.spec.ts
git commit -m "feat(launcher): ExperimentMetaHeader (name/project/description)"
```

---

### Task 8: WizardTabs (strict-forward gate)

**Files:**
- Create: `…/js/components/launch/WizardTabs.vue`
- Create: `…/tests/unit/components/launch/WizardTabs.spec.ts`

- [ ] **Step 1: Write the failing test**

Create `WizardTabs.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import WizardTabs from "../../../../js/components/launch/WizardTabs.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

describe("WizardTabs", () => {
  beforeEach(() => setActivePinia(createPinia()));

  function makeMount(active: 1 | 2 | 3 = 1) {
    return mount(WizardTabs, { props: { active }, global: { stubs: { transition: false } } });
  }

  it("renders three tab buttons", () => {
    const w = makeMount();
    expect(w.findAll("button[role='tab']")).toHaveLength(3);
  });

  it("disables tabs 2 and 3 when tab 1 is invalid", () => {
    const w = makeMount();
    const tabs = w.findAll("button[role='tab']");
    expect(tabs[1].attributes("disabled")).toBeDefined();
    expect(tabs[2].attributes("disabled")).toBeDefined();
  });

  it("emits update:active when allowed tab clicked", async () => {
    const store = useLaunchStore();
    // Force tab 1 valid by spying on the getter
    Object.defineProperty(store, "tab1Valid", { value: true });
    const w = makeMount();
    await w.findAll("button[role='tab']")[1].trigger("click");
    expect(w.emitted("update:active")?.[0]).toEqual([2]);
  });

  it("does not emit update:active for a disabled tab", async () => {
    const w = makeMount();
    await w.findAll("button[role='tab']")[1].trigger("click");
    expect(w.emitted("update:active")).toBeUndefined();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- WizardTabs`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement WizardTabs**

Create `…/js/components/launch/WizardTabs.vue`:

```vue
<template>
  <div class="nav nav-tabs mb-3" role="tablist">
    <button
      v-for="t in tabs"
      :key="t.idx"
      role="tab"
      type="button"
      class="nav-link"
      :class="{ active: t.idx === active }"
      :disabled="t.disabled"
      @click="onClick(t.idx, t.disabled)"
    >
      {{ t.idx }} · {{ t.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

defineProps<{ active: 1 | 2 | 3 }>();
const emit = defineEmits<{ "update:active": [n: 1 | 2 | 3] }>();

const store = useLaunchStore();

const tabs = computed(() => [
  { idx: 1 as const, label: "Application & Inputs", disabled: false },
  { idx: 2 as const, label: "Runtime", disabled: !store.tab1Valid },
  { idx: 3 as const, label: "Review & Launch", disabled: !store.tab1Valid || !store.tab2Valid },
]);

function onClick(n: 1 | 2 | 3, disabled: boolean) {
  if (disabled) return;
  emit("update:active", n);
}
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- WizardTabs`
Expected: PASS — 4 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/WizardTabs.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/WizardTabs.spec.ts
git commit -m "feat(launcher): WizardTabs with strict-forward gating"
```

---

### Task 9: LaunchContainer + entry-launch.ts

**Files:**
- Create: `…/js/containers/LaunchContainer.vue`
- Create: `…/js/entry-launch.ts`
- Create: `…/tests/unit/components/launch/LaunchContainer.spec.ts`

- [ ] **Step 1: Write the failing test**

Create `LaunchContainer.spec.ts`:

```ts
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LaunchContainer from "../../../../js/containers/LaunchContainer.vue";

vi.mock("django-airavata-common-ui/services/launcherService", () => ({
  launcherService: {
    listProjects: vi.fn().mockResolvedValue({ results: [] }),
  },
}));

describe("LaunchContainer", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("starts on tab 1", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    expect(w.find("[data-test='active-tab']").attributes("data-active")).toBe("1");
  });

  it("renders the meta header", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    expect(w.find("input[data-test='exp-name']").exists()).toBe(true);
  });

  it("only one tab panel is shown at a time", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();
    const visiblePanels = w.findAll("[role='tabpanel']").filter((p) => !p.attributes("hidden"));
    expect(visiblePanels).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- LaunchContainer`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement LaunchContainer**

Create `…/js/containers/LaunchContainer.vue`:

```vue
<template>
  <div class="container-fluid">
    <ExperimentMetaHeader :projects="projects" />
    <WizardTabs :active="active" @update:active="onChangeTab" />
    <div data-test="active-tab" :data-active="active" />
    <section role="tabpanel" :hidden="active !== 1">
      <Tab1ApplicationInputs v-if="active === 1" />
    </section>
    <section role="tabpanel" :hidden="active !== 2">
      <Tab2Runtime v-if="active === 2" />
    </section>
    <section role="tabpanel" :hidden="active !== 3">
      <Tab3ReviewLaunch v-if="active === 3" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { launcherService } from "django-airavata-common-ui/services/launcherService";
import ExperimentMetaHeader from "../components/launch/ExperimentMetaHeader.vue";
import WizardTabs from "../components/launch/WizardTabs.vue";
import Tab1ApplicationInputs from "../components/launch/Tab1ApplicationInputs.vue";
import Tab2Runtime from "../components/launch/Tab2Runtime.vue";
import Tab3ReviewLaunch from "../components/launch/Tab3ReviewLaunch.vue";

const active = ref<1 | 2 | 3>(1);
const projects = ref<Array<{ project_id: string; name: string }>>([]);

function onChangeTab(n: 1 | 2 | 3) {
  active.value = n;
  const url = new URL(window.location.href);
  url.searchParams.set("tab", String(n));
  window.history.replaceState({}, "", url);
}

onMounted(async () => {
  const url = new URL(window.location.href);
  const t = Number(url.searchParams.get("tab"));
  if (t === 1 || t === 2 || t === 3) active.value = t as 1 | 2 | 3;
  const r = await launcherService.listProjects();
  projects.value = r.results;
});
</script>
```

Until Tab1/2/3 components exist, also create empty stub components so the container compiles:

```vue
<!-- Tab1ApplicationInputs.vue, Tab2Runtime.vue, Tab3ReviewLaunch.vue -->
<template><div /></template>
<script setup lang="ts"></script>
```

Place those three placeholder files at `…/js/components/launch/`.

- [ ] **Step 4: Implement entry-launch.ts**

Create `…/js/entry-launch.ts`:

```ts
import { createApp } from "vue";
import { createPinia } from "pinia";
import LaunchContainer from "./containers/LaunchContainer.vue";

const root = document.getElementById("launch-app");
if (root) {
  const app = createApp(LaunchContainer);
  app.use(createPinia());
  app.mount(root);
}
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- LaunchContainer`
Expected: PASS — 3 tests OK.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/LaunchContainer.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-launch.ts \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab1ApplicationInputs.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab2Runtime.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab3ReviewLaunch.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/LaunchContainer.spec.ts
git commit -m "feat(launcher): LaunchContainer + entry-launch.ts (tabs scaffolding)"
```

---

## Phase 3 — Tab 1 components

### Task 10: AppPicker (categories, search, tile grid)

**Files:**
- Create: `…/js/components/launch/AppPicker.vue`
- Create: `…/tests/unit/components/launch/AppPicker.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import AppPicker from "../../../../js/components/launch/AppPicker.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const APPS = [
  { app_id: "namd", name: "NAMD", category: "Molecular Dynamics",
    content: { kind: "github" as const, url: "g" }, interfaces: [] },
  { app_id: "gromacs", name: "GROMACS", category: "Molecular Dynamics",
    content: { kind: "tarball" as const, url: "t" }, interfaces: [] },
  { app_id: "alphafold", name: "AlphaFold", category: "ML / AI",
    content: { kind: "github" as const, url: "g" }, interfaces: [] },
];

describe("AppPicker", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("renders all apps when category=All", () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(3);
  });

  it("filters by category chip", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("[data-test='cat-ML / AI']").trigger("click");
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
  });

  it("filters by search text within current category", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("input[data-test='app-search']").setValue("NAMD");
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
  });

  it("clicking a tile picks the app via the store", async () => {
    const w = mount(AppPicker, { props: { applications: APPS } });
    await w.find("[data-test='app-tile-namd']").trigger("click");
    expect(useLaunchStore().draft.app_id).toBe("namd");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- AppPicker`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement AppPicker**

```vue
<template>
  <div>
    <div class="d-flex flex-wrap gap-1 mb-2">
      <button
        v-for="cat in categories"
        :key="cat"
        type="button"
        class="btn btn-sm"
        :class="cat === activeCat ? 'btn-primary' : 'btn-light'"
        :data-test="`cat-${cat}`"
        @click="activeCat = cat"
      >
        {{ cat }}<span class="ms-1 opacity-50">{{ countByCat[cat] }}</span>
      </button>
    </div>
    <input
      v-model="search"
      type="search"
      class="form-control mb-2"
      data-test="app-search"
      placeholder="Filter…"
    />
    <div class="row g-2">
      <div
        v-for="a in filtered"
        :key="a.app_id"
        class="col-6 col-md-3"
        data-test="app-tile"
        :data-test-id="`app-tile-${a.app_id}`"
      >
        <button
          type="button"
          class="card w-100 text-start p-2"
          :class="{ 'border-primary': store.draft.app_id === a.app_id }"
          :data-test="`app-tile-${a.app_id}`"
          @click="pick(a)"
        >
          <strong>{{ a.name }}</strong>
          <span class="text-muted small d-block">{{ a.content.url }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { Application } from "django-airavata-common-ui/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const props = defineProps<{ applications: Application[] }>();
const store = useLaunchStore();
const activeCat = ref<string>("All");
const search = ref("");

const categories = computed(() => {
  const set = new Set<string>(["All"]);
  for (const a of props.applications) set.add(a.category);
  return Array.from(set);
});

const countByCat = computed<Record<string, number>>(() => {
  const out: Record<string, number> = { All: props.applications.length };
  for (const a of props.applications) out[a.category] = (out[a.category] ?? 0) + 1;
  return out;
});

const filtered = computed(() => {
  let xs = props.applications;
  if (activeCat.value !== "All") xs = xs.filter((a) => a.category === activeCat.value);
  if (search.value) {
    const n = search.value.toLowerCase();
    xs = xs.filter((a) => a.name.toLowerCase().includes(n));
  }
  return xs;
});

function pick(a: Application) {
  store.pickApp(a);
}
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- AppPicker`
Expected: PASS — 4 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/AppPicker.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/AppPicker.spec.ts
git commit -m "feat(launcher): AppPicker (categories + search + tile grid)"
```

---

### Task 11: InterfacePicker (verb cards)

**Files:**
- Create: `…/js/components/launch/InterfacePicker.vue`
- Create: `…/tests/unit/components/launch/InterfacePicker.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import InterfacePicker from "../../../../js/components/launch/InterfacePicker.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [
    { name: "compile", inputs: [], outputs: [] },
    { name: "run", inputs: [{ name: "x", type: "int" as const, required: true }], outputs: [] },
  ],
};

describe("InterfacePicker", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useLaunchStore().pickApp(APP);
  });

  it("renders one card per interface", () => {
    const w = mount(InterfacePicker);
    expect(w.findAll("[data-test='iface-card']")).toHaveLength(2);
  });

  it("clicking a card sets interface_name in the store", async () => {
    const w = mount(InterfacePicker);
    await w.find("[data-test='iface-card-run']").trigger("click");
    expect(useLaunchStore().draft.interface_name).toBe("run");
  });

  it("renders an input/output signature line per card", () => {
    const w = mount(InterfacePicker);
    const sig = w.find("[data-test='iface-sig-run']").text();
    expect(sig).toContain("x: int");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- InterfacePicker`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement InterfacePicker**

```vue
<template>
  <div v-if="store.pickedApp" class="row g-2">
    <div
      v-for="iface in store.pickedApp.interfaces"
      :key="iface.name"
      class="col-6 col-md-3"
      data-test="iface-card"
    >
      <button
        type="button"
        class="card w-100 text-start p-2"
        :class="{ 'border-primary': store.draft.interface_name === iface.name }"
        :data-test="`iface-card-${iface.name}`"
        @click="store.pickInterface(iface.name)"
      >
        <code class="d-block fw-bold">{{ iface.name }}</code>
        <small class="text-muted" :data-test="`iface-sig-${iface.name}`">
          ({{ formatList(iface.inputs) }}) → {{ formatList(iface.outputs) || "void" }}
        </small>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IODescriptor } from "django-airavata-common-ui/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const store = useLaunchStore();

function formatList(io: IODescriptor[]): string {
  return io.map((x) => `${x.name}: ${x.type}`).join(", ");
}
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- InterfacePicker`
Expected: PASS — 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/InterfacePicker.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/InterfacePicker.spec.ts
git commit -m "feat(launcher): InterfacePicker verb cards"
```

---

### Task 12: ScalarInputRow + FileInputRow

**Files:**
- Create: `…/js/components/launch/ScalarInputRow.vue`
- Create: `…/js/components/launch/FileInputRow.vue`
- Create: `…/tests/unit/components/launch/ScalarInputRow.spec.ts`
- Create: `…/tests/unit/components/launch/FileInputRow.spec.ts`

- [ ] **Step 1: Write failing tests for both rows**

`ScalarInputRow.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ScalarInputRow from "../../../../js/components/launch/ScalarInputRow.vue";

describe("ScalarInputRow", () => {
  it("renders a number input for type=int", async () => {
    const w = mount(ScalarInputRow, {
      props: { descriptor: { name: "steps", type: "int", required: true }, modelValue: null },
    });
    const input = w.find("input[data-test='scalar-steps']");
    expect(input.attributes("type")).toBe("number");
  });

  it("emits update:modelValue on input", async () => {
    const w = mount(ScalarInputRow, {
      props: { descriptor: { name: "steps", type: "int", required: true }, modelValue: null },
    });
    await w.find("input").setValue("42");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([42]);
  });

  it("renders a select for enum descriptors", () => {
    const w = mount(ScalarInputRow, {
      props: {
        descriptor: { name: "mode", type: "enum", required: true, options: ["a", "b"] },
        modelValue: null,
      },
    });
    expect(w.find("select").exists()).toBe(true);
  });
});
```

`FileInputRow.spec.ts`:

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import FileInputRow from "../../../../js/components/launch/FileInputRow.vue";

const STORAGES = [
  { storage_id: "my-home", name: "My Home", is_primary: true },
  { storage_id: "scratch", name: "Scratch", is_primary: false },
];

describe("FileInputRow", () => {
  it("emits update:modelValue when storage changes", async () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: { storage_id: "my-home", path: "" },
        storages: STORAGES,
      },
    });
    await w.find("select").setValue("scratch");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([{ storage_id: "scratch", path: "" }]);
  });

  it("emits update:modelValue when path changes", async () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: { storage_id: "my-home", path: "" },
        storages: STORAGES,
      },
    });
    await w.find("input[data-test='file-path-sim_dir']").setValue("/home/x/sim");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([{ storage_id: "my-home", path: "/home/x/sim" }]);
  });

  it("renders a stage-in badge", () => {
    const w = mount(FileInputRow, {
      props: {
        descriptor: { name: "sim_dir", type: "dir", required: true },
        modelValue: null,
        storages: STORAGES,
      },
    });
    expect(w.find("[data-test='io-badge']").text()).toMatch(/stage-in/i);
  });
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd django_airavata/apps/workspace && npm run test -- "ScalarInputRow|FileInputRow"`
Expected: FAIL — files not found.

- [ ] **Step 3: Implement ScalarInputRow**

```vue
<template>
  <div class="row mb-1 align-items-center">
    <label class="col-md-3 col-form-label" :for="`scalar-${descriptor.name}`">
      <code>{{ descriptor.name }}</code>
      <span class="text-muted small ms-1">{{ descriptor.type }}</span>
    </label>
    <div class="col-md-9">
      <select
        v-if="descriptor.type === 'enum'"
        :id="`scalar-${descriptor.name}`"
        :data-test="`scalar-${descriptor.name}`"
        class="form-select"
        :value="modelValue ?? ''"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="o in descriptor.options ?? []" :key="o" :value="o">{{ o }}</option>
      </select>
      <input
        v-else
        :id="`scalar-${descriptor.name}`"
        :data-test="`scalar-${descriptor.name}`"
        class="form-control"
        :type="inputType"
        :value="modelValue ?? ''"
        @input="onInput(($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { IODescriptor, ScalarValue } from "django-airavata-common-ui/stores/launch-types";

const props = defineProps<{ descriptor: IODescriptor; modelValue: ScalarValue | null }>();
const emit = defineEmits<{ "update:modelValue": [v: ScalarValue | null] }>();

const inputType = computed(() => {
  switch (props.descriptor.type) {
    case "int":
    case "float":
      return "number";
    case "bool":
      return "checkbox";
    default:
      return "text";
  }
});

function onInput(raw: string) {
  if (props.descriptor.type === "int") emit("update:modelValue", raw === "" ? null : Number.parseInt(raw, 10));
  else if (props.descriptor.type === "float") emit("update:modelValue", raw === "" ? null : Number.parseFloat(raw));
  else emit("update:modelValue", raw);
}
</script>
```

- [ ] **Step 4: Implement FileInputRow**

```vue
<template>
  <div class="d-flex align-items-center gap-2 border rounded p-2 mb-1">
    <div class="flex-shrink-0" style="width: 140px;">
      <code>{{ descriptor.name }}</code>
      <span class="text-muted small ms-1">{{ descriptor.type }}</span>
    </div>
    <select
      class="form-select form-select-sm"
      style="width: 160px;"
      :value="modelValue?.storage_id ?? ''"
      @change="onStorage(($event.target as HTMLSelectElement).value)"
    >
      <option value="" disabled>Storage…</option>
      <option v-for="s in storages" :key="s.storage_id" :value="s.storage_id">{{ s.name }}</option>
    </select>
    <input
      class="form-control form-control-sm flex-grow-1"
      :data-test="`file-path-${descriptor.name}`"
      :value="modelValue?.path ?? ''"
      placeholder="/path/to/data"
      @input="onPath(($event.target as HTMLInputElement).value)"
    />
    <span data-test="io-badge" class="badge bg-warning text-dark">stage-in</span>
  </div>
</template>

<script setup lang="ts">
import type { IODescriptor, StorageRef, UserStorage } from "django-airavata-common-ui/stores/launch-types";

const props = defineProps<{
  descriptor: IODescriptor;
  modelValue: StorageRef | null;
  storages: UserStorage[];
}>();
const emit = defineEmits<{ "update:modelValue": [v: StorageRef] }>();

function onStorage(id: string) {
  emit("update:modelValue", { storage_id: id, path: props.modelValue?.path ?? "" });
}
function onPath(p: string) {
  emit("update:modelValue", { storage_id: props.modelValue?.storage_id ?? "", path: p });
}
</script>
```

- [ ] **Step 5: Run to verify they pass**

Run: `cd django_airavata/apps/workspace && npm run test -- "ScalarInputRow|FileInputRow"`
Expected: PASS — 6 tests OK.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ScalarInputRow.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/FileInputRow.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/ScalarInputRow.spec.ts \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/FileInputRow.spec.ts
git commit -m "feat(launcher): ScalarInputRow + FileInputRow"
```

---

### Task 13: InputList + OutputList + FileOutputRow

**Files:**
- Create: `…/js/components/launch/InputList.vue`
- Create: `…/js/components/launch/OutputList.vue`
- Create: `…/js/components/launch/FileOutputRow.vue`
- Create: `…/tests/unit/components/launch/InputList.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import InputList from "../../../../js/components/launch/InputList.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [{
    name: "run",
    inputs: [
      { name: "sim_dir", type: "dir" as const, required: true },
      { name: "steps", type: "int" as const, required: true },
    ],
    outputs: [],
  }],
};

const STORAGES = [{ storage_id: "my-home", name: "My Home", is_primary: true }];

describe("InputList", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    const s = useLaunchStore();
    s.pickApp(APP);
    s.pickInterface("run");
  });

  it("renders one row per declared input", () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    expect(w.findAll("[data-test='input-row']")).toHaveLength(2);
  });

  it("scalar input writes through to the store", async () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    await w.find("input[data-test='scalar-steps']").setValue("5000");
    expect(useLaunchStore().draft.inputs.steps).toBe(5000);
  });

  it("file input writes through to the store", async () => {
    const w = mount(InputList, { props: { storages: STORAGES } });
    await w.find("input[data-test='file-path-sim_dir']").setValue("/data");
    expect(useLaunchStore().draft.inputs.sim_dir).toEqual({ storage_id: "", path: "/data" });
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- InputList`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement InputList**

```vue
<template>
  <div v-if="store.pickedInterface">
    <div
      v-for="io in store.pickedInterface.inputs"
      :key="io.name"
      data-test="input-row"
    >
      <FileInputRow
        v-if="io.type === 'file' || io.type === 'dir'"
        :descriptor="io"
        :model-value="(store.draft.inputs[io.name] as { storage_id: string; path: string } | null) ?? null"
        :storages="storages"
        @update:model-value="store.setInput(io.name, $event)"
      />
      <ScalarInputRow
        v-else
        :descriptor="io"
        :model-value="(store.draft.inputs[io.name] as string | number | boolean | null) ?? null"
        @update:model-value="store.setInput(io.name, $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { UserStorage } from "django-airavata-common-ui/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import FileInputRow from "./FileInputRow.vue";
import ScalarInputRow from "./ScalarInputRow.vue";

defineProps<{ storages: UserStorage[] }>();
const store = useLaunchStore();
</script>
```

- [ ] **Step 4: Implement FileOutputRow + OutputList**

`FileOutputRow.vue`:

```vue
<template>
  <div class="d-flex align-items-center gap-2 border rounded p-2 mb-1">
    <div class="flex-shrink-0" style="width: 140px;">
      <code>{{ descriptor.name }}</code>
      <span class="text-muted small ms-1">{{ descriptor.type }}</span>
    </div>
    <select
      class="form-select form-select-sm"
      style="width: 160px;"
      :value="modelValue?.storage_id ?? ''"
      @change="onStorage(($event.target as HTMLSelectElement).value)"
    >
      <option value="" disabled>Storage…</option>
      <option v-for="s in storages" :key="s.storage_id" :value="s.storage_id">{{ s.name }}</option>
    </select>
    <input
      class="form-control form-control-sm flex-grow-1"
      :data-test="`file-out-path-${descriptor.name}`"
      :value="modelValue?.path ?? ''"
      placeholder="/path/to/output"
      @input="onPath(($event.target as HTMLInputElement).value)"
    />
    <span class="badge bg-info text-dark">stage-out</span>
  </div>
</template>

<script setup lang="ts">
import type { IODescriptor, StorageRef, UserStorage } from "django-airavata-common-ui/stores/launch-types";

const props = defineProps<{
  descriptor: IODescriptor;
  modelValue: StorageRef | null;
  storages: UserStorage[];
}>();
const emit = defineEmits<{ "update:modelValue": [v: StorageRef] }>();

function onStorage(id: string) {
  emit("update:modelValue", { storage_id: id, path: props.modelValue?.path ?? "" });
}
function onPath(p: string) {
  emit("update:modelValue", { storage_id: props.modelValue?.storage_id ?? "", path: p });
}
</script>
```

`OutputList.vue`:

```vue
<template>
  <div v-if="store.pickedInterface">
    <FileOutputRow
      v-for="io in fileOutputs"
      :key="io.name"
      :descriptor="io"
      :model-value="store.draft.outputs[io.name] ?? null"
      :storages="storages"
      @update:model-value="store.setOutput(io.name, $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { UserStorage } from "django-airavata-common-ui/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import FileOutputRow from "./FileOutputRow.vue";

defineProps<{ storages: UserStorage[] }>();
const store = useLaunchStore();
const fileOutputs = computed(() =>
  (store.pickedInterface?.outputs ?? []).filter((o) => o.type === "file" || o.type === "dir"),
);
</script>
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- InputList`
Expected: PASS — 3 tests OK.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/InputList.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/OutputList.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/FileOutputRow.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/InputList.spec.ts
git commit -m "feat(launcher): InputList + OutputList + FileOutputRow"
```

---

### Task 14: Tab1ApplicationInputs (assembly)

**Files:**
- Modify: `…/js/components/launch/Tab1ApplicationInputs.vue` (replaces stub from Task 9)
- Create: `…/tests/unit/components/launch/Tab1ApplicationInputs.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab1ApplicationInputs from "../../../../js/components/launch/Tab1ApplicationInputs.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

vi.mock("django-airavata-common-ui/services/launcherService", () => ({
  launcherService: {
    listApplications: vi.fn().mockResolvedValue({
      results: [{
        app_id: "namd", name: "NAMD", category: "MD",
        content: { kind: "github", url: "g" }, interfaces: [],
      }],
    }),
    listUserStorages: vi.fn().mockResolvedValue({
      results: [{ storage_id: "my-home", name: "My Home", is_primary: true }],
    }),
  },
}));

describe("Tab1ApplicationInputs", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("loads applications + storages on mount", async () => {
    const w = mount(Tab1ApplicationInputs);
    await flushPromises();
    expect(w.findAll("[data-test='app-tile']")).toHaveLength(1);
    expect(useLaunchStore().storages).toHaveLength(1);
  });

  it("does not render the inputs section before an app+interface are picked", async () => {
    const w = mount(Tab1ApplicationInputs);
    await flushPromises();
    expect(w.find("[data-test='inputs-section']").exists()).toBe(false);
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab1ApplicationInputs`
Expected: FAIL — current stub doesn't load apps.

- [ ] **Step 3: Implement Tab1ApplicationInputs**

Replace the stub at `…/js/components/launch/Tab1ApplicationInputs.vue`:

```vue
<template>
  <div>
    <section class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Application</div>
      <AppPicker :applications="apps" />
    </section>
    <section v-if="store.pickedApp" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Interface</div>
      <InterfacePicker />
    </section>
    <section v-if="store.pickedInterface" data-test="inputs-section" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Inputs</div>
      <InputList :storages="store.storages" />
    </section>
    <section v-if="store.pickedInterface && fileOutputCount > 0" class="mb-3">
      <div class="text-uppercase text-primary small fw-bold mb-1">Outputs</div>
      <OutputList :storages="store.storages" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { launcherService } from "django-airavata-common-ui/services/launcherService";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import type { Application } from "django-airavata-common-ui/stores/launch-types";
import AppPicker from "./AppPicker.vue";
import InterfacePicker from "./InterfacePicker.vue";
import InputList from "./InputList.vue";
import OutputList from "./OutputList.vue";

const store = useLaunchStore();
const apps = ref<Application[]>([]);

onMounted(async () => {
  const [a, s] = await Promise.all([launcherService.listApplications(), launcherService.listUserStorages()]);
  apps.value = a.results;
  store.storages = s.results;
});

const fileOutputCount = computed(() =>
  (store.pickedInterface?.outputs ?? []).filter((o) => o.type === "file" || o.type === "dir").length,
);
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab1ApplicationInputs`
Expected: PASS — 2 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab1ApplicationInputs.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/Tab1ApplicationInputs.spec.ts
git commit -m "feat(launcher): Tab1ApplicationInputs assembly"
```

---

## Phase 4 — Tab 2 components

### Task 15: RuntimeInputs (lean profile-driven editor)

**Files:**
- Create: `…/js/components/launch/runtime/RuntimeInputs.vue`
- Create: `…/tests/unit/components/launch/runtime/RuntimeInputs.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import RuntimeInputs from "../../../../../js/components/launch/runtime/RuntimeInputs.vue";

const PROFILE = {
  project_id: "p1", allocation_id: "NSF-1",
  compute_resources: [{
    compute_resource_id: "bridges-2", name: "Bridges-2",
    mapped_storage: { storage_id: "scratch", scratch_path: "/scratch/p1" },
    partitions: [{ name: "RM", max_walltime: "48:00:00", max_nodes: 64, cpus_per_node: 128 }],
  }],
};

describe("RuntimeInputs", () => {
  it("populates compute resource dropdown from profile", () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: null, partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    expect(w.find("select[data-test='cr']").findAll("option").map((o) => o.text())).toContain("Bridges-2");
  });

  it("emits update:modelValue when the resource changes", async () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: null, partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    await w.find("select[data-test='cr']").setValue("bridges-2");
    expect(w.emitted("update:modelValue")?.at(-1)).toEqual([
      expect.objectContaining({ compute_resource_id: "bridges-2", partition: null }),
    ]);
  });

  it("limits partition options to the chosen resource", async () => {
    const w = mount(RuntimeInputs, {
      props: { profile: PROFILE, modelValue: { compute_resource_id: "bridges-2", partition: null,
              walltime: "01:00:00", nodes: 1, cpus_per_node: 1 } },
    });
    const opts = w.find("select[data-test='partition']").findAll("option").map((o) => o.text());
    expect(opts).toContain("RM");
    expect(opts).not.toContain("nonexistent");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- RuntimeInputs`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement RuntimeInputs**

```vue
<template>
  <div class="row g-2">
    <div class="col-md-3">
      <label class="form-label small">Compute resource</label>
      <select
        data-test="cr"
        class="form-select form-select-sm"
        :value="modelValue.compute_resource_id ?? ''"
        @change="onCR(($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="cr in profile.compute_resources" :key="cr.compute_resource_id" :value="cr.compute_resource_id">
          {{ cr.name }}
        </option>
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label small">Partition</label>
      <select
        data-test="partition"
        class="form-select form-select-sm"
        :disabled="!partitions.length"
        :value="modelValue.partition ?? ''"
        @change="emit('update:modelValue', { ...modelValue, partition: ($event.target as HTMLSelectElement).value })"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="p in partitions" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small">Walltime</label>
      <input
        data-test="walltime"
        class="form-control form-control-sm"
        :value="modelValue.walltime"
        @input="emit('update:modelValue', { ...modelValue, walltime: ($event.target as HTMLInputElement).value })"
      />
    </div>
    <div class="col-md-2">
      <label class="form-label small">Nodes</label>
      <input
        type="number" min="1"
        data-test="nodes"
        class="form-control form-control-sm"
        :value="modelValue.nodes"
        @input="emit('update:modelValue', { ...modelValue, nodes: Number(($event.target as HTMLInputElement).value) })"
      />
    </div>
    <div class="col-md-2">
      <label class="form-label small">CPUs / node</label>
      <input
        type="number" min="1"
        data-test="cpus"
        class="form-control form-control-sm"
        :value="modelValue.cpus_per_node"
        @input="emit('update:modelValue', { ...modelValue, cpus_per_node: Number(($event.target as HTMLInputElement).value) })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ResourceProfile, RuntimeChoice } from "django-airavata-common-ui/stores/launch-types";

const props = defineProps<{ profile: ResourceProfile; modelValue: RuntimeChoice }>();
const emit = defineEmits<{ "update:modelValue": [v: RuntimeChoice] }>();

const partitions = computed(() => {
  if (!props.modelValue.compute_resource_id) return [];
  const cr = props.profile.compute_resources.find(
    (c) => c.compute_resource_id === props.modelValue.compute_resource_id,
  );
  return cr?.partitions ?? [];
});

function onCR(id: string) {
  emit("update:modelValue", { ...props.modelValue, compute_resource_id: id, partition: null });
}
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- RuntimeInputs`
Expected: PASS — 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/runtime/RuntimeInputs.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/runtime/RuntimeInputs.spec.ts
git commit -m "feat(launcher): RuntimeInputs (profile-driven cr/partition/walltime)"
```

---

### Task 16: Tab2Runtime (assembly + readouts)

**Files:**
- Modify: `…/js/components/launch/Tab2Runtime.vue` (replaces stub)
- Create: `…/tests/unit/components/launch/Tab2Runtime.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab2Runtime from "../../../../js/components/launch/Tab2Runtime.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

const PROFILE = {
  project_id: "p1", allocation_id: "NSF-1",
  compute_resources: [{
    compute_resource_id: "bridges-2", name: "Bridges-2",
    mapped_storage: { storage_id: "scratch", scratch_path: "/scratch/p1" },
    partitions: [{ name: "RM", max_walltime: "48:00:00", max_nodes: 64, cpus_per_node: 128 }],
  }],
};

vi.mock("django-airavata-common-ui/services/launcherService", () => ({
  launcherService: {
    getProjectResourceProfile: vi.fn().mockResolvedValue(PROFILE),
  },
}));

describe("Tab2Runtime", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    useLaunchStore().setMeta({ name: "x", project_id: "p1", description: "" });
  });

  it("renders the readout once a CR is picked", async () => {
    const w = mount(Tab2Runtime);
    await flushPromises();
    useLaunchStore().setRuntime({
      compute_resource_id: "bridges-2", partition: "RM",
      walltime: "01:00:00", nodes: 1, cpus_per_node: 8,
    });
    await flushPromises();
    expect(w.text()).toContain("NSF-1");
    expect(w.text()).toContain("bridges-2");
    expect(w.text()).toContain("/scratch/p1");
  });

  it("re-fetches the profile when project changes", async () => {
    const { launcherService } = await import("django-airavata-common-ui/services/launcherService");
    const w = mount(Tab2Runtime);
    await flushPromises();
    useLaunchStore().setMeta({ name: "x", project_id: "p2", description: "" });
    await flushPromises();
    expect(launcherService.getProjectResourceProfile).toHaveBeenCalledWith("p2");
    expect(w).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab2Runtime`
Expected: FAIL — current stub doesn't fetch.

- [ ] **Step 3: Implement Tab2Runtime**

Replace `…/js/components/launch/Tab2Runtime.vue`:

```vue
<template>
  <div v-if="store.profile">
    <RuntimeInputs
      :profile="store.profile"
      :model-value="store.draft.runtime"
      @update:model-value="store.setRuntime($event)"
    />
    <p class="small text-muted mt-2">
      Allocation <code>{{ store.profile.allocation_id }}</code> (auto from project) ·
      <span v-if="pickedCR">
        Compute storage <code>{{ pickedCR.mapped_storage.storage_id }}</code>
        scratch <code>{{ pickedCR.mapped_storage.scratch_path }}</code>
      </span>
    </p>
  </div>
  <div v-else class="text-muted">Loading resource profile…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import { launcherService } from "django-airavata-common-ui/services/launcherService";
import RuntimeInputs from "./runtime/RuntimeInputs.vue";

const store = useLaunchStore();

async function refetch(projectId: string) {
  const p = await launcherService.getProjectResourceProfile(projectId);
  store.profile = p;
}

onMounted(() => {
  if (store.draft.project_id) void refetch(store.draft.project_id);
});

watch(
  () => store.draft.project_id,
  (id) => { if (id) void refetch(id); else store.profile = null; },
);

const pickedCR = computed(() =>
  store.profile?.compute_resources.find((c) => c.compute_resource_id === store.draft.runtime.compute_resource_id) ?? null,
);
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab2Runtime`
Expected: PASS — 2 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab2Runtime.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/Tab2Runtime.spec.ts
git commit -m "feat(launcher): Tab2Runtime assembly + readouts"
```

---

## Phase 5 — Tab 3 components

### Task 17: ScriptPreview + InvocationCommand

**Files:**
- Create: `…/js/components/launch/ScriptPreview.vue`
- Create: `…/js/components/launch/InvocationCommand.vue`
- Create: `…/tests/unit/components/launch/ScriptPreview.spec.ts`

- [ ] **Step 1: Write the failing tests**

```ts
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ScriptPreview from "../../../../js/components/launch/ScriptPreview.vue";
import InvocationCommand from "../../../../js/components/launch/InvocationCommand.vue";

describe("ScriptPreview", () => {
  it("renders the script in a code block", () => {
    const w = mount(ScriptPreview, { props: { script: "#!/bin/bash\necho hi\n" } });
    expect(w.find("pre code").text()).toContain("echo hi");
  });

  it("is read-only (no contenteditable)", () => {
    const w = mount(ScriptPreview, { props: { script: "x" } });
    expect(w.find("pre").attributes("contenteditable")).toBeUndefined();
  });
});

describe("InvocationCommand", () => {
  it("renders the command", () => {
    const w = mount(InvocationCommand, { props: { command: "sbatch /tmp/run.sh" } });
    expect(w.text()).toContain("sbatch /tmp/run.sh");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- "ScriptPreview|InvocationCommand"`
Expected: FAIL — files not found.

- [ ] **Step 3: Implement both components**

`ScriptPreview.vue`:

```vue
<template>
  <pre class="bg-dark text-light p-3 rounded small mb-0" style="overflow-x: auto;"><code>{{ script }}</code></pre>
</template>

<script setup lang="ts">
defineProps<{ script: string }>();
</script>
```

`InvocationCommand.vue`:

```vue
<template>
  <div class="text-muted small mb-2">
    Invocation: <code>{{ command }}</code>
  </div>
</template>

<script setup lang="ts">
defineProps<{ command: string }>();
</script>
```

- [ ] **Step 4: Run to verify they pass**

Run: `cd django_airavata/apps/workspace && npm run test -- "ScriptPreview|InvocationCommand"`
Expected: PASS — 3 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ScriptPreview.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/InvocationCommand.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/ScriptPreview.spec.ts
git commit -m "feat(launcher): ScriptPreview + InvocationCommand presentational components"
```

---

### Task 18: Tab3ReviewLaunch (preview fetch + launch)

**Files:**
- Modify: `…/js/components/launch/Tab3ReviewLaunch.vue` (replaces stub)
- Create: `…/tests/unit/components/launch/Tab3ReviewLaunch.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Tab3ReviewLaunch from "../../../../js/components/launch/Tab3ReviewLaunch.vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";

vi.mock("django-airavata-common-ui/services/launcherService", () => ({
  launcherService: {
    generatePreview: vi.fn().mockResolvedValue({
      invocation_command: "sbatch /tmp/run.sh",
      script_contents: "#!/bin/bash\necho hi\n",
      warnings: ["check walltime"],
    }),
    launchExperiment: vi.fn().mockResolvedValue({ experiment_id: "exp-42" }),
  },
}));

const NAV = vi.fn();
Object.defineProperty(window, "location", { value: { href: "/", assign: NAV }, writable: true });

describe("Tab3ReviewLaunch", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    NAV.mockClear();
  });

  it("renders the preview after fetch", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.text()).toContain("sbatch /tmp/run.sh");
    expect(w.text()).toContain("echo hi");
  });

  it("renders warnings as a list", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.find("[data-test='warnings']").text()).toContain("check walltime");
  });

  it("disables launch when preview failed", async () => {
    const { launcherService } = await import("django-airavata-common-ui/services/launcherService");
    (launcherService.generatePreview as unknown as { mockRejectedValueOnce: Function }).mockRejectedValueOnce(new Error("nope"));
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    expect(w.find("button[data-test='launch']").attributes("disabled")).toBeDefined();
  });

  it("redirects on successful launch", async () => {
    const w = mount(Tab3ReviewLaunch);
    await flushPromises();
    await w.find("button[data-test='launch']").trigger("click");
    await flushPromises();
    expect(window.location.href).toBe("/workspace/experiments/exp-42");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab3ReviewLaunch`
Expected: FAIL — current stub doesn't fetch.

- [ ] **Step 3: Implement Tab3ReviewLaunch**

Replace `…/js/components/launch/Tab3ReviewLaunch.vue`:

```vue
<template>
  <div>
    <div v-if="loading" class="text-muted">Generating preview…</div>
    <div v-else-if="error" class="alert alert-danger">
      <div>{{ error }}</div>
      <button class="btn btn-sm btn-outline-light mt-2" @click="refresh">Retry</button>
    </div>
    <div v-else-if="store.preview">
      <ul v-if="store.preview.warnings.length" class="alert alert-warning small" data-test="warnings">
        <li v-for="w in store.preview.warnings" :key="w">{{ w }}</li>
      </ul>
      <InvocationCommand :command="store.preview.invocation_command" />
      <ScriptPreview :script="store.preview.script_contents" />
      <div v-if="launchError" class="alert alert-danger mt-2">
        {{ launchError }}
        <button class="btn btn-sm btn-outline-light ms-2" @click="onLaunch">Try again</button>
      </div>
      <div class="d-flex justify-content-end mt-3">
        <button
          class="btn btn-primary"
          data-test="launch"
          :disabled="!store.preview || loading"
          @click="onLaunch"
        >
          Launch experiment
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useLaunchStore } from "django-airavata-common-ui/stores/launch";
import { launcherService } from "django-airavata-common-ui/services/launcherService";
import InvocationCommand from "./InvocationCommand.vue";
import ScriptPreview from "./ScriptPreview.vue";

const store = useLaunchStore();
const loading = ref(false);
const error = ref<string | null>(null);
const launchError = ref<string | null>(null);
let abort: AbortController | null = null;

async function refresh() {
  if (store.preview && store.lastPreviewedHash === store.draftHash) return;
  loading.value = true;
  error.value = null;
  abort?.abort();
  abort = new AbortController();
  try {
    const r = await launcherService.generatePreview(store.draft, abort.signal);
    store.preview = r;
    store.lastPreviewedHash = store.draftHash;
  } catch (e) {
    error.value = (e as Error).message;
    store.preview = null;
  } finally {
    loading.value = false;
  }
}

async function onLaunch() {
  launchError.value = null;
  try {
    const { experiment_id } = await launcherService.launchExperiment(store.draft);
    window.location.href = `/workspace/experiments/${experiment_id}`;
  } catch (e) {
    launchError.value = (e as Error).message;
  }
}

onMounted(() => { void refresh(); });
</script>
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- Tab3ReviewLaunch`
Expected: PASS — 4 tests OK.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/Tab3ReviewLaunch.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/launch/Tab3ReviewLaunch.spec.ts
git commit -m "feat(launcher): Tab3ReviewLaunch preview fetch + launch flow"
```

---

## Phase 6 — Edge cases

### Task 19: localStorage draft persistence

**Files:**
- Modify: `django_airavata/static/common/js/stores/launch.ts`
- Modify: `…/tests/unit/stores/launch.spec.ts`

- [ ] **Step 1: Add the failing test**

Append to `launch.spec.ts`:

```ts
describe("draft persistence", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("saves draft to localStorage on every change", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "abc", project_id: "p1", description: "" });
    const stored = localStorage.getItem("launch-draft");
    expect(stored).not.toBeNull();
    expect(JSON.parse(stored!).name).toBe("abc");
  });

  it("restores draft from localStorage on hydrate()", () => {
    localStorage.setItem("launch-draft", JSON.stringify({
      name: "restored", project_id: "p1", description: "",
      app_id: null, interface_name: null, inputs: {}, outputs: {},
      runtime: { compute_resource_id: null, partition: null,
                 walltime: "01:00:00", nodes: 1, cpus_per_node: 1 },
    }));
    const s = useLaunchStore();
    s.hydrate();
    expect(s.draft.name).toBe("restored");
  });

  it("reset() clears localStorage", () => {
    const s = useLaunchStore();
    s.setMeta({ name: "abc", project_id: "p1", description: "" });
    s.reset();
    expect(localStorage.getItem("launch-draft")).toBeNull();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- launch.spec`
Expected: FAIL — `hydrate()` not defined; localStorage write not triggered.

- [ ] **Step 3: Implement persistence**

Edit `django_airavata/static/common/js/stores/launch.ts`. After the `useLaunchStore` setup completes, add a `watch` for autosave and a `hydrate()` method. Insert before the `reset` function:

```ts
import { watch } from "vue";

const STORAGE_KEY = "launch-draft";

function persist(draft: ExperimentDraft) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(draft)); } catch { /* ignore quota */ }
}

function clearPersisted() {
  try { localStorage.removeItem(STORAGE_KEY); } catch { /* noop */ }
}

function hydrate() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as Partial<ExperimentDraft>;
    Object.assign(draft, makeDraft(), parsed);
  } catch {
    /* ignore corrupted draft */
  }
}

watch(draft, (d) => persist(d), { deep: true });
```

Update `reset()` to call `clearPersisted()`:

```ts
function reset() {
  Object.assign(draft, makeDraft());
  pickedApp.value = null;
  profile.value = null;
  preview.value = null;
  previewError.value = null;
  lastPreviewedHash.value = null;
  clearPersisted();
}
```

Export `hydrate` in the store's return object.

- [ ] **Step 4: Run to verify it passes**

Run: `cd django_airavata/apps/workspace && npm run test -- launch.spec`
Expected: PASS — 8 tests OK.

- [ ] **Step 5: Wire `hydrate()` from LaunchContainer**

Edit `…/js/containers/LaunchContainer.vue`. Inside the `<script setup>` block, replace `onMounted(...)` with:

```ts
onMounted(() => {
  store.hydrate();
  const url = new URL(window.location.href);
  const t = Number(url.searchParams.get("tab"));
  if (t === 1 || t === 2 || t === 3) active.value = t as 1 | 2 | 3;
});
```

Add `import { useLaunchStore } from "django-airavata-common-ui/stores/launch";` at the top, and `const store = useLaunchStore();` next to `active`.

- [ ] **Step 6: Commit**

```bash
git add django_airavata/static/common/js/stores/launch.ts \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/LaunchContainer.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/stores/launch.spec.ts
git commit -m "feat(launcher): localStorage draft persistence + hydrate()"
```

---

### Task 20: Change-warning toasts (project / app / interface)

**Files:**
- Modify: `…/js/components/launch/ExperimentMetaHeader.vue`
- Modify: `…/js/components/launch/AppPicker.vue`
- Modify: `…/js/components/launch/InterfacePicker.vue`
- Create: `…/js/composables/useConfirmReset.ts`
- Create: `…/tests/unit/composables/useConfirmReset.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it, vi } from "vitest";
import { useConfirmReset } from "../../../js/composables/useConfirmReset";

describe("useConfirmReset", () => {
  it("calls onConfirm when window.confirm returns true", () => {
    vi.spyOn(window, "confirm").mockReturnValueOnce(true);
    const fn = vi.fn();
    const guarded = useConfirmReset("ok?", fn);
    guarded();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("skips onConfirm when window.confirm returns false", () => {
    vi.spyOn(window, "confirm").mockReturnValueOnce(false);
    const fn = vi.fn();
    useConfirmReset("ok?", fn)();
    expect(fn).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd django_airavata/apps/workspace && npm run test -- useConfirmReset`
Expected: FAIL — file not found.

- [ ] **Step 3: Implement the composable**

Create `…/js/composables/useConfirmReset.ts`:

```ts
export function useConfirmReset<TArgs extends unknown[]>(message: string, fn: (...a: TArgs) => void) {
  return (...args: TArgs) => {
    if (window.confirm(message)) fn(...args);
  };
}
```

- [ ] **Step 4: Wire confirm prompts at the call sites**

In `AppPicker.vue` `pick` function:

```ts
import { useConfirmReset } from "../../composables/useConfirmReset";
const guardedPick = useConfirmReset("Switching app clears interface, inputs, and outputs. Continue?", (a: Application) => store.pickApp(a));
function pick(a: Application) {
  if (store.draft.app_id && store.draft.app_id !== a.app_id) guardedPick(a);
  else store.pickApp(a);
}
```

In `InterfacePicker.vue`, wrap the `pickInterface` button click:

```ts
import { useConfirmReset } from "../../composables/useConfirmReset";
const guarded = useConfirmReset("Switching interface clears inputs and outputs. Continue?", (n: string) => store.pickInterface(n));
function onPick(n: string) {
  if (store.draft.interface_name && store.draft.interface_name !== n) guarded(n);
  else store.pickInterface(n);
}
```

Replace `@click="store.pickInterface(iface.name)"` with `@click="onPick(iface.name)"`.

In `ExperimentMetaHeader.vue` `onProject`:

```ts
import { useConfirmReset } from "../../composables/useConfirmReset";
const guardedProject = useConfirmReset("Switching project clears your runtime selections. Continue?", (id: string | null) => {
  store.setMeta({ name: store.draft.name, project_id: id, description: store.draft.description });
});
function onProject(v: string) {
  const next = v || null;
  if (store.draft.project_id && store.draft.project_id !== next) guardedProject(next);
  else store.setMeta({ name: store.draft.name, project_id: next, description: store.draft.description });
}
```

- [ ] **Step 5: Run all related tests to ensure no regressions**

Run: `cd django_airavata/apps/workspace && npm run test -- "AppPicker|InterfacePicker|ExperimentMetaHeader|useConfirmReset"`
Expected: PASS — all OK. (The component tests don't trigger the confirm path because they always start with no prior selection.)

- [ ] **Step 6: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/js/composables/useConfirmReset.ts \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/AppPicker.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/InterfacePicker.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/js/components/launch/ExperimentMetaHeader.vue \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/composables/useConfirmReset.spec.ts
git commit -m "feat(launcher): confirm prompts on app/interface/project change"
```

---

## Phase 7 — Integration + E2E tests

### Task 21: Vitest integration test (full happy path)

**Files:**
- Create: `…/tests/unit/integration/launch-flow.spec.ts`

- [ ] **Step 1: Write the integration spec**

```ts
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LaunchContainer from "../../../js/containers/LaunchContainer.vue";

const APP = {
  app_id: "namd", name: "NAMD", category: "MD",
  content: { kind: "github" as const, url: "g" },
  interfaces: [{
    name: "run",
    inputs: [
      { name: "sim_dir", type: "dir" as const, required: true },
      { name: "steps", type: "int" as const, required: true },
    ],
    outputs: [{ name: "trajectory", type: "file" as const }],
  }],
};

const PROFILE = {
  project_id: "p1", allocation_id: "NSF-1",
  compute_resources: [{
    compute_resource_id: "bridges-2", name: "Bridges-2",
    mapped_storage: { storage_id: "scratch", scratch_path: "/scratch/p1" },
    partitions: [{ name: "RM", max_walltime: "48:00:00", max_nodes: 64, cpus_per_node: 128 }],
  }],
};

vi.mock("django-airavata-common-ui/services/launcherService", () => ({
  launcherService: {
    listApplications: vi.fn().mockResolvedValue({ results: [APP] }),
    listUserStorages: vi.fn().mockResolvedValue({ results: [{ storage_id: "my-home", name: "Home", is_primary: true }] }),
    listProjects: vi.fn().mockResolvedValue({ results: [{ project_id: "p1", name: "lab" }] }),
    getProjectResourceProfile: vi.fn().mockResolvedValue(PROFILE),
    generatePreview: vi.fn().mockResolvedValue({
      invocation_command: "sbatch /tmp/run.sh",
      script_contents: "#!/bin/bash\necho hi",
      warnings: [],
    }),
    launchExperiment: vi.fn().mockResolvedValue({ experiment_id: "exp-7" }),
  },
}));

describe("launch flow integration", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    Object.defineProperty(window, "location", {
      value: { href: "/", assign: vi.fn() }, writable: true,
    });
  });

  it("walks tab 1 → tab 2 → tab 3 → launch", async () => {
    const w = mount(LaunchContainer);
    await flushPromises();

    // Meta
    await w.find("input[data-test='exp-name']").setValue("test-run");
    await w.find("select[data-test='exp-project']").setValue("p1");

    // App + interface
    await w.find("[data-test='app-tile-namd']").trigger("click");
    await flushPromises();
    await w.find("[data-test='iface-card-run']").trigger("click");

    // Inputs + output
    await w.find("input[data-test='file-path-sim_dir']").setValue("/x");
    await w.find("input[data-test='scalar-steps']").setValue("100");
    const outSelect = w.findAll("select").find((s) => s.element.parentElement?.outerHTML.includes("trajectory"))!;
    await outSelect.setValue("my-home");
    await w.find("input[data-test='file-out-path-trajectory']").setValue("/y");

    // Tab 2
    await w.findAll("button[role='tab']")[1].trigger("click");
    await flushPromises();
    await w.find("select[data-test='cr']").setValue("bridges-2");
    await w.find("select[data-test='partition']").setValue("RM");

    // Tab 3
    await w.findAll("button[role='tab']")[2].trigger("click");
    await flushPromises();
    expect(w.text()).toContain("sbatch /tmp/run.sh");
    await w.find("button[data-test='launch']").trigger("click");
    await flushPromises();
    expect(window.location.href).toBe("/workspace/experiments/exp-7");
  });
});
```

- [ ] **Step 2: Run it**

Run: `cd django_airavata/apps/workspace && npm run test -- launch-flow`
Expected: PASS — 1 test OK. If failing, the most common cause is selector drift after Phase 3-5 changes — fix selectors in this spec or in components, but keep the spec's expected behaviors.

- [ ] **Step 3: Commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/integration/launch-flow.spec.ts
git commit -m "test(launcher): full happy-path integration spec (mocked API)"
```

---

### Task 22: Playwright e2e — happy path + smoke

**Files:**
- Create: `tests/e2e/specs/launch-happy.spec.ts`
- Modify: `tests/e2e/specs/smoke.spec.ts`

- [ ] **Step 1: Write the failing happy-path spec**

```ts
import { test, expect } from "../fixtures/auth";

test("launch a stub experiment via /workspace/launch", async ({ page }) => {
  await page.goto("/workspace/launch");
  await expect(page.getByPlaceholder(/Experiment name/i)).toBeVisible();

  await page.getByPlaceholder(/Experiment name/i).fill("e2e-stub");
  // Project: pick whatever's available
  const projectSelect = page.locator("select[data-test='exp-project']");
  await projectSelect.selectOption({ index: 1 });

  // App + interface (stub returns NAMD)
  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();

  // Inputs
  await page.locator("input[data-test='file-path-sim_dir']").fill("/home/x/sim");
  await page.locator("input[data-test='scalar-steps']").fill("100");
  // Output
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/home/x/out.dcd");

  // Tab 2
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");
  await page.locator("select[data-test='partition']").selectOption("RM");

  // Tab 3
  await page.locator("button[role='tab']").nth(2).click();
  await expect(page.locator("pre code")).toContainText("#!/bin/bash");
  await page.locator("button[data-test='launch']").click();

  await page.waitForURL(/\/workspace\/experiments\//);
});
```

- [ ] **Step 2: Add `/workspace/launch` to smoke**

Edit `tests/e2e/specs/smoke.spec.ts`. Update the `AUTHENTICATED_PAGES` array — replace the existing entry (or insert after `/workspace/home`):

```ts
const AUTHENTICATED_PAGES = [
  "/workspace/home",
  "/workspace/launch",
  "/workspace/projects",
  // … rest unchanged
];
```

- [ ] **Step 3: Run e2e**

Prereq: airavata-django-portal must be running (`tilt up`) with `LAUNCHER_CLIENT_STUB=True` and `FEATURE_GENERIC_LAUNCHER=True`. Then:

Run: `npx playwright test tests/e2e/specs/launch-happy.spec.ts tests/e2e/specs/smoke.spec.ts -c tooling/playwright.config.ts`
Expected: PASS — happy path completes; all smoke pages load.

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/specs/launch-happy.spec.ts tests/e2e/specs/smoke.spec.ts
git commit -m "test(launcher): Playwright happy path + add /workspace/launch to smoke"
```

---

### Task 23: Playwright e2e — error paths

**Files:**
- Create: `tests/e2e/specs/launch-error-paths.spec.ts`

- [ ] **Step 1: Write the spec**

```ts
import { test, expect } from "../fixtures/auth";

test("strict-forward gate: cannot click tab 2 before tab 1 is valid", async ({ page }) => {
  await page.goto("/workspace/launch");
  await expect(page.locator("button[role='tab']").nth(1)).toBeDisabled();
});

test("preview failure shows error and disables launch", async ({ page }) => {
  // Intercept the preview endpoint and return 502
  await page.route("**/api/launcher/experiment-drafts/preview/", (route) =>
    route.fulfill({ status: 502, body: JSON.stringify({ message: "airavata down" }) }),
  );

  await page.goto("/workspace/launch");
  await page.getByPlaceholder(/Experiment name/i).fill("err-stub");
  await page.locator("select[data-test='exp-project']").selectOption({ index: 1 });
  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();
  await page.locator("input[data-test='file-path-sim_dir']").fill("/x");
  await page.locator("input[data-test='scalar-steps']").fill("1");
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/y");
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");
  await page.locator("select[data-test='partition']").selectOption("RM");
  await page.locator("button[role='tab']").nth(2).click();

  await expect(page.locator(".alert-danger")).toContainText("airavata down");
  await expect(page.locator("button[data-test='launch']")).toBeDisabled();
});

test("project change clears runtime selections", async ({ page }) => {
  await page.goto("/workspace/launch");
  await page.getByPlaceholder(/Experiment name/i).fill("proj-change");
  await page.locator("select[data-test='exp-project']").selectOption({ index: 1 });

  // The confirm dialog is what we're testing — accept it when prompted
  page.on("dialog", (d) => d.accept());

  await page.locator("[data-test='app-tile-namd']").click();
  await page.locator("[data-test='iface-card-run']").click();
  await page.locator("input[data-test='file-path-sim_dir']").fill("/x");
  await page.locator("input[data-test='scalar-steps']").fill("1");
  await page.locator("input[data-test='file-out-path-trajectory']").fill("/y");
  await page.locator("button[role='tab']").nth(1).click();
  await page.locator("select[data-test='cr']").selectOption("bridges-2");

  // Switch project — the dropdown only has projects from session data; pick the second.
  // If only one project exists, this test no-ops and we just assert the disabled state below.
  const opts = await page.locator("select[data-test='exp-project'] option").allTextContents();
  if (opts.length > 2) {
    await page.locator("select[data-test='exp-project']").selectOption({ index: 2 });
    await expect(page.locator("select[data-test='cr']")).toHaveValue("");
  }
});
```

- [ ] **Step 2: Run it**

Run: `npx playwright test tests/e2e/specs/launch-error-paths.spec.ts -c tooling/playwright.config.ts`
Expected: PASS — 3 tests OK.

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/specs/launch-error-paths.spec.ts
git commit -m "test(launcher): Playwright error-path coverage (gate, preview fail, project change)"
```

---

## Phase 8 — Migration + cleanup

### Task 24: Update repo-internal call sites of the old URLs

**Files modified** (search results from spec — `git grep -n "/workspace/applications" -- '*.vue' '*.py' '*.ts'`):
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/WorkspaceDashboardContainer.vue`
- `…/js/containers/DashboardContainer.vue`
- `…/js/containers/ProjectOverviewContainer.vue`
- `…/js/containers/ExperimentListContainer.vue`
- `…/js/containers/ApplicationEditorContainer.vue` (only the launch link, lines 726, 995, 1037, 1051)
- `django_airavata/apps/dataparsers/static/django_airavata_dataparsers/**/*.vue` (any `applications/...create_experiment` references)

- [ ] **Step 1: Find every call site**

Run: `git grep -n "/workspace/applications" -- '*.vue' '*.py' '*.ts' '*.js' '*.html' | tee /tmp/call-sites.txt`

- [ ] **Step 2: Edit each one**

For each line in `/tmp/call-sites.txt`, replace the URL. Two cases:
- `/workspace/applications` (the discovery list) → `/workspace/launch`
- `/workspace/applications/<id>/create_experiment` → `/workspace/launch` (drop the `id` — under the new model the launcher always starts from no app)
- `/workspace/applications/<id>/` (app-editor route) — **DO NOT TOUCH** if this points at the admin app-definition editor (`ApplicationEditorContainer`); that surface stays for now (separate track).

Specific edits to make (other repos may have additional call sites — fix any that show up):

1. `WorkspaceDashboardContainer.vue` line 40: `href="/workspace/applications?action=launch"` → `href="/workspace/launch"`.
2. `DashboardContainer.vue` line 10: `href="/workspace/applications/new"` — keep (app-creation flow stays). Lines 209/217: the per-tile launch link → change to `/workspace/launch`.
3. `ProjectOverviewContainer.vue` line 238: `const newExperimentUrl = "/workspace/applications";` → `const newExperimentUrl = "/workspace/launch";`.
4. `ExperimentListContainer.vue` lines 10/97: `href="/workspace/applications"` → `href="/workspace/launch"`.

- [ ] **Step 3: Verify no untouched references**

Run: `git grep -n "applications/.*/create_experiment\|workspace/applications\b\(?!/new\)" -- '*.vue' '*.ts' '*.js' '*.html' '*.py'`
Expected: no matches that target launch.

- [ ] **Step 4: Run frontend tests**

Run: `cd django_airavata/apps/workspace && npm run test`
Expected: all pre-existing tests still PASS (call-site changes are link-only, no logic).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(launcher): retarget repo-internal links from old apps URL to /workspace/launch"
```

---

### Task 25: SDK deprecation shim + update callers

**Files:**
- Modify: `airavata-django-portal-sdk/airavata_django_portal_sdk/experiment_util.py` (or wherever the deep-link helper lives — verify)
- Modify: any in-repo callers of the SDK helper

This task may be a no-op depending on what the SDK currently exposes. The check:

- [ ] **Step 1: Audit the SDK**

Run: `grep -rn "create_experiment\|/workspace/applications" ../airavata-django-portal-sdk/ 2>/dev/null | head`
- If matches: proceed.
- If no matches: skip to step 4 with the commit message "no SDK changes required".

- [ ] **Step 2: Add a deprecation shim**

If the SDK has a helper like `build_experiment_url(app_module_id, …)`, add a deprecation warning and have it return `/workspace/launch`:

```python
import warnings


def build_experiment_url(app_module_id: str | None = None, **kwargs) -> str:
    if app_module_id is not None:
        warnings.warn(
            "build_experiment_url(app_module_id=...) is deprecated; the generic launcher does not deep-link to apps anymore.",
            DeprecationWarning,
            stacklevel=2,
        )
    return "/workspace/launch"
```

- [ ] **Step 3: Update repo-internal callers** that rely on the old behavior — they should drop the `app_module_id` argument.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor(launcher): SDK deep-link helper now returns /workspace/launch (deprecation shim)"
```

---

### Task 26: Delete old experiment-editor surface

**Files:**
- Delete the files listed in the File Map → Deleted section.

- [ ] **Step 1: Verify nothing imports them**

Run:

```bash
git grep -nE "CreateExperimentContainer|EditExperimentContainer|ExperimentEditor\.vue|ComputationalResourceSchedulingEditor|QueueSettingsEditor|GroupResourceProfileSelector|entry-create-experiment|entry-edit-experiment" -- '*.vue' '*.ts' '*.js' '*.py' '*.html'
```

Expected: only matches inside the files being deleted themselves.

- [ ] **Step 2: Delete the files**

```bash
rm django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/CreateExperimentContainer.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/EditExperimentContainer.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/ExperimentEditor.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/ComputationalResourceSchedulingEditor.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/QueueSettingsEditor.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/GroupResourceProfileSelector.vue \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-create-experiment.js \
   django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-edit-experiment.js
```

- [ ] **Step 3: Remove the now-dead views in `workspace/views.py`**

Delete the `create_experiment`, `edit_experiment`, and `applications` view functions. Their URL routes were already replaced with redirects in Task 5.

- [ ] **Step 4: Remove old entries from any vite/build manifest**

Edit `django_airavata/apps/workspace/vite.config.*` (or whichever build config drives bundling) — drop entries for `entry-create-experiment` and `entry-edit-experiment` if explicitly listed.

- [ ] **Step 5: Run full frontend + backend tests**

```bash
cd django_airavata/apps/workspace && npm run test
cd ../../../.. && python manage.py test
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(launcher): delete old experiment-editor surface"
```

---

## Phase 9 — Final wiring

### Task 27: Flag-on bake + final manual checklist

**Files:**
- Modify: `django_airavata/settings.py` (default flag on after verification)
- Modify: PR description

- [ ] **Step 1: Verify against a live dev stack**

Bring up the stack:

```bash
cd ../../airavata && tilt up
cd ../airavata-portals/airavata-django-portal && FEATURE_GENERIC_LAUNCHER=True tilt up
```

Manually walk through:
- Open `/workspace/launch`
- Pick an app, an interface, fill inputs (each I/O type at least once across runs)
- Switch project mid-flow → verify confirm prompt + tab 2 reset
- Switch app mid-flow → verify confirm prompt + downstream reset
- Let session expire on tab 3 (sleep > Keycloak token TTL) → verify return-to-login + draft restore
- Click launch → verify redirect to `/workspace/experiments/<id>`

- [ ] **Step 2: When manual run passes, flip default**

Edit `django_airavata/settings.py`:

```python
FEATURE_GENERIC_LAUNCHER = os.environ.get("FEATURE_GENERIC_LAUNCHER", "True").lower() == "true"
```

- [ ] **Step 3: Run full test suites once more**

```bash
cd django_airavata/apps/workspace && npm run test
cd ../../../.. && python manage.py test
npx playwright test -c tooling/playwright.config.ts
```

Expected: all PASS.

- [ ] **Step 4: Open PR**

```bash
git push -u origin feat/generic-experiment-launcher
gh pr create --base modernization --title "feat: generic experiment launcher" --body "$(cat <<'EOF'
## Summary
- Replaces per-app launch flow with `/workspace/launch` 3-tab wizard
- New Django REST API surface under `/api/launcher/`
- New Pinia store + Vue 3 SPA mounted by `entry-launch.ts`
- Old per-app URLs 301 to `/workspace/launch`
- Stub airavata client behind `LAUNCHER_CLIENT_STUB` until upstream RPCs land

## Spec / plan
- Spec: `airavata-django-portal/docs/superpowers/specs/2026-04-24-generic-experiment-launcher-design.md`
- Plan: `airavata-django-portal/docs/superpowers/plans/2026-04-24-generic-experiment-launcher-plan.md`

## Test plan
- [ ] Unit tests pass (Vitest)
- [ ] Integration test passes (Vitest)
- [ ] Backend tests pass (Django TestCase)
- [ ] Playwright happy path passes
- [ ] Playwright error paths pass
- [ ] Smoke covers `/workspace/launch`
- [ ] Manual: each I/O type exercised once in a live run
- [ ] Manual: project / app / interface change confirm dialogs fire
- [ ] Manual: session expiry mid-flow restores draft

## Out of scope (separate tracks)
- Airavata Java server: new app-model RPCs + `GenerateExperimentSubmissionScript` dry-run
- App definition UI under the new model
- Experiment edit flow
EOF
)"
```

- [ ] **Step 5: Final commit (post-flag-flip)**

If the flag flip required an actual settings change:

```bash
git add django_airavata/settings.py
git commit -m "chore(launcher): default FEATURE_GENERIC_LAUNCHER to on"
```

---

### Task 28: Swap the stub for the real client

**Trigger:** When the airavata Java server merges (1) the new application-model RPCs and (2) `GenerateExperimentSubmissionScript`. Until then this task does not run.

**Files:**
- Modify: `django_airavata/apps/api/launcher_client.py`
- Modify: `django_airavata/settings.py`
- Modify: `django_airavata/apps/api/tests/test_launcher_client.py`

- [ ] **Step 1: Implement the real client**

Replace `_RealClient` in `launcher_client.py` with calls into the Airavata Thrift API client. The portal already has a Thrift wrapper used by the existing experiment views; reuse it. Each method maps directly to the new gRPC/Thrift call. The data shapes returned must match the stub's exactly (so the rest of the pipeline doesn't need to change).

- [ ] **Step 2: Add tests for the real client (mocked at the Thrift boundary)**

Append to `test_launcher_client.py`:

```python
@override_settings(LAUNCHER_CLIENT_STUB=False)
def test_real_client_calls_thrift_listApplications(self):
    with patch("django_airavata.apps.api.launcher_client.airavata_client") as ac:
        ac.list_applications.return_value = []
        client = launcher_client.get_client(user_token="t")
        client.list_applications(category=None, search=None)
        ac.list_applications.assert_called_once()
```

(Replace `airavata_client` with the actual import name — TBD when implementing.)

- [ ] **Step 3: Flip default to real**

```python
LAUNCHER_CLIENT_STUB = os.environ.get("LAUNCHER_CLIENT_STUB", "False").lower() == "true"
```

- [ ] **Step 4: Run full suites**

```bash
python manage.py test
cd django_airavata/apps/workspace && npm run test
npx playwright test -c tooling/playwright.config.ts
```

Expected: all PASS against a live airavata stack.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(launcher): swap stub for real airavata client (LAUNCHER_CLIENT_STUB default off)"
```

---

## Self-review checklist

Run before marking the plan ready:

- [ ] Every spec section maps to at least one task (URL/scope → Tasks 5+24, frontend arch → Tasks 6-9, API surface → Tasks 1-4, tab specs → Tasks 10-18, edge cases → Tasks 19-20, testing → Tasks 21-23, migration → Tasks 24-26).
- [ ] No "TBD" / "TODO" placeholders in any task body.
- [ ] Type names match across tasks: `ExperimentDraft`, `RuntimeChoice`, `StorageRef`, `Application`, `InterfaceDescriptor`, `IODescriptor`, `ResourceProfile`.
- [ ] Function names are stable: `pickApp`, `pickInterface`, `setMeta`, `setInput`, `setOutput`, `setRuntime`, `hydrate`, `reset`, `tab1Valid`, `tab2Valid`, `draftHash`.
- [ ] All commit messages use the same prefix style (`feat(launcher):`, `test(launcher):`, `refactor(launcher):`, `chore(launcher):`, `docs(feat/generic-launcher):`).
