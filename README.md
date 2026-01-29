# Jetson Edge Monitoring Dashboard

A Streamlit in Snowflake (SiS) application for real-time monitoring and analysis of NVIDIA Jetson edge device telemetry data.

## Overview

This dashboard provides visibility into edge computing infrastructure by visualizing system metrics streamed from Jetson devices. It enables operations teams to monitor device health, identify performance bottlenecks, and export data for further analysis.

## Features

| Feature | Description |
|---------|-------------|
| **Host Filter** | Filter data by specific edge device hostname |
| **Date Range** | Select custom time windows for analysis |
| **Key Metrics** | At-a-glance KPIs: record count, avg CPU temp, CPU/memory usage |
| **Time Series Charts** | Interactive visualizations for CPU temp, CPU/Memory/Disk usage trends |
| **Data Table** | Sortable, scrollable table of all readings |
| **CSV Export** | Download filtered dataset for offline analysis |

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Jetson Device  │ ──▶  │    Snowflake    │ ──▶  │  Streamlit App  │
│  (Edge Sensor)  │      │  JETSON_EDGE_   │      │   (Dashboard)   │
│                 │      │     STREAM      │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Data Source

### Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `ROW_ID` | VARCHAR | Unique record identifier (UUID) |
| `HOST` | VARCHAR | Hostname of the Jetson device |
| `IP_ADDRESS` | VARCHAR | Device IP address |
| `MAC_ADDRESS` | VARCHAR | Device MAC address |
| `TS_UTC` | TIMESTAMP_NTZ | Timestamp of the reading (UTC) |
| `TS_EPOCH_MS` | NUMBER | Epoch timestamp in milliseconds |
| `CPU_TEMP_C` | NUMBER(10,3) | CPU temperature in Celsius |
| `CPU_USAGE_PCT` | NUMBER(10,3) | CPU utilization percentage |
| `MEM_USAGE_PCT` | NUMBER(10,3) | Memory utilization percentage |
| `DISK_USAGE_PCT` | NUMBER(10,3) | Disk utilization percentage |
| `THERMAL_ZONES` | VARIANT | JSON object with thermal zone details |
| `EDGE_AI_SUMMARY` | VARCHAR | AI-generated summary from edge processing |
| `IMAGE_PATH` | VARCHAR | Path to captured image (if any) |
| `IMAGE_CAPTURED` | BOOLEAN | Flag indicating if image was captured |
| `IMAGE_AI_SUMMARY` | VARCHAR | AI-generated summary of captured image |
| `PAYLOAD` | VARIANT | Full JSON payload from device |

### Source Table

- **Database**: `DEMO`
- **Schema**: `DEMO`
- **Table**: `JETSON_EDGE_STREAM`

## Deployment

### Prerequisites

- Snowflake account with Streamlit enabled
- Access to `DEMO.DEMO` schema
- A warehouse (e.g., `INGEST`)

### Step 1: Create Stage

```sql
CREATE STAGE IF NOT EXISTS DEMO.DEMO.STREAMLIT_STAGE
    DIRECTORY = (ENABLE = TRUE);
```

### Step 2: Upload Application Files

Using SnowSQL or Snowsight:

```sql
PUT file:///path/to/streamlit_app.py @DEMO.DEMO.STREAMLIT_STAGE/jetson_monitor/ 
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

PUT file:///path/to/requirements.txt @DEMO.DEMO.STREAMLIT_STAGE/jetson_monitor/ 
    AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

Or using Snow CLI:

```bash
snow stage copy ./streamlit_app.py @DEMO.DEMO.STREAMLIT_STAGE/jetson_monitor/
snow stage copy ./requirements.txt @DEMO.DEMO.STREAMLIT_STAGE/jetson_monitor/
```

### Step 3: Create Streamlit Application

```sql
CREATE OR REPLACE STREAMLIT DEMO.DEMO.JETSON_EDGE_MONITOR
    ROOT_LOCATION = '@DEMO.DEMO.STREAMLIT_STAGE/jetson_monitor'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'INGEST'
    COMMENT = 'Jetson Edge Device Monitoring Dashboard';
```

### Step 4: Verify Deployment

```sql
SHOW STREAMLITS IN SCHEMA DEMO.DEMO;

DESCRIBE STREAMLIT DEMO.DEMO.JETSON_EDGE_MONITOR;
```

### Step 5: Grant Access (Optional)

```sql
GRANT USAGE ON STREAMLIT DEMO.DEMO.JETSON_EDGE_MONITOR TO ROLE DATA_ANALYST;
GRANT USAGE ON STREAMLIT DEMO.DEMO.JETSON_EDGE_MONITOR TO ROLE OPERATIONS;
```

### Step 6: Access the App

Navigate to Snowsight → Projects → Streamlit → JETSON_EDGE_MONITOR

Or construct the URL:
```
https://<account>.snowflakecomputing.com/streamlit-apps/DEMO.DEMO.JETSON_EDGE_MONITOR
```

## Local Development

### Setup

1. Clone or download the project files
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install streamlit  # Additional for local dev
```

### Configuration

For local development, modify `streamlit_app.py` to use a connection config:

```python
import snowflake.connector

@st.cache_resource
def get_session():
    conn = snowflake.connector.connect(
        connection_name="default"  # Uses ~/.snowflake/connections.toml
    )
    return conn
```

### Run Locally

```bash
streamlit run streamlit_app.py --server.port 8501
```

## Caching Strategy

| Cache | TTL | Purpose |
|-------|-----|---------|
| `get_session()` | Resource (permanent) | Snowpark session reuse |
| `load_data()` | 60 seconds | Main data query results |
| `get_hosts()` | 300 seconds | Host dropdown options |

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No data found" | Check date range; ensure data exists in table |
| Session errors | Verify warehouse is running and accessible |
| Slow performance | Reduce date range; check warehouse size |
| Permission denied | Ensure role has SELECT on `JETSON_EDGE_STREAM` |

### Debug Queries

Check if data exists:

```sql
SELECT COUNT(*), MIN(TS_UTC), MAX(TS_UTC) 
FROM DEMO.DEMO.JETSON_EDGE_STREAM;
```

Check distinct hosts:

```sql
SELECT DISTINCT HOST FROM DEMO.DEMO.JETSON_EDGE_STREAM;
```

## Future Enhancements

- [ ] Add alerting thresholds for high CPU temp/usage
- [ ] Include thermal zone breakdown visualization
- [ ] Display captured images inline
- [ ] Add AI summary analysis panel
- [ ] Multi-device comparison view
- [ ] Historical trend analysis with anomaly detection

## License

Internal use only.

## Contact

For questions or issues, contact your Snowflake administrator.
