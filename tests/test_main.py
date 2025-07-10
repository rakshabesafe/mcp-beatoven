import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import importlib # Moved importlib here
import api_client # Added import for the module
from main import app, get_api_client
from models import CompositionRequest, Prompt, CompositionResponse, TaskStatus, TrackMeta
from api_client import BeatovenAPIClient # Corrected import

# Create a TestClient instance for your FastAPI app
client = TestClient(app)

# --- Mocks for BeatovenAPIClient ---
@pytest.fixture
def mock_api_client():
    mock = AsyncMock(spec=BeatovenAPIClient)
    # Configure default return values for mocked methods
    mock.compose_track.return_value = CompositionResponse(status="started", task_id="fake_task_id")

    mock_track_meta = TrackMeta(
        project_id="proj_id",
        track_id="track_id_from_mock",
        prompt=Prompt(text="mock prompt"),
        version=1,
        track_url="http://example.com/mock_track.wav",
        stems_url={"bass": "http://example.com/mock_bass.wav"}
    )
    mock.get_task_status.return_value = TaskStatus(status="composed", meta=mock_track_meta)
    return mock

# --- Dependency Override ---
# This fixture will be used by tests to override the get_api_client dependency
@pytest.fixture(autouse=True) # autouse=True to apply this to all tests in this file
def override_api_client_dependency(mock_api_client):
    app.dependency_overrides[get_api_client] = lambda: mock_api_client
    yield
    # Clean up: remove the override after tests are done
    app.dependency_overrides = {}


# --- Test Cases for /compose endpoint ---
def test_compose_success(mock_api_client):
    payload = {"prompt": {"text": "A happy tune"}, "format": "mp3"}
    response = client.post("/compose", json=payload)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "started"
    assert json_response["task_id"] == "fake_task_id"

    # Verify that the mock client's method was called correctly
    mock_api_client.compose_track.assert_awaited_once()
    # You can add more detailed assertions on the arguments if needed
    # For example, checking the CompositionRequest object passed to the mock
    called_with_request = mock_api_client.compose_track.call_args[0][0]
    assert isinstance(called_with_request, CompositionRequest)
    assert called_with_request.prompt.text == "A happy tune"
    assert called_with_request.format == "mp3"

def test_compose_validation_error():
    # Invalid format
    payload = {"prompt": {"text": "A sad tune"}, "format": "ogg"}
    response = client.post("/compose", json=payload)
    assert response.status_code == 422 # Unprocessable Entity for validation errors

    # Missing prompt
    payload = {"format": "wav"}
    response = client.post("/compose", json=payload)
    assert response.status_code == 422

def test_compose_api_client_exception(mock_api_client):
    mock_api_client.compose_track.side_effect = Exception("Beatoven API is down")

    payload = {"prompt": {"text": "An epic score"}}
    response = client.post("/compose", json=payload)

    assert response.status_code == 500
    assert response.json() == {"detail": "Beatoven API is down"}

# --- Test Cases for /tasks/{task_id} endpoint ---
def test_get_task_status_success(mock_api_client):
    task_id = "some_task_id"
    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "composed"
    assert json_response["meta"]["track_id"] == "track_id_from_mock"

    mock_api_client.get_task_status.assert_awaited_once_with(task_id)

def test_get_task_status_api_client_exception(mock_api_client):
    task_id = "another_task_id"
    mock_api_client.get_task_status.side_effect = Exception("Failed to fetch status")

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to fetch status"}

# Test for API Key not configured scenario for the dependency
def test_api_client_dependency_init_failure():
    # Temporarily remove the override for this specific test
    app.dependency_overrides = {}

    with patch.dict(importlib.import_module("api_client").os.environ, {"BEATOVEN_API_KEY": ""}):
        # Ensure api_client is reloaded to pick up the patched environment variable
        # Using module-level imports for importlib and api_client
        importlib.reload(api_client)

        # Make a call that would trigger the dependency
        response = client.post("/compose", json={"prompt": {"text": "test"}})
        assert response.status_code == 500 # or whatever status code your app returns
        assert "BEATOVEN_API_KEY environment variable not set" in response.json()["detail"]

        # Restore API_KEY for other tests by reloading again
        # Or set it back to a valid dummy value if needed for module-level constants
        original_api_key = os.getenv("BEATOVEN_API_KEY_ORIGINAL_FOR_TEST", "dummy_key_to_prevent_later_failures") # Store original if exists
        os.environ["BEATOVEN_API_KEY"] = original_api_key # Restore or set dummy
        importlib.reload(api_client)
        if "BEATOVEN_API_KEY_ORIGINAL_FOR_TEST" not in os.environ : # cleanup if we set it
             del os.environ["BEATOVEN_API_KEY"]


    # Re-apply the mock dependency for other tests if it was removed
    # This might be better handled by not using autouse=True on the override fixture
    # or by structuring tests that need real dependencies differently.
    # For now, assuming the override_api_client_dependency fixture will re-apply if it runs again.
    # However, explicit re-application here is safer if the order of test execution is not guaranteed.
    # app.dependency_overrides[get_api_client] = lambda: AsyncMock(spec=BeatovenAPIClient) # Re-apply a generic mock

# Add a conftest.py for test configuration if needed, e.g. for pytest_asyncio mode.
# For now, assuming pytest handles asyncio tests correctly with pytest-asyncio installed.
# Ensure requirements_test.txt includes:
# pytest
# pytest-asyncio
# httpx (FastAPI's TestClient uses it)
# fastapi
# uvicorn
# pydantic
# aiohttp
# python-dotenv
# requests (often useful for testing, though not directly used here)
import os
# importlib is moved to the top
