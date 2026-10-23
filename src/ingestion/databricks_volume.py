import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from src.utils.logging import get_logger

logger = get_logger(__name__)

load_dotenv()

VOLUME_PATH = ("/Volumes/energy/raw/fingrid/consumption/")

def upload_raw_file(local_path: str | Path, volume_directory: str) -> str:
    """Upload a local raw-data file to a Databricks Volume."""
    logger.info(f"Uploading raw file {local_path} to volume directory {volume_directory} on Databricks")
    local_file = Path(local_path)

    if not local_file.is_file():
        raise FileNotFoundError(
            f"Raw data file not found: {local_file}"
        )

    # Give each upload a unique name so reruns don't
    # accidentally overwrite an earlier raw-data snapshot.
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    remote_name = (
        f"{local_file.stem}_{timestamp}{local_file.suffix}"
        
    )
    remote_directory = f"{VOLUME_PATH}/{volume_directory}"
    remote_path = f"{remote_directory}/{remote_name}"
    
    workspace = WorkspaceClient(
        host=f"https://{os.environ['DATABRICKS_SERVER_HOSTNAME']}",
        token=os.environ['DATABRICKS_TOKEN']
    )
    
    try:
        entries = workspace.files.list_directory_contents(
            remote_directory
        )

        logger.info(f"Directory is accessible: {remote_directory}")

        for entry in entries:
            kind = "Directory" if entry.is_directory else "File"
            logger.info(f"{kind}: {entry.name}")

    except:
        logger.info(f"Creating remote directory {remote_directory} on Databricks")
        workspace.files.create_directory(remote_directory)
    
    logger.info(f"Uploading file to remote path {remote_path}")
    
    workspace.files.upload_from(
        remote_path,
        str(local_file.resolve()),
        overwrite=False,
    )

    logger.info(f"Uploaded {local_file.name} to {remote_path}")
    return remote_path