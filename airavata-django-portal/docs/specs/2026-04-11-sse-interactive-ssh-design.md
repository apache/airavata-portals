# SSE Infrastructure + Interactive SSH Proxy

**Date:** 2026-04-11
**Status:** Draft
**Scope:** Sub-project 1 of 4 (Portal Functionality)

## Overview

Add a server-sent events (SSE) infrastructure to the Airavata Django portal and an interactive SSH proxy that handles authentication prompts in real-time. This is the foundation for storage/compute connection testing, HPC discovery, and experiment submission auth flows.

## Architecture

```
Browser                    Django (ASGI/uvicorn)          Remote Host
+--------------+          +-------------------+          +----------+
|  EventSource +---SSE--->|  /api/events/     |          |          |
|  (subscribe) |          |  (async stream)   |          |  SSH     |
|              |          |                   | asyncssh |  Server  |
|  fetch POST  +---REST-->|  /api/ssh/test/   |--------->|          |
|  (respond)   |          |  /api/ssh/respond/|          |          |
+--------------+          +-------------------+          +----------+
```

- SSE for server-to-browser push (prompts, results, notifications)
- REST POST for browser-to-server responses (prompt answers)
- Django 5.1 native async views under uvicorn (no Channels)
- asyncssh for non-blocking SSH connections

## SSE Event Protocol

All events are JSON with a `type` field. The SSE stream uses standard `data:` framing.

### Server to Browser

```json
{"type": "ssh_prompt", "session_id": "abc123", "prompt": "Password: ", "echo": false}
{"type": "ssh_result", "session_id": "abc123", "success": true, "message": "Connected", "data": null}
{"type": "ssh_output", "session_id": "abc123", "output": "partition|nodes|..."}
{"type": "notification", "id": "n-456", "title": "...", "message": "...", "level": "info"}
{"type": "heartbeat"}
```

- `echo: false` tells the frontend to mask the input field (password)
- `ssh_output` streams command output line-by-line
- `data` on `ssh_result` carries parsed results (e.g., HPC info JSON)

### Browser to Server

```
POST /api/ssh/respond/
{"session_id": "abc123", "response": "my_password"}
```

## Server-Side Components

### 1. `apps/api/sse.py` --- Event Bus

Per-user async queue for SSE events.

- `push_event(user_id: int, event: dict)` --- enqueue event
- `event_stream(user_id: int) -> AsyncGenerator[str]` --- yields SSE-formatted lines
- Heartbeat every 15 seconds to keep the connection alive
- Queue per user, created on first SSE connection, cleaned up on disconnect

### 2. `apps/api/ssh_manager.py` --- SSH Session Manager

Manages asyncssh sessions with interactive auth support.

- `start_connection(user_id, session_id, hostname, port, credential_token, gateway_id)`:
  1. Fetches SSH private key from credential store via `airavata_client.credential.get_SSH_credential()`
  2. Attempts `asyncssh.connect()` with key auth
  3. If interactive auth required: pushes `ssh_prompt` event, awaits response via `asyncio.Event`
  4. On success: pushes `ssh_result` with `success: true`
  5. On failure: pushes `ssh_result` with `success: false, message: error`

- `submit_response(session_id, response)`: Sets the response value and unblocks the waiting auth handler

- `run_command(session_id, command)`: Executes a shell command on an established session. Streams stdout lines as `ssh_output` events. Returns full output.

- `close_session(session_id)`: Closes SSH connection, removes from active sessions

- Sessions auto-expire after 5 minutes of inactivity (background cleanup task)
- Session dict: `{session_id: {conn, user_id, hostname, pending_event, pending_response, last_activity}}`

### 3. `apps/api/views_ssh.py` --- API Endpoints

All endpoints require authentication (`@login_required`).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/events/` | SSE stream (async `StreamingHttpResponse`) |
| POST | `/api/ssh/test/` | Start test connection: `{hostname, port, credential_token}` |
| POST | `/api/ssh/respond/` | Submit prompt response: `{session_id, response}` |
| POST | `/api/ssh/run/` | Run command: `{session_id, command}` |
| POST | `/api/ssh/close/` | Close session: `{session_id}` |

The `/api/events/` endpoint:
- Returns `Content-Type: text/event-stream`
- Async view using `StreamingHttpResponse` with async generator
- CSRF exempt (GET-only, session-authenticated)
- One connection per browser tab (auto-reconnects via EventSource)

The `/api/ssh/test/` endpoint:
- Generates a `session_id` (UUID)
- Kicks off `ssh_manager.start_connection()` as an async task
- Returns immediately with `{session_id}` --- results come via SSE
- The credential token maps to the SSH key in the Airavata credential store

## Frontend Components

### 1. `apps/api/static/django_airavata_api/js/utils/SSEClient.js` --- Client Singleton

```javascript
class SSEClient {
  constructor() { this.listeners = {}; this.source = null; }
  connect() { /* EventSource to /api/events/, parse JSON, dispatch */ }
  on(type, callback) { /* register listener */ }
  off(type, callback) { /* unregister */ }
  disconnect() { /* close EventSource */ }
}
export default new SSEClient();
```

- Auto-reconnects with exponential backoff (1s, 2s, 4s, max 30s)
- Initialized in `MainLayout.vue` on mount
- Parses each SSE `data:` line as JSON, dispatches to typed listeners

### 2. `static/common/js/components/SshPromptNotification.vue` --- Prompt Widget

- Fixed-position toast at top-right of content area
- Listens for `ssh_prompt` and `ssh_result` events via SSEClient
- Renders: hostname label + prompt text + input field + Submit button
- Input is `type="password"` when `echo: false`, `type="text"` otherwise
- On submit: `POST /api/ssh/respond/` with `{session_id, response}`
- Shows spinner between submit and next event
- On `ssh_result` success: green check + message, auto-dismiss 3s
- On `ssh_result` failure: red X + error message, manual dismiss
- Stacks multiple concurrent prompts vertically

### 3. Integration Points

**MainLayout.vue:**
- Import and mount `SshPromptNotification` component
- Initialize `SSEClient.connect()` on mount, disconnect on unmount

**Storage/Compute pages (usage pattern):**
```javascript
async testConnection(hostname, credentialToken) {
  const { session_id } = await FetchUtils.post('/api/ssh/test/', {
    hostname, port: 22, credential_token: credentialToken
  });
  // SSE handles all prompts/results automatically via SshPromptNotification
  // Caller can also listen: SSEClient.on('ssh_result', handler)
}
```

## ASGI Migration

### New Dependencies (pyproject.toml)
- `asyncssh>=2.17`
- `uvicorn[standard]>=0.32`

### New File: `django_airavata/asgi.py`
Standard Django ASGI application entry point.

### Settings Change
- Add `ASGI_APPLICATION = "django_airavata.asgi.application"`

### Tiltfile Change
Replace runserver with uvicorn:
```
uv run uvicorn django_airavata.asgi:application --host 0.0.0.0 --port 8000 --reload
```

Existing synchronous views continue to work unchanged under uvicorn.

## Credential Flow

1. User selects a credential token from the SSH credential selector dropdown
2. On "Test Connection", portal sends `{hostname, credential_token}` to `/api/ssh/test/`
3. Server fetches the encrypted private key from Airavata credential store via gRPC
4. Server decrypts and loads the key into asyncssh
5. If key auth succeeds: `ssh_result` with success
6. If interactive auth needed: `ssh_prompt` with the prompt text
7. User responds via notification form
8. Server forwards response to SSH session
9. Repeat 6-8 until auth completes or fails
10. Private keys never leave the server

## HPC Discovery (info.sh)

Once an SSH session is established to an HPC host:

1. Server runs `info.sh` via `ssh_manager.run_command()`
2. Output streamed as `ssh_output` events
3. Frontend parses the pipe-delimited output:
   ```
   partition|nodes|max_cpus_per_node|max_mem_mb_per_node|max_gpus_per_node|gpu_types|accounts
   ```
4. Auto-populates the compute resource's batch queues, GPU types, and account lists
5. The `info.sh` script is embedded in the Django app (copied from CS-Bridge)

## Session Lifecycle

```
test/ called --> session created --> key auth attempted
                                         |
                              +----------+-----------+
                              |                      |
                         auth success            auth prompt
                              |                      |
                        ssh_result(ok)          ssh_prompt(text)
                              |                      |
                         ready for              user responds
                         run_command()               |
                              |                 auth callback
                              |                      |
                         run/ called          (loop or success)
                              |
                        ssh_output(lines)
                              |
                        ssh_result(data)
                              |
                        close/ called
                              |
                        session destroyed
```

Sessions expire after 5 minutes of inactivity. Background cleanup runs every 60 seconds.

## Security

- All endpoints require Django session authentication
- SSE endpoint is CSRF-exempt (GET only, no state mutation)
- POST endpoints use standard CSRF token from cookie
- SSH private keys are held in server memory only during active sessions
- Session IDs are UUIDs, not guessable
- Each user can only access their own SSH sessions
- Rate limit: max 5 concurrent SSH sessions per user

## Testing Plan

1. Unit test `ssh_manager.py` with mock asyncssh (key auth, interactive auth, timeout)
2. Unit test `sse.py` event queue and streaming
3. Integration test: start SSE connection, trigger test, verify events received
4. Manual test in Chrome: connect to local SFTP container (key auth, no prompt)
5. Manual test: connect to HPC host requiring password (interactive prompt flow)
6. Manual test: run info.sh on HPC host, verify partition data parsed correctly
