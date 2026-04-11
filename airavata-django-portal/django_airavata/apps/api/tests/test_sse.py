import asyncio
import json
import pytest
from django_airavata.apps.api.sse import EventBus


@pytest.fixture
def bus():
    return EventBus()


@pytest.mark.asyncio
async def test_push_and_receive(bus):
    """Pushed events appear in the user's queue."""
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
