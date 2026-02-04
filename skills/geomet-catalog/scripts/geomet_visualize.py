#!/usr/bin/env python3
"""Generate matplotlib visualizations from GeoMet OGC API data.

Usage:
    python geomet_visualize.py climate-hourly --type timeseries --y-field TEMP --limit 100
    python geomet_visualize.py climate-hourly --type bar --x-field LOCAL_MONTH --y-field TEMP --limit 500
    python geomet_visualize.py aqhi-observations-realtime --type map --limit 100
    python geomet_visualize.py climate-daily --type scatter --x-field MIN_TEMP --y-field MAX_TEMP --limit 200

Requires matplotlib: pip install matplotlib
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "https://api.weather.gc.ca"

# Common date field names across GeoMet collections
DATE_FIELDS = [
    "LOCAL_DATE", "LOCAL_DATETIME", "DATE", "DATETIME",
    "OBSERVATION_DATE_LOCAL", "OBSERVATION_DATETIME_LOCAL",
    "date", "datetime", "time", "timestamp",
    "TIMESTAMP", "TIME", "PERIOD_BEGIN", "PERIOD_END"
]


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
    """Fetch items with optional pagination."""
    all_features = []
    limit_per_page = min(args.limit or 100, 500)
    offset = 0
    max_items = args.limit or 100

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

        if len(all_features) < max_items:
            time.sleep(0.1)

    return all_features[:max_items]


def detect_date_field(features):
    """Auto-detect date field from feature properties."""
    if not features:
        return None
    sample = features[0].get("properties", {})
    for field in DATE_FIELDS:
        if field in sample:
            return field
    return None


def parse_date(value):
    """Try to parse a date string into a datetime object."""
    from datetime import datetime
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y%m%d"
    ]
    if isinstance(value, str):
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def to_numeric(value):
    """Try to convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def plot_timeseries(features, args):
    """Generate a time series plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    y_field = args.y_field
    if not y_field:
        print("Error: --y-field is required for timeseries plots.", file=sys.stderr)
        sys.exit(1)

    x_field = args.x_field
    if not x_field:
        x_field = detect_date_field(features)
        if not x_field:
            print("Error: Could not auto-detect date field. Use --x-field.", file=sys.stderr)
            sys.exit(1)
        print(f"Auto-detected date field: {x_field}", file=sys.stderr)

    dates = []
    values = []
    for f in features:
        props = f.get("properties", {})
        d = parse_date(props.get(x_field))
        v = to_numeric(props.get(y_field))
        if d is not None and v is not None:
            dates.append(d)
            values.append(v)

    if not dates:
        print("Error: No valid date/value pairs found.", file=sys.stderr)
        sys.exit(1)

    # Sort by date
    paired = sorted(zip(dates, values))
    dates, values = zip(*paired)

    fig, ax = plt.subplots(figsize=(12, 6))

    if args.group_by:
        groups = {}
        for f in features:
            props = f.get("properties", {})
            group = str(props.get(args.group_by, "unknown"))
            d = parse_date(props.get(x_field))
            v = to_numeric(props.get(y_field))
            if d is not None and v is not None:
                groups.setdefault(group, ([], []))
                groups[group][0].append(d)
                groups[group][1].append(v)
        for label, (gd, gv) in sorted(groups.items()):
            paired = sorted(zip(gd, gv))
            gd, gv = zip(*paired)
            ax.plot(gd, gv, marker=".", label=label, alpha=0.7)
        ax.legend(fontsize=8)
    else:
        ax.plot(dates, values, marker=".", color="#2196F3", alpha=0.7)

    ax.set_xlabel(x_field)
    ax.set_ylabel(y_field)
    ax.set_title(args.title or f"{args.collection}: {y_field} over time")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    output = args.output or f"{args.collection}_timeseries.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved timeseries plot to {output}")


def plot_bar(features, args):
    """Generate a bar chart."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_field = args.x_field
    y_field = args.y_field
    if not x_field or not y_field:
        print("Error: --x-field and --y-field are required for bar plots.", file=sys.stderr)
        sys.exit(1)

    # Aggregate by x_field
    aggregated = {}
    counts = {}
    for f in features:
        props = f.get("properties", {})
        x = str(props.get(x_field, ""))
        v = to_numeric(props.get(y_field))
        if x and v is not None:
            aggregated[x] = aggregated.get(x, 0) + v
            counts[x] = counts.get(x, 0) + 1

    # Average
    for k in aggregated:
        aggregated[k] /= counts[k]

    if not aggregated:
        print("Error: No valid data for bar chart.", file=sys.stderr)
        sys.exit(1)

    labels = sorted(aggregated.keys())
    values = [aggregated[l] for l in labels]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(labels)), values, color="#4CAF50", alpha=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel(x_field)
    ax.set_ylabel(f"Avg {y_field}")
    ax.set_title(args.title or f"{args.collection}: {y_field} by {x_field}")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()

    output = args.output or f"{args.collection}_bar.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved bar chart to {output}")


def plot_scatter(features, args):
    """Generate a scatter plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_field = args.x_field
    y_field = args.y_field
    if not x_field or not y_field:
        print("Error: --x-field and --y-field are required for scatter plots.", file=sys.stderr)
        sys.exit(1)

    xs = []
    ys = []
    groups = [] if args.group_by else None
    for f in features:
        props = f.get("properties", {})
        x = to_numeric(props.get(x_field))
        y = to_numeric(props.get(y_field))
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
            if groups is not None:
                groups.append(str(props.get(args.group_by, "unknown")))

    if not xs:
        print("Error: No valid data for scatter plot.", file=sys.stderr)
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(10, 8))

    if groups:
        unique_groups = sorted(set(groups))
        colors = plt.cm.tab10(range(len(unique_groups)))
        for i, g in enumerate(unique_groups):
            gx = [x for x, gr in zip(xs, groups) if gr == g]
            gy = [y for y, gr in zip(ys, groups) if gr == g]
            ax.scatter(gx, gy, label=g, alpha=0.6, s=20, color=colors[i % len(colors)])
        ax.legend(fontsize=8)
    else:
        ax.scatter(xs, ys, alpha=0.6, s=20, color="#FF5722")

    ax.set_xlabel(x_field)
    ax.set_ylabel(y_field)
    ax.set_title(args.title or f"{args.collection}: {y_field} vs {x_field}")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    output = args.output or f"{args.collection}_scatter.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved scatter plot to {output}")


def plot_map(features, args):
    """Generate a simple map (scatter plot of lon/lat)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lons = []
    lats = []
    values = []
    y_field = args.y_field

    for f in features:
        geom = f.get("geometry")
        if not geom or geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) >= 2:
            lons.append(coords[0])
            lats.append(coords[1])
            if y_field:
                v = to_numeric(f.get("properties", {}).get(y_field))
                values.append(v if v is not None else 0)

    if not lons:
        print("Error: No Point geometries found for map.", file=sys.stderr)
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(12, 8))

    if values and y_field:
        sc = ax.scatter(lons, lats, c=values, cmap="RdYlBu_r", alpha=0.7, s=30,
                        edgecolors="gray", linewidth=0.5)
        plt.colorbar(sc, ax=ax, label=y_field, shrink=0.8)
    else:
        ax.scatter(lons, lats, alpha=0.7, s=30, color="#2196F3",
                   edgecolors="gray", linewidth=0.5)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(args.title or f"{args.collection}: Station Map")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    output = args.output or f"{args.collection}_map.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    print(f"Saved map to {output}")


def main():
    try:
        import matplotlib
    except ImportError:
        print("Error: matplotlib is required for visualization.", file=sys.stderr)
        print("Install it with: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Generate visualizations from GeoMet OGC API data"
    )
    parser.add_argument("collection", help="Collection ID (e.g., climate-hourly)")
    parser.add_argument("--type", choices=["timeseries", "bar", "scatter", "map"],
                        required=True, dest="plot_type",
                        help="Visualization type")
    parser.add_argument("--x-field", help="Property to use for X axis")
    parser.add_argument("--y-field", help="Property to use for Y axis / color")
    parser.add_argument("--group-by", help="Property to group data by")
    parser.add_argument("--title", help="Chart title (auto-generated if omitted)")
    parser.add_argument("--output", "-o", help="Output PNG path (auto-generated if omitted)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of items to fetch (default: 100)")
    parser.add_argument("--bbox", help="Bounding box: west,south,east,north")
    parser.add_argument("--datetime",
                        help="Datetime filter: single, range, or open")
    parser.add_argument("--properties", nargs="+", metavar="KEY=VALUE",
                        help="Filter by property values")
    parser.add_argument("--sortby", help="Sort by property")

    args = parser.parse_args()

    print(f"Fetching data from '{args.collection}'...", file=sys.stderr)
    features = fetch_all(args.collection, args)
    print(f"Retrieved {len(features)} features.", file=sys.stderr)

    if not features:
        print("No data to visualize.", file=sys.stderr)
        sys.exit(1)

    if args.plot_type == "timeseries":
        plot_timeseries(features, args)
    elif args.plot_type == "bar":
        plot_bar(features, args)
    elif args.plot_type == "scatter":
        plot_scatter(features, args)
    elif args.plot_type == "map":
        plot_map(features, args)


if __name__ == "__main__":
    main()
