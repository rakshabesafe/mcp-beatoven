# Agent Instructions for Beatoven MCP Server

Welcome, agent! This document provides guidelines for working on the Beatoven MCP Server codebase.

## Project Overview

This project is a FastAPI server that acts as a client to the Beatoven.ai API. It exposes two main endpoints:
1.  `/compose`: To submit a music composition request.
2.  `/tasks/{task_id}`: To check the status of a composition task.

Key files:
-   `main.py`: Contains the FastAPI application logic and endpoint definitions.
-   `api_client.py`: Implements the `BeatovenAPIClient` class responsible for making asynchronous HTTP requests to the actual Beatoven.ai API.
-   `models.py`: Defines Pydantic models for request/response validation and data structuring.
-   `tests/`: Contains unit tests for the API client and FastAPI endpoints.
    -   `tests/test_api_client.py`
    -   `tests/test_main.py`
    -   `tests/conftest.py`: Configures pytest, notably by adding the project root to `sys.path` so that modules like `api_client` can be imported correctly in tests.

## Development Guidelines

1.  **Environment Setup**:
    *   Ensure you have Python 3.8+ installed.
    *   Use a virtual environment.
    *   Install dependencies using `pip install -r requirements.txt`.
    *   For running tests, install test dependencies: `pip install -r requirements-test.txt`.
    *   An API key for Beatoven.ai is required. It should be set in a `.env` file in the project root as `BEATOVEN_API_KEY="YOUR_KEY"`. The `api_client.py` uses `python-dotenv` to load this.

2.  **Code Style & Conventions**:
    *   Follow PEP 8 for Python code.
    *   Use type hints for all function signatures and important variables. Pydantic models inherently use them.
    *   Keep functions and methods reasonably short and focused on a single responsibility.
    *   Logging: Basic logging is set up in `main.py` and `api_client.py`. Use `logger.info()`, `logger.error()`, etc., for relevant messages.

3.  **API Client (`api_client.py`)**:
    *   All interactions with the external Beatoven.ai API should go through `BeatovenAPIClient`.
    *   Use `aiohttp` for asynchronous HTTP requests.
    *   Implement robust error handling for API requests (e.g., connection errors, HTTP status errors). Raise appropriate exceptions.

4.  **FastAPI Endpoints (`main.py`)**:
    *   Endpoints should primarily delegate business logic to other components (like `BeatovenAPIClient`).
    *   Use Pydantic models defined in `models.py` for request body validation and response serialization.
    *   Use FastAPI's `Depends` for dependency injection (e.g., for the `BeatovenAPIClient`).
    *   Return appropriate HTTP status codes and error responses. `HTTPException` is useful here.

5.  **Models (`models.py`)**:
    *   All data structures exchanged with the external API or through the server's own API should have corresponding Pydantic models.
    *   Use `Optional` and default values appropriately.
    *   Add validation where necessary (e.g., using `Field` for patterns or constraints).

6.  **Testing (`tests/`)**:
    *   Write unit tests for all new functionality.
    *   Use `pytest` as the test runner.
    *   Use `unittest.mock` (especially `AsyncMock` for async methods and `patch`) to mock external dependencies like the Beatoven.ai API calls. This ensures tests are fast and reliable.
    *   The `TestClient` from FastAPI is used for testing API endpoints in `tests/test_main.py`.
    *   Ensure tests cover both success cases and error conditions.
    *   To run tests: `pytest tests/` from the project root.
    *   The `tests/conftest.py` file is crucial for making sure imports work correctly within the tests by adding the project root to `sys.path`. Do not remove this unless a better project structure (e.g., installable package) is implemented.

7.  **Dependencies**:
    *   Add new runtime dependencies to `requirements.txt`.
    *   Add new test-specific dependencies to `requirements-test.txt`.
    *   Keep dependencies up-to-date if necessary, but ensure compatibility.

8.  **Documentation**:
    *   Update `README.md` if you change server setup, add new endpoints, or make significant architectural changes.
    *   Add comments to your code where the logic is complex or non-obvious. Docstrings for public functions/methods are good.

9.  **Committing and Submitting Changes**:
    *   Follow standard commit message conventions (e.g., a short subject line, followed by a more detailed body if needed).
    *   Ensure all tests pass before submitting your changes.
    *   If you are asked to make changes that deviate significantly from the original plan, please confirm this with the user.

## Common Pitfalls & Troubleshooting

*   **`ModuleNotFoundError` during tests**: This is often due to Python's import system not finding the project's root modules. `tests/conftest.py` attempts to solve this. If you encounter it, ensure `pytest` is run from the project root.
*   **API Key Issues**: If tests related to API key handling fail, or if the application can't connect to Beatoven.ai, double-check that the `BEATOVEN_API_KEY` is correctly set in your `.env` file and that `python-dotenv` is working as expected.
*   **Async/Await Issues**: Remember to `await` asynchronous function calls. Use `AsyncMock` for mocking async methods in tests.

By following these guidelines, you'll help maintain the quality and consistency of the codebase. If anything is unclear, please ask for clarification.Tool output for `create_file_with_block`:
