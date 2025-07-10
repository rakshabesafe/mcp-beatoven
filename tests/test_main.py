import pytest
import pytest_asyncio # For async fixtures
import json
import asyncio
import logging # Added logger
from unittest.mock import patch, AsyncMock, MagicMock

# Import FastMCP and its client
from fastmcp import FastMCP as FastMCPApp # Alias to avoid confusion with mcp fixture
from fastmcp.client import Client as FastMCPClient
from fastmcp.exceptions import ToolError # For testing tool exceptions

# Import FastAPI TestClient for custom routes
from fastapi.testclient import TestClient

# Modules from our application
from main import mcp as global_mcp_server_instance, asgi_app as global_asgi_app
from models import CompositionRequest, Prompt, CompositionResponse, TaskStatus, TrackMeta
from api_client import BeatovenAPIClient # For mocking

# --- Fixtures ---

@pytest.fixture
def mock_beatoven_api_client_instance():
    """Mocks an instance of BeatovenAPIClient."""
    mock = AsyncMock(spec=BeatovenAPIClient)
    mock.compose_track.return_value = CompositionResponse(status="started", task_id="fake_task_id")
    mock.get_task_status = AsyncMock()
    return mock

@pytest_asyncio.fixture
async def mcp_server_with_mocked_api(mock_beatoven_api_client_instance: AsyncMock):
    """
    Provides the FastMCP server instance from main.py, with BeatovenAPIClient patched.
    """
    with patch('main.BeatovenAPIClient', return_value=mock_beatoven_api_client_instance):
        yield global_mcp_server_instance

@pytest_asyncio.fixture
async def f_mcp_client(mcp_server_with_mocked_api: FastMCPApp):
    """Provides a FastMCPClient configured to talk to our MCP server in-memory."""
    # The server argument for FastMCPClient is the FastMCPApp instance itself.
    async with FastMCPClient(mcp_server_with_mocked_api) as client: # Corrected: positional argument
        yield client

@pytest.fixture
def http_test_client(mock_beatoven_api_client_instance: AsyncMock):
    """
    Provides a FastAPI TestClient for the global ASGI app, with BeatovenAPIClient patched.
    """
    with patch('main.BeatovenAPIClient', return_value=mock_beatoven_api_client_instance):
        client = TestClient(global_asgi_app)
        yield client


# --- Tests for MCP Tools ---

@pytest.mark.asyncio
async def test_compose_track_tool_success(f_mcp_client: FastMCPClient, mock_beatoven_api_client_instance: AsyncMock):
    tool_input = {
        "prompt_text": "A happy tune",
        "format": "mp3",
        "looping": True
    }
    result = await f_mcp_client.call_tool("compose_track", tool_input)

    assert result.data is not None
    # Assuming result.data is already the CompositionResponse instance as returned by the tool
    response_data: CompositionResponse = result.data

    assert response_data.status == "started"
    assert response_data.task_id == "fake_task_id"

    mock_beatoven_api_client_instance.compose_track.assert_awaited_once()
    called_with_request: CompositionRequest = mock_beatoven_api_client_instance.compose_track.call_args[0][0]
    assert called_with_request.prompt.text == "A happy tune"
    assert called_with_request.format == "mp3"
    assert called_with_request.looping is True

@pytest.mark.asyncio
async def test_compose_track_tool_api_exception(f_mcp_client: FastMCPClient, mock_beatoven_api_client_instance: AsyncMock):
    expected_error_detail = "Beatoven API is down"
    # The tool in main.py raises HTTPException. FastMCP converts this.
    # Based on FastMCP behavior, it often wraps it in a ToolError, and the detail might be the stringified HTTPException.
    mock_beatoven_api_client_instance.compose_track.side_effect = Exception(expected_error_detail)

    tool_input = {"prompt_text": "An epic score"}

    with pytest.raises(ToolError) as exc_info:
        await f_mcp_client.call_tool("compose_track", tool_input)

    # FastMCP's ToolError.detail often contains the string representation of the original error,
    # or a dictionary if the original error was structured (like an MCPError).
    # If the tool raises HTTPException("detail_string"), the detail in ToolError might be that string.
    # The string representation of ToolError itself should contain the original error message.
    assert expected_error_detail in str(exc_info.value)


# --- Tests for Custom SSE Route ---

@pytest.mark.anyio(backend='asyncio')
def test_subscribe_to_task_updates_sse(http_test_client: TestClient, mock_beatoven_api_client_instance: AsyncMock):
    task_id = "test_sse_task_id"

    status_composing = TaskStatus(status="composing", meta=None)
    status_composed_meta = TrackMeta(
        project_id="proj", track_id=task_id, prompt=Prompt(text="test"), version=1,
        track_url="http://example.com/track.wav", stems_url={}
    )
    status_composed = TaskStatus(status="composed", meta=status_composed_meta)

    mock_beatoven_api_client_instance.get_task_status.side_effect = [
        status_composing,
        status_composed
    ]
    print(f"DEBUG test_sse: mock_client is {id(mock_beatoven_api_client_instance)}, mock_client.get_task_status is {id(mock_beatoven_api_client_instance.get_task_status)}")


    # Use http_test_client.stream for SSE
    with http_test_client.stream("GET", f"/tasks/{task_id}/subscribe") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8" # Corrected assertion

        events = []
        current_event = {}
        # response.iter_lines() is from httpx.Response, used by TestClient
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event["event"] = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                current_event["data"] = line.split(":", 1)[1].strip()
            elif line == "" and current_event:
                events.append(current_event)
                current_event = {}

        if current_event:
            events.append(current_event)

    assert len(events) == 3

    assert events[0]["event"] == "update"
    data0 = json.loads(events[0]["data"])
    assert data0["status"] == "composing"

    assert events[1]["event"] == "update"
    data1 = json.loads(events[1]["data"])
    assert data1["status"] == "composed"

    assert events[2]["event"] == "complete"
    data2 = json.loads(events[2]["data"])
    assert data2["status"] == "composed"

    assert mock_beatoven_api_client_instance.get_task_status.call_count == 2
    mock_beatoven_api_client_instance.get_task_status.assert_any_call(task_id)


@pytest.mark.anyio(backend='asyncio')
def test_subscribe_to_task_updates_sse_api_error(http_test_client: TestClient, mock_beatoven_api_client_instance: AsyncMock):
    task_id = "test_sse_error_task_id"
    mock_beatoven_api_client_instance.get_task_status.side_effect = Exception("API Call Failed")

    with http_test_client.stream("GET", f"/tasks/{task_id}/subscribe") as response:
        assert response.status_code == 200

        events = []
        current_event = {}
        for line in response.iter_lines():
            if line.startswith("event:"):
                current_event["event"] = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                current_event["data"] = line.split(":", 1)[1].strip()
            elif line == "" and current_event:
                events.append(current_event)
                current_event = {}
        if current_event:
            events.append(current_event)

    assert len(events) == 1
    assert events[0]["event"] == "error"
    data = json.loads(events[0]["data"])
    assert "API Call Failed" in data["error"]
    assert data["task_id"] == task_id

    mock_beatoven_api_client_instance.get_task_status.assert_called_once_with(task_id)


@pytest.mark.skip(reason="Dependency init failure test needs rework for FastMCP context")
def test_api_client_dependency_init_failure():
    pass
