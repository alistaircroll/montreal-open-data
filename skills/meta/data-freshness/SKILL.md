---
name: data-freshness
description: |
  Patterns for checking when Montréal open data was last updated, detecting
  stale data, and understanding update schedules across different datasets.
  / Stratégies pour vérifier la fraîcheur des données, détecter les données
  périmées et comprendre les calendriers de mise à jour.
triggers:
  - fresh, stale, updated, last update, current, outdated, when
  - frais, périmé, mise à jour, dernière, actuel, quand
---

# Data Freshness / Fraîcheur des données

## Why This Matters / Pourquoi c'est important

Not all datasets update at the same rate. Some are real-time (BIXI station status, every minute). Others are annual snapshots. An agent must know the difference to set user expectations correctly.

---

## Update Frequency by Dataset / Fréquence de mise à jour

### Real-Time (minutes)
| Dataset | Update Rate | Source |
|---------|------------|--------|
| BIXI station status | ~1 min | GBFS feed |
| STM bus positions | Multiple/min | GTFS-RT (API key required) |
| Air quality (RSQA) | ~50 min lag | DataStore |

### Daily to Weekly
| Dataset | Update Rate | Source |
|---------|------------|--------|
| 311 requests | Daily | DataStore |
| Snow removal status | During operations | Planif-Neige SOAP |
| Skating rink conditions | During season | JSON feed |
| Tree inventory | Weekly (DHP history) | DataStore |

### Monthly
| Dataset | Update Rate | Source |
|---------|------------|--------|
| Building permits | Monthly | DataStore |
| Criminal acts | Monthly | DataStore |
| Fire interventions | Monthly | DataStore |
| Road collisions | Monthly | DataStore |

### Annual or Periodic
| Dataset | Update Rate | Source |
|---------|------------|--------|
| Budget | Annual (Jan) | DataStore |
| Property assessment | Every 3 years | DataStore |
| Tree inventory (main) | Monthly field updates, periodic full refresh | DataStore |
| Building footprints | Periodic | GeoJSON download |
| BIXI trip history | Annual | CSV download |

---

## How to Check Freshness / Comment vérifier la fraîcheur

### Method 1: Dataset Metadata

```bash
# Check when a dataset was last modified
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=DATASET_SLUG' | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)['result']
print(f'Title: {d[\"title\"]}')
print(f'Metadata modified: {d[\"metadata_modified\"]}')
for r in d['resources']:
    print(f'  Resource: {r.get(\"name\",\"?\")[:50]}')
    print(f'    Last modified: {r.get(\"last_modified\", \"unknown\")}')
    print(f'    Created: {r.get(\"created\", \"unknown\")}')
"
```

### Method 2: Data Timestamps

Many datasets have date fields. Query the most recent record:

```sql
-- Most recent permit
SELECT MAX("DATE_EMISSION") as latest FROM "RESOURCE_UUID"

-- Most recent 311 request
SELECT MAX("DATE_CREATION") as latest FROM "RESOURCE_UUID"

-- Most recent tree survey
SELECT MAX("Date_Releve") as latest FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
```

### Method 3: BIXI (GBFS)

The GBFS status feed includes a `last_updated` Unix timestamp:

```python
import requests
status = requests.get('https://gbfs.velobixi.com/gbfs/en/station_status.json').json()
print(f"Last updated: {status['last_updated']}")  # Unix epoch
```

---

## Staleness Thresholds / Seuils de péremption

Use these as rules of thumb when presenting data to users:

| Dataset Type | "Fresh" if updated within | Warning after |
|---|---|---|
| Real-time feeds | 5 minutes | 30 minutes |
| Daily datasets (311, snow) | 48 hours | 1 week |
| Monthly datasets (permits, crime) | 45 days | 90 days |
| Annual datasets (budget) | 13 months | 18 months |
| Periodic (assessment, footprints) | 3 years | 5 years |

### Agent behavior when data is stale:

1. **Still fresh**: Present data normally.
2. **Approaching stale**: Present data with note: "This data was last updated on [date]."
3. **Stale**: Present data with warning: "⚠️ This data may be outdated (last updated [date]). Check the portal for updates."

---

## Seasonal Data / Données saisonnières

Some datasets are only meaningful during certain periods:

| Dataset | Active Season | Off-Season Behavior |
|---------|-------------|---------------------|
| BIXI | April–November | Stations show 0 bikes (normal, not broken) |
| Skating rinks | December–March | No condition updates |
| Ski conditions | December–March | No condition updates |
| Snow removal | November–April | No operations data |
| Pool schedules | June–September | May show off-season programming |

**Agent should know the current month** and adjust expectations accordingly. If a user asks about BIXI in January, explain it's seasonal rather than reporting "no bikes available."

---

## The `catalog-stats.json` Shortcut

After running `scripts/catalog-refresh.py`, the file `reference/catalog-stats.json` contains a timestamp of the last catalog pull. Agents can check this before making API calls:

```python
import json
from datetime import datetime, timezone
stats = json.load(open('reference/catalog-stats.json'))
age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(stats['timestamp'])).total_seconds() / 3600
if age_hours > 168:  # > 1 week
    print("Catalog cache is stale. Run catalog-refresh.py.")
```

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side freshness detection patterns |
| **Applies to** | All Montréal open data sources |
| **Last verified** | March 2026 |

---

## Related Skills / Compétences connexes

- `error-recovery` — Handle stale endpoints that return errors
- `query-dataset` — Timestamp field patterns
- `discover-datasets` — Metadata freshness checks
