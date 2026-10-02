import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fingrid_client import FingridClient
from utils.logging import get_logger
from utils.config import get_api_key, get_config

logger = get_logger(__name__)

CONSUMPTION_DATASET_ID = 1234  # Replace with the actual dataset ID for consumption data

RAW_DATA_PATH = Path("raw_data/consumption")  # Replace with the desired path for raw consumption data

def ingest_consumption(
    start_time: datetime,
    end_time: datetime,
) -> None:
    """Fingrid data ingestion package."""
    
    logger.info(f"Starting ingestion for consumption data from {start_time} to {end_time}")
    
    api_key = get_api_key()
    
    client = FingridClient(api_key=api_key)
    
    data = client.get_dataset(
        dataset_id=CONSUMPTION_DATASET_ID,
        start_time=start_time,
        end_time=end_time,
    )
    
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    filename = (
        f"consumption_{start_time.strftime('%Y%m%d%H%M%S')}_{end_time.strftime('%Y%m%d%H%M%S')}.json"
    )
    
    output_path = RAW_DATA_PATH / filename
    
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        

    logger.info(f"Finished ingestion for consumption data. Data saved to {output_path}")
    
if __name__ == "__main__":
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=1)
    
    ingest_consumption(start_time=start_time, end_time=end_time)

    
    
