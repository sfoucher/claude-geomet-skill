#!/usr/bin/env python3
"""Export GeoMet OGC API data to CSV or GeoJSON files.

Usage:
    python geomet_export.py climate-hourly --format csv --limit 10
    python geomet_export.py aqhi-observations-realtime --format geojson --limit 10
    python geomet_export.py climate-daily --format csv --bbox -80,43,-70,47 --all-pages --max-items 200
    python geomet_export.py hydrometric-daily-mean --format csv --properties STATION_NUMBER=02HA003 --limit 50
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

BASE_URL = "https://api.weather.gc.ca"


def fetch_json(url):
    """Fetch JSON from URL. Returns parsed dict or exits on error."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "geomet-catalog-skill/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
            print(f"Response: {body}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def build_url(collection_id, limit, offset, bbox=None, dt=None, properties=None,
              sortby=None):
    """Build the items URL with query parameters."""
    params = {
        "limit": str(limit),
        "offset": str(offset),
        "f": "json"
    }
    if bbox:
        params["bbox"] = bbox
    if dt:
        params["datetime"] = dt
    if sortby:
        params["sortby"] = sortby
    if properties:
        for prop in properties:
            key, value = prop.split("=", 1)
            params[key] = value

    query = urllib.parse.urlencode(params)
    return f"{BASE_URL}/collections/{collection_id}/items?{query}"


def fetch_all(collection_id, args):
    """Fetch items, optionally paginating through all pages."""
    all_features = []
    limit_per_page = min(args.limit or 100, 500)
    offset = 0
    max_items = args.max_items if args.all_pages else (args.limit or 10)

    while len(all_features) < max_items:
        current_limit = min(limit_per_page, max_items - len(all_features))
        url = build_url(
            collection_id, current_limit, offset,
            bbox=args.bbox, dt=args.datetime, properties=args.properties,
            sortby=args.sortby
        )
        data = fetch_json(url)
        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        offset += len(features)

        links = data.get("links", [])
        has_next = any(link.get("rel") == "next" for link in links)
        if not has_next:
            break

        if args.all_pages and len(all_features) < max_items:
            print(f"  Fetched {len(all_features)} items...", file=sys.stderr)
            time.sleep(0.1)

    return all_features[:max_items]


def extract_geometry_coords(feature):
    """Extract lon/lat from geometry if it's a Point."""
    geom = feature.get("geometry")
    if not geom:
        return None, None
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])
    if geom_type == "Point" and len(coords) >= 2:
        return coords[0], coords[1]
    return None, None


def export_csv(features, collection_id, output_path=None):
    """Export features to CSV, flattening geometry into lon/lat columns."""
    if not features:
        print("No features to export.", file=sys.stderr)
        return

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{collection_id}_{timestamp}.csv"

    # Collect all property keys
    all_keys = set()
    for f in features:
        all_keys.update(f.get("properties", {}).keys())
    columns = ["id", "longitude", "latitude"] + sorted(all_keys)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for feature in features:
            props = feature.get("properties", {})
            lon, lat = extract_geometry_coords(feature)
            row = [
                feature.get("id", ""),
                lon if lon is not None else "",
                lat if lat is not None else ""
            ]
            for key in sorted(all_keys):
                val = props.get(key, "")
                if val is None:
                    val = ""
                row.append(val)
            writer.writerow(row)

    print(f"Exported {len(features)} features to {output_path}")
    return output_path


def export_geojson(features, collection_id, output_path=None):
    """Export features as a GeoJSON FeatureCollection."""
    if not features:
        print("No features to export.", file=sys.stderr)
        return

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{collection_id}_{timestamp}.geojson"

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(geojson, fh, indent=2, ensure_ascii=False)

    print(f"Exported {len(features)} features to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Export GeoMet OGC API data to CSV or GeoJSON"
    )
    parser.add_argument("collection", help="Collection ID (e.g., climate-hourly)")
    parser.add_argument("--format", choices=["csv", "geojson"], default="csv",
                        dest="fmt", help="Output format (default: csv)")
    parser.add_argument("--output", "-o", help="Output file path (auto-generated if omitted)")
    parser.add_argument("--bbox", help="Bounding box: west,south,east,north")
    parser.add_argument("--datetime",
                        help="Datetime filter: single, range (start/end), or open (../end)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Items per page (default: 100)")
    parser.add_argument("--properties", nargs="+", metavar="KEY=VALUE",
                        help="Filter by property values")
    parser.add_argument("--sortby", help="Sort by property (prefix with - for descending)")
    parser.add_argument("--all-pages", action="store_true",
                        help="Fetch all pages of results")
    parser.add_argument("--max-items", type=int, default=1000,
                        help="Max total items when using --all-pages (default: 1000)")

    args = parser.parse_args()

    print(f"Fetching from '{args.collection}'...", file=sys.stderr)
    features = fetch_all(args.collection, args)
    print(f"Retrieved {len(features)} features.", file=sys.stderr)

    if args.fmt == "csv":
        export_csv(features, args.collection, args.output)
    else:
        export_geojson(features, args.collection, args.output)


if __name__ == "__main__":
    main()
