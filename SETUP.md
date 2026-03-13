---
name: montreal-open-data-setup
description: |
  Onboarding instructions for the Montreal Open Data skill system.
  Read by both humans and AI agents during installation.
triggers:
  - setup, install, configure, onboard, getting started
  - installation, configuration, démarrage
---

# Setup / Installation

## For Humans / Pour les humains

### Step 1: Install the plugin

**Claude Code:**
```bash
git clone https://github.com/alistaircroll/montreal-open-data.git
cd montreal-open-data
python3 -m venv .venv && source .venv/bin/activate && pip install mcp
claude mcp add --transport stdio montreal-data --scope project -- "$(pwd)/.venv/bin/python3" "$(pwd)/mcp/read-server/server.py"
ln -s "$(pwd)/skills" ~/.claude/skills/montreal-open-data
```

**Other agents:** Clone this repo and point your agent at the `skills/` directory.

### Step 2: Run the setup script

```bash
python3 scripts/setup.py
```

This will:
- Test connectivity to all Montreal data endpoints
- Optionally configure API keys (e.g., STM real-time — free registration)
- Save a `config.local.json` for the agent to read

### Step 3: Refresh the catalog (optional but recommended)

```bash
python3 scripts/catalog-refresh.py
```

Generates local JSON files in `reference/` so the agent can find datasets without API calls.

### That's it.

Ask your agent: "How many trees are in the Plateau?" or "Combien d'arbres dans le Plateau?"

---

## For AI Agents / Pour les agents IA

If you are an AI agent reading this, here is what you need to know:

### Architecture

```
skills/
├── core/              ← Load these first. They work for any CKAN portal.
│   ├── understand-ckan/     API reference (endpoints, pagination, response format)
│   ├── discover-datasets/   Catalog search (keyword → dataset slug)
│   ├── query-dataset/       DataStore queries (SQL, filters, aggregation)
│   └── download-resource/   File downloads (CSV, GeoJSON, GBFS, GTFS)
├── domains/           ← Load the relevant domain when the user asks about a topic.
│   ├── transit/             STM, BIXI, Exo, STL
│   ├── environment/         Trees, air quality, green spaces
│   ├── permits-and-planning/  Building permits, zoning, property assessment
│   ├── safety/              Crime, 311 requests, fire, police, collisions
│   ├── budget-and-finance/  Budget, contracts, subsidies, tax rates
│   ├── culture-and-recreation/  Parks, sports, murals, skating rinks
│   └── infrastructure/      Roads, snow removal, garbage, water/sewer
├── geo/               ← Load for any location-based query.
│   └── borough-context/     19 boroughs + 15 municipalities, name mappings
├── meta/              ← Load when you encounter problems or need context.
│   ├── bilingual-handling/  French/English navigation patterns
│   ├── error-recovery/      API failure recovery patterns
│   └── data-freshness/      Update schedules, staleness detection
├── analysis/          ← (Coming soon) Cross-dataset analysis patterns
reference/             ← Machine-readable JSON for fast lookups
scripts/               ← Automation tools
```

### Loading Strategy

1. **Always load first:** `bilingual-handling` (you need it for every query)
2. **Load on demand:** Domain skills based on user's question topic
3. **Load on error:** `error-recovery` when an API call fails
4. **Load for location:** `borough-context` when user mentions a neighborhood

### Language Handling

- **Detect** user language from their message. Do not ask.
- **Search** the CKAN API in French (all metadata is French).
- **Present** results in the user's language.
- **Borough names** are proper nouns — keep them as-is in both languages.

### Authentication Tiers

| Tier | Examples | What to do |
|------|----------|------------|
| **Public** | CKAN API, BIXI GBFS, GTFS static | Just call it. No auth needed. |
| **Free registration** | STM real-time (GTFS-RT) | Check `config.local.json` for API key. If absent, tell user to register at the portal and run `setup.py`. |
| **Request-based** | Exo real-time | Tell user to submit request on Exo website. Offer static GTFS fallback. |
| **Not available** | Municipal court records | Tell user this data is not digitally accessible. |

**Never** attempt to register for API keys on the user's behalf.
**Never** use browser automation for authentication.
**Always** offer the public fallback when premium access is unavailable.

### Scripts Available

| Script | Purpose | When to run |
|--------|---------|-------------|
| `scripts/setup.py --json` | Check endpoint health + config | Before first query, or on errors |
| `scripts/health-check.py --json` | Test all endpoints | When API calls fail |
| `scripts/catalog-refresh.py --json` | Stats about the catalog | Periodically, or when looking for new datasets |
| `scripts/field-inspector.py <slug_or_uuid> --json` | Discover actual field names | When a query returns unexpected results |

### Reference Files

| File | Content | Usage |
|------|---------|-------|
| `reference/dataset-catalog.json` | All 397 datasets with metadata | Fast dataset lookup without API call |
| `reference/endpoint-registry.json` | All 918 DataStore resource UUIDs | Find queryable resources |
| `reference/borough-lookup.json` | Borough codes, names, aliases, coordinates | Resolve user location references |
| `reference/org-summary.json` | Datasets grouped by organization | Understand data publishers |
| `reference/catalog-stats.json` | Catalog refresh timestamp + summary stats | Check if reference data is stale |

### The Golden Rule

**Always use the DataStore SQL API when possible.** It's faster, more precise, and doesn't require downloading entire files. Save file downloads for formats that aren't in DataStore (GeoJSON, Shapefile, GBFS, GTFS).

```
https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=YOUR_SQL_HERE
```

---

## Troubleshooting / Dépannage

| Problem | Solution |
|---------|----------|
| "Resource not found" (404) | Resource UUID changed. Run `catalog-refresh.py` or use `package_show` to get current IDs. |
| "Bad request" (400) | SQL syntax error or wrong field name. Run `field-inspector.py` on the resource. |
| Empty results | Check field name case (case-sensitive), borough name format, date format. |
| Garbled characters | Ensure UTF-8 decoding. Some CSVs use UTF-8-BOM. |
| BIXI returns 0 bikes | It's winter (April-November only). This is normal. |
| STM real-time fails | API key missing or expired. Check `config.local.json`. |

---

## File: config.local.json

This file is created by `setup.py` and should NOT be committed to version control.

```json
{
  "language": "en",
  "api_keys": {
    "stm_realtime": "YOUR_KEY_HERE"
  },
  "endpoints": { ... },
  "last_setup": "2026-03-13T01:50:00+00:00",
  "last_health_check": "2026-03-13T01:50:00+00:00"
}
```

Add `config.local.json` to your `.gitignore`.
