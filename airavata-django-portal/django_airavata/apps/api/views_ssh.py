"""SSE streaming and SSH proxy API endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Final

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django_airavata.apps.api.sse import event_bus
from django_airavata.apps.api.ssh_manager import SSHSessionManager

logger: Final = logging.getLogger(__name__)

# Singleton SSH session manager
ssh_manager: Final = SSHSessionManager(event_bus)

# Path to the HPC info script
INFO_SCRIPT_PATH: Final[str] = os.path.join(os.path.dirname(__file__), "scripts", "info.sh")


@csrf_exempt
@login_required
@require_GET
async def sse_events(request: HttpRequest) -> StreamingHttpResponse:
    """SSE endpoint — streams events to the authenticated user."""
    user_id: int = request.user.id

    async def stream() -> Any:
        try:
            async for line in event_bus.event_stream(user_id):
                yield line
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.cleanup(user_id)

    response = StreamingHttpResponse(stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@login_required
@require_POST
async def ssh_test(request: HttpRequest) -> JsonResponse:
    """Start an SSH test connection."""
    body: dict[str, Any] = json.loads(request.body)
    hostname: str = body["hostname"]
    port: int = body.get("port", 22)
    credential_token: str = body["credential_token"]
    session_id: str = str(uuid.uuid4())
    user_id: int = request.user.id
    gateway_id: str = settings.GATEWAY_ID

    # Fetch the SSH private key from the credential store
    try:
        credential = request.airavata_client.credential.get_SSH_credential(
            credential_token, gateway_id
        )
        private_key_pem = credential.privateKey
    except Exception as e:
        logger.warning("Failed to fetch credential token %s: %s", credential_token, e)
        return JsonResponse({"error": f"Failed to fetch credential: {e}", "error_type": "INVALID_KEY"}, status=400)

    # Start connection as a background task
    asyncio.create_task(
        ssh_manager.start_connection(
            user_id=user_id,
            session_id=session_id,
            hostname=hostname,
            port=port,
            private_key_pem=private_key_pem,
            username=request.user.username,
        )
    )

    return JsonResponse({"session_id": session_id})


@login_required
@require_POST
async def ssh_respond(request: HttpRequest) -> JsonResponse:
    """Submit a response to an interactive SSH prompt."""
    body: dict[str, Any] = json.loads(request.body)
    session_id: str = body["session_id"]
    response_text: str = body["response"]

    ok: bool = await ssh_manager.submit_response(session_id, response_text)
    if not ok:
        return JsonResponse({"error": "Session not found"}, status=404)
    return JsonResponse({"ok": True})


@login_required
@require_POST
async def ssh_run(request: HttpRequest) -> JsonResponse:
    """Run a command on an established SSH session."""
    body: dict[str, Any] = json.loads(request.body)
    session_id: str = body["session_id"]
    command: str = body["command"]

    try:
        output: str = await ssh_manager.run_command(session_id, command)
        return JsonResponse({"output": output})
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)


@login_required
@require_POST
async def ssh_run_info(request: HttpRequest) -> JsonResponse:
    """Run the HPC info.sh script on an established SSH session."""
    body: dict[str, Any] = json.loads(request.body)
    session_id: str = body["session_id"]

    with open(INFO_SCRIPT_PATH) as f:
        script_content = f.read()

    try:
        output: str = await ssh_manager.run_command(
            session_id, f"sh -s <<'INFOSCRIPT'\n{script_content}\nINFOSCRIPT"
        )

        partitions: list[dict[str, Any]] = []
        lines: list[str] = output.strip().split("\n")
        if len(lines) > 1:
            for line in lines[1:]:
                parts: list[str] = line.split("|")
                if len(parts) >= 7:
                    partitions.append({
                        "partition": parts[0],
                        "nodes": int(parts[1]) if parts[1] else 0,
                        "maxCpusPerNode": int(parts[2]) if parts[2] else 0,
                        "maxMemMbPerNode": int(parts[3]) if parts[3] else 0,
                        "maxGpusPerNode": int(parts[4]) if parts[4] else 0,
                        "gpuTypes": parts[5].split(",") if parts[5] else [],
                        "accounts": parts[6].split(",") if parts[6] else [],
                    })

        return JsonResponse({"output": output, "partitions": partitions})
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)


@login_required
@require_POST
async def ssh_close(request: HttpRequest) -> JsonResponse:
    """Close an SSH session."""
    body: dict[str, Any] = json.loads(request.body)
    session_id: str = body["session_id"]

    await ssh_manager.close_session(session_id)
    return JsonResponse({"ok": True})
