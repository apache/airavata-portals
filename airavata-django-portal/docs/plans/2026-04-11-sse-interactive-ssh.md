# SSE Infrastructure + Interactive SSH Proxy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SSE-based real-time event streaming and an interactive SSH proxy to the Django portal, enabling connection testing with interactive authentication prompts and HPC resource discovery.

**Architecture:** Django 5.1 async views under uvicorn serve an SSE event stream per user. An asyncssh-based session manager holds SSH connections server-side, emitting prompt events via SSE and accepting responses via REST POST. A Vue notification widget renders prompts inline and submits responses.

**Tech Stack:** Django 5.1 (ASGI), uvicorn, asyncssh, EventSource API, Vue 3

---

### Task 1: Add Dependencies and ASGI Configuration

**Files:**
- Modify: `pyproject.toml` (add asyncssh, uvicorn)
- Create: `django_airavata/asgi.py`
- Modify: `django_airavata/settings.py` (add ASGI_APPLICATION)
- Modify: `Tiltfile` (switch runserver to uvicorn)

- [ ] **Step 1: Add dependencies to pyproject.toml**

In `pyproject.toml`, add to the `dependencies` list after the existing `"django-vite>=3.0"` line:

```toml
    "asyncssh>=2.17",
    "uvicorn[standard]>=0.32",
```

- [ ] **Step 2: Create ASGI entry point**

Create `django_airavata/asgi.py`:

```python
"""ASGI config for django_airavata project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_airavata.settings")

application = get_asgi_application()
```

- [ ] **Step 3: Add ASGI_APPLICATION to settings.py**

In `django_airavata/settings.py`, after the existing `WSGI_APPLICATION` line (line 123), add:

```python
ASGI_APPLICATION = "django_airavata.asgi.application"
```

- [ ] **Step 4: Update Tiltfile to use uvicorn**

In `Tiltfile`, replace line 13:
```python
        'uv run manage.py runserver 0.0.0.0:8000',
```
with:
```python
        'uv run uvicorn django_airavata.asgi:application --host 0.0.0.0 --port 8000 --reload --reload-dir django_airavata',
```

- [ ] **Step 5: Install dependencies and verify server starts**

Run:
```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal
uv sync
uv run uvicorn django_airavata.asgi:application --host 0.0.0.0 --port 8000
```

Expected: Server starts, existing pages load at `http://localhost:8000/workspace/applications`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml django_airavata/asgi.py django_airavata/settings.py Tiltfile uv.lock
git commit -m "feat: add ASGI support with uvicorn and asyncssh dependencies"
```

---

### Task 2: SSE Event Bus

**Files:**
- Create: `django_airavata/apps/api/sse.py`
- Create: `django_airavata/apps/api/tests/test_sse.py`

- [ ] **Step 1: Write tests for the event bus**

Create `django_airavata/apps/api/tests/test_sse.py`:

```python
import asyncio
import json
import pytest
from django_airavata.apps.api.sse import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest.mark.asyncio
async def test_push_and_receive(bus):
    """Pushed events appear in the user's stream."""
    bus.push_event(1, {"type": "test", "msg": "hello"})
    queue = bus.get_queue(1)
    event = queue.get_nowait()
    assert event["type"] == "test"
    assert event["msg"] == "hello"


@pytest.mark.asyncio
async def test_separate_user_queues(bus):
    """Each user has an independent queue."""
    bus.push_event(1, {"type": "a"})
    bus.push_event(2, {"type": "b"})
    q1 = bus.get_queue(1)
    q2 = bus.get_queue(2)
    assert q1.get_nowait()["type"] == "a"
    assert q2.get_nowait()["type"] == "b"


@pytest.mark.asyncio
async def test_format_sse(bus):
    """event_stream yields SSE-formatted lines."""
    bus.push_event(1, {"type": "test", "value": 42})
    # Drain one event from the async generator
    gen = bus.event_stream(1)
    line = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
    assert line.startswith("data: ")
    payload = json.loads(line.removeprefix("data: ").strip())
    assert payload["type"] == "test"
    assert payload["value"] == 42


@pytest.mark.asyncio
async def test_cleanup(bus):
    """cleanup removes a user's queue."""
    bus.push_event(1, {"type": "test"})
    bus.cleanup(1)
    assert 1 not in bus._queues
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest django_airavata/apps/api/tests/test_sse.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'django_airavata.apps.api.sse'`

- [ ] **Step 3: Implement the event bus**

Create `django_airavata/apps/api/sse.py`:

```python
"""Server-Sent Events (SSE) event bus.

Per-user async queues for pushing real-time events to the browser.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


class EventBus:
    """In-process event bus with per-user async queues."""

    def __init__(self) -> None:
        self._queues: dict[int, asyncio.Queue] = {}

    def get_queue(self, user_id: int) -> asyncio.Queue:
        if user_id not in self._queues:
            self._queues[user_id] = asyncio.Queue()
        return self._queues[user_id]

    def push_event(self, user_id: int, event: dict) -> None:
        queue = self.get_queue(user_id)
        queue.put_nowait(event)

    async def event_stream(self, user_id: int) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted lines.

        Includes a heartbeat comment every HEARTBEAT_INTERVAL seconds
        to keep the connection alive through proxies.
        """
        queue = self.get_queue(user_id)
        last_heartbeat = time.monotonic()

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                yield f"data: {json.dumps(event)}\n\n"
                last_heartbeat = time.monotonic()
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
                last_heartbeat = time.monotonic()

    def cleanup(self, user_id: int) -> None:
        self._queues.pop(user_id, None)


# Singleton instance — shared across the Django process
event_bus = EventBus()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest django_airavata/apps/api/tests/test_sse.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/api/sse.py django_airavata/apps/api/tests/test_sse.py
git commit -m "feat: add SSE event bus with per-user async queues"
```

---

### Task 3: SSH Session Manager

**Files:**
- Create: `django_airavata/apps/api/ssh_manager.py`
- Create: `django_airavata/apps/api/tests/test_ssh_manager.py`

- [ ] **Step 1: Write tests for the SSH session manager**

Create `django_airavata/apps/api/tests/test_ssh_manager.py`:

```python
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from django_airavata.apps.api.ssh_manager import SSHSessionManager
from django_airavata.apps.api.sse import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def manager(bus):
    return SSHSessionManager(bus)


@pytest.mark.asyncio
async def test_start_connection_key_auth_success(manager, bus):
    """Successful key auth emits ssh_result with success=True."""
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=MagicMock(stdout="output", exit_status=0))

    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        await manager.start_connection(
            user_id=1,
            session_id="sess-1",
            hostname="localhost",
            port=22,
            private_key_pem="fake-key",
            username="testuser",
        )

    queue = bus.get_queue(1)
    event = queue.get_nowait()
    assert event["type"] == "ssh_result"
    assert event["session_id"] == "sess-1"
    assert event["success"] is True


@pytest.mark.asyncio
async def test_start_connection_failure(manager, bus):
    """Failed connection emits ssh_result with success=False."""
    with patch("asyncssh.connect", new_callable=AsyncMock, side_effect=OSError("Connection refused")):
        await manager.start_connection(
            user_id=1,
            session_id="sess-2",
            hostname="bad-host",
            port=22,
            private_key_pem="fake-key",
            username="testuser",
        )

    queue = bus.get_queue(1)
    event = queue.get_nowait()
    assert event["type"] == "ssh_result"
    assert event["success"] is False
    assert "Connection refused" in event["message"]


@pytest.mark.asyncio
async def test_run_command(manager, bus):
    """run_command streams output and emits ssh_result."""
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=MagicMock(stdout="line1\nline2\n", exit_status=0))

    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        await manager.start_connection(
            user_id=1, session_id="sess-3", hostname="host",
            port=22, private_key_pem="key", username="user",
        )

    # Drain the ssh_result from connection
    bus.get_queue(1).get_nowait()

    output = await manager.run_command("sess-3", "echo hello")
    assert "line1" in output


@pytest.mark.asyncio
async def test_close_session(manager, bus):
    """close_session removes the session."""
    mock_conn = AsyncMock()
    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        await manager.start_connection(
            user_id=1, session_id="sess-4", hostname="host",
            port=22, private_key_pem="key", username="user",
        )
    bus.get_queue(1).get_nowait()  # drain connect event

    await manager.close_session("sess-4")
    assert "sess-4" not in manager._sessions
    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_max_sessions_per_user(manager, bus):
    """Enforces max 5 concurrent sessions per user."""
    mock_conn = AsyncMock()
    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        for i in range(5):
            await manager.start_connection(
                user_id=1, session_id=f"s-{i}", hostname="host",
                port=22, private_key_pem="key", username="user",
            )
        # 6th should fail
        await manager.start_connection(
            user_id=1, session_id="s-5", hostname="host",
            port=22, private_key_pem="key", username="user",
        )

    # Drain all events, last one should be failure
    events = []
    queue = bus.get_queue(1)
    while not queue.empty():
        events.append(queue.get_nowait())
    last = events[-1]
    assert last["type"] == "ssh_result"
    assert last["success"] is False
    assert "limit" in last["message"].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest django_airavata/apps/api/tests/test_ssh_manager.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the SSH session manager**

Create `django_airavata/apps/api/ssh_manager.py`:

```python
"""SSH session manager with interactive auth support.

Manages asyncssh connections, emits SSE events for prompts/results,
and accepts user responses via the event bus.
"""

from __future__ import annotations

import asyncio
import io
import logging
import time
import uuid
from dataclasses import dataclass, field

import asyncssh

from django_airavata.apps.api.sse import EventBus

logger = logging.getLogger(__name__)

MAX_SESSIONS_PER_USER = 5
SESSION_TIMEOUT = 300  # 5 minutes


@dataclass
class SSHSession:
    session_id: str
    user_id: int
    hostname: str
    conn: asyncssh.SSHClientConnection | None = None
    pending_event: asyncio.Event = field(default_factory=asyncio.Event)
    pending_response: str | None = None
    last_activity: float = field(default_factory=time.monotonic)


class InteractiveAuthHandler(asyncssh.SSHClient):
    """SSH client that emits prompts via SSE and waits for user responses."""

    def __init__(self, manager: SSHSessionManager, session: SSHSession) -> None:
        self._manager = manager
        self._session = session

    def connection_made(self, conn: asyncssh.SSHClientConnection) -> None:
        logger.info("SSH connection established to %s", self._session.hostname)

    def connection_lost(self, exc: Exception | None) -> None:
        if exc:
            logger.warning("SSH connection lost to %s: %s", self._session.hostname, exc)


class SSHSessionManager:
    """Manages SSH sessions with interactive authentication."""

    def __init__(self, event_bus: EventBus) -> None:
        self._bus = event_bus
        self._sessions: dict[str, SSHSession] = {}

    def _user_session_count(self, user_id: int) -> int:
        return sum(1 for s in self._sessions.values() if s.user_id == user_id)

    async def start_connection(
        self,
        user_id: int,
        session_id: str,
        hostname: str,
        port: int,
        private_key_pem: str,
        username: str,
    ) -> None:
        """Start an SSH connection. Results are pushed via SSE."""
        if self._user_session_count(user_id) >= MAX_SESSIONS_PER_USER:
            self._bus.push_event(user_id, {
                "type": "ssh_result",
                "session_id": session_id,
                "success": False,
                "message": f"Session limit reached (max {MAX_SESSIONS_PER_USER})",
                "data": None,
            })
            return

        session = SSHSession(session_id=session_id, user_id=user_id, hostname=hostname)
        self._sessions[session_id] = session

        try:
            # Load the private key
            key = asyncssh.import_private_key(private_key_pem)

            conn = await asyncssh.connect(
                hostname,
                port=port,
                username=username,
                client_keys=[key],
                known_hosts=None,  # Accept any host key in dev
            )
            session.conn = conn
            session.last_activity = time.monotonic()

            self._bus.push_event(user_id, {
                "type": "ssh_result",
                "session_id": session_id,
                "success": True,
                "message": f"Connected to {hostname}",
                "data": None,
            })

        except asyncssh.KeyImportError as e:
            self._cleanup_session(session_id)
            self._bus.push_event(user_id, {
                "type": "ssh_result",
                "session_id": session_id,
                "success": False,
                "message": f"Invalid SSH key: {e}",
                "data": None,
            })

        except (OSError, asyncssh.Error) as e:
            self._cleanup_session(session_id)
            self._bus.push_event(user_id, {
                "type": "ssh_result",
                "session_id": session_id,
                "success": False,
                "message": str(e),
                "data": None,
            })

    async def submit_response(self, session_id: str, response: str) -> bool:
        """Submit a response to a pending interactive prompt."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.pending_response = response
        session.pending_event.set()
        session.last_activity = time.monotonic()
        return True

    async def run_command(self, session_id: str, command: str) -> str:
        """Run a command on an established SSH session."""
        session = self._sessions.get(session_id)
        if not session or not session.conn:
            raise ValueError(f"No active session: {session_id}")

        session.last_activity = time.monotonic()

        try:
            result = await session.conn.run(command, check=False)
            output = result.stdout or ""

            # Stream output lines as ssh_output events
            for line in output.strip().split("\n"):
                if line:
                    self._bus.push_event(session.user_id, {
                        "type": "ssh_output",
                        "session_id": session_id,
                        "output": line,
                    })

            return output

        except (asyncssh.Error, OSError) as e:
            self._bus.push_event(session.user_id, {
                "type": "ssh_result",
                "session_id": session_id,
                "success": False,
                "message": f"Command failed: {e}",
                "data": None,
            })
            return ""

    async def close_session(self, session_id: str) -> None:
        """Close an SSH session and clean up."""
        session = self._sessions.get(session_id)
        if session and session.conn:
            session.conn.close()
        self._cleanup_session(session_id)

    def _cleanup_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def cleanup_expired(self) -> None:
        """Remove sessions that have been inactive for SESSION_TIMEOUT seconds."""
        now = time.monotonic()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_activity > SESSION_TIMEOUT
        ]
        for sid in expired:
            logger.info("Expiring SSH session %s", sid)
            await self.close_session(sid)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest django_airavata/apps/api/tests/test_ssh_manager.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/api/ssh_manager.py django_airavata/apps/api/tests/test_ssh_manager.py
git commit -m "feat: add SSH session manager with interactive auth support"
```

---

### Task 4: SSE and SSH API Endpoints

**Files:**
- Create: `django_airavata/apps/api/views_ssh.py`
- Modify: `django_airavata/apps/api/urls.py` (add routes)
- Create: `django_airavata/apps/api/scripts/info.sh` (copy from CS-Bridge)

- [ ] **Step 1: Copy info.sh into the API app**

```bash
cp /Users/yasith/code/artisan/CS-Bridge/main/scripts/info.sh \
   /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/apps/api/scripts/info.sh
```

- [ ] **Step 2: Create the API views**

Create `django_airavata/apps/api/views_ssh.py`:

```python
"""SSE streaming and SSH proxy API endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from django_airavata.apps.api.sse import event_bus
from django_airavata.apps.api.ssh_manager import SSHSessionManager

logger = logging.getLogger(__name__)

# Singleton SSH session manager
ssh_manager = SSHSessionManager(event_bus)

# Path to the HPC info script
INFO_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "scripts", "info.sh")


@csrf_exempt
@login_required
@require_GET
async def sse_events(request):
    """SSE endpoint — streams events to the authenticated user."""
    user_id = request.user.id

    async def stream():
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
async def ssh_test(request):
    """Start an SSH test connection.

    Request body: {"hostname": str, "port": int, "credential_token": str}
    Response: {"session_id": str}
    """
    body = json.loads(request.body)
    hostname = body["hostname"]
    port = body.get("port", 22)
    credential_token = body["credential_token"]
    session_id = str(uuid.uuid4())
    user_id = request.user.id
    gateway_id = settings.GATEWAY_ID

    # Fetch the SSH private key from the credential store
    try:
        credential = request.airavata_client.credential.get_SSH_credential(
            credential_token, gateway_id
        )
        # The credential object has a publicKey field; the private key
        # is stored encrypted in the credential store. For asyncssh we
        # need the PEM-encoded private key.
        private_key_pem = credential.privateKey
    except Exception as e:
        return JsonResponse({
            "error": f"Failed to fetch credential: {e}"
        }, status=400)

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
async def ssh_respond(request):
    """Submit a response to an interactive SSH prompt.

    Request body: {"session_id": str, "response": str}
    """
    body = json.loads(request.body)
    session_id = body["session_id"]
    response_text = body["response"]

    ok = await ssh_manager.submit_response(session_id, response_text)
    if not ok:
        return JsonResponse({"error": "Session not found"}, status=404)
    return JsonResponse({"ok": True})


@login_required
@require_POST
async def ssh_run(request):
    """Run a command on an established SSH session.

    Request body: {"session_id": str, "command": str}
    Response: {"output": str}
    """
    body = json.loads(request.body)
    session_id = body["session_id"]
    command = body["command"]

    try:
        output = await ssh_manager.run_command(session_id, command)
        return JsonResponse({"output": output})
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)


@login_required
@require_POST
async def ssh_run_info(request):
    """Run the HPC info.sh script on an established SSH session.

    Request body: {"session_id": str}
    Response: {"output": str, "partitions": [...]}
    """
    body = json.loads(request.body)
    session_id = body["session_id"]

    # Read the info script
    with open(INFO_SCRIPT_PATH) as f:
        script_content = f.read()

    try:
        output = await ssh_manager.run_command(session_id, f"sh -s <<'INFOSCRIPT'\n{script_content}\nINFOSCRIPT")

        # Parse the pipe-delimited output
        partitions = []
        lines = output.strip().split("\n")
        if len(lines) > 1:
            # Skip header line
            for line in lines[1:]:
                parts = line.split("|")
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
async def ssh_close(request):
    """Close an SSH session.

    Request body: {"session_id": str}
    """
    body = json.loads(request.body)
    session_id = body["session_id"]

    await ssh_manager.close_session(session_id)
    return JsonResponse({"ok": True})
```

- [ ] **Step 3: Add URL routes**

In `django_airavata/apps/api/urls.py`, add after line 7 (`from . import views`):

```python
from . import views_ssh
```

Then add to the `urlpatterns` list (before line 80 `urlpatterns = router.urls + ...`):

```python
    # SSE and SSH proxy endpoints
    re_path(r"^events/$", views_ssh.sse_events, name="sse-events"),
    re_path(r"^ssh/test/$", views_ssh.ssh_test, name="ssh-test"),
    re_path(r"^ssh/respond/$", views_ssh.ssh_respond, name="ssh-respond"),
    re_path(r"^ssh/run/$", views_ssh.ssh_run, name="ssh-run"),
    re_path(r"^ssh/run-info/$", views_ssh.ssh_run_info, name="ssh-run-info"),
    re_path(r"^ssh/close/$", views_ssh.ssh_close, name="ssh-close"),
```

- [ ] **Step 4: Verify endpoints are accessible**

Run the server and test:
```bash
curl -v http://localhost:8000/api/events/ 2>&1 | head -5
```
Expected: 302 redirect to login (since not authenticated) or 200 with `text/event-stream` content type if already logged in.

- [ ] **Step 5: Commit**

```bash
git add django_airavata/apps/api/views_ssh.py django_airavata/apps/api/urls.py django_airavata/apps/api/scripts/info.sh
git commit -m "feat: add SSE streaming and SSH proxy API endpoints"
```

---

### Task 5: Frontend SSE Client

**Files:**
- Create: `django_airavata/apps/api/static/django_airavata_api/js/utils/SSEClient.js`

- [ ] **Step 1: Create the SSE client singleton**

Create `django_airavata/apps/api/static/django_airavata_api/js/utils/SSEClient.js`:

```javascript
/**
 * SSE Client — singleton EventSource wrapper with typed event dispatch.
 *
 * Usage:
 *   import SSEClient from "./utils/SSEClient";
 *   SSEClient.connect();
 *   SSEClient.on("ssh_prompt", (event) => { ... });
 *   SSEClient.off("ssh_prompt", handler);
 */

class _SSEClient {
  constructor() {
    this._listeners = {};
    this._source = null;
    this._retryDelay = 1000;
    this._maxRetryDelay = 30000;
    this._connected = false;
  }

  connect() {
    if (this._source) return;

    this._source = new EventSource("/api/events/");
    this._retryDelay = 1000;

    this._source.onopen = () => {
      this._connected = true;
      this._retryDelay = 1000;
    };

    this._source.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);
        this._dispatch(event.type, event);
      } catch (err) {
        // Ignore parse errors (e.g. heartbeat comments)
      }
    };

    this._source.onerror = () => {
      this._connected = false;
      this._source.close();
      this._source = null;
      // Reconnect with exponential backoff
      setTimeout(() => this.connect(), this._retryDelay);
      this._retryDelay = Math.min(this._retryDelay * 2, this._maxRetryDelay);
    };
  }

  disconnect() {
    if (this._source) {
      this._source.close();
      this._source = null;
      this._connected = false;
    }
  }

  on(type, callback) {
    if (!this._listeners[type]) {
      this._listeners[type] = [];
    }
    this._listeners[type].push(callback);
  }

  off(type, callback) {
    if (!this._listeners[type]) return;
    this._listeners[type] = this._listeners[type].filter((cb) => cb !== callback);
  }

  _dispatch(type, event) {
    const handlers = this._listeners[type];
    if (handlers) {
      handlers.forEach((cb) => {
        try {
          cb(event);
        } catch (err) {
          console.error(`SSE handler error for ${type}:`, err);
        }
      });
    }
  }

  get connected() {
    return this._connected;
  }
}

const SSEClient = new _SSEClient();
export default SSEClient;
```

- [ ] **Step 2: Export from the API package**

In `django_airavata/apps/api/static/django_airavata_api/js/index.js`, find the utils exports section and add SSEClient. Search for where `FetchUtils` is exported and add alongside it:

```javascript
import SSEClient from "./utils/SSEClient";
```

And add `SSEClient` to the exported `utils` object.

- [ ] **Step 3: Commit**

```bash
git add django_airavata/apps/api/static/django_airavata_api/js/utils/SSEClient.js
git add django_airavata/apps/api/static/django_airavata_api/js/index.js
git commit -m "feat: add SSE client singleton with typed event dispatch"
```

---

### Task 6: SSH Prompt Notification Component

**Files:**
- Create: `django_airavata/static/common/js/components/SshPromptNotification.vue`
- Modify: `django_airavata/static/common/js/components/MainLayout.vue`

- [ ] **Step 1: Create the SSH prompt notification component**

Create `django_airavata/static/common/js/components/SshPromptNotification.vue`:

```vue
<template>
  <div class="ssh-prompts">
    <div v-for="prompt in activePrompts" :key="prompt.session_id" class="ssh-prompt-toast">
      <div class="ssh-prompt-toast__header">
        <i class="fa fa-terminal me-1"></i>
        <strong>SSH Authentication</strong>
      </div>
      <div class="ssh-prompt-toast__body">
        <div class="mb-2 text-muted" style="font-size: 0.8125rem;">{{ prompt.hostname }}</div>
        <div class="mb-2">{{ prompt.prompt }}</div>
        <div v-if="prompt.waiting" class="text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i>Authenticating...
        </div>
        <div v-else class="d-flex gap-2">
          <input
            class="form-control form-control-sm"
            :type="prompt.echo === false ? 'password' : 'text'"
            v-model="prompt.response"
            @keydown.enter="submitResponse(prompt)"
            placeholder="Enter response..."
            ref="promptInput"
          />
          <button class="btn btn-primary btn-sm" @click="submitResponse(prompt)">Send</button>
        </div>
      </div>
    </div>
    <div v-for="result in results" :key="result.session_id" class="ssh-prompt-toast"
      :class="result.success ? 'ssh-prompt-toast--success' : 'ssh-prompt-toast--error'">
      <div class="ssh-prompt-toast__body">
        <i :class="result.success ? 'fa fa-check-circle text-success' : 'fa fa-times-circle text-danger'" class="me-1"></i>
        {{ result.message }}
      </div>
    </div>
  </div>
</template>

<script>
import { utils } from "django-airavata-api";

const SSEClient = utils.SSEClient;
const FetchUtils = utils.FetchUtils;

export default {
  name: "ssh-prompt-notification",
  data() {
    return {
      activePrompts: [],
      results: [],
    };
  },
  methods: {
    onSshPrompt(event) {
      // Add or update prompt for this session
      const existing = this.activePrompts.find((p) => p.session_id === event.session_id);
      if (existing) {
        existing.prompt = event.prompt;
        existing.echo = event.echo;
        existing.waiting = false;
        existing.response = "";
      } else {
        this.activePrompts.push({
          session_id: event.session_id,
          hostname: event.hostname || "",
          prompt: event.prompt,
          echo: event.echo,
          response: "",
          waiting: false,
        });
      }
    },
    onSshResult(event) {
      // Remove any active prompt for this session
      this.activePrompts = this.activePrompts.filter((p) => p.session_id !== event.session_id);
      // Show result toast
      this.results.push({
        session_id: event.session_id,
        success: event.success,
        message: event.message,
      });
      // Auto-dismiss success after 3s
      if (event.success) {
        setTimeout(() => {
          this.results = this.results.filter((r) => r.session_id !== event.session_id);
        }, 3000);
      }
    },
    async submitResponse(prompt) {
      prompt.waiting = true;
      try {
        await FetchUtils.post("/api/ssh/respond/", {
          session_id: prompt.session_id,
          response: prompt.response,
        });
      } catch (e) {
        prompt.waiting = false;
      }
    },
    dismissResult(session_id) {
      this.results = this.results.filter((r) => r.session_id !== session_id);
    },
  },
  mounted() {
    SSEClient.on("ssh_prompt", this.onSshPrompt);
    SSEClient.on("ssh_result", this.onSshResult);
  },
  beforeUnmount() {
    SSEClient.off("ssh_prompt", this.onSshPrompt);
    SSEClient.off("ssh_result", this.onSshResult);
  },
};
</script>

<style scoped>
.ssh-prompts {
  position: fixed;
  top: 60px;
  right: 20px;
  z-index: 10001;
  width: 360px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ssh-prompt-toast {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}
.ssh-prompt-toast__header {
  padding: 8px 12px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.8125rem;
}
.ssh-prompt-toast__body {
  padding: 10px 12px;
  font-size: 0.875rem;
}
.ssh-prompt-toast--success {
  border-left: 3px solid #10b981;
}
.ssh-prompt-toast--error {
  border-left: 3px solid #ef4444;
}
</style>
```

- [ ] **Step 2: Integrate into MainLayout.vue**

In `django_airavata/static/common/js/components/MainLayout.vue`:

Add import after line 42 (`import NotificationsDisplay from "./NotificationsDisplay.vue";`):

```javascript
import SshPromptNotification from "./SshPromptNotification.vue";
import { utils } from "django-airavata-api";
```

Add to the components object (add `SshPromptNotification` alongside existing components).

In the `<template>`, add just before `<notifications-display />` (line 7):

```html
      <ssh-prompt-notification />
```

In `created()`, add SSE client initialization after the existing event listeners (after line 79):

```javascript
    // Connect the SSE client for real-time events
    utils.SSEClient.connect();
```

In `beforeUnmount()`, add cleanup after the existing removeEventListener calls:

```javascript
    utils.SSEClient.disconnect();
```

- [ ] **Step 3: Build common JS bundle to verify compilation**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/static/common
npx vite build
```

Expected: Build succeeds without errors.

- [ ] **Step 4: Commit**

```bash
git add django_airavata/static/common/js/components/SshPromptNotification.vue
git add django_airavata/static/common/js/components/MainLayout.vue
git commit -m "feat: add SSH prompt notification component with SSE integration"
```

---

### Task 7: End-to-End Manual Test

**Files:** None (verification only)

- [ ] **Step 1: Build all frontend bundles**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal
cd django_airavata/apps/api && yarn && yarn run build
cd ../../static/common && npx vite build
cd ../../apps/workspace && npx vite build
cd ../admin && npx vite build
cd ../groups && npx vite build
```

- [ ] **Step 2: Start the portal with uvicorn**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal
uv sync
uv run uvicorn django_airavata.asgi:application --host 0.0.0.0 --port 8000 --reload --reload-dir django_airavata
```

- [ ] **Step 3: Verify SSE connection in browser**

Open Chrome DevTools, go to `http://localhost:8000/workspace/applications`.
In the Network tab, filter by "EventStream" — verify `/api/events/` connection is established and heartbeats arrive every 15s.

- [ ] **Step 4: Test SSH connection to local SFTP container**

Open browser console and run:
```javascript
fetch('/api/ssh/test/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1]},
  body: JSON.stringify({hostname: 'localhost', port: 2222, credential_token: '<dev-sftp-token>'}),
  credentials: 'same-origin'
}).then(r => r.json()).then(d => console.log('SESSION:', d));
```

Expected: Either a success notification toast appears (key auth works), or a prompt notification appears requesting password.

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "feat: SSE infrastructure + interactive SSH proxy complete"
```
