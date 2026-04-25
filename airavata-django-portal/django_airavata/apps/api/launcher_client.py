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
