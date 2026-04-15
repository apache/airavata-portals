"""Server-Sent Events (SSE) event bus.

Per-connection async queues for pushing real-time events to the browser.

Each SSE connection creates a fresh ``asyncio.Queue`` inside its own event
loop and registers it as a subscriber. Events published via
:meth:`EventBus.push_event` are fanned out to every live subscriber for that
user. This avoids the "Queue is bound to a different event loop" error that
happens when a module-level / long-lived queue is reused across separate
``StreamingHttpResponse`` invocations (Django creates a new event loop per
async request when running under the classic WSGI-with-async-views bridge).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


class EventBus:
    """In-process event bus with per-connection async queues.

    ``_subscribers`` maps ``user_id`` -> list of live subscriber queues.
    A new queue is created for every :meth:`event_stream` invocation so it
    is always bound to the caller's current event loop.

    ``_pending`` buffers events pushed for a user who has no live subscriber
    yet. When a subscriber connects it drains the pending buffer first. This
    preserves the simple "push then get_queue" usage pattern exercised by
    tests without the lifetime hazards of a shared, loop-bound queue.
    """

    def __init__(self) -> None:
        self._subscribers: dict[int, list[asyncio.Queue]] = defaultdict(list)
        self._pending: dict[int, list[dict]] = defaultdict(list)
        # Kept for backward compatibility with existing tests that poke at
        # ``_queues`` / ``get_queue`` directly.
        self._queues: dict[int, asyncio.Queue] = {}

    def _subscribe(self, user_id: int) -> asyncio.Queue:
        """Create and register a fresh queue for the current event loop."""
        queue: asyncio.Queue = asyncio.Queue()
        # Drain any events that were pushed before this subscriber arrived.
        for event in self._pending.pop(user_id, []):
            queue.put_nowait(event)
        self._subscribers[user_id].append(queue)
        return queue

    def _unsubscribe(self, user_id: int, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(user_id)
        if not subs:
            return
        try:
            subs.remove(queue)
        except ValueError:
            pass
        if not subs:
            self._subscribers.pop(user_id, None)

    def get_queue(self, user_id: int) -> asyncio.Queue:
        """Return a per-user queue.

        Primarily kept for tests and synchronous inspection. If events were
        pushed before any subscriber existed, they are moved into this queue
        so callers can drain them with ``get_nowait``.
        """
        queue = self._queues.get(user_id)
        if queue is None:
            queue = asyncio.Queue()
            self._queues[user_id] = queue
        for event in self._pending.pop(user_id, []):
            queue.put_nowait(event)
        return queue

    def push_event(self, user_id: int, event: dict) -> None:
        """Publish an event to every live subscriber for ``user_id``.

        If there are no live subscribers and no legacy ``_queues`` entry,
        the event is buffered in ``_pending`` so the next subscriber (or
        ``get_queue`` caller) can drain it.
        """
        delivered = False
        for queue in list(self._subscribers.get(user_id, [])):
            try:
                queue.put_nowait(event)
                delivered = True
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to enqueue SSE event for user %s", user_id)

        legacy_queue = self._queues.get(user_id)
        if legacy_queue is not None:
            try:
                legacy_queue.put_nowait(event)
                delivered = True
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to enqueue SSE event on legacy queue for user %s", user_id)

        if not delivered:
            self._pending[user_id].append(event)

    async def event_stream(self, user_id: int) -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted lines.

        Creates a fresh queue bound to the caller's current event loop and
        unregisters it on exit. Includes a heartbeat comment every
        ``HEARTBEAT_INTERVAL`` seconds to keep the connection alive through
        proxies.
        """
        queue = self._subscribe(user_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            self._unsubscribe(user_id, queue)

    def cleanup(self, user_id: int) -> None:
        """Forget any legacy queue state for ``user_id``.

        Live subscribers clean themselves up in ``event_stream``'s ``finally``
        block; this method only clears the legacy ``_queues`` mapping and any
        pending buffer, matching the semantics expected by existing tests.
        """
        self._queues.pop(user_id, None)
        self._pending.pop(user_id, None)


# Singleton instance
event_bus = EventBus()
