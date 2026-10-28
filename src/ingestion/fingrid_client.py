import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from typing import Any
import time

from src.utils.logging import get_logger

logger = get_logger(__name__)

def create_session() -> requests.Session:
    retry_policy = Retry(
        total=5,
        connect=3,
        read=3,
        status=5,
        allowed_methods=frozenset(["GET"]),
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1,
        backoff_jitter=0.5,
        backoff_max=30,
        respect_retry_after_header=True,
        retry_after_max=60,
    )

    adapter = HTTPAdapter(max_retries=retry_policy)

    session = requests.Session()
    session.mount("https://", adapter)

    return session


class FingridAPIError(Exception):
    """Raised when the Fingrid API request fails."""


class FingridClient:
    """Client for interacting with the Fingrid Open Data API."""

    BASE_URL = "https://data.fingrid.fi/api"
    REQUEST_DELAY_SECONDS = 3

    def __init__(self, api_key: str, timeout: int = 50):
        self.api_key = api_key
        self.timeout = timeout
        self.session = create_session()
    
    
    def get_dataset(
        self,
        dataset_id: int,
        start_time: datetime,
        end_time: datetime,
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
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                
                response.raise_for_status()
            
            except requests.RequestException as e:
                logger.exception(
                    "Request failed for dataset %s, page %s",
                    dataset_id,
                    page,
                )
                raise FingridAPIError(
                    f"Failed to retrieve dataset {dataset_id}, "
                    f"page {page}: {e}"
                ) from e

            try:
                result = response.json()
                
            except requests.JSONDecodeError as e:
                raise FingridAPIError(
                    f"Failed to decode JSON for dataset {dataset_id}, "
                    f"page {page}: {e}"
                ) from e
                
            if not isinstance(result, dict):
                raise FingridAPIError(
                    f"Unexpected response format for dataset {dataset_id}, "
                    f"page {page}: expected a JSON object"
                )
            
            logger.debug("Page: %s", page)
            logger.debug("Response keys: %s", result.keys())
            logger.debug("Pagination: %s", result.get("pagination"))
            logger.debug("Records returned: %s", len(result.get("data", [])))
            
            page_data = result.get("data", [])
            pagination = result.get("pagination", {})
            
            if not isinstance(page_data, list):
                raise FingridAPIError(
                    f"Missing or invalid 'data' list for dataset "
                    f"{dataset_id}, page {page}"
                )

            if not isinstance(pagination, dict):
                raise FingridAPIError(
                    f"Missing or invalid pagination metadata for dataset "
                    f"{dataset_id}, page {page}"
                )
            
            all_data.extend(page_data)
            
            logger.info(
                f"Retrieved page {page}: {len(page_data)} records"
            )

            per_page = pagination.get("perPage")

            if not isinstance(per_page, int) or per_page <= 0:
                raise FingridAPIError(
                    f"Invalid pagination page size for dataset {dataset_id}, "
                    f"page {page}"
                )

            if len(page_data) < per_page:
                break

            page += 1
            
            time.sleep(self.REQUEST_DELAY_SECONDS)

        logger.info(
            f"Retrieved all pages: {len(all_data)} records for dataset {dataset_id}"
        )
        
        return all_data
            
            