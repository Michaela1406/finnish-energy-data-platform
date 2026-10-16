

import os
import certifi
from dotenv import load_dotenv
from databricks import sql

load_dotenv()

print("Using CA bundle:", certifi.where(), flush=True)
print("Connecting to Databricks...", flush=True)

with sql.connect(
    server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
    http_path=os.environ["DATABRICKS_HTTP_PATH"],
    access_token=os.environ["DATABRICKS_TOKEN"],
    _tls_trusted_ca_file=certifi.where(),
    _retry_stop_after_attempts_count=2,
) as connection:
    print("Connection established!", flush=True)

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("Query result:", cursor.fetchone(), flush=True)

