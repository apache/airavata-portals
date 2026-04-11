"""SSH session manager with interactive auth support.

Manages asyncssh connections, emits SSE events for prompts/results,
and accepts user responses via the event bus.
"""

from __future__ import annotations

import asyncio
import logging
import time
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
            key = asyncssh.import_private_key(private_key_pem)

            conn = await asyncssh.connect(
                hostname,
                port=port,
                username=username,
                client_keys=[key],
                known_hosts=None,
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
        """Remove sessions inactive for SESSION_TIMEOUT seconds."""
        now = time.monotonic()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_activity > SESSION_TIMEOUT
        ]
        for sid in expired:
            logger.info("Expiring SSH session %s", sid)
            await self.close_session(sid)
