import requests
from datetime import datetime
from typing import Any


class FingridAPIError(Exception):
    """Raised when the Fingrid API request fails."""


class FingridClient:
    """Client for interacting with the Fingrid Open Data API."""

    BASE_URL = "https://data.fingrid.fi/api"

    def __init__(self, api_key: str, timeout: int = 50):
        self.api_key = api_key
        self.timeout = timeout

    def get_dataset(
        self,
        dataset_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> list[dict[str, Any]]:
        """
        Retrieve a Fingrid dataset for a given time range.
        """

        url = f"{self.BASE_URL}/datasets/{dataset_id}/data"

        params = {
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "page": 2,
        }

        headers = {
            "x-api-key": self.api_key
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()

        except requests.RequestException as e:
            raise FingridAPIError(
                f"Failed to retrieve dataset {dataset_id}: {e}"
            ) from e

        return response.json()