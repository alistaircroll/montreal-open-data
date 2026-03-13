---
name: Montreal Infrastructure Data
description: |
  Access and query Montreal's infrastructure datasets including snow removal status, garbage collection schedules, road closures, parking regulations, and street signage information. Provides real-time data via REST API and specialized SOAP API for snow removal operations.

description_fr: |
  Accédez aux données d'infrastructure de Montréal, notamment l'état du déneigement, les horaires de collecte des ordures, les fermetures de routes, les réglementations de stationnement et les informations de signalisation routière. Fournit des données en temps réel via l'API REST et l'API SOAP spécialisée pour les opérations de déneigement.

triggers:
  - snow removal
  - déneigement
  - garbage collection
  - collecte
  - road closure
  - obstruction de route
  - parking regulations
  - stationnement
  - street infrastructure
  - infrastructure routière
  - signage
  - signalisation
  - sidewalk
  - trottoir
  - bike paths
  - pistes cyclables
---

## Overview | Aperçu

This skill provides access to Montreal's infrastructure datasets from the **CKAN Open Data Portal** (`donnees.montreal.ca`) and specialized real-time APIs for snow removal operations. Infrastructure data covers waste collection, snow removal progress, road closures, parking regulations, and signage.

## Available Datasets | Datasets Disponibles

| Dataset | Slug | Type | Update Frequency | Description |
|---------|------|------|------------------|-------------|
| Garbage Collection Sectors | `info-collectes` | GeoJSON/CSV | Monthly | Residential garbage and recycling collection zones by borough |
| Snow Removal Status | `deneigement` | GeoJSON | Real-time (via API) | Current and planned snow removal operations by street/sector |
| Free Parking (Snow Removal) | `stationnements-deneigement` | DataStore API | Seasonal | Temporary free parking locations during snow removal periods |
| Snow Removal Contracts | `contrats-transaction-deneigement` | DataStore API | Annual | Approved contractors and transaction history for snow removal |
| Road Network | `reseau-routier` | GeoJSON | Updated regularly | Complete road inventory with classifications |
| Sidewalks | `trottoirs` | GeoJSON | Updated regularly | Pedestrian sidewalk network |
| Bike Paths | `pistes-cyclables` | GeoJSON | Updated regularly | Cycling infrastructure network |
| Road Closures/Obstructions | `entrave` | GeoJSON/CSV | Real-time | Active construction work and street closures |
| Water/Sewer Infrastructure | `reseau-eau-egouts` | GeoJSON | Updated regularly | Water and sanitation network infrastructure |
| Street Signage | `signalisation-routiere` | GeoJSON | Updated regularly | Traffic signs, regulatory signs, and warning signs across the city |

## CKAN REST API | API REST CKAN

**Base URL:** `https://donnees.montreal.ca/api/3/action/`

### Package Search
```
GET /package_search?q=<query>&rows=<n>
```
Search for datasets by keyword. Example:
```
https://donnees.montreal.ca/api/3/action/package_search?q=deneigement&rows=10
```

### Package Show
```
GET /package_show?id=<slug>
```
Retrieve full dataset metadata and resource URLs:
```
https://donnees.montreal.ca/api/3/action/package_show?id=deneigement
```

### Resource Show
```
GET /resource_show?id=<resource_id>
```
Get direct access to GeoJSON, CSV, or other formats.

## Real-Time Planif-Neige (Info-Neige) SOAP API | API SOAP

**Important:** This API uses SOAP/XML protocol, not REST.

**WSDL Endpoint:** `https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService?WSDL`

This is the official real-time API for snow removal operations. It provides minute-by-minute updates on which streets are currently being serviced.

### Available Operations

#### GetPlanificationsForDate
Retrieve all snow removal planifications scheduled for a specific date.

**Parameters:**
- `pDate` (string, ISO format): Target date (e.g., `2026-03-13`)

**Returns:** List of scheduled operations with street segments and estimated times.

#### GetPlanificationInfosForDate
Get detailed status information for all snow removal operations on a given date.

**Parameters:**
- `pDate` (string, ISO format): Target date

**Returns:** Operation status, current location, progress percentage, and street names.

### SOAP Example (Python with zeep library)
```python
from zeep import Client

wsdl = 'https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService?WSDL'
client = Client(wsdl=wsdl)

# Get today's operations
result = client.service.GetPlanificationsForDate('2026-03-13')

# Get operation details
details = client.service.GetPlanificationInfosForDate('2026-03-13')
```

**Note:** SOAP responses are XML. Parse with standard XML libraries (ElementTree, lxml, etc.).

## Common Queries | Requêtes Courantes

### 1. Snow Removal Status Today
```bash
curl "https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService" \
  -H "Content-Type: application/soap+xml" \
  -d '<soap request XML>'
```
Or use Python zeep client to call `GetPlanificationInfosForDate` with today's date.

### 2. Garbage Collection Schedule
```bash
curl "https://donnees.montreal.ca/api/3/action/package_show?id=info-collectes" \
  | jq '.result.resources[] | select(.format=="GeoJSON")'
```

### 3. Current Road Closures
```bash
curl "https://donnees.montreal.ca/api/3/action/package_show?id=entrave" \
  | jq '.result.resources[0].url'
```
Then download the GeoJSON and filter for active closures with current date.

### 4. Bike Path Inventory
```bash
curl "https://donnees.montreal.ca/api/3/action/package_show?id=pistes-cyclables"
```

### 5. Street Signage by Borough
```bash
curl "https://donnees.montreal.ca/api/3/action/resource_show?id=<resource_id>" \
  | jq '.geometry[] | select(.properties.ARRONDISSEMENT=="<borough_name>")'
```

## Common Questions | Questions Fréquentes

- **Where is snow removal happening right now?** → Use Planif-Neige SOAP API `GetPlanificationInfosForDate`
- **What's my garbage collection day?** → Query `info-collectes` dataset with your address/sector
- **Are there street closures on my route?** → Check `entrave` dataset for active obstructions
- **Where can I park for free during snow removal?** → Query `stationnements-deneigement` DataStore
- **What are the bike paths in my area?** → Filter `pistes-cyclables` by coordinates/borough
- **Which contractor is handling snow removal on my street?** → Query `contrats-transaction-deneigement`

## Gotchas & Limitations | Points d'Attention

1. **SOAP API is unusual** — Planif-Neige uses SOAP/XML instead of REST. Requires XML parsing. Not JSON.
2. **Snow removal is seasonal** — Data is only updated Nov–Apr. Summer queries return minimal results.
3. **Collection schedules vary by sector** — Garbage collection is not city-wide uniform. Always validate against your sector code.
4. **DataStore APIs require special endpoint** — `stationnements-deneigement` and `contrats-transaction-deneigement` use CKAN DataStore, not standard package endpoints.
5. **Signage data is incomplete** — Notably missing for Île-Bizard–Sainte-Geneviève borough. Some arrondissements have sparse coverage.
6. **Real-time SOAP responses are large** — Planif-Neige returns full XML documents. Filter aggressively by date or street.
7. **GeoJSON coordinates are lat/lon** — Ensure your mapping library handles WGS84 (EPSG:4326) correctly.

## Data Provenance | Provenance des Données

| Dataset | Authority | License | Updated |
|---------|-----------|---------|---------|
| `info-collectes` | Arrondissements | CC-BY 4.0 | Monthly |
| `deneigement` | Service des Travaux Publics | CC-BY 4.0 | Real-time (Nov–Apr) |
| `entrave` | Service de Mobilité | CC-BY 4.0 | Daily |
| `signalisation-routiere` | Arrondissements (via SIGNALEC system) | CC-BY 4.0 | Quarterly |
| Planif-Neige SOAP API | Service des Travaux Publics | Proprietary | Real-time |

All CKAN datasets are licensed under **Creative Commons Attribution 4.0 International (CC-BY 4.0)**.

## Related Skills | Compétences Connexes

- **Transit & Mobility** — Bus routes, transit schedules, bike-sharing stations
- **Permits & Regulations** — Construction permits, zoning information
- **Geographic Data** — Borough boundaries, neighborhood clusters
- **Emergency Services** — Police stations, fire stations, hospital locations

---

*Last Updated: 2026-03-13 | CKAN Portal: https://donnees.montreal.ca*
