import logging
from fastapi import FastAPI, HTTPException, Depends
from models import CompositionRequest, CompositionResponse, TaskStatus
from api_client import BeatovenAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Beatoven MCP Server",
    description="A server implementing the Model Context Protocol for Beatoven.ai API.",
    version="0.1.0",
)

def get_api_client():
    try:
        return BeatovenAPIClient()
    except ValueError as e:
        # This will be caught by FastAPI's exception handling for dependency errors
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compose", response_model=CompositionResponse)
async def compose(
    request: CompositionRequest, client: BeatovenAPIClient = Depends(get_api_client)
):
    """
    Accepts a composition request and forwards it to the Beatoven API.
    """
    logger.info(f"Received composition request: {request.model_dump_json()}")
    try:
        response = await client.compose_track(request)
        logger.info(f"Beatoven API compose response: {response.model_dump_json()}")
        return response
    except Exception as e:
        logger.error(f"Error during composition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task(
    task_id: str, client: BeatovenAPIClient = Depends(get_api_client)
):
    """
    Retrieves the status of a composition task from the Beatoven API.
    """
    logger.info(f"Received task status request for task_id: {task_id}")
    try:
        status = await client.get_task_status(task_id)
        logger.info(f"Beatoven API task status response: {status.model_dump_json()}")
        return status
    except Exception as e:
        logger.error(f"Error retrieving task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This is for local development and debugging.
    # In a production environment, you'd use a proper ASGI server like Uvicorn or Hypercorn managed by a process manager.
    logger.info("Starting Uvicorn server for local development.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
