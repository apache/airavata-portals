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
        with patch("asyncssh.import_private_key", return_value=MagicMock()):
            await manager.start_connection(
                user_id=1, session_id="sess-1", hostname="localhost",
                port=22, private_key_pem="fake-key", username="testuser",
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
        with patch("asyncssh.import_private_key", return_value=MagicMock()):
            await manager.start_connection(
                user_id=1, session_id="sess-2", hostname="bad-host",
                port=22, private_key_pem="fake-key", username="testuser",
            )

    queue = bus.get_queue(1)
    event = queue.get_nowait()
    assert event["type"] == "ssh_result"
    assert event["success"] is False
    assert "Connection refused" in event["message"]


@pytest.mark.asyncio
async def test_run_command(manager, bus):
    """run_command streams output and returns it."""
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=MagicMock(stdout="line1\nline2\n", exit_status=0))

    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        with patch("asyncssh.import_private_key", return_value=MagicMock()):
            await manager.start_connection(
                user_id=1, session_id="sess-3", hostname="host",
                port=22, private_key_pem="key", username="user",
            )

    bus.get_queue(1).get_nowait()  # drain connect event
    output = await manager.run_command("sess-3", "echo hello")
    assert "line1" in output


@pytest.mark.asyncio
async def test_close_session(manager, bus):
    """close_session removes the session."""
    mock_conn = AsyncMock()
    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        with patch("asyncssh.import_private_key", return_value=MagicMock()):
            await manager.start_connection(
                user_id=1, session_id="sess-4", hostname="host",
                port=22, private_key_pem="key", username="user",
            )
    bus.get_queue(1).get_nowait()

    await manager.close_session("sess-4")
    assert "sess-4" not in manager._sessions
    mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_max_sessions_per_user(manager, bus):
    """Enforces max 5 concurrent sessions per user."""
    mock_conn = AsyncMock()
    with patch("asyncssh.connect", new_callable=AsyncMock, return_value=mock_conn):
        with patch("asyncssh.import_private_key", return_value=MagicMock()):
            for i in range(5):
                await manager.start_connection(
                    user_id=1, session_id=f"s-{i}", hostname="host",
                    port=22, private_key_pem="key", username="user",
                )
            await manager.start_connection(
                user_id=1, session_id="s-5", hostname="host",
                port=22, private_key_pem="key", username="user",
            )

    events = []
    queue = bus.get_queue(1)
    while not queue.empty():
        events.append(queue.get_nowait())
    last = events[-1]
    assert last["type"] == "ssh_result"
    assert last["success"] is False
    assert "limit" in last["message"].lower()
