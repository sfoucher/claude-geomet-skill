# GeoMet OGC API Reference

Base URL: `https://api.weather.gc.ca`

No authentication required. All endpoints are free and public.

## Endpoints

### List Collections

```
GET /collections?f=json
```

Returns all available data collections.

**Response structure:**
```json
{
  "collections": [
    {
      "id": "climate-hourly",
      "title": "Hourly Climate Observations",
      "description": "...",
      "keywords": ["climate", "hourly", "temperature"],
      "extent": {
        "spatial": {
          "bbox": [[-141.0, 41.7, -52.6, 83.1]],
          "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
        },
        "temporal": {
          "interval": [["1953-01-01T00:00:00Z", null]]
        }
      },
      "links": [...]
    }
  ]
}
```

### Collection Metadata

```
GET /collections/{collectionId}?f=json
```

Returns full metadata for a single collection.

### Queryable Properties

```
GET /collections/{collectionId}/queryables?f=json
```

Returns filterable properties and their types.

**Response structure:**
```json
{
  "properties": {
    "STATION_NAME": {
      "title": "Station Name",
      "type": "string"
    },
    "TEMP": {
      "title": "Temperature",
      "type": "number"
    }
  }
}
```

### Fetch Items

```
GET /collections/{collectionId}/items?f=json
```

**Parameters:**

| Parameter  | Type   | Description                                          |
|-----------|--------|------------------------------------------------------|
| `f`       | string | Format: `json`, `csv`, `html`                        |
| `limit`   | int    | Max items per response (default varies, max ~500)     |
| `offset`  | int    | Skip N items for pagination                          |
| `bbox`    | string | Bounding box: `west,south,east,north` (WGS84)       |
| `datetime`| string | Temporal filter (see patterns below)                  |
| `sortby`  | string | Sort field, prefix `-` for descending                |
| `properties`| string | Comma-separated list of properties to return       |
| `{property}` | string | Filter by any queryable property              |

**Response structure (GeoJSON FeatureCollection):**
```json
{
  "type": "FeatureCollection",
  "numberMatched": 1234567,
  "numberReturned": 10,
  "features": [
    {
      "type": "Feature",
      "id": "climate-hourly.12345",
      "geometry": {
        "type": "Point",
        "coordinates": [-75.7, 45.4]
      },
      "properties": {
        "STATION_NAME": "OTTAWA CDA",
        "TEMP": 5.2,
        "LOCAL_DATE": "2023-06-15",
        ...
      }
    }
  ],
  "links": [
    {"rel": "next", "href": "...?offset=10"}
  ]
}
```

## Datetime Filter Patterns

| Pattern                          | Meaning                          |
|---------------------------------|----------------------------------|
| `2023-06-15`                    | Exact date                       |
| `2023-06-15T14:00:00Z`         | Exact datetime                   |
| `2023-01-01/2023-12-31`        | Date range (inclusive)           |
| `2023-01-01T00:00:00Z/2023-01-31T23:59:59Z` | Datetime range    |
| `../2023-06-15`                 | Everything before date           |
| `2023-06-15/..`                 | Everything after date            |

## Bounding Box Examples (Canadian Regions)

| Region              | bbox                            |
|--------------------|---------------------------------|
| All of Canada       | `-141.0,41.7,-52.6,83.1`       |
| Ontario            | `-95.2,41.7,-74.3,56.9`        |
| Quebec             | `-79.8,44.9,-57.1,62.6`        |
| British Columbia   | `-139.1,48.3,-114.0,60.0`      |
| Alberta            | `-120.0,49.0,-110.0,60.0`      |
| Prairies (MB+SK)   | `-110.0,49.0,-88.0,60.0`       |
| Atlantic Canada    | `-67.0,43.4,-52.6,52.2`        |
| Northern Canada    | `-141.0,60.0,-52.6,83.1`       |
| Toronto area       | `-80.0,43.4,-79.0,44.0`        |
| Montreal area      | `-74.0,45.3,-73.3,45.7`        |
| Vancouver area     | `-123.5,49.0,-122.5,49.5`      |
| Ottawa area        | `-76.0,45.2,-75.3,45.6`        |

## Key Collections by Category

### Climate

| Collection ID      | Description                                    | Key Properties                     |
|-------------------|------------------------------------------------|-------------------------------------|
| `climate-hourly`  | Hourly observations from climate stations       | TEMP, DEW_POINT_TEMP, REL_HUM, WIND_SPD, STN_PRESSURE, STATION_NAME, LOCAL_DATE, LOCAL_DATETIME |
| `climate-daily`   | Daily summaries from climate stations           | MAX_TEMP, MIN_TEMP, MEAN_TEMP, TOTAL_PRECIP, TOTAL_RAIN, TOTAL_SNOW, STATION_NAME, LOCAL_DATE |
| `climate-monthly` | Monthly climate summaries                       | MEAN_TEMP, TOTAL_PRECIP, STATION_NAME, LOCAL_MONTH, LOCAL_YEAR |
| `climate-normals` | 30-year climate normals (1981-2010, 1991-2020) | Various normal values               |

### Hydrometric

| Collection ID            | Description                          | Key Properties                       |
|-------------------------|--------------------------------------|---------------------------------------|
| `hydrometric-daily-mean`| Daily mean water levels/discharge     | DISCHARGE, LEVEL, STATION_NUMBER, STATION_NAME, DATE |
| `hydrometric-monthly-mean`| Monthly mean water data            | DISCHARGE, LEVEL, STATION_NUMBER, STATION_NAME |
| `hydrometric-annual-peaks`| Annual peak water levels           | PEAK, PEAK_ID, STATION_NUMBER        |
| `hydrometric-annual-statistics`| Annual statistics              | Various                               |
| `hydrometric-realtime`  | Real-time hydrometric data           | DISCHARGE, LEVEL, STATION_NUMBER      |

### Air Quality

| Collection ID                  | Description                    | Key Properties            |
|-------------------------------|--------------------------------|----------------------------|
| `aqhi-observations-realtime`  | Real-time AQHI observations    | AQHI, STATION_NAME         |
| `aqhi-forecasts-realtime`     | AQHI forecasts                 | AQHI, FORECAST_DATETIME    |

### Weather

| Collection ID                  | Description                    | Key Properties             |
|-------------------------------|--------------------------------|-----------------------------|
| `citypageweather-realtime`    | Current conditions by city     | Various weather fields      |
| `swob-realtime`               | Surface Weather Observations   | Various observation fields  |

### Marine / Ocean

| Collection ID       | Description                              |
|--------------------|------------------------------------------|
| `wis2-discovery-metadata` | WMO WIS2 discovery metadata        |

## Pagination

The API uses `offset` + `limit` pagination:

- Default limit varies by collection (typically 10-500)
- Check `numberMatched` in response for total count
- Check `links` array for `"rel": "next"` to detect more pages
- Maximum limit per request is typically 500

**Pagination example:**
```
# Page 1
GET /collections/climate-hourly/items?limit=100&offset=0&f=json

# Page 2
GET /collections/climate-hourly/items?limit=100&offset=100&f=json
```

**Important:** Some collections have tens of millions of records. Always use filters (bbox, datetime, property filters) to narrow results before paginating.

## Property Filtering

Filter by any queryable property by adding it as a query parameter:

```
GET /collections/climate-hourly/items?STATION_NAME=OTTAWA+CDA&f=json
GET /collections/hydrometric-daily-mean/items?STATION_NUMBER=02HA003&f=json
GET /collections/climate-daily/items?PROVINCE_CODE=ON&f=json
```

To discover available filter properties, use the queryables endpoint:
```
GET /collections/{collectionId}/queryables?f=json
```

## Sorting

Sort results using the `sortby` parameter:
```
# Ascending by date
?sortby=LOCAL_DATE

# Descending by temperature
?sortby=-TEMP
```

## Common Property Schemas

### climate-hourly

| Property          | Type    | Description                    |
|------------------|---------|--------------------------------|
| STATION_NAME     | string  | Weather station name            |
| CLIMATE_ID       | string  | Climate station identifier      |
| LOCAL_DATE       | string  | Observation date (YYYY-MM-DD)  |
| LOCAL_DATETIME   | string  | Full datetime                   |
| LOCAL_YEAR       | integer | Year                            |
| LOCAL_MONTH      | integer | Month                           |
| LOCAL_DAY        | integer | Day                             |
| LOCAL_HOUR       | integer | Hour                            |
| TEMP             | number  | Temperature (C)                |
| DEW_POINT_TEMP   | number  | Dew point temperature (C)      |
| REL_HUM          | integer | Relative humidity (%)           |
| WIND_SPD         | number  | Wind speed (km/h)              |
| WIND_DIR         | integer | Wind direction (degrees)        |
| STN_PRESSURE     | number  | Station pressure (kPa)          |
| VISIBILITY       | number  | Visibility (km)                 |
| PROVINCE_CODE    | string  | Province code (ON, QC, BC...)   |

### climate-daily

| Property          | Type    | Description                    |
|------------------|---------|--------------------------------|
| STATION_NAME     | string  | Weather station name            |
| CLIMATE_ID       | string  | Climate station identifier      |
| LOCAL_DATE       | string  | Observation date (YYYY-MM-DD)  |
| LOCAL_YEAR       | integer | Year                            |
| LOCAL_MONTH      | integer | Month                           |
| MAX_TEMP         | number  | Maximum temperature (C)        |
| MIN_TEMP         | number  | Minimum temperature (C)        |
| MEAN_TEMP        | number  | Mean temperature (C)           |
| TOTAL_PRECIP     | number  | Total precipitation (mm)        |
| TOTAL_RAIN       | number  | Total rain (mm)                |
| TOTAL_SNOW       | number  | Total snow (cm)                |
| SNOW_ON_GRND     | number  | Snow on ground (cm)            |
| PROVINCE_CODE    | string  | Province code                   |

### hydrometric-daily-mean

| Property          | Type    | Description                    |
|------------------|---------|--------------------------------|
| STATION_NUMBER   | string  | Hydrometric station ID          |
| STATION_NAME     | string  | Station name                    |
| PROV_TERR_STATE_LOC | string | Province/territory code     |
| DATE             | string  | Observation date                |
| DISCHARGE        | number  | Discharge (m3/s)               |
| LEVEL            | number  | Water level (m)                |

### aqhi-observations-realtime

| Property          | Type    | Description                    |
|------------------|---------|--------------------------------|
| AQHI             | number  | Air Quality Health Index (1-10+)|
| STATION_NAME     | string  | Monitoring station name         |
| OBSERVATION_DATETIME_LOCAL | string | Observation time       |

### citypageweather-realtime

| Property          | Type    | Description                    |
|------------------|---------|--------------------------------|
| STATION_EN       | string  | Station name (English)          |
| TEMPERATURE      | number  | Current temperature (C)        |
| HUMIDEX          | number  | Humidex value                   |
| WINDCHILL        | number  | Wind chill value                |
| RELATIVE_HUMIDITY| number  | Relative humidity (%)           |
| WIND_SPEED       | number  | Wind speed (km/h)              |
| CONDITION_EN     | string  | Current conditions (English)    |
