import logging
import asyncio
from fastmcp import FastMCP, Context
from fastapi import HTTPException
from sse_starlette.sse import EventSourceResponse
from models import CompositionRequest, CompositionResponse, TaskStatus, Prompt
from api_client import BeatovenAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Beatoven MCP Server"
)

@mcp.tool(name="compose_track")
async def compose_track_tool(
    prompt_text: str,
    format: str = "wav",
    looping: bool = False,
) -> CompositionResponse:
    api_client = BeatovenAPIClient()
    logger.info(f"Received composition request: prompt='{prompt_text}', format='{format}', looping={looping}")
    request_data = CompositionRequest(
        prompt=Prompt(text=prompt_text),
        format=format,
        looping=looping
    )
    try:
        response = await api_client.compose_track(request_data)
        logger.info(f"Beatoven API compose response: {response.model_dump_json()}")
        return response
    except Exception as e:
        logger.error(f"Error during composition: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_task_updates(current_task_id: str, client: BeatovenAPIClient): # Renamed arg
    logger.info(f"stream_task_updates called with current_task_id: {current_task_id} (type: {type(current_task_id)})")
    POLL_INTERVAL = 5
    MAX_ATTEMPTS = 360

    for attempt in range(MAX_ATTEMPTS):
        try:
            logger.info(f"stream_task_updates: client is {id(client)}, client.get_task_status is {id(client.get_task_status)}")
            status_data = await client.get_task_status(current_task_id) # Use renamed arg
            logger.info(f"Polling task {current_task_id}, status: {status_data.status}")
            yield {"event": "update", "data": status_data.model_dump_json()}
            if status_data.status in ["composed", "failed"]:
                logger.info(f"Task {current_task_id} reached terminal state: {status_data.status}")
                yield {"event": "complete", "data": status_data.model_dump_json()}
                break
            await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            logger.error(f"Error polling task {current_task_id} (type: {type(current_task_id)}): {e}")
            yield {"event": "error", "data": {"error": str(e), "task_id": str(current_task_id)}} # Ensure task_id is stringified
            break
    else:
        logger.warning(f"Max polling attempts reached for task {current_task_id} (type: {type(current_task_id)}).")
        yield {"event": "error", "data": {"error": "Polling timeout", "task_id": str(current_task_id)}} # Ensure task_id is stringified

@mcp.custom_route("/tasks/{path_param_task_id}/subscribe", methods=["GET"]) # Renamed path parameter
async def subscribe_to_task_updates_route(path_param_task_id: str): # Renamed function argument
    logger.info(f"subscribe_to_task_updates_route called with path_param_task_id: {path_param_task_id} (type: {type(path_param_task_id)})")
    api_client = BeatovenAPIClient()
    return EventSourceResponse(stream_task_updates(path_param_task_id, api_client)) # Pass renamed arg

asgi_app = mcp.http_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server for Beatoven MCP.")
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
