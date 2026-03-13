#!/usr/bin/env python3
"""
Montreal Open Data — Endpoint Health Check
============================================
Tests every data endpoint referenced by the skills. Designed to be run:
  - By the setup script during onboarding
  - Periodically by a scheduled task
  - By an AI agent before attempting queries (via --json flag)

Usage:
  python3 scripts/health-check.py              # Human-readable output
  python3 scripts/health-check.py --json       # Machine-readable for agents
  python3 scripts/health-check.py --verbose    # Show response details
"""

import json
import sys
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone
from pathlib import Path

# All endpoints referenced across the skill hierarchy
ENDPOINTS = [
    # Tier 1: Municipal CKAN Portal
    {
        "name": "ckan_site",
        "tier": "municipal",
        "url": "https://donnees.montreal.ca/api/3/action/site_read",
        "critical": True,
        "skill": "understand-ckan",
    },
    {
        "name": "ckan_package_search",
        "tier": "municipal",
        "url": "https://donnees.montreal.ca/api/3/action/package_search?q=arbre&rows=1",
        "critical": True,
        "skill": "discover-datasets",
    },
    {
        "name": "ckan_datastore_search",
        "tier": "municipal",
        "url": "https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&limit=1",
        "critical": True,
        "skill": "query-dataset",
    },
    {
        "name": "ckan_datastore_sql",
        "tier": "municipal",
        "url": 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+COUNT(*)+as+n+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"',
        "critical": True,
        "skill": "query-dataset",
    },
    # Tier 2: Transit (multi-agency)
    {
        "name": "bixi_gbfs",
        "tier": "transit",
        "url": "https://gbfs.velobixi.com/gbfs/en/station_information.json",
        "critical": False,
        "skill": "transit",
    },
    {
        "name": "bixi_status",
        "tier": "transit",
        "url": "https://gbfs.velobixi.com/gbfs/en/station_status.json",
        "critical": False,
        "skill": "transit",
    },
    {
        "name": "stm_gtfs_static",
        "tier": "transit",
        "url": "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip",
        "critical": False,
        "skill": "transit",
        "method": "HEAD",
    },
    # Tier 3: Provincial
    {
        "name": "donnees_quebec",
        "tier": "provincial",
        "url": "https://www.donneesquebec.ca/recherche/api/3/action/site_read",
        "critical": False,
        "skill": "discover-datasets",
    },
    # Tier 4: Utilities
    {
        "name": "hydro_quebec",
        "tier": "utility",
        "url": "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/production.json",
        "critical": False,
        "skill": "environment",
        "method": "HEAD",
    },
]


def check_endpoint(ep, verbose=False):
    """Test one endpoint. Returns dict with status."""
    method = ep.get("method", "GET")
    result = {
        "name": ep["name"],
        "tier": ep["tier"],
        "critical": ep["critical"],
        "skill": ep["skill"],
        "url": ep["url"],
    }

    start = datetime.now(timezone.utc)
    try:
        req = urllib.request.Request(ep["url"], method=method)
        req.add_header("User-Agent", "MontrealOpenData-HealthCheck/1.0")
        with urllib.request.urlopen(req, timeout=20) as resp:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            result["status"] = "ok"
            result["http_code"] = resp.status
            result["latency_s"] = round(elapsed, 2)

            if method != "HEAD" and verbose:
                body = resp.read().decode("utf-8", errors="replace")[:2000]
                try:
                    data = json.loads(body)
                    if "result" in data:
                        r = data["result"]
                        if isinstance(r, dict) and "count" in r:
                            result["record_count"] = r["count"]
                        elif isinstance(r, dict) and "records" in r:
                            result["sample_fields"] = list(r["records"][0].keys()) if r["records"] else []
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

    except urllib.error.HTTPError as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result["status"] = "http_error"
        result["http_code"] = e.code
        result["error"] = str(e.reason)[:100]
        result["latency_s"] = round(elapsed, 2)
    except (urllib.error.URLError, TimeoutError) as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result["status"] = "connection_error"
        result["error"] = str(e)[:100]
        result["latency_s"] = round(elapsed, 2)
    except Exception as e:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        result["status"] = "unknown_error"
        result["error"] = str(e)[:100]
        result["latency_s"] = round(elapsed, 2)

    return result


def main():
    parser = argparse.ArgumentParser(description="Montreal Open Data Health Check")
    parser.add_argument("--json", action="store_true", help="JSON output for agents")
    parser.add_argument("--verbose", action="store_true", help="Include response details")
    parser.add_argument("--tier", help="Check only a specific tier (municipal, transit, provincial, utility)")
    args = parser.parse_args()

    endpoints = ENDPOINTS
    if args.tier:
        endpoints = [e for e in endpoints if e["tier"] == args.tier]

    results = []
    for ep in endpoints:
        r = check_endpoint(ep, verbose=args.verbose)
        results.append(r)

    if args.json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "failed": sum(1 for r in results if r["status"] != "ok"),
            "critical_failed": sum(1 for r in results if r["status"] != "ok" and r["critical"]),
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\n🏥 Montreal Open Data — Health Check")
        print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   Testing {len(endpoints)} endpoints...\n")

        current_tier = None
        for r in results:
            if r["tier"] != current_tier:
                current_tier = r["tier"]
                print(f"  [{current_tier.upper()}]")

            if r["status"] == "ok":
                latency = f"({r['latency_s']}s)"
                extra = ""
                if "record_count" in r:
                    extra = f" — {r['record_count']:,} records"
                print(f"    ✅ {r['name']:<30} {latency:>8}{extra}")
            else:
                marker = "❌" if r["critical"] else "⚠️ "
                err = r.get("error", r.get("http_code", "unknown"))
                print(f"    {marker} {r['name']:<30} {err}")

        ok = sum(1 for r in results if r["status"] == "ok")
        fail = len(results) - ok
        crit_fail = sum(1 for r in results if r["status"] != "ok" and r["critical"])

        print(f"\n  Summary: {ok}/{len(results)} OK", end="")
        if crit_fail:
            print(f" — ❌ {crit_fail} CRITICAL failures")
        elif fail:
            print(f" — ⚠️  {fail} optional endpoints down")
        else:
            print(" — all systems go 🚀")

    sys.exit(1 if any(r["status"] != "ok" and r["critical"] for r in results) else 0)


if __name__ == "__main__":
    main()
