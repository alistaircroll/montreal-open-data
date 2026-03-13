#!/usr/bin/env python3
"""
Montreal Open Data — Field Inspector
======================================
The single most useful debugging tool for this skill system.

Skills document expected field names, but datasets change. This script
queries the actual DataStore schema for any resource, showing:
  - Real field names (case-sensitive)
  - Data types
  - Sample values
  - Null counts

Usage:
  python3 scripts/field-inspector.py <resource_id>
  python3 scripts/field-inspector.py <dataset_slug>         # Auto-finds DataStore resources
  python3 scripts/field-inspector.py <resource_id> --json   # Machine-readable
  python3 scripts/field-inspector.py <resource_id> --sample 5  # Show N sample rows

Examples:
  python3 scripts/field-inspector.py 64e28fe6-ef37-437a-972d-d1d3f1f7d891   # Trees
  python3 scripts/field-inspector.py arbres                                   # Find by slug
  python3 scripts/field-inspector.py permis-construction                      # Building permits
"""

import json
import sys
import urllib.request
import urllib.error
import urllib.parse
import argparse
from datetime import datetime, timezone


CKAN_BASE = "https://donnees.montreal.ca/api/3/action"


def fetch_json(url):
    """Fetch JSON from a URL."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "MontrealOpenData-FieldInspector/1.0")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def resolve_slug_to_resources(slug):
    """Given a dataset slug, find all DataStore-active resource IDs."""
    url = f"{CKAN_BASE}/package_show?id={urllib.parse.quote(slug)}"
    data = fetch_json(url)

    if "error" in data or not data.get("success"):
        return []

    resources = []
    for r in data["result"].get("resources", []):
        if r.get("datastore_active"):
            resources.append({
                "id": r["id"],
                "name": r.get("name", "(unnamed)"),
                "format": r.get("format", ""),
            })
    return resources


def inspect_resource(resource_id, sample_size=3):
    """Get field info and sample data for a DataStore resource."""
    # Get schema via datastore_info (or fallback to datastore_search with limit=0)
    info_url = f"{CKAN_BASE}/datastore_search?resource_id={resource_id}&limit=0"
    info = fetch_json(info_url)

    if "error" in info or not info.get("success"):
        return {"error": f"Cannot access resource {resource_id}: {info.get('error', 'unknown')}"}

    result = info["result"]
    fields = result.get("fields", [])
    total = result.get("total", 0)

    # Get sample rows
    sample_url = f"{CKAN_BASE}/datastore_search?resource_id={resource_id}&limit={sample_size}"
    sample_data = fetch_json(sample_url)
    sample_records = sample_data.get("result", {}).get("records", []) if sample_data.get("success") else []

    # Build field report
    field_report = []
    for f in fields:
        name = f["id"]
        ftype = f.get("type", "unknown")

        # Skip internal CKAN field
        if name == "_id":
            continue

        # Get sample values for this field
        samples = [str(r.get(name, ""))[:60] for r in sample_records if r.get(name) is not None]

        field_report.append({
            "name": name,
            "type": ftype,
            "samples": samples[:sample_size],
        })

    return {
        "resource_id": resource_id,
        "total_records": total,
        "field_count": len(field_report),
        "fields": field_report,
    }


def print_human(report):
    """Pretty-print field report for humans."""
    if "error" in report:
        print(f"❌ {report['error']}")
        return

    print(f"\n🔍 Resource: {report['resource_id']}")
    print(f"   Records: {report['total_records']:,}")
    print(f"   Fields:  {report['field_count']}\n")

    # Column widths
    name_w = max(len(f["name"]) for f in report["fields"]) + 2
    type_w = 12

    print(f"  {'FIELD':<{name_w}} {'TYPE':<{type_w}} SAMPLE VALUES")
    print(f"  {'─' * name_w} {'─' * type_w} {'─' * 50}")

    for f in report["fields"]:
        samples_str = " │ ".join(f["samples"][:3]) if f["samples"] else "(empty)"
        if len(samples_str) > 50:
            samples_str = samples_str[:47] + "..."
        print(f"  {f['name']:<{name_w}} {f['type']:<{type_w}} {samples_str}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Inspect field names and types for a Montreal Open Data resource"
    )
    parser.add_argument("target", help="Resource UUID or dataset slug")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--sample", type=int, default=3, help="Number of sample rows")
    args = parser.parse_args()

    target = args.target.strip()

    # Detect if it's a UUID (contains hyphens and is ~36 chars) or a slug
    is_uuid = len(target) > 30 and "-" in target

    if is_uuid:
        resource_ids = [target]
    else:
        # It's a dataset slug — resolve to resource IDs
        if not args.json:
            print(f"\n📦 Looking up dataset: {target}")
        resources = resolve_slug_to_resources(target)

        if not resources:
            msg = f"No DataStore-active resources found for '{target}'"
            if args.json:
                print(json.dumps({"error": msg}))
            else:
                print(f"❌ {msg}")
                print("   Try the full resource UUID instead, or check the dataset slug.")
            sys.exit(1)

        if not args.json:
            print(f"   Found {len(resources)} DataStore resource(s):")
            for r in resources:
                print(f"   • {r['name']} ({r['format']}) — {r['id']}")

        resource_ids = [r["id"] for r in resources]

    # Inspect each resource
    all_reports = []
    for rid in resource_ids:
        report = inspect_resource(rid, sample_size=args.sample)
        all_reports.append(report)

        if args.json:
            continue
        print_human(report)

    if args.json:
        output = all_reports[0] if len(all_reports) == 1 else all_reports
        print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
