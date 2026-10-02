import requests
from datetime import datetime
from typing import Any

class FingridAPIError(Exception):
    """Raised when the Fingrid API request fails."""
    
class FingridClient:
    """Client for interacting with the Fingrid Open Data API."""
    
    BASE_URL = "https://data.fingrid.fi/"
    
    def __init__(self, api_key: str, timeout: int = 10):
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
        
        url = f"{self.BASE_URL}/api/data"
        
        params = {
            "dataset": dataset_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "api_key": self.api_key
        }

        headers = {
            "x-api-key": self.api_key
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise FingridAPIError(f"Failed to retrieve dataset {dataset_id}: {response.status_code} {response.text}")
        
        return response.json()