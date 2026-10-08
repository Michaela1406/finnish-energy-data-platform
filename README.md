# Finnish Energy Data Platform

A data engineering portfolio project built around Finnish electricity consumption data from **Fingrid**.

The project demonstrates an end-to-end data pipeline from API ingestion to analytics using **Python, PySpark, Databricks and Delta Lake**. The goal is to build the project incrementally, starting with a small working pipeline and extending it towards a more production-like data platform.

> **Project status: Milestone 1 — in progress**
>
> The first milestone focuses on establishing the core ingestion pipeline and Databricks medallion architecture. The project will be expanded with larger datasets, incremental processing, Azure services, data quality checks and orchestration.

---

## Architecture

```text
                 Fingrid API
                     │
                     ▼
             Python ingestion
                     │
                     ▼
                Raw JSON
                     │
                     ▼
             ┌───────────────┐
             │    Bronze     │
             │ Raw Delta data│
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │    Silver     │
             │ Cleaned &     │
             │ validated data│
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │     Gold      │
             │ Analytics-    │
             │ ready data    │
             └───────────────┘
```

The project follows the **medallion architecture**:

- **Bronze** — source data stored in Delta format with minimal transformation
- **Silver** — cleaned, typed, deduplicated and validated data
- **Gold** — aggregated data designed for analytics and business use

---

## Data Source

The project uses electricity consumption data provided by **Fingrid**, the Finnish transmission system operator.

The current dataset contains electricity consumption measurements at approximately **3-minute intervals**.

Each measurement contains information such as:

- Dataset ID
- Start time
- End time
- Consumption value

The project currently uses Fingrid dataset **193 — electricity consumption**.

---

## Technologies

### Data ingestion
- Python
- REST API
- JSON
- `requests`

### Data processing
- PySpark
- SQL

### Data platform
- Databricks
- Delta Lake
- Unity Catalog

### Development
- Git
- GitHub
- Python virtual environment
- Testing
- Environment variables

### Planned technologies

As the project grows, I plan to explore:

- Azure Data Lake Storage
- Incremental data ingestion
- Databricks Jobs / orchestration
- Data quality monitoring
- CI/CD with GitHub Actions
- Larger-scale historical datasets

---

## Project Structure

```text
finnish-energy-data-platform/
│
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── fingrid_client.py
│   │   └── ingest_consumption.py
│   │
│   └── utils/
│       ├── config.py
│       └── logging.py
│
├── databricks/
│   ├── 01_bronze_consumption.py
│   ├── 02_silver_consumption.py
│   └── 03_gold_consumption.py
│
├── tests/ //To be implemented
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Pipeline

### 1. API ingestion

A Python client connects to the Fingrid API and retrieves electricity consumption data for a specified time range.

The API response is stored as raw JSON before further processing.

---

### 2. Bronze layer

The raw JSON data is loaded into Databricks and converted into a Delta table.

The Bronze layer stays close to the original source structure so that the original data can be traced through the pipeline.

**Table:**

```text
energy.bronze.consumption
```

---

### 3. Silver layer

The Bronze data is transformed into a cleaner analytical structure.

Current transformations include:

- Explicit data types
- Standardized column names
- Timestamp conversion
- Duplicate removal
- Required-field validation
- Time interval validation
- Dataset validation

The current Silver schema is approximately:

| Column | Description |
|---|---|
| `dataset_id` | Fingrid dataset identifier |
| `start_time` | Start of measurement interval |
| `end_time` | End of measurement interval |
| `consumption_mw` | Electricity consumption |

Invalid records are separated into a quarantine table rather than silently discarded.

**Tables:**

```text
energy.silver.consumption
energy.silver.consumption_quarantine
```

---

### 4. Gold layer

The Gold layer contains analytics-oriented data derived from the validated Silver data.

The first version focuses on aggregating the 3-minute measurements into hourly and daily metrics.

#### Hourly consumption

```text
energy.gold.hourly_consumption
```

Example metrics:

- Average consumption
- Minimum consumption
- Maximum consumption
- Number of measurements

#### Daily consumption

```text
energy.gold.daily_consumption
```

Example metrics:

- Average consumption
- Minimum consumption
- Maximum consumption
- Number of measurements
- Expected number of measurements
- Data completeness

This demonstrates how raw high-frequency measurements can be transformed into data that is easier for analysts and business users to consume.

---

## Data Quality

Data quality is handled as part of the Silver layer rather than only at the final analytics stage.

Current validation checks include:

- Required fields are present
- Timestamps are valid
- `end_time` occurs after `start_time`
- Dataset ID matches the expected dataset
- Consumption values are valid
- Duplicate measurements are removed

Invalid records are stored separately in a quarantine table together with information about the validation failure.

---

## Current Progress

### Milestone 1 — Core pipeline

- [x] Fingrid API client
- [x] API authentication through environment variables
- [x] Raw JSON ingestion
- [x] Databricks / Unity Catalog setup
- [x] Bronze Delta layer
- [x] Silver transformation layer
- [x] Basic data validation
- [x] Quarantine for invalid records
- [x] Gold aggregation layer
- [ ] Expand historical dataset
- [ ] Improve incremental ingestion

### Milestone 2 — Scale and automation

Planned:

- [ ] Larger historical dataset
- [ ] Incremental ingestion
- [ ] Azure storage
- [ ] More robust data quality checks
- [ ] Automated pipeline execution
- [ ] CI/CD with GitHub Actions
- [ ] Improved testing

### Milestone 3 — Production-like platform

Planned:

- [ ] Orchestration
- [ ] Monitoring and pipeline observability
- [ ] Production-style incremental processing
- [ ] Data quality monitoring
- [ ] Analytics/dashboard layer
- [ ] Further cloud architecture improvements

---

## Why I Built This

I wanted to fill my skill gap between software engineering and data science and decided to dive into **data engineering**. Therefore, I wanted to build something where I could apply the concepts I have been learning to a real-world dataset.

Rather than focusing only on individual tools, the goal of this project is to understand how the different components fit together:

```text
API
 ↓
Ingestion
 ↓
Storage
 ↓
Transformation
 ↓
Data Quality
 ↓
Analytics
```

The project is intentionally being developed incrementally. The first version focuses on getting the fundamentals working correctly before introducing additional infrastructure and complexity.

---

## Disclaimer

This is a personal learning and portfolio project. The architecture is intentionally simplified compared with a production data platform and will evolve as the project progresses.