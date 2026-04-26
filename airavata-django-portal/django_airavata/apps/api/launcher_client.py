"""Abstraction layer over the airavata server's launcher RPCs.

The new-model RPCs (apps with content + user-defined interfaces, dry-run preview)
are landing in the Java server separately. Until they ship, this module bridges
the launcher schema to the legacy ``ApplicationModule``/``ApplicationInterface``
catalog so the launcher's Tab 1 stays 1-1 with what the Applications page shows.

Resource profile, storages, projects, generate_preview, and launch_experiment
remain stubbed — those wait for upstream pieces.

The settings flag ``LAUNCHER_CLIENT_STUB`` selects between the bridge stub and
the (still NotImplemented) ``_RealClient``. Tests should construct the client
without a request to use built-in fixtures.
"""

from __future__ import annotations

import copy
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


# Test-only fixture used when the client is constructed without a request
# (e.g., from `test_launcher_client.py`). Real Django views always pass the
# request and hit the live Thrift API instead.
_FIXTURE_APPS: list[dict[str, Any]] = [
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


def _proto_data_type_to_launcher_type(proto_type: int) -> str:
    """Map proto DataType enum value to the launcher's IO type strings."""
    from airavata_sdk.generated.org.apache.airavata.model.application.io.application_io_pb2 import (
        DataType as ProtoDataType,
    )
    if proto_type == ProtoDataType.INTEGER:
        return "int"
    if proto_type == ProtoDataType.FLOAT:
        return "float"
    if proto_type in (ProtoDataType.URI, ProtoDataType.URI_COLLECTION,
                      ProtoDataType.STDOUT, ProtoDataType.STDERR):
        return "file"
    return "string"


def _adapt_io(io_proto: Any) -> dict[str, Any]:
    return {
        "name": io_proto.name,
        "type": _proto_data_type_to_launcher_type(io_proto.type),
        "required": bool(getattr(io_proto, "is_required", False)),
    }


def _adapt_interface(iface_proto: Any) -> dict[str, Any]:
    """Adapt a legacy ApplicationInterfaceDescription into a launcher InterfaceDescriptor.

    Legacy apps have a single interface per module, so we surface it as the
    user-facing verb "run". Once the upstream new-model app ships multiple
    user-defined interfaces, this collapses naturally to one entry per verb.
    """
    return {
        "name": "run",
        "inputs": [_adapt_io(i) for i in (iface_proto.application_inputs or [])],
        "outputs": [_adapt_io(o) for o in (iface_proto.application_outputs or [])],
    }


def _adapt_module(module_proto: Any, interfaces: list[Any]) -> dict[str, Any]:
    return {
        "app_id": module_proto.app_module_id,
        "name": module_proto.app_module_name,
        # Legacy app catalog has no category; bucket everything under
        # "Applications" so the chip filter still renders predictably.
        "category": "Applications",
        # Legacy app catalog has no content reference (tarball/github URL).
        # Show the version (or a placeholder) on the tile.
        "content": {
            "kind": "tarball",
            "url": module_proto.app_module_version or module_proto.app_module_description or module_proto.app_module_name,
        },
        "interfaces": [_adapt_interface(ai) for ai in interfaces],
    }


class _StubClient:
    """Bridge between the launcher schema and the legacy app catalog.

    When constructed with a Django request it fetches real ApplicationModule
    data; without a request it returns built-in fixtures (used by unit tests).
    """

    def __init__(self, user_token: str = "", request: Any = None) -> None:
        self.user_token = user_token
        self._request = request

    def _airavata_client(self) -> Any | None:
        req = self._request
        if req is None:
            return None
        return getattr(req, "airavata_client", None)

    def list_applications(self, *, category: str | None, search: str | None) -> list[dict[str, Any]]:
        client = self._airavata_client()
        if client is None:
            results = [copy.deepcopy(a) for a in _FIXTURE_APPS]
        else:
            modules = client.research.get_accessible_app_modules(settings.GATEWAY_ID)
            interfaces_by_mod = self._interfaces_by_module(client)
            results = [
                _adapt_module(m, interfaces_by_mod.get(m.app_module_id, []))
                for m in modules
            ]
        if category:
            results = [a for a in results if a["category"] == category]
        if search:
            needle = search.lower()
            results = [a for a in results if needle in a["name"].lower()]
        return results

    def get_application(self, *, app_id: str) -> dict[str, Any]:
        client = self._airavata_client()
        if client is None:
            for a in _FIXTURE_APPS:
                if a["app_id"] == app_id:
                    return copy.deepcopy(a)
            raise LookupError(f"unknown app_id {app_id!r}")
        try:
            module = client.research.get_application_module(app_id)
        except Exception as e:
            raise LookupError(f"unknown app_id {app_id!r}") from e
        all_interfaces = client.research.get_all_application_interfaces(settings.GATEWAY_ID)
        module_interfaces = [
            ai for ai in all_interfaces
            if ai.application_modules and app_id in ai.application_modules
        ]
        return _adapt_module(module, module_interfaces)

    def _interfaces_by_module(self, client: Any) -> dict[str, list[Any]]:
        all_interfaces = client.research.get_all_application_interfaces(settings.GATEWAY_ID)
        out: dict[str, list[Any]] = {}
        for ai in all_interfaces:
            for mod_id in (ai.application_modules or []):
                out.setdefault(mod_id, []).append(ai)
        return out

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
        client = self._airavata_client()
        if client is None:
            return [{"project_id": "proj-stub", "name": "stub-lab-2026"}]
        username = self._request.user.username if self._request and getattr(self._request, "user", None) else ""
        projects = client.research.get_user_projects(settings.GATEWAY_ID, username, -1, 0)
        return [{"project_id": p.project_id, "name": p.name} for p in projects]

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
    def __init__(self, user_token: str = "", request: Any = None) -> None:
        self.user_token = user_token
        self._request = request

    def list_applications(self, *, category: str | None, search: str | None) -> list[dict[str, Any]]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def get_application(self, *, app_id: str) -> dict[str, Any]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def get_project_resource_profile(self, *, project_id: str) -> dict[str, Any]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def list_user_storages(self) -> list[dict[str, Any]]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def list_projects(self) -> list[dict[str, Any]]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def generate_preview(self, draft: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")

    def launch_experiment(self, draft: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("real client requires airavata server new-model RPCs (Task 28)")


def get_client(user_token: str = "", request: Any = None) -> LauncherClient:
    """Construct a LauncherClient.

    Pass ``request`` from view code so the bridge stub can call the real
    Thrift API. Unit tests should set ``LAUNCHER_USE_FIXTURES=True`` to force
    the in-memory fixture path even when middleware has attached an
    ``airavata_client`` to the request.
    """
    if getattr(settings, "LAUNCHER_CLIENT_STUB", True):
        if getattr(settings, "LAUNCHER_USE_FIXTURES", False):
            return _StubClient(user_token=user_token, request=None)
        return _StubClient(user_token=user_token, request=request)
    return _RealClient(user_token=user_token, request=request)
