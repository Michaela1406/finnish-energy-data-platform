import requests
from datetime import datetime
from typing import Any
import time

from src.utils.logging import get_logger

logger = get_logger(__name__)


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
        
        headers = {
                    "x-api-key": self.api_key
                }
        
        all_data = []
        page = 1

        while True:
            params = {
                "startTime": start_time.isoformat(),
                "endTime": end_time.isoformat(),
                "page": page,
            }

            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

                response.raise_for_status()

            except requests.RequestException as e:
                raise FingridAPIError(
                    f"Failed to retrieve dataset {dataset_id}, page {page}: {e}"
                ) from e

            result = response.json()
            
            page_data = result.get("data", [])
            pagination = result.get("pagination", {})
            
            all_data.extend(page_data)
            
            logger.info(
                f"Retrieved page {page}: {len(page_data)} records"
            )
            
            per_page = pagination.get("perPage", 10)

            if len(page_data) < per_page:
                break

            page += 1
            
            time.sleep(2) # Sleep for 2 seconds between requests to avoid hitting rate limits

        logger.info(
            f"Retrieved all pages: {len(all_data)} records for dataset {dataset_id}"
        )
        
        return all_data
            
            