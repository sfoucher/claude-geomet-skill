---
name: geomet-catalog
description: >
  Browse, query, visualize, and export Canadian weather, climate, hydrometric,
  and air quality data from the MSC GeoMet OGC API.
  Triggers: weather data, climate data, GeoMet, ECCC, MSC, hydrometric,
  AQHI, air quality, Environment Canada, water levels, climate observations
---

# GeoMet Catalog Skill

Query Environment and Climate Change Canada's open data via the MSC GeoMet OGC API.

**Base URL:** `https://api.weather.gc.ca`
**Auth:** None required — free and public
**Format:** OGC API - Features (GeoJSON)

## Workflow

1. **Discover** — find available collections with `geomet_collections.py`
2. **Inspect** — check queryable properties for filter options
3. **Fetch** — retrieve data with spatial/temporal/property filters using `geomet_fetch.py`
4. **Export/Visualize** — save to CSV/GeoJSON or generate charts with `geomet_export.py` / `geomet_visualize.py`

## Scripts

All scripts are in `scripts/` relative to this skill directory. They use only Python stdlib (except `geomet_visualize.py` which needs `matplotlib`).

### geomet_collections.py — Browse Collections

```bash
# List all collections
python geomet_collections.py --list

# Search by keyword
python geomet_collections.py --search climate
python geomet_collections.py --search hydro

# Full metadata for one collection
python geomet_collections.py --info climate-hourly

# Show filterable properties
python geomet_collections.py --queryables climate-hourly

# Group collections by category
python geomet_collections.py --categories
```

### geomet_fetch.py — Fetch Data

```bash
# Basic fetch (10 items by default)
python geomet_fetch.py climate-hourly --limit 5

# Filter by property
python geomet_fetch.py hydrometric-daily-mean --properties STATION_NUMBER=02HA003 --limit 10

# Spatial + temporal filter
python geomet_fetch.py climate-daily --bbox -80,43,-70,47 --datetime 2023-01-01/2023-01-31 --limit 20

# Select specific fields
python geomet_fetch.py climate-hourly --fields STATION_NAME,TEMP,LOCAL_DATE --limit 10

# JSON output
python geomet_fetch.py climate-hourly --limit 5 --json

# Paginate through results (with safety cap)
python geomet_fetch.py climate-hourly --all-pages --max-items 200

# Sort results
python geomet_fetch.py climate-daily --sortby -MAX_TEMP --limit 10
```

### geomet_export.py — Export to File

```bash
# Export to CSV
python geomet_export.py climate-hourly --format csv --limit 50

# Export to GeoJSON
python geomet_export.py aqhi-observations-realtime --format geojson --limit 50

# Export with filters
python geomet_export.py climate-daily --format csv --bbox -80,43,-70,47 --datetime 2023-06-01/2023-06-30

# Custom output path
python geomet_export.py climate-hourly --format csv --limit 100 -o my_data.csv

# Paginate all results (capped at 1000)
python geomet_export.py hydrometric-daily-mean --format csv --properties STATION_NUMBER=02HA003 --all-pages --max-items 500
```

CSV output flattens Point geometry into `longitude` and `latitude` columns.

### geomet_visualize.py — Generate Charts (requires matplotlib)

```bash
# Time series
python geomet_visualize.py climate-hourly --type timeseries --y-field TEMP --limit 200

# Time series grouped by station
python geomet_visualize.py climate-hourly --type timeseries --y-field TEMP --group-by STATION_NAME --limit 200

# Bar chart (averages by category)
python geomet_visualize.py climate-daily --type bar --x-field LOCAL_MONTH --y-field MEAN_TEMP --limit 500

# Scatter plot
python geomet_visualize.py climate-daily --type scatter --x-field MIN_TEMP --y-field MAX_TEMP --limit 200

# Map of stations colored by value
python geomet_visualize.py aqhi-observations-realtime --type map --y-field AQHI --limit 100

# Map of all stations
python geomet_visualize.py climate-hourly --type map --limit 200

# Custom title and output
python geomet_visualize.py climate-hourly --type timeseries --y-field TEMP --title "Ottawa Temps" --output ottawa.png --properties STATION_NAME=OTTAWA+CDA --limit 200
```

All charts are saved as PNG. The `--x-field` for timeseries is auto-detected from common date field names.

## Common Collections

### Climate
| ID | Description |
|----|-------------|
| `climate-hourly` | Hourly observations (temp, humidity, wind, pressure) |
| `climate-daily` | Daily summaries (max/min/mean temp, precipitation) |
| `climate-monthly` | Monthly aggregates |
| `climate-normals` | 30-year normals |

### Hydrometric (Water)
| ID | Description |
|----|-------------|
| `hydrometric-daily-mean` | Daily mean water level and discharge |
| `hydrometric-monthly-mean` | Monthly mean water data |
| `hydrometric-annual-peaks` | Annual peak water levels |
| `hydrometric-realtime` | Real-time water data |

### Air Quality
| ID | Description |
|----|-------------|
| `aqhi-observations-realtime` | Real-time Air Quality Health Index |
| `aqhi-forecasts-realtime` | AQHI forecasts |

### Weather
| ID | Description |
|----|-------------|
| `citypageweather-realtime` | Current city weather conditions |
| `swob-realtime` | Surface weather observations |

## Key Query Patterns

### Filter by location (bounding box)
```
--bbox west,south,east,north
--bbox -76.0,45.2,-75.3,45.6    # Ottawa area
--bbox -80.0,43.4,-79.0,44.0    # Toronto area
--bbox -141.0,41.7,-52.6,83.1   # All of Canada
```

### Filter by time
```
--datetime 2023-06-15                           # Exact date
--datetime 2023-01-01/2023-12-31                # Date range
--datetime 2023-06-01T00:00:00Z/2023-06-30T23:59:59Z  # Datetime range
--datetime ../2023-06-15                        # Before date
--datetime 2023-06-15/..                        # After date
```

### Filter by property
```
--properties STATION_NAME=OTTAWA+CDA
--properties PROVINCE_CODE=ON
--properties STATION_NUMBER=02HA003
```

Multiple property filters can be combined:
```
--properties PROVINCE_CODE=ON STATION_NAME=TORONTO
```

## Pagination Safety

Some collections have 100M+ records. The scripts enforce safety caps:
- `geomet_fetch.py`: default `--max-items 500`
- `geomet_export.py`: default `--max-items 1000`
- Always add filters (bbox, datetime, properties) before using `--all-pages`

## Detailed API Reference

See `references/api_reference.md` for:
- Full endpoint parameter tables
- Response JSON structures
- Property schemas for each major collection
- Bounding box examples for Canadian regions
