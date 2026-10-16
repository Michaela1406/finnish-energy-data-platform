import os
import certifi
from dotenv import load_dotenv
from databricks import sql
from src.utils.logging import get_logger

logger = get_logger(__name__)

load_dotenv()


def get_api_key() -> str:
    
    api_key = os.getenv("FINGRID_API_KEY")
    
    if not api_key:
        raise RuntimeError("FINGRID_API_KEY environment variable is not set")
    
    return api_key


def get_latest_bronze_timestamp() -> str | None:
    
    logger.info("Connecting to Databricks...")

    with sql.connect(
        server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
        http_path=os.environ["DATABRICKS_HTTP_PATH"],
        access_token=os.environ["DATABRICKS_TOKEN"],
         _tls_trusted_ca_file=certifi.where(),
    ) as connection:
        logger.info("Connection established!")

        with connection.cursor() as cursor:
            logger.info("Cursor created!")            
            cursor.execute("""
            SELECT
                COUNT(*) AS record_count,
                MAX(startTime) AS latest_timestamp
            FROM energy.bronze.consumption
        """)
            result = cursor.fetchone()
        logger.info(f"Record count: {result[0]}")
        logger.info(f"Latest timestamp: {result[1]}")
    
    logger.info(f"Latest bronze timestamp found in Databricks energy.bronze.consumption: {result[1] if result else None}")
    return result[1] if result else None
