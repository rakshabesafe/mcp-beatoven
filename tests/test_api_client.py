import pytest
import pytest_asyncio
import aiohttp
import os # Added import
from unittest.mock import patch, MagicMock
from api_client import BeatovenAPIClient, API_KEY, BASE_URL
from models import CompositionRequest, Prompt, CompositionResponse, TaskStatus, TrackMeta

@pytest.fixture
def client():
    if not API_KEY:
        pytest.skip("BEATOVEN_API_KEY not set, skipping integration tests that might require it if mocks fail")
    return BeatovenAPIClient()

@pytest_asyncio.fixture
async def mock_session_post():
    with patch("aiohttp.ClientSession.post") as mock_post:
        yield mock_post

@pytest_asyncio.fixture
async def mock_session_get():
    with patch("aiohttp.ClientSession.get") as mock_get:
        yield mock_get

@pytest.mark.asyncio
async def test_compose_track_success(client: BeatovenAPIClient, mock_session_post):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json.return_value = {"status": "started", "task_id": "test_task_id"}
    mock_session_post.return_value.__aenter__.return_value = mock_response

    request_data = CompositionRequest(prompt=Prompt(text="test prompt"))
    response = await client.compose_track(request_data)

    assert response.status == "started"
    assert response.task_id == "test_task_id"
    mock_session_post.assert_called_once_with(
        f"{BASE_URL}/tracks/compose",
        json={"prompt": {"text": "test prompt"}, "format": "wav", "looping": False},
        headers=client.headers,
    )

@pytest.mark.asyncio
async def test_get_task_status_success(client: BeatovenAPIClient, mock_session_get):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_task_meta = TrackMeta(
        project_id="proj_id",
        track_id="track_id",
        prompt=Prompt(text="test prompt"),
        version=1,
        track_url="http://example.com/track.wav",
        stems_url={"bass": "http://example.com/bass.wav"}
    )
    mock_response.json.return_value = {"status": "composed", "meta": mock_task_meta.model_dump()}
    mock_session_get.return_value.__aenter__.return_value = mock_response

    task_id = "test_task_id"
    response = await client.get_task_status(task_id)

    assert response.status == "composed"
    assert response.meta is not None
    assert response.meta.track_id == "track_id"
    mock_session_get.assert_called_once_with(
        f"{BASE_URL}/tasks/{task_id}",
        json=None,
        headers=client.headers,
    )

@pytest.mark.asyncio
async def test_compose_track_connection_error(client: BeatovenAPIClient, mock_session_post):
    mock_session_post.side_effect = aiohttp.ClientConnectionError("Connection failed")

    request_data = CompositionRequest(prompt=Prompt(text="test prompt"))
    with pytest.raises(Exception, match="Could not connect to Beatoven API: Connection failed"):
        await client.compose_track(request_data)

@pytest.mark.asyncio
async def test_get_task_status_api_error(client: BeatovenAPIClient, mock_session_get):
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.message = "Internal Server Error"
    mock_response.json.return_value = {"error": "Server error"} # Ensure json() is awaitable if called

    # Make raise_for_status() do its job
    mock_response.raise_for_status = MagicMock(side_effect=aiohttp.ClientResponseError(
        request_info=MagicMock(),
        history=MagicMock(),
        status=500,
        message="Internal Server Error",
        headers=MagicMock()
    ))
    mock_session_get.return_value.__aenter__.return_value = mock_response

    task_id = "test_task_id"
    with pytest.raises(Exception, match="Beatoven API request failed with status 500: {'error': 'Server error'}"):
        await client.get_task_status(task_id)

def test_api_client_init_no_key():
    with patch.dict(os.environ, {"BEATOVEN_API_KEY": ""}):
         # Reload api_client to re-evaluate API_KEY at module level after patch
        import importlib
        import api_client
        importlib.reload(api_client)
        with pytest.raises(ValueError, match="BEATOVEN_API_KEY environment variable not set."):
            api_client.BeatovenAPIClient()
        # Restore original API_KEY for other tests
        importlib.reload(api_client) # Reload again to restore original state if necessary
        api_client.API_KEY = API_KEY # Or directly restore the original module variable

@pytest.mark.asyncio
async def test_api_client_request_unexpected_error(client: BeatovenAPIClient, mock_session_post):
    mock_session_post.side_effect = Exception("Unexpected network issue")
    request_data = CompositionRequest(prompt=Prompt(text="test prompt"))
    with pytest.raises(Exception, match="An unexpected error occurred: Unexpected network issue"):
        await client.compose_track(request_data)
