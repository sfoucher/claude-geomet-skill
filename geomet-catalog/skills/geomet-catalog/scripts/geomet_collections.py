#!/usr/bin/env python3
"""Browse and discover GeoMet OGC API collections.

Usage:
    python geomet_collections.py --list
    python geomet_collections.py --search climate
    python geomet_collections.py --info climate-hourly
    python geomet_collections.py --queryables climate-hourly
    python geomet_collections.py --categories
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

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


def list_collections():
    """List all collection IDs and titles."""
    data = fetch_json(f"{BASE_URL}/collections?f=json")
    collections = data.get("collections", [])
    if not collections:
        print("No collections found.")
        return

    # Find max ID length for alignment
    max_id = max(len(c.get("id", "")) for c in collections)
    max_id = min(max_id, 50)

    print(f"{'ID':<{max_id}}  TITLE")
    print(f"{'-' * max_id}  {'-' * 60}")
    for c in sorted(collections, key=lambda x: x.get("id", "")):
        cid = c.get("id", "")
        title = c.get("title", "(no title)")
        print(f"{cid:<{max_id}}  {title}")

    print(f"\nTotal: {len(collections)} collections")


def search_collections(keyword):
    """Search collections by keyword in ID, title, description, and keywords."""
    data = fetch_json(f"{BASE_URL}/collections?f=json")
    collections = data.get("collections", [])
    keyword_lower = keyword.lower()

    matches = []
    for c in collections:
        searchable = " ".join([
            c.get("id", ""),
            c.get("title", ""),
            c.get("description", ""),
            " ".join(c.get("keywords", []))
        ]).lower()
        if keyword_lower in searchable:
            matches.append(c)

    if not matches:
        print(f"No collections matching '{keyword}'.")
        return

    max_id = max(len(c.get("id", "")) for c in matches)
    max_id = min(max_id, 50)

    print(f"{'ID':<{max_id}}  TITLE")
    print(f"{'-' * max_id}  {'-' * 60}")
    for c in sorted(matches, key=lambda x: x.get("id", "")):
        cid = c.get("id", "")
        title = c.get("title", "(no title)")
        print(f"{cid:<{max_id}}  {title}")

    print(f"\nFound: {len(matches)} collections matching '{keyword}'")


def show_info(collection_id):
    """Show full metadata for a collection."""
    data = fetch_json(f"{BASE_URL}/collections/{collection_id}?f=json")

    print(f"Collection: {data.get('id', collection_id)}")
    print(f"Title:      {data.get('title', 'N/A')}")
    print(f"Description:\n  {data.get('description', 'N/A')}")

    keywords = data.get("keywords", [])
    if keywords:
        print(f"Keywords:   {', '.join(keywords)}")

    extent = data.get("extent", {})
    spatial = extent.get("spatial", {})
    bbox = spatial.get("bbox", [])
    if bbox:
        print(f"Spatial:    {bbox[0]}")
        crs = spatial.get("crs")
        if crs:
            print(f"CRS:        {crs}")

    temporal = extent.get("temporal", {})
    interval = temporal.get("interval", [])
    if interval:
        print(f"Temporal:   {interval[0]}")

    links = data.get("links", [])
    if links:
        print("\nLinks:")
        for link in links:
            rel = link.get("rel", "")
            href = link.get("href", "")
            ltype = link.get("type", "")
            title = link.get("title", "")
            print(f"  [{rel}] {title or href}")
            if title and href:
                print(f"    {href}")


def show_queryables(collection_id):
    """Show filterable properties for a collection."""
    data = fetch_json(f"{BASE_URL}/collections/{collection_id}/queryables?f=json")

    props = data.get("properties", {})
    if not props:
        print(f"No queryable properties for '{collection_id}'.")
        return

    print(f"Queryable properties for '{collection_id}':")
    print(f"{'PROPERTY':<35}  {'TYPE':<15}  TITLE")
    print(f"{'-' * 35}  {'-' * 15}  {'-' * 40}")
    for name, info in sorted(props.items()):
        ptype = info.get("type", "unknown")
        title = info.get("title", "")
        print(f"{name:<35}  {ptype:<15}  {title}")


def show_categories():
    """Group collections by category prefix (text before first dash)."""
    data = fetch_json(f"{BASE_URL}/collections?f=json")
    collections = data.get("collections", [])

    categories = {}
    for c in collections:
        cid = c.get("id", "")
        # Use text before first dash as category, or full ID if no dash
        parts = cid.split("-")
        cat = parts[0] if len(parts) > 1 else "other"
        categories.setdefault(cat, []).append(c)

    for cat in sorted(categories):
        items = sorted(categories[cat], key=lambda x: x.get("id", ""))
        print(f"\n[{cat}] ({len(items)} collections)")
        for c in items:
            cid = c.get("id", "")
            title = c.get("title", "(no title)")
            print(f"  {cid}: {title}")


def main():
    parser = argparse.ArgumentParser(
        description="Browse GeoMet OGC API collections"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true",
                       help="List all collection IDs and titles")
    group.add_argument("--search", metavar="KEYWORD",
                       help="Search collections by keyword")
    group.add_argument("--info", metavar="COLLECTION_ID",
                       help="Show full metadata for a collection")
    group.add_argument("--queryables", metavar="COLLECTION_ID",
                       help="Show filterable properties for a collection")
    group.add_argument("--categories", action="store_true",
                       help="Group collections by category prefix")

    args = parser.parse_args()

    if args.list:
        list_collections()
    elif args.search:
        search_collections(args.search)
    elif args.info:
        show_info(args.info)
    elif args.queryables:
        show_queryables(args.queryables)
    elif args.categories:
        show_categories()


if __name__ == "__main__":
    main()
