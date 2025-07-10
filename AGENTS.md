# Agent Instructions for Beatoven MCP Server (FastMCP)

Welcome, agent! This document provides guidelines for working on the Beatoven MCP Server codebase, which uses **FastMCP**.

## Project Overview

This project is a **FastMCP** server that acts as a client to the Beatoven.ai API. It exposes:
1.  An MCP Tool (`compose_track`): To submit a music composition request.
2.  A custom HTTP SSE endpoint (`/tasks/{task_id}/subscribe`): To provide real-time status updates for composition tasks.

Key files:
-   `main.py`: Contains the FastMCP application logic, MCP tool definitions, and the custom SSE endpoint. The FastMCP instance is `mcp`, and the runnable ASGI app is `asgi_app = mcp.http_app()`.
-   `api_client.py`: Implements the `BeatovenAPIClient` class responsible for making asynchronous HTTP requests to the actual Beatoven.ai API.
-   `models.py`: Defines Pydantic models for data validation and structuring, used by both the MCP tool and the SSE data.
-   `tests/`: Contains unit tests.
    -   `tests/test_api_client.py`: Tests for `BeatovenAPIClient`.
    -   `tests/test_main.py`: Tests for the FastMCP application. It uses `fastmcp.client.Client` for testing MCP tools and FastAPI's `TestClient` for the custom SSE HTTP route.
    -   `tests/conftest.py`: Configures pytest, notably by adding the project root to `sys.path`.

## Development Guidelines

1.  **Environment Setup**:
    *   Ensure you have Python 3.8+ installed.
    *   Use a virtual environment.
    *   Install dependencies: `pip install -r requirements.txt` (includes `fastmcp`).
    *   For running tests, install test dependencies: `pip install -r requirements-test.txt`.
    *   An API key for Beatoven.ai is required. Set it in a `.env` file in the project root as `BEATOVEN_API_KEY="YOUR_KEY"`.

2.  **Code Style & Conventions**:
    *   Follow PEP 8.
    *   Use type hints.
    *   Keep functions focused.
    *   Logging: Use the `logger` instances configured in `main.py` and `api_client.py`.

3.  **FastMCP Server (`main.py`)**:
    *   The core application is a `FastMCP` instance.
    *   **MCP Tools**: Defined using `@mcp.tool`. These are the primary way to expose functionality to MCP clients. Tool functions should typically take simple arguments that FastMCP can map from requests. They return Pydantic models or basic Python types. Error handling within tools should ideally use FastMCP's mechanisms if available (e.g., `ctx.error()`) or raise exceptions that FastMCP can convert to appropriate MCP errors (like `fastmcp.exceptions.ToolError`). Currently, it raises `HTTPException` which FastMCP may convert.
    *   **Custom HTTP Routes**: For non-MCP HTTP functionality (like our SSE endpoint), use `@mcp.custom_route`. These are essentially Starlette/FastAPI routes.
    *   **SSE Implementation**: The `/tasks/{task_id}/subscribe` endpoint uses `sse_starlette.EventSourceResponse` with an async generator (`stream_task_updates`) to send events. Events are dictionaries with `event` and `data` keys.
    *   **Dependencies**: `BeatovenAPIClient` is currently instantiated directly in handlers. For more complex scenarios, explore FastMCP's dependency injection or context features if available and suitable.

4.  **API Client (`api_client.py`)**:
    *   Remains largely the same: an `aiohttp`-based client for the external Beatoven API.

5.  **Models (`models.py`)**:
    *   Pydantic models are used for tool return types and for the data payload of SSE events.

6.  **Testing (`tests/`)**:
    *   **MCP Tools**: Test using `fastmcp.client.Client` connected in-memory to the server instance, as shown in `tests/test_main.py`. This client's `call_tool` method is used.
    *   **Custom HTTP Routes (SSE)**: Test using `fastapi.testclient.TestClient` initialized with the `asgi_app` from `main.py`. Testing SSE streams requires careful handling of the streaming response.
    *   **Mocking**: Use `unittest.mock` (`AsyncMock`, `patch`) for external services like `BeatovenAPIClient`. Ensure patches target the correct instantiation points in `main.py`.
    *   **Current Test Issues (Important!)**: As of the last update, the SSE tests in `tests/test_main.py` (`test_subscribe_to_task_updates_sse` and `test_subscribe_to_task_updates_sse_api_error`) are **failing**.
        *   One issue involves the `BeatovenAPIClient.get_task_status` mock recording calls with a Starlette `Request` object instead of the expected string `task_id`, despite application logs showing the string `task_id` is correctly passed within the application code. This makes mock assertions difficult.
        *   Another issue is a `RuntimeError` related to asyncio event loops when `TestClient` interacts with the `sse-starlette` endpoint, particularly in error scenarios.
        *   These issues indicate complex interactions between the testing tools and the async/ASGI libraries. If tasked with fixing these, proceed with caution and detailed debugging. Consider alternative ways to assert SSE behavior if direct mock verification remains problematic.

7.  **Dependencies**:
    *   Runtime: `requirements.txt` (ensure `fastmcp` is there).
    *   Test: `requirements-test.txt`.

8.  **Documentation**:
    *   Update `README.md` for user-facing changes.
    *   Update this `AGENTS.md` for agent-specific guidelines.

## Common Pitfalls & Troubleshooting (FastMCP specific)

*   **MCP Tool vs. Custom Route**: Understand when to use `@mcp.tool` (for MCP-compliant functionality) versus `@mcp.custom_route` (for standard HTTP endpoints like SSE feeds or web pages not directly part of the MCP interaction model).
*   **Tool Signatures**: FastMCP tools often map request parameters to function arguments directly. Avoid complex objects as direct tool arguments unless you know FastMCP handles their deserialization from the specific transport.
*   **Streaming with FastMCP**:
    *   `ctx.report_progress()`: This is the primary MCP mechanism for tools to send progress updates during long-running operations. The client needs to support progress tokens.
    *   Custom SSE: For dedicated, non-MCP event streams (like our task status), using `@mcp.custom_route` with `EventSourceResponse` is a viable approach.
*   **Testing FastMCP**: Use `fastmcp.client.Client` for in-memory testing of MCP components. For custom HTTP routes on the `mcp.http_app()`, use a standard ASGI test client like `fastapi.testclient.TestClient`.
*   **Test Failures (see above)**: Be aware of the ongoing issues with SSE tests. Do not assume they will pass without further fixes.

By following these guidelines, you'll help maintain the quality and consistency of the codebase. If anything is unclear, please ask for clarification.
