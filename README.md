# Beatoven MCP Server

This project implements a Model Context Protocol (MCP) server for the Beatoven.ai API using FastAPI. It allows users to compose music tracks and check their status through a simple HTTP interface.

## Features

-   Compose new music tracks using text prompts.
-   Check the status of ongoing composition tasks.
-   Asynchronous API client for non-blocking communication with Beatoven.ai.
-   Pydantic models for request and response validation.

## Project Structure

```
.
├── api_client.py           # Client for interacting with the Beatoven.ai API
├── main.py                 # FastAPI application exposing MCP endpoints
├── models.py               # Pydantic models for data validation
├── requirements.txt        # Main Python dependencies
├── requirements-test.txt   # Dependencies for running tests
├── .env                    # Environment variables (contains API_KEY, gitignored)
├── .gitignore              # Specifies intentionally untracked files that Git should ignore
├── README.md               # This file
├── AGENTS.md               # Instructions for AI agents
└── tests/                  # Unit and integration tests
    ├── __init__.py
    ├── conftest.py         # Pytest configuration, adds project root to sys.path
    ├── test_api_client.py  # Tests for the BeatovenAPIClient
    └── test_main.py        # Tests for the FastAPI application endpoints
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
    Create a `.env` file in the project root by copying the example:
    ```bash
    cp .env.example .env # If you create an .env.example
    ```
    Or create it manually and add your Beatoven API key:
    ```
    BEATOVEN_API_KEY="YOUR_BEATOVEN_API_KEY_HERE"
    ```
    Replace `"YOUR_BEATOVEN_API_KEY_HERE"` with your actual API key.

## Running the Server

To run the FastAPI server locally:

```bash
uvicorn main:app --reload
```

The server will typically be available at `http://127.0.0.1:8000`. You can access the OpenAPI documentation at `http://127.0.0.1:8000/docs`.

## Running Tests

To run the test suite:

```bash
pytest tests/
```
Ensure you have installed `requirements-test.txt`. Some tests related to API key validation might be skipped if the `BEATOVEN_API_KEY` is not set in the environment or `.env` file during the test run, or if it *is* set (for tests checking its absence).

## API Endpoints

### `POST /compose`

Initiates a music composition task.

**Request Body:**

```json
{
  "prompt": {
    "text": "A 30 second upbeat electronic track for a workout video"
  },
  "format": "wav", // Optional, defaults to "wav". Can be "mp3", "aac", "wav".
  "looping": false // Optional, defaults to false.
}
```

**Successful Response (200 OK):**

```json
{
  "status": "started",
  "task_id": "some-unique-task-id"
}
```

### `GET /tasks/{task_id}`

Retrieves the status of a previously initiated composition task.

**Path Parameter:**

-   `task_id` (string): The ID of the task returned by the `/compose` endpoint.

**Successful Response (200 OK when task is complete):**

```json
{
  "status": "composed", // Other statuses: "composing", "running", "failed"
  "meta": {
    "project_id": "project-id",
    "track_id": "track-id",
    "prompt": {
      "text": "A 30 second upbeat electronic track for a workout video"
    },
    "version": 1,
    "track_url": "https://example.com/path/to/track.wav",
    "stems_url": {
      "bass": "https://example.com/path/to/bass.wav",
      "drums": "https://example.com/path/to/drums.wav"
      // ... other stems
    }
  }
}
```

**Response (200 OK when task is still processing):**
```json
{
  "status": "composing", // or "running"
  "meta": null
}
```

## Contributing

Please refer to `AGENTS.md` for guidelines if you are an AI agent. For human contributors, please follow standard coding practices, ensure tests pass, and update documentation as needed.
