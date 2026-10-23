import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.ingestion.fingrid_client import FingridClient

from src.utils.config import get_api_key, get_latest_bronze_timestamp
from src.utils.logging import get_logger

from src.ingestion.databricks_volume import upload_raw_file

logger = get_logger(__name__)

CONSUMPTION_DATASET_ID = 193  # Replace with the actual dataset ID for consumption data

RAW_DATA_PATH = Path("raw_data/consumption/ingestion")  # Replace with the desired path for raw consumption data

VOLUME_SUB_DIRECTORY = "ingestion"

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
    
    return output_path
    
    
from datetime import datetime, timedelta, timezone


def get_incremental_window():
    logger.info("Determining the incremental ingestion window based on the latest bronze timestamp.")
    
    latest_timestamp = get_latest_bronze_timestamp()

    if latest_timestamp is None:
        # First run: choose a sensible initial backfill window.
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=1)
    else:
        # Handle a datetime returned by the SQL connector.
        if isinstance(latest_timestamp, str):
            latest_timestamp = datetime.fromisoformat(
                latest_timestamp.replace("Z", "+00:00")
            )

        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(
                tzinfo=timezone.utc
            )

        # Re-fetch recent records to capture late updates.
        start_time = latest_timestamp - timedelta(minutes=30)
        end_time = datetime.now(timezone.utc)
        
        logger.info(f"Incremental ingestion window determined: start_time={start_time}, end_time={end_time}")

    return start_time, end_time
    
if __name__ == "__main__":
    start_time, end_time = get_incremental_window()

    output_path = ingest_consumption(start_time=start_time, end_time=end_time)
    upload_raw_file(local_path=output_path, volume_directory=VOLUME_SUB_DIRECTORY)
    

    
    
