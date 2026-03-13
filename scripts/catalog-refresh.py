#!/usr/bin/env python3
"""
Montreal Open Data — Catalog Refresh
======================================
Pulls the full dataset catalog from CKAN and generates reference JSON files
that skills and agents can use for fast lookups without API calls.

Outputs:
  reference/dataset-catalog.json    — All datasets with key metadata
  reference/endpoint-registry.json  — All DataStore-active resource UUIDs
  reference/org-summary.json        — Organization breakdown

Usage:
  python3 scripts/catalog-refresh.py              # Refresh all
  python3 scripts/catalog-refresh.py --stats      # Show stats only
  python3 scripts/catalog-refresh.py --json       # Stats as JSON (for agents)
"""

import json
import sys
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REF_DIR = REPO_ROOT / "reference"
CKAN_BASE = "https://donnees.montreal.ca/api/3/action"
ROWS_PER_PAGE = 100


def fetch_json(url):
    """Fetch JSON from a URL. Returns parsed dict or None."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "MontrealOpenData-CatalogRefresh/1.0")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url[:80]}...: {e}", file=sys.stderr)
        return None


def fetch_all_datasets():
    """Paginate through all datasets in the catalog."""
    all_datasets = []
    start = 0

    while True:
        url = f"{CKAN_BASE}/package_search?rows={ROWS_PER_PAGE}&start={start}"
        data = fetch_json(url)
        if not data or not data.get("success"):
            break

        results = data["result"]["results"]
        if not results:
            break

        all_datasets.extend(results)
        total = data["result"]["count"]
        start += ROWS_PER_PAGE

        print(f"  📥 Fetched {len(all_datasets)}/{total} datasets...", end="\r")

        if len(all_datasets) >= total:
            break

    print(f"  📥 Fetched {len(all_datasets)} datasets total.        ")
    return all_datasets


def build_catalog(datasets):
    """Build the dataset-catalog.json reference file."""
    catalog = []

    for ds in datasets:
        # Extract territory codes
        territories = []
        for extra in ds.get("extras", []):
            if extra.get("key") == "territoire":
                try:
                    territories = json.loads(extra["value"])
                except (json.JSONDecodeError, TypeError):
                    territories = [extra["value"]]

        # Extract resources summary
        resources = []
        for r in ds.get("resources", []):
            resources.append({
                "id": r["id"],
                "name": r.get("name", ""),
                "format": r.get("format", "").upper(),
                "datastore_active": r.get("datastore_active", False),
                "url": r.get("url", ""),
            })

        catalog.append({
            "slug": ds["name"],
            "title": ds.get("title", ""),
            "organization": ds.get("organization", {}).get("title", ""),
            "org_name": ds.get("organization", {}).get("name", ""),
            "tags": [t["name"] for t in ds.get("tags", [])],
            "territories": territories,
            "num_resources": len(resources),
            "has_datastore": any(r["datastore_active"] for r in resources),
            "resources": resources,
            "metadata_modified": ds.get("metadata_modified", ""),
        })

    return catalog


def build_endpoint_registry(catalog):
    """Extract all DataStore-active resource UUIDs for quick agent lookup."""
    registry = []

    for ds in catalog:
        for r in ds["resources"]:
            if r["datastore_active"]:
                registry.append({
                    "resource_id": r["id"],
                    "dataset_slug": ds["slug"],
                    "dataset_title": ds["title"],
                    "resource_name": r["name"],
                    "format": r["format"],
                })

    return registry


def build_org_summary(catalog):
    """Summarize datasets by organization."""
    orgs = {}
    for ds in catalog:
        org = ds["organization"] or "Unknown"
        if org not in orgs:
            orgs[org] = {"count": 0, "with_datastore": 0, "datasets": []}
        orgs[org]["count"] += 1
        if ds["has_datastore"]:
            orgs[org]["with_datastore"] += 1
        orgs[org]["datasets"].append(ds["slug"])

    return dict(sorted(orgs.items(), key=lambda x: -x[1]["count"]))


def save_json(data, filename):
    """Save JSON to reference directory."""
    REF_DIR.mkdir(parents=True, exist_ok=True)
    path = REF_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    size_kb = path.stat().st_size / 1024
    print(f"  💾 Saved {filename} ({size_kb:.0f} KB)")
    return path


def main():
    parser = argparse.ArgumentParser(description="Montreal Open Data Catalog Refresh")
    parser.add_argument("--stats", action="store_true", help="Show stats only, don't save files")
    parser.add_argument("--json", action="store_true", help="Output stats as JSON")
    args = parser.parse_args()

    if not args.json:
        print(f"\n📚 Montreal Open Data — Catalog Refresh")
        print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Fetch everything
    datasets = fetch_all_datasets()
    if not datasets:
        print("❌ Failed to fetch any datasets.", file=sys.stderr)
        sys.exit(1)

    # Build reference structures
    catalog = build_catalog(datasets)
    registry = build_endpoint_registry(catalog)
    org_summary = build_org_summary(catalog)

    # Stats
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_datasets": len(catalog),
        "datasets_with_datastore": sum(1 for d in catalog if d["has_datastore"]),
        "total_datastore_resources": len(registry),
        "organizations": {org: info["count"] for org, info in org_summary.items()},
        "top_tags": {},
    }

    # Compute top tags
    tag_counts = {}
    for ds in catalog:
        for tag in ds["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    stats["top_tags"] = dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:20])

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.stats:
        print(f"\n  📊 Statistics:")
        print(f"     Total datasets: {stats['total_datasets']}")
        print(f"     With DataStore: {stats['datasets_with_datastore']}")
        print(f"     DataStore resources: {stats['total_datastore_resources']}")
        print(f"     Organizations: {len(stats['organizations'])}")
        print(f"\n  🏢 By organization:")
        for org, count in stats["organizations"].items():
            print(f"     {org}: {count}")
        print(f"\n  🏷️  Top tags:")
        for tag, count in list(stats["top_tags"].items())[:10]:
            print(f"     {tag}: {count}")
        sys.exit(0)

    # Save files
    print()
    save_json(catalog, "dataset-catalog.json")
    save_json(registry, "endpoint-registry.json")
    save_json(org_summary, "org-summary.json")
    save_json(stats, "catalog-stats.json")

    print(f"\n  ✅ Catalog refresh complete.")
    print(f"     {len(catalog)} datasets, {len(registry)} queryable resources.\n")


if __name__ == "__main__":
    main()
