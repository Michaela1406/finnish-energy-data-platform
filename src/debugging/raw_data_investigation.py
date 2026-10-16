from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

# Replace this with the path to the raw data file you want to investigate.
DATA_PATH = "raw_data/consumption/backfill/consumption_20261001_010000_test.json"

records = json.loads(Path(DATA_PATH).read_text(encoding="utf-8"))


actual = {
    datetime.fromisoformat(
        row["startTime"].replace("Z", "+00:00")
    )
    for row in records
}

# Use a UTC calendar day or hour depending on the granularity of the data.
hour = datetime(2026, 10, 1,1, tzinfo=timezone.utc)
expected = {
    hour + timedelta(minutes=3 * i)
    for i in range(20)
}

missing = sorted(expected - actual)

print(f"Returned records: {len(records)}")
print(f"Unique timestamps: {len(actual)}")
print(f"Missing timestamps: {len(missing)}")
print("\nFirst 30 missing timestamps:")

for timestamp in missing[:30]:
    print(timestamp.isoformat())