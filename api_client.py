import os
import logging
import aiohttp
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from models import CompositionRequest, CompositionResponse, TaskStatus

logger = logging.getLogger(__name__)

load_dotenv() # Load environment variables from .env file

BASE_URL = "https://public-api.beatoven.ai/api/v1"
API_KEY = os.getenv("BEATOVEN_API_KEY")

class BeatovenAPIClient:
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("BEATOVEN_API_KEY environment variable not set.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, json=data, headers=self.headers) as response:
                    response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
                    return await response.json()
            except aiohttp.ClientConnectionError as e:
                logger.error(f"Connection error to {url}: {e}")
                raise Exception(f"Could not connect to Beatoven API: {e}")
            except aiohttp.ClientResponseError as e:
                logger.error(f"API request failed {url} with status {e.status}: {e.message}")
                # Attempt to get more details from the response body
                try:
                    error_details = await response.json()
                    logger.error(f"Error details: {error_details}")
                    raise Exception(f"Beatoven API request failed with status {e.status}: {error_details}")
                except Exception: # If response is not JSON or another error occurs
                    raise Exception(f"Beatoven API request failed with status {e.status}: {e.message}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while requesting {url}: {e}")
                raise Exception(f"An unexpected error occurred: {e}")

    async def compose_track(self, request_data: CompositionRequest) -> CompositionResponse:
        """
        Starts a track composition task.
        """
        payload = request_data.model_dump(exclude_none=True)
        response_data = await self._request("POST", "/tracks/compose", data=payload)
        return CompositionResponse(**response_data)

    async def get_task_status(self, task_id: str) -> TaskStatus:
        """
        Retrieves the status of a composition task.
        """
        response_data = await self._request("GET", f"/tasks/{task_id}")
        return TaskStatus(**response_data)
