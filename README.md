# Beatoven MCP Server (using FastMCP)

This project implements a Model Context Protocol (MCP) server for the Beatoven.ai API using **FastMCP**. It allows users to compose music tracks and receive real-time status updates for composition tasks via Server-Sent Events (SSE).

## Features

-   Compose new music tracks using text prompts via an MCP tool.
-   Receive real-time status updates for composition tasks via an SSE endpoint.
-   Built with FastMCP for MCP compliance.
-   Asynchronous API client (`BeatovenAPIClient`) for non-blocking communication with Beatoven.ai.
-   Pydantic models for request and response validation.

## Project Structure

```
.
├── api_client.py           # Client for interacting with the Beatoven.ai API
├── main.py                 # FastMCP application exposing MCP tools and custom SSE endpoint
├── models.py               # Pydantic models for data validation
├── requirements.txt        # Main Python dependencies (includes fastmcp)
├── requirements-test.txt   # Dependencies for running tests
├── .env                    # Environment variables (contains API_KEY, gitignored)
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── README.md               # This file
├── AGENTS.md               # Instructions for AI agents
└── tests/                  # Unit and integration tests
    ├── __init__.py
    ├── conftest.py         # Pytest configuration, adds project root to sys.path
    ├── test_api_client.py  # Tests for the BeatovenAPIClient
    └── test_main.py        # Tests for the FastMCP application (tools and custom routes)
```

## Setup

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    For development and running tests, also install test dependencies:
    ```bash
    pip install -r requirements-test.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root. You can copy `.env.example` if it exists, or create it manually and add your Beatoven API key:
    ```env
    BEATOVEN_API_KEY="YOUR_BEATOVEN_API_KEY_HERE"
    ```
    Replace `"YOUR_BEATOVEN_API_KEY_HERE"` with your actual API key.

## Running the Server

To run the FastMCP server locally using Uvicorn:

```bash
uvicorn main:asgi_app --reload --host 0.0.0.0 --port 8000
```
(Note: `main:asgi_app` refers to the `asgi_app` object created by `mcp.http_app()` in `main.py`)

The server will typically be available at `http://127.0.0.1:8000`.
-   FastMCP tools will be available under the `/mcp/` path (e.g., `/mcp/tools/compose_track/invoke`).
-   The custom SSE endpoint for task status is at `/tasks/{task_id}/subscribe`.
-   FastMCP may also expose its own OpenAPI documentation, typically at `/openapi.json` or a similar path relative to where the FastMCP app is served.

## API and MCP Endpoints

### MCP Tool: `compose_track`

Initiates a music composition task. This is an MCP tool.

**Invocation (example using `curl` or an MCP client):**
An MCP client would typically discover and call this tool. For HTTP invocation (if enabled and depending on FastMCP transport, usually POST):
```bash
# This is a conceptual representation. Actual invocation depends on the MCP client or HTTP binding.
# Example: POST /mcp/tools/compose_track/invoke
# Body (JSON, matching tool parameters):
# {
#   "prompt_text": "A 30 second upbeat electronic track",
#   "format": "wav",
#   "looping": false
# }
```

**Input Parameters for the tool:**
-   `prompt_text` (string, required): The text prompt for the music.
-   `format` (string, optional, default: "wav"): Desired audio format (`wav`, `mp3`, `aac`).
-   `looping` (boolean, optional, default: false): Whether the track should be looping.

**Successful Response (Pydantic model `CompositionResponse`):**
```json
{
  "status": "started",
  "task_id": "some-unique-task-id"
}
```

### Custom SSE Endpoint: `GET /tasks/{task_id}/subscribe`

Subscribes to real-time status updates for a composition task using Server-Sent Events.

**Path Parameter:**
-   `task_id` (string): The ID of the task returned by the `compose_track` tool.

**SSE Events Stream:**
The server will stream events as the task progresses. Each event has an `event` type and `data` (JSON string).

-   **Event type: `update`**
    -   `data`: JSON string of `TaskStatus` model (see `models.py`).
        Example: `data: {"status": "composing", "meta": null}`
        Example: `data: {"status": "composed", "meta": {"project_id": "...", "track_id": "...", ...}}`

-   **Event type: `complete`**
    -   `data`: JSON string of the final `TaskStatus` model (when status is `composed` or `failed`).
        Example: `data: {"status": "composed", "meta": {...}}`

-   **Event type: `error`**
    -   `data`: JSON string indicating an error during polling or a timeout.
        Example: `data: {"error": "Polling timeout", "task_id": "some-task-id"}`
        Example: `data: {"error": "Description of API error", "task_id": "some-task-id"}`

**Consuming SSE (JavaScript example):**
```javascript
const eventSource = new EventSource("http://127.0.0.1:8000/tasks/YOUR_TASK_ID/subscribe");

eventSource.addEventListener("update", function(event) {
    console.log("Update:", JSON.parse(event.data));
});

eventSource.addEventListener("complete", function(event) {
    console.log("Complete:", JSON.parse(event.data));
    eventSource.close(); // Close connection on completion
});

eventSource.addEventListener("error", function(event) {
    if (event.target.readyState === EventSource.CLOSED) {
        console.log('SSE connection closed by server.');
    } else if (event.target.readyState === EventSource.CONNECTING) {
        console.log('SSE connection lost, attempting to reconnect...');
    } else {
        // An error event from the server (e.g., our custom error)
        // Note: event.data might not always be present for generic network errors
        if (event.data) {
             console.error("Server Error Event:", JSON.parse(event.data));
        } else {
             console.error("SSE Error (no data):", event);
        }
        // Depending on the error, you might want to close:
        // eventSource.close();
    }
});

// Handling generic SSE connection errors
eventSource.onerror = function(err) {
    console.error("EventSource failed:", err);
    // The browser will automatically attempt to reconnect for some errors.
    // If you want to stop retrying under certain conditions:
    // eventSource.close();
};
```

## Running Tests

To run the test suite:
```bash
pytest tests/
```
Ensure you have installed `requirements-test.txt`. Some tests related to API key validation in `test_api_client.py` might be skipped depending on environment setup. Tests for SSE functionality in `test_main.py` are currently experiencing some issues related to mock interactions and asyncio event loops (see `AGENTS.md` or commit history for details).

## Contributing

Please refer to `AGENTS.md` for guidelines if you are an AI agent. For human contributors, please follow standard coding practices, ensure tests pass (or document known issues clearly), and update documentation as needed.
