import os

import httpx
from dotenv import load_dotenv

from exceptions import PollServiceUnavailableError


class PollClient:
    def __init__(self):
        self.base_url = os.environ["POLL_SERVICE_URL"].rstrip("/")

    def delete_user_answers(self, user_id: int):
        try:
            response = httpx.delete(f"{self.base_url}/users/{user_id}/answers",timeout=5.0,)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise PollServiceUnavailableError("Could not reach the poll service") from exc
        except httpx.HTTPStatusError as exc:
            raise PollServiceUnavailableError("Poll service returned an unexpected HTTP status") from exc
