# claude-geomet-skill

A Claude Code plugin that provides access to Environment and Climate Change Canada's open data through the MSC GeoMet OGC API. Browse, query, visualize, and export Canadian weather, climate, hydrometric, and air quality data -- all from within Claude Code.

## Installation

```
/plugin marketplace add sfoucher/claude-geomet-skill
/plugin install geomet-catalog@claude-geomet-skill
```

## Quick Start

Once installed, the skill triggers automatically when you ask about Canadian weather or climate data. Here are some example prompts:

```
Search for climate collections on GeoMet

Fetch the last 20 hourly temperature readings from Ottawa

Export daily climate data for Toronto area (June 2023) to CSV

Plot a time series of temperature from climate-hourly for Ottawa
```

## Available Scripts

| Script | Description | Dependencies |
|--------|-------------|--------------|
| `geomet_collections.py` | Browse and search available data collections | Python stdlib only |
| `geomet_fetch.py` | Fetch and display data with spatial/temporal/property filters | Python stdlib only |
| `geomet_export.py` | Export data to CSV or GeoJSON files | Python stdlib only |
| `geomet_visualize.py` | Generate time series, bar, scatter, and map charts | matplotlib |

## Data Categories

- **Climate** -- Hourly, daily, monthly observations and 30-year normals
- **Hydrometric** -- Water levels, discharge, annual peaks (real-time and historical)
- **Air Quality** -- Real-time AQHI observations and forecasts
- **Weather** -- Current city conditions and surface weather observations

## Requirements

- Python 3.8+
- `matplotlib` (optional, only needed for `geomet_visualize.py`)

No API key required. The GeoMet API is free and public.

## API Reference

Full API documentation is included in `skills/geomet-catalog/references/api_reference.md`, covering endpoints, filter patterns, bounding box examples for Canadian regions, and property schemas for major collections.

- GeoMet OGC API: https://api.weather.gc.ca
- MSC GeoMet Documentation: https://eccc-msc.github.io/open-data/msc-geomet/readme_en/

## License

[MIT](LICENSE)
