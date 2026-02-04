#!/usr/bin/env python3
"""Fetch items/features from a GeoMet OGC API collection with filters.

Usage:
    python geomet_fetch.py climate-hourly --limit 5
    python geomet_fetch.py hydrometric-daily-mean --properties STATION_NUMBER=02HA003 --limit 10
    python geomet_fetch.py climate-daily --bbox -80,43,-70,47 --datetime 2023-01-01/2023-01-31 --limit 20
    python geomet_fetch.py climate-hourly --limit 10 --json
    python geomet_fetch.py climate-hourly --all-pages --max-items 100
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

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


def build_url(collection_id, args):
    """Build the items URL with query parameters."""
    params = {}

    if args.limit:
        params["limit"] = str(args.limit)
    if args.offset:
        params["offset"] = str(args.offset)
    if args.bbox:
        params["bbox"] = args.bbox
    if args.datetime:
        params["datetime"] = args.datetime
    if args.sortby:
        params["sortby"] = args.sortby
    if args.fields:
        params["properties"] = args.fields

    # Custom property filters
    if args.properties:
        for prop in args.properties:
            key, value = prop.split("=", 1)
            params[key] = value

    params["f"] = "json"

    query = urllib.parse.urlencode(params)
    return f"{BASE_URL}/collections/{collection_id}/items?{query}"


def extract_properties(feature):
    """Extract properties from a GeoJSON feature, flattening as needed."""
    props = dict(feature.get("properties", {}))
    props["id"] = feature.get("id", "")
    return props


def print_table(features, fields=None):
    """Print features as an aligned text table."""
    if not features:
        print("No features returned.")
        return

    all_props = [extract_properties(f) for f in features]

    # Determine columns
    if fields:
        columns = [f.strip() for f in fields.split(",")]
    else:
        # Collect all keys, put id first
        col_set = set()
        for p in all_props:
            col_set.update(p.keys())
        col_set.discard("id")
        columns = ["id"] + sorted(col_set)

    # Limit columns for readability (max 10 in auto mode)
    if not fields and len(columns) > 10:
        columns = columns[:10]
        truncated = True
    else:
        truncated = False

    # Calculate widths
    widths = {}
    for col in columns:
        values = [str(p.get(col, ""))[:40] for p in all_props]
        widths[col] = max(len(col), max((len(v) for v in values), default=0))
        widths[col] = min(widths[col], 40)

    # Header
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("  ".join("-" * widths[col] for col in columns))

    # Rows
    for p in all_props:
        row = "  ".join(str(p.get(col, ""))[:40].ljust(widths[col]) for col in columns)
        print(row)

    if truncated:
        print(f"\n(Showing first 10 of {len(col_set) + 1} columns. Use --fields to select specific columns.)")


def fetch_all_pages(collection_id, args, max_items):
    """Fetch multiple pages of results."""
    all_features = []
    limit_per_page = min(args.limit or 100, 500)
    offset = args.offset or 0

    while len(all_features) < max_items:
        # Temporarily set limit/offset for this page
        args.limit = limit_per_page
        args.offset = offset
        url = build_url(collection_id, args)
        data = fetch_json(url)

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        offset += len(features)

        # Check for next link
        links = data.get("links", [])
        has_next = any(link.get("rel") == "next" for link in links)
        if not has_next:
            break

        if len(all_features) < max_items:
            time.sleep(0.1)  # Be polite

        print(f"  Fetched {len(all_features)} items so far...", file=sys.stderr)

    # Trim to max_items
    return all_features[:max_items]


def main():
    parser = argparse.ArgumentParser(
        description="Fetch items from a GeoMet OGC API collection"
    )
    parser.add_argument("collection", help="Collection ID (e.g., climate-hourly)")
    parser.add_argument("--bbox", help="Bounding box: west,south,east,north")
    parser.add_argument("--datetime",
                        help="Datetime filter: single, range (start/end), or open (../end, start/..)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Max items per request (default: 10)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Starting offset (default: 0)")
    parser.add_argument("--properties", nargs="+", metavar="KEY=VALUE",
                        help="Filter by property values")
    parser.add_argument("--sortby", help="Sort by property (prefix with - for descending)")
    parser.add_argument("--fields", help="Comma-separated list of fields to display")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output raw JSON instead of table")
    parser.add_argument("--all-pages", action="store_true",
                        help="Fetch all pages of results")
    parser.add_argument("--max-items", type=int, default=500,
                        help="Max total items when using --all-pages (default: 500)")

    args = parser.parse_args()

    if args.all_pages:
        features = fetch_all_pages(args.collection, args, args.max_items)
        print(f"Total items fetched: {len(features)}", file=sys.stderr)
    else:
        url = build_url(args.collection, args)
        data = fetch_json(url)
        features = data.get("features", [])
        matched = data.get("numberMatched", "unknown")
        returned = data.get("numberReturned", len(features))
        print(f"Matched: {matched} | Returned: {returned}", file=sys.stderr)

    if args.json_output:
        print(json.dumps(features, indent=2, ensure_ascii=False))
    else:
        print_table(features, args.fields)


if __name__ == "__main__":
    main()
