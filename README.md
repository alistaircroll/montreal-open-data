# Données ouvertes de Montréal pour agents IA

Une hiérarchie de compétences composable qui donne aux agents IA un accès natif aux 397 jeux de données et 918 ressources interrogeables de Montréal.

## Montréal Open Data for AI Agents

A composable skill hierarchy that gives AI agents native access to Montréal's 397 open datasets and 918 queryable resources — trees, transit, permits, crime, budget, and more.

---

## Quick Start / Démarrage rapide

### Installation

**Claude Code:**
```bash
/plugin marketplace add montrealdata/montreal-open-data
```

**Manual (n'importe quel agent):**
```bash
git clone https://github.com/montrealdata/montreal-open-data
python3 scripts/setup.py     # Verify connectivity + configure API keys
python3 scripts/catalog-refresh.py  # Generate local reference files
```

### First Query / Première requête

Once installed, ask your agent naturally:

> "How many trees are there in the Plateau?"
> "Combien d'arbres y a-t-il dans le Plateau?"
> "Show me building permits in my neighborhood this month."
> "Quels crimes ont été signalés près de chez moi?"

The agent uses the skills to find the right dataset, build the API call, and present results in your language.

---

## What's Inside / Contenu

### 15 competences parmi 5 catégories / 15 Skills across 5 categories

**Core** (4 skills) — Works for any CKAN portal:
- `understand-ckan` — API reference (endpoints, pagination, conventions)
- `discover-datasets` — Catalog search (397 datasets, keyword → slug)
- `query-dataset` — DataStore SQL queries (filters, aggregation, pagination)
- `download-resource` — File downloads (CSV, GeoJSON, Shapefile, GBFS, GTFS)

**Domains** (7 skills) — Montréal-specific dataset expertise:
- `transit` — STM bus/metro, BIXI bike-sharing, Exo commuter trains
- `environment` — 333,556 trees, air quality, green spaces, canopy
- `permits-and-planning` — Building permits, zoning, property assessment
- `safety` — Crime, 311 requests, fire interventions, road collisions
- `budget-and-finance` — Operating budget, contracts, subsidies, tax rates
- `culture-and-recreation` — Parks, sports, murals, skating rinks
- `infrastructure` — Roads, snow removal, garbage, Planif-Neige SOAP API

**Geographic** (1 skill):
- `borough-context` — 19 boroughs + 15 municipalities, name aliases, coordinates

**Meta** (3 skills):
- `bilingual-handling` — French/English navigation (all metadata is French)
- `error-recovery` — API failure diagnosis and recovery patterns
- `data-freshness` — Update schedules, staleness detection

### 4 Scripts

| Script | Purpose |
|--------|---------|
| `scripts/setup.py` | Onboarding wizard: health check + API key config |
| `scripts/health-check.py` | Validate all 9 data endpoints |
| `scripts/catalog-refresh.py` | Pull fresh catalog → reference JSON files |
| `scripts/field-inspector.py` | Discover actual field names for any dataset |

### 5 Reference Files (generated)

| File | Content |
|------|---------|
| `reference/dataset-catalog.json` | All 397 datasets with metadata |
| `reference/endpoint-registry.json` | All 918 DataStore resource UUIDs |
| `reference/borough-lookup.json` | Borough codes, names, aliases, coordinates |
| `reference/org-summary.json` | Datasets grouped by organization |
| `reference/catalog-stats.json` | Catalog refresh timestamp + summary |

---

## Architecture / Architecture

```
montreal-open-data/
├── skills/
│   ├── core/           ← Load first. Works for any CKAN portal.
│   ├── domains/        ← Load by topic. Montréal-specific expertise.
│   ├── geo/            ← Load for location queries.
│   ├── meta/           ← Load for language, errors, freshness.
│   └── analysis/       ← (Coming soon) Cross-dataset reasoning.
├── reference/          ← Machine-readable JSON for fast lookups.
├── scripts/            ← Automation (setup, health, catalog, inspect).
├── plugin.json         ← Plugin manifest for Claude Code.
├── SETUP.md            ← Human + agent readable onboarding guide.
└── .gitignore
```

These skills are delivered as a set of composable SKILL.md files that agents load on demand.

---

## Data Sources / Sources de données

**Primary:** City of Montréal's open data portal
- Portal: [donnees.montreal.ca](https://donnees.montreal.ca/en)
- API: CKAN Action API v3
- License: CC BY 4.0
- 397 datasets from 6 organizations

### MCP Server (9 tools)

For agents that support the Model Context Protocol:
```bash
claude mcp add montreal-data python3 mcp/read-server/server.py
```

Tools: `search_datasets`, `query_dataset`, `get_dataset_fields`, `get_borough_info`,
`find_nearby`, `bixi_stations`, `dataset_stats`, `list_datasets_by_topic`, `health_check`

See `mcp/read-server/README.md` for configuration with Claude Desktop, Cursor, and other clients.

---

**Also covered:**
- BIXI bike-sharing (GBFS — public, no auth)
- STM bus/metro schedules (GTFS static — public) and real-time (GTFS-RT — free registration)
- Exo commuter trains (GTFS — public)
- Planif-Neige snow removal (SOAP API — public)
- Données Québec provincial portal (CKAN — public)

---

## Roadmap / Feuille de route

- [x] Phase 1: Core skills (CKAN, discovery, query, bilingual)
- [x] Phase 2: Domain skills (transit, environment, permits, safety, budget, culture, infrastructure)
- [x] Phase 3: Scripts + reference data (catalog, health check, field inspector, borough lookup)
- [x] Phase 4: Analysis skills (cross-dataset joins, time series, visualization)
- [x] Phase 5: MCP server — 9 tools for deterministic data access (search, SQL, spatial, BIXI, boroughs)
- [ ] Phase 6: Citizen-agent delegation (authenticated municipal actions)

---

## Contributing / Contribuer

We welcome contributions! / Les contributions sont les bienvenues!

1. Fork this repo
2. Add or improve a SKILL.md file
3. Test against the live API: `python3 scripts/health-check.py`
4. Submit a pull request

See `SETUP.md` for the skill format specification and architecture guide.

---

## License / Licence

CC BY 4.0, matching the City of Montréal's open data license.

*Built with care for the city I love. / Construit avec soin pour la ville que j'adore.*
