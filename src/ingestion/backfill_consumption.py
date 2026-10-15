import json
import csv
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from src.ingestion.fingrid_client import FingridClient

from src.utils.config import get_api_key
from src.utils.logging import get_logger

logger = get_logger(__name__)

DATASET_ID = 193
INTERVAL_MINUTES = 3
EXPECTED_PER_DAY = 24 * 60 // INTERVAL_MINUTES

BACKFILL_DIR = Path("raw_data/consumption/backfill")
REPORT_DIR = Path("raw_data/consumption/reports")

TESTING = False

START_DATE = date(2026, 9, 15)  # Example start date for backfill
END_DATE = date(2026, 9, 29)  # Example end date for backfill


def utc_day_window(day: date):
    """Return the UTC start and end of a calendar day."""
    start = datetime.combine(
        day, time.min, tzinfo=timezone.utc
    )
    # Use the final second of the day for the API query.
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end


def expected_timestamps(day: date) -> set[datetime]:
    """Expected measurement start times on a 3-minute grid."""
    start, _ = utc_day_window(day)
    return {
        start + timedelta(minutes=INTERVAL_MINUTES * i)
        for i in range(EXPECTED_PER_DAY)
    }


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp and normalize it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp has no timezone: {value}")

    return parsed.astimezone(timezone.utc)


def analyse_day(day: date, records: list[dict]):
    expected = expected_timestamps(day)

    actual_timestamps = [
        parse_timestamp(row["startTime"])
        for row in records
        if row.get("startTime")
    ]

    # Count unique expected-grid timestamps separately from duplicates
    # and unexpected timestamps.
    counts = Counter(actual_timestamps)
    actual_expected = set(counts) & expected
    missing = sorted(expected - set(counts))
    duplicates = sum(count - 1 for count in counts.values() if count > 1)
    unexpected = sorted(set(counts) - expected)

    completeness = len(actual_expected) / len(expected) * 100

    return {
        "date_utc": day.isoformat(),
        "expected_intervals": len(expected),
        "records_received": len(records),
        "unique_expected_intervals": len(actual_expected),
        "missing_intervals": len(missing),
        "duplicate_records": duplicates,
        "unexpected_timestamps": len(unexpected),
        "completeness_pct": round(completeness, 2),
    }, missing, unexpected


def save_json(path: Path, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            {"data": records},
            file,
            indent=2,
            ensure_ascii=False,
        )


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        return
    
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as write_file:
            writer = csv.DictWriter(write_file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return

    else: 
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, fieldnames=list(rows[0].keys()))
            if reader.fieldnames is None:
                with path.open("w", newline="", encoding="utf-8") as write_file:
                    writer = csv.DictWriter(write_file, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
            elif reader.fieldnames == list(rows[0].keys()):
                with path.open("a", newline="", encoding="utf-8") as write_file:
                    appender = csv.DictWriter(write_file, fieldnames=list(rows[0].keys()))
                    appender.writerows(rows)
            elif reader.fieldnames != list(rows[0].keys()):
                print(f"Fieldnames do not match for file {path}")
                print(f"Expected fieldnames: {list(rows[0].keys())}, but got: {reader.fieldnames}")
            else:
                print(f"Unexpected condition for file {path}")



def backfill_consumption(
    start_date: date,
    end_date: date
) -> None:
    """Fingrid data ingestion package."""
    
    logger.info(f"Starting backfill ingestion for consumption data from {start_date} to {end_date}")
    
    BACKFILL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    daily_reports = []
    missing_rows = []
    unexpected_rows = []

    current_day = start_date
    
    api_key = get_api_key()
    
    client = FingridClient(api_key=api_key)
    
    current_day = start_date

    while current_day <= end_date:

        # Save every successful response, including days with gaps.
        filename = f"consumption_{current_day:%Y%m%d}.json"
        output_path = BACKFILL_DIR / filename

        if output_path.exists():
            logger.info(
                "Skipping %s: output file already exists",
                current_day,
            )
            
        else:
            start_time, end_time = utc_day_window(current_day)
            
            print(f"Backfilling {current_day.isoformat()} UTC")
    
            # If this raises an API error, stop rather than report a
            # failed request as a day with zero source records.
            records = client.get_dataset(
                dataset_id=DATASET_ID,
                start_time=start_time,
                end_time=end_time,
            )
                    
            save_json(BACKFILL_DIR / filename, records)

            report, missing, unexpected = analyse_day(
                current_day, records
            )
            daily_reports.append(report)

            for timestamp in missing:
                missing_rows.append({
                    "date_utc": current_day.isoformat(),
                    "missing_start_time_utc": timestamp.isoformat(),
                })

            for timestamp in unexpected:
                unexpected_rows.append({
                    "date_utc": current_day.isoformat(),
                    "unexpected_start_time_utc": timestamp.isoformat(),
                })

            if TESTING:
                print(
                    f"  received={report['records_received']}, "
                    f"unique_expected={report['unique_expected_intervals']}, "
                    f"missing={report['missing_intervals']}, "
                    f"completeness={report['completeness_pct']}%"
                )

        current_day += timedelta(days=1)

    write_csv(
        REPORT_DIR / "daily_completeness.csv",
        daily_reports,
    )
    write_csv(
        REPORT_DIR / "missing_intervals.csv",
        missing_rows,
    )
    write_csv(
        REPORT_DIR / "unexpected_timestamps.csv",
        unexpected_rows,
    )

    print(f"\nBackfill finished: {len(daily_reports)} days")
    print(f"Reports saved to: {REPORT_DIR}")

if __name__ == "__main__":
    end_date = END_DATE
    start_date = START_DATE
    
    backfill_consumption(start_date=start_date, end_date=end_date)