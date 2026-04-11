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

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": heartbeat\n\n"

    def cleanup(self, user_id: int) -> None:
        self._queues.pop(user_id, None)


# Singleton instance
event_bus = EventBus()
