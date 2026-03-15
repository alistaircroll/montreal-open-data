---
name: Montreal Infrastructure Data
description: |
  Access and query Montreal's infrastructure datasets including snow removal status, garbage collection schedules, road closures, parking regulations, property assessment, nearby amenities, and street signage. Provides real-time data via REST API, SOAP API for snow removal, Overpass QL for amenities, and external APIs for utility outages.

description_fr: |
  Accédez aux données d'infrastructure de Montréal, notamment l'état du déneigement, les horaires de collecte des ordures, les fermetures de routes, les réglementations de stationnement, l'évaluation foncière, les commodités de proximité et la signalisation routière. Fournit des données en temps réel via l'API REST, l'API SOAP pour le déneigement, Overpass QL pour les commodités et des API externes pour les pannes de services publics.

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
  - property assessment
  - évaluation foncière
  - tax valuation
  - taxes municipales
  - nearby amenities
  - commodités
  - power outage
  - panne électricité
---

## Overview | Aperçu

This skill provides access to Montreal's infrastructure datasets from the **CKAN Open Data Portal** (`donnees.montreal.ca`), specialized real-time APIs for snow removal, OpenStreetMap Overpass for nearby amenities, and external utility APIs. Infrastructure data covers waste collection, snow removal progress, road closures, property assessment, parking regulations, nearby civic amenities, utility outages, and signage.

## Available Datasets | Datasets Disponibles

| Dataset | Slug | Type | Update Frequency | Description |
|---------|------|------|------------------|-------------|
| Garbage Collection Sectors | `info-collectes` | GeoJSON/CSV | Monthly | Residential garbage and recycling collection zones by borough |
| Snow Removal Status | `deneigement` | GeoJSON | Real-time (via API) | Current and planned snow removal operations by street/sector |
| Free Parking (Snow Removal) | `stationnements-deneigement` | DataStore API | Seasonal | Temporary free parking locations during snow removal periods |
| Snow Removal Contracts | `contrats-transaction-deneigement` | DataStore API | Annual | Approved contractors and transaction history for snow removal |
| Property Assessment (Taxes) | `taxes-municipales` | DataStore API | Annual | Property valuations by borough — one resource ID per borough |
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

### DataStore Query Helper

All DataStore queries use two patterns — parameterized search and direct SQL:

```python
# Parameterized search (simple filters)
import requests, json

CKAN_BASE = "https://donnees.montreal.ca/api/3/action"

def datastore_search(resource_id, filters=None, fields=None, limit=100, offset=0):
    params = {"resource_id": resource_id, "limit": limit, "offset": offset}
    if filters:
        params["filters"] = json.dumps(filters)
    if fields:
        params["fields"] = ",".join(fields)
    resp = requests.get(f"{CKAN_BASE}/datastore_search", params=params, timeout=20)
    if resp.status_code == 409:  # Resource incomplete or missing
        return {"records": [], "total": 0}
    resp.raise_for_status()
    return resp.json()["result"]

# Direct SQL (complex queries with WHERE, ORDER BY, aggregation)
def datastore_sql(sql):
    resp = requests.get(f"{CKAN_BASE}/datastore_search_sql",
                        params={"sql": sql}, timeout=30)
    if resp.status_code == 409:
        return {"records": [], "total": 0}
    resp.raise_for_status()
    return resp.json()["result"]
```

**SQL escaping:** Always escape single quotes in user-provided values:
```python
def escape_sql(value):
    return value.replace("'", "''")
```

### Resource Show
```
GET /resource_show?id=<resource_id>
```
Get direct access to GeoJSON, CSV, or other formats.

## Real-Time Planif-Neige SOAP API | API SOAP

**Important:** This API uses SOAP/XML protocol, not REST. It is a city-operated service providing real-time snow removal data.

**WSDL Endpoint:** `https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService?WSDL`

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

### SOAP Response Structure

**Critical:** The response has nested structure and can return a single object OR an array:

```
GetPlanificationsForDateResult
  └── Planification  ← may be a single object OR an array of objects
        ├── NomArr       (borough name, e.g., "Le Plateau-Mont-Royal")
        ├── Etat         (status: "2" or "3" = active operation)
        ├── DateDebut    (start date/time)
        ├── DateFin      (end date/time, if known)
        └── ... other fields
```

Always normalize to an array before processing:
```python
planifications = result.get("Planification", [])
if not isinstance(planifications, list):
    planifications = [planifications]
```

**Status codes:** `Etat == "2"` or `Etat == "3"` indicates active snow removal. Other values mean planned or completed.

**Seasonal guard:** Snow removal only operates October–March. Check the month before making API calls — summer queries return empty or stale data.

### SOAP Examples

**Python (zeep library):**
```python
from zeep import Client

wsdl = 'https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService?WSDL'
client = Client(wsdl=wsdl)

# Get today's operations
result = client.service.GetPlanificationsForDate('2026-03-13')

# Check if a specific borough has active operations
planifs = result.Planification
if not isinstance(planifs, list):
    planifs = [planifs] if planifs else []

active = [p for p in planifs if p.NomArr == "Le Plateau-Mont-Royal" and p.Etat in ("2", "3")]
```

**Node.js (soap package):**
```javascript
const soap = require("soap");

const WSDL = "https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService?wsdl";

async function getSnowStatus(borough) {
  const client = await soap.createClientAsync(WSDL);
  const today = new Date().toISOString().split("T")[0];
  const [result] = await client.GetPlanificationsForDateAsync({ date: today });

  const inner = result?.GetPlanificationsForDateResult;
  const planifs = inner?.Planification ?? [];
  const arr = Array.isArray(planifs) ? planifs : [planifs];

  return arr.find(p => p.NomArr === borough && (p.Etat === "2" || p.Etat === "3")) ?? null;
}
```

**Note:** The `soap` package is Node-only (not browser-compatible). In frameworks that bundle for both server and client (such as Next.js, Nuxt), use dynamic imports or isolate the SOAP call to a server-side API route.

## Common Queries | Requêtes Courantes

### 1. Snow Removal Status Today
```bash
curl "https://servicesenligne2.ville.montreal.qc.ca/api/infoneige/InfoneigeWebService" \
  -H "Content-Type: application/soap+xml" \
  -d '<soap request XML>'
```
Or use the Python zeep / Node.js soap examples above.

### 2. Garbage Collection Schedule

Dataset `info-collectes` (package ID: `2df0fa28-7a7b-46c6-912f-93b215bd201e`) has 12 resources — 6 GeoJSON + 6 SHP. **These are download-only (not DataStore queryable)**. Use direct download URLs:

| Type | Resource ID | Filename |
|------|-------------|----------|
| Ordures ménagères | `5f3fb372-64e8-45f2-a406-f1614930305c` | `collecte-des-ordures-menageres.geojson` |
| Recyclage | `d02dac7d-a114-4113-8e52-266001447591` | `collecte-des-matieres-recyclables.geojson` |
| Résidus alimentaires | `61e8c7e6-9bf1-45d9-8ebe-d7c0d50cfdbb` | `collecte-des-residus-alimentaires.geojson` |
| Matières organiques | `06ec4987-47c9-4f05-a1ae-e164a96699c7` | `collecte-des-matieres-organiques.geojson` |
| Résidus verts | `d0882022-c74d-4fe2-813d-1aa37f6427c9` | `collecte-des-residus-verts-incluant-feuilles-mortes.geojson` |
| Encombrants/CRD | `2345d55a-5325-488c-b4fc-a885fae458e2` | `collecte-des-residus-de-construction-de-renovation-et-de-demolition-crd-et-encombrants.geojson` |

**Download URL pattern:**
```
https://donnees.montreal.ca/dataset/2df0fa28-7a7b-46c6-912f-93b215bd201e/resource/{RESOURCE_ID}/download/{FILENAME}
```

**IMPORTANT:** `resource_show` does NOT work for these resources. Use direct download.

#### Determining collection day for an address (Point-in-Polygon)

The GeoJSON files define geographic zones. To find which collection day applies to a given address, perform a **point-in-polygon** lookup:

```python
import json
from shapely.geometry import shape, Point

# Load the GeoJSON
with open("collecte-des-ordures-menageres.geojson") as f:
    data = json.load(f)

# CRITICAL: GeoJSON uses [longitude, latitude] order, NOT [lat, lng]
user_point = Point(-73.58, 45.53)  # [lng, lat]

for feature in data["features"]:
    polygon = shape(feature["geometry"])
    if polygon.contains(user_point):
        print(feature["properties"]["MESSAGE_FR"])
        print(feature["properties"]["MESSAGE_EN"])
        break
```

**JavaScript equivalent** (with Turf.js):
```javascript
const booleanPointInPolygon = require("@turf/boolean-point-in-polygon").default;
const { point } = require("@turf/helpers");

// CRITICAL: [lng, lat] order for GeoJSON
const pt = point([-73.58, 45.53]);

for (const feature of geojson.features) {
  try {
    if (booleanPointInPolygon(pt, feature.geometry)) {
      console.log(feature.properties.MESSAGE_FR);
      break;
    }
  } catch (e) {
    // Skip malformed geometry
  }
}
```

#### Extracting the day name from schedule messages

The `MESSAGE_FR`/`MESSAGE_EN` properties contain the schedule day embedded in free text. The format varies and has no separator — e.g., `"Jour de collecte :  MercrediHeures de dépôt..."` (no space before "Heures").

Extract the day name with explicit matching — do NOT use `\w+`:

```python
import re

DAYS_FR = "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
DAYS_EN = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"

def extract_day(message, locale="fr"):
    days = DAYS_FR if locale == "fr" else DAYS_EN
    # Match "Jour de collecte: Mercredi" or "Collection day(s): Wednesday"
    m = re.search(rf"(?:Jour de collecte|Collection day(?:\(s\))?)[\s:]*({days})s?", message, re.I)
    if m:
        return m.group(1).capitalize()
    # Fallback: match any standalone day name
    m = re.search(rf"\b({days})s?\b", message, re.I)
    return m.group(1).capitalize() if m else None
```

### 3. Current Road Closures (Entraves)

Dataset slug: `entraves` (not `entrave`). Resource ID: `cc41b532-f12d-40fb-9f55-eb58c9a2b12b`. **DataStore queryable.**

**Actual field names** (NOT what old documentation says):
```
_id, id, permit_permit_id, contractnumber, boroughid, permitcategory,
currentstatus, duration_start_date, duration_end_date, reason_category,
occupancy_name, submittercategory, organizationname, longitude, latitude
```

**WARNING:** Old docs reference `id_request`, `streetid`, `short_description` — these fields DO NOT EXIST. Use `occupancy_name` for street location, `reason_category` for type, `organizationname` for responsible org.

Filter by borough: `filters={"boroughid":"Le Plateau-Mont-Royal"}` (uses full borough name string, not numeric ID).

```bash
curl "https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=cc41b532-f12d-40fb-9f55-eb58c9a2b12b&filters={\"boroughid\":\"Le Plateau-Mont-Royal\"}&limit=5"
```

### 4. Property Assessment (Tax Valuation) | Évaluation Foncière

Each borough has its own DataStore resource for property tax data. You must look up the correct resource ID for the borough before querying.

**Borough → Tax Resource ID mapping:**

| Borough | Resource ID |
|---------|-------------|
| Ahuntsic-Cartierville | `da06242e-86c7-4e97-baf2-4a13dc33ebc0` |
| Anjou | `ecfa4615-abe1-4690-88e1-ac1fbc684050` |
| Côte-des-Neiges-Notre-Dame-de-Grâce | `8819693b-870a-4288-bb09-f7eb20a6f095` |
| Lachine | `be7e2fe0-3bab-4926-b57d-2f3c3bbb4907` |
| LaSalle | `d09a68c2-95dc-4a7b-9da3-b74b19e9ad2a` |
| Le Plateau-Mont-Royal | `d7383f9d-1676-4e78-96de-a0c9392d4737` |
| Le Sud-Ouest | `faf7bf64-42ce-4dca-aeb3-c11eeede1029` |
| L'Île-Bizard-Sainte-Geneviève | `09bccbad-8b32-4166-b8ee-b8bdd7a844fa` |
| Mercier-Hochelaga-Maisonneuve | `85c58a3b-e38f-4476-8e3a-c69dfc2bb4c9` |
| Montréal-Nord | `dd5b8faf-e279-4cae-87a3-cf93c0854c10` |
| Outremont | `60def2b9-cdd3-4a72-8db9-23e3b08a2a79` |
| Pierrefonds-Roxboro | `a11f8f56-4a31-4ef2-9a0e-cd26c8f0d7ee` |
| Rivière-des-Prairies-Pointe-aux-Trembles | `ded14f87-64b9-4c96-b271-f27455154254` |
| Rosemont-La Petite-Patrie | `25a404c9-f875-4bbb-8e0d-0fa72ca8a5eb` |
| Saint-Laurent | `92b8aa64-e3d7-4609-8543-d1b34e345a35` |
| Saint-Léonard | `5e786fd8-4855-4c74-b635-5c6a5f1e1ddf` |
| Verdun | `10dac7e8-4aa3-4f8c-895d-aee3aa0c1b54` |
| Ville-Marie | `6c0e8ad9-fc77-4e8c-a3df-3c1a09a1f7c8` |
| Villeray-Saint-Michel-Parc-Extension | `f8ec02d5-06e6-405b-acfe-54e40e0b1c83` |

**Key fields:**
- `VAL_IMPOSABLE` — assessed property value (text, parse as float)
- `ANNEE_EXERCICE` — tax year
- `AD_EMPLAC_CIV1` — civic number (exact match)
- `AD_EMPLAC_RUE` — street name (use LIKE for partial matching)
- `CODE_DESCR_LONGUE` — `'B00'` = residential property

**Query pattern:**
```python
resource_id = "d7383f9d-1676-4e78-96de-a0c9392d4737"  # Le Plateau-Mont-Royal
civic_num = "4335"
street = escape_sql("GARNIER")

sql = f'''SELECT "VAL_IMPOSABLE", "ANNEE_EXERCICE", "NO_COMPTE"
  FROM "{resource_id}"
  WHERE "AD_EMPLAC_CIV1" = '{civic_num}'
    AND UPPER("AD_EMPLAC_RUE") LIKE '%{street}%'
    AND "CODE_DESCR_LONGUE" = 'B00'
  ORDER BY "ANNEE_EXERCICE" DESC LIMIT 2'''

result = datastore_sql(sql)
# First record = current year, second = prior year → compute delta
```

**Year-over-year change:**
```python
if len(result["records"]) >= 2:
    current = float(result["records"][0]["VAL_IMPOSABLE"])
    previous = float(result["records"][1]["VAL_IMPOSABLE"])
    delta_pct = ((current - previous) / previous) * 100
```

### 5. Nearby Amenities via Overpass QL | Commodités de Proximité

OpenStreetMap's Overpass API provides real-time amenity data within a radius. This is the best source for civic amenities (libraries, pools, arenas, community centres, CLSCs, parks, metro stations, bus stops).

**Overpass query template:**
```
[out:json][timeout:10];
(
  node["amenity"="library"](around:{radius},{lat},{lng});
  node["amenity"="community_centre"](around:{radius},{lat},{lng});
  node["leisure"="swimming_pool"](around:{radius},{lat},{lng});
  node["leisure"="ice_rink"](around:{radius},{lat},{lng});
  node["leisure"="park"](around:{radius},{lat},{lng});
  way["leisure"="park"](around:{radius},{lat},{lng});
  node["amenity"="clinic"]["healthcare"="clsc"](around:{radius},{lat},{lng});
  node["highway"="bus_stop"](around:{radius},{lat},{lng});
  node["railway"="station"]["network"="STM"](around:{radius},{lat},{lng});
);
out center 100;
```

**Coordinate gotcha for ways:** Nodes return `el.lat`/`el.lon` directly. Ways (such as parks) return `el.center.lat`/`el.center.lon` instead (because `out center` computes the centroid).

```python
import requests

def fetch_nearby_amenities(lat, lng, radius_m=800):
    query = f"""[out:json][timeout:10];
    (
      node["amenity"="library"](around:{radius_m},{lat},{lng});
      node["leisure"="park"](around:{radius_m},{lat},{lng});
      way["leisure"="park"](around:{radius_m},{lat},{lng});
      node["highway"="bus_stop"](around:{radius_m},{lat},{lng});
      node["railway"="station"]["network"="STM"](around:{radius_m},{lat},{lng});
    );
    out center 100;"""

    resp = requests.post("https://overpass-api.de/api/interpreter",
                         data={"data": query}, timeout=15)
    resp.raise_for_status()

    amenities = []
    for el in resp.json().get("elements", []):
        # Ways use center coordinates
        el_lat = el.get("lat") or el.get("center", {}).get("lat")
        el_lng = el.get("lon") or el.get("center", {}).get("lon")
        if not el_lat or not el_lng:
            continue

        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:fr") or ""

        # Classify by tags
        if tags.get("railway") in ("station", "stop"):
            amenity_type = "metro"
        elif tags.get("highway") == "bus_stop":
            amenity_type = "bus_stop"
        elif tags.get("leisure") == "park":
            amenity_type = "park"
        elif tags.get("amenity") == "library":
            amenity_type = "library"
        else:
            continue

        amenities.append({"type": amenity_type, "name": name, "lat": el_lat, "lng": el_lng})

    return amenities
```

**Combining with BIXI stations:** BIXI data comes from GBFS, not Overpass. Merge results from both:
```python
# After fetching Overpass amenities, add BIXI stations within same radius
bixi_info = requests.get("https://gbfs.velobixi.com/gbfs/en/station_information.json").json()
for station in bixi_info["data"]["stations"]:
    if haversine_km(lat, lng, station["lat"], station["lon"]) <= radius_m / 1000:
        amenities.append({
            "type": "bixi", "name": station["name"],
            "lat": station["lat"], "lng": station["lon"]
        })
```

**Cache strategy:** Overpass data changes slowly — cache for 1 hour. BIXI availability changes rapidly — don't cache (or cache for 60 seconds max).

### 6. Bike Path Inventory
```bash
curl "https://donnees.montreal.ca/api/3/action/package_show?id=pistes-cyclables"
```

### 7. Street Signage by Borough
```bash
curl "https://donnees.montreal.ca/api/3/action/resource_show?id=<resource_id>" \
  | jq '.geometry[] | select(.properties.ARRONDISSEMENT=="<borough_name>")'
```

## External Real-Time APIs | APIs Externes en Temps Réel

### Hydro-Québec Power Outages | Pannes Hydro-Québec

**Endpoint:** `https://pannes.hydroquebec.com/pannes/donnees/v3_0/bismarkers.json`

**No authentication required.** Returns current power outage markers across Québec.

**Response structure is flexible** — the response may be `{"markers": [...]}` OR a bare array at the root. Always handle both:

```python
import requests

def fetch_hydro_outages(lat, lng, radius_km=1.0):
    resp = requests.get(
        "https://pannes.hydroquebec.com/pannes/donnees/v3_0/bismarkers.json",
        timeout=10
    )
    if not resp.ok:
        return []

    data = resp.json()
    markers = data.get("markers", data) if isinstance(data, dict) else data

    outages = []
    for m in markers:
        dist = haversine_km(lat, lng, m["lat"], m["lng"])
        if dist <= radius_km:
            outages.append({
                "customers": m.get("nbClients", 0),
                "cause": m.get("cause", {}).get("fr", ""),  # Nested: cause.fr
                "start": m.get("dateDebPanne", ""),
                "estimated_end": m.get("dateFinPrevue", ""),
                "distance_km": dist,
            })
    return outages
```

**Key fields:**
- `nbClients` — number of affected customers
- `cause.fr` — cause description in French (nested object with language keys)
- `dateDebPanne` — outage start time
- `dateFinPrevue` — estimated restoration time
- `lat`, `lng` — outage coordinates

### Internet Outage Monitoring

Two complementary sources for detecting internet outages in the Montréal region:

**IODA (Internet Outage Detection & Analysis):**
- API: `https://api.ioda.inetintel.cc.gatech.edu/v2/signals/raw/region/CA-QC`
- Provides ISP-level outage signals for the province of Québec
- Useful for detecting large-scale connectivity issues

**Cloudflare Radar:**
- API: `https://api.cloudflare.com/client/v4/radar/http/timeseries`
- Requires Cloudflare API token
- Provides per-ASN traffic anomaly detection

Both APIs return time-series data. Significant drops from baseline indicate outages.

## Spatial Query Patterns | Requêtes Spatiales

### Text-Based Bounding Box (When CAST() Is Forbidden)

CKAN returns `403 "Not authorized to call function CAST"` on large datasets. For spatial filtering, use **text comparison** on coordinate fields instead.

**Critical gotcha for negative longitudes:** Text sort order is **reversed** for negative numbers. `"-73.585"` is text-greater-than `"-73.575"`, which is the opposite of numeric ordering. You must **swap the min/max bounds** for longitude:

```python
radius_km = 0.3
delta = radius_km / 111  # ~0.003 degrees per 0.3 km

lat_min = f"{lat - delta:.6f}"
lat_max = f"{lat + delta:.6f}"

# For NEGATIVE longitudes: swap min/max for text comparison
lng_text_low  = f"{lng + delta:.6f}"   # Less negative = text-smaller
lng_text_high = f"{lng - delta:.6f}"   # More negative = text-larger

sql = f'''SELECT "Latitude", "Longitude", "Essence_fr"
  FROM "{resource_id}"
  WHERE "Latitude" >= '{lat_min}' AND "Latitude" <= '{lat_max}'
    AND "Longitude" >= '{lng_text_low}' AND "Longitude" <= '{lng_text_high}'
  LIMIT 200'''
```

**This pattern works for any CKAN dataset with text coordinate fields.** After the bounding box filter, refine with Haversine distance calculation client-side (see `geo/spatial-queries` skill).

### Degrees-to-Kilometers Conversion

For rough bounding boxes around Montréal (latitude ~45.5°):
- 1° latitude ≈ 111 km
- 1° longitude ≈ 78 km (at 45.5° latitude)
- Quick approximation: `delta_degrees = radius_km / 111`

## Common Questions | Questions Fréquentes

- **Where is snow removal happening right now?** → Use Planif-Neige SOAP API `GetPlanificationsForDate` with today's date; filter by `NomArr` and `Etat in ("2", "3")`
- **What's my garbage collection day?** → Download the GeoJSON for your collection type, perform point-in-polygon with your coordinates (remember `[lng, lat]` order), extract day from `MESSAGE_FR`/`MESSAGE_EN`
- **What's my property worth?** → Look up your borough's tax resource ID, query with civic number + street name, compare current vs prior year `VAL_IMPOSABLE`
- **Are there street closures on my route?** → Query `entraves` resource by `boroughid` filter
- **Where can I park for free during snow removal?** → Query `stationnements-deneigement` DataStore
- **What amenities are near me?** → Overpass QL for civic amenities + BIXI GBFS for bike stations
- **Is there a power outage near me?** → Hydro-Québec outage markers API filtered by distance
- **What are the bike paths in my area?** → Filter `pistes-cyclables` by coordinates/borough
- **Which contractor is handling snow removal on my street?** → Query `contrats-transaction-deneigement`

## Gotchas & Limitations | Points d'Attention

### API & Protocol
1. **SOAP API is unusual** — Planif-Neige uses SOAP/XML instead of REST. Requires XML parsing (not JSON). Use `zeep` (Python) or `soap` (Node.js), not `requests`/`fetch`.
2. **SOAP response may be single object or array** — Always normalize `Planification` to a list before iterating. A single scheduled operation returns an object, not a one-element array.
3. **Snow removal is seasonal** — Data is only meaningful Oct–Apr. Summer queries return stale or empty results. Guard with a month check before calling.
4. **Collection GeoJSON resources are download-only** — `resource_show` fails for `info-collectes`. Use direct download URLs with the dataset package ID.
5. **409 Conflict on incomplete resources** — Some resources return HTTP 409 instead of data. Handle gracefully by returning empty results, not raising errors.
6. **Hydro-Québec response structure varies** — May be `{"markers": [...]}` or bare array. Check `isinstance(data, dict)` and use `.get("markers", data)`.

### Field Names & Data Types
7. **CKAN field names are case-sensitive** — Trees: `Essence_fr`, `Latitude` (title case). Entraves: `boroughid`, `occupancy_name` (lowercase). 311: `DDS_DATE_CREATION`. Always verify with `datastore_search?limit=1`.
8. **Entraves field names changed** — Old docs reference `id_request`, `streetid`, `short_description`. Current fields: `occupancy_name`, `reason_category`, `organizationname`.
9. **Elected officials have field name variants** — Resource `211f6903-1440-438a-9f6c-9718ecf2d3ee` may use `Prenom` or `Prénom`, `Fonction elective` or `Fonction`. Check for both and fall back.
10. **All DataStore values are text** — Parse coordinates, amounts, and counts as numbers explicitly. Use `float()` / `parseFloat()`, not direct arithmetic.

### Spatial & Geographic
11. **CAST() is forbidden** — CKAN returns 403 on large datasets. Use text comparison for bounding boxes (see Spatial Query Patterns above).
12. **Negative longitude text sort is reversed** — `"-73.585" > "-73.575"` in text ordering (opposite of numeric). Swap min/max bounds in SQL WHERE clauses.
13. **GeoJSON uses [lng, lat] order** — Point-in-polygon libraries (Turf.js, Shapely) expect `[longitude, latitude]`. Passing `[lat, lng]` silently matches the wrong zone or no zone at all.
14. **Overpass ways return center coordinates** — Nodes use `el.lat`/`el.lon`, but ways (parks, buildings) use `el.center.lat`/`el.center.lon` when queried with `out center`.

### Collection Schedule
15. **Schedule text has no separator** — `MESSAGE_FR` contains `"Jour de collecte :  MercrediHeures de dépôt..."` (no space before "Heures"). Use explicit day-name regex, not generic word matching.
16. **Ordinal patterns exist** — Some schedules say `"2e et 4e lundis du mois"` (2nd and 4th Mondays). Parse these separately from simple day names.

### Infrastructure
17. **BIXI GBFS uses v1 URL** — `https://gbfs.velobixi.com/gbfs/en/` (NOT `/gbfs/2/en/` which returns 404). Merge `station_information.json` + `station_status.json` by `station_id`. Check `is_renting` to exclude closed stations. Coordinate field: `lon` (not `lng`).
18. **Signage data is incomplete** — Missing for Île-Bizard–Sainte-Geneviève. Some boroughs have sparse coverage.
19. **Borough names must be exact in CKAN filters** — `"Le Plateau-Mont-Royal"` works; `"Plateau"` or `"le plateau-mont-royal"` does not. Use the `geo/borough-context` skill for canonical names and aliases.
20. **Property tax has one resource per borough** — There is no city-wide tax resource. Look up the borough first, then use the corresponding resource ID from the mapping table.

## Data Provenance | Provenance des Données

| Dataset | Authority | License | Updated |
|---------|-----------|---------|---------|
| `info-collectes` | Arrondissements | CC-BY 4.0 | Monthly |
| `deneigement` | Service des Travaux Publics | CC-BY 4.0 | Real-time (Nov–Apr) |
| `taxes-municipales` | Service des Finances | CC-BY 4.0 | Annual (January) |
| `entrave` | Service de Mobilité | CC-BY 4.0 | Daily |
| `signalisation-routiere` | Arrondissements (via SIGNALEC system) | CC-BY 4.0 | Quarterly |
| Planif-Neige SOAP API | Service des Travaux Publics | Proprietary | Real-time |
| Hydro-Québec Outages | Hydro-Québec | Public feed | Real-time |
| Overpass / OpenStreetMap | OSM Community | ODbL | Continuous |

All CKAN datasets are licensed under **Creative Commons Attribution 4.0 International (CC-BY 4.0)**.

## Related Skills | Compétences Connexes

- **`geo/spatial-queries`** — Haversine formula, radius search, bounding box patterns
- **`geo/address-geocoding`** — Nominatim geocoding, coordinate conversion
- **`geo/borough-context`** — Borough names, codes, aliases, canonical lookups
- **`core/query-dataset`** — DataStore SQL, field discovery, pagination
- **`core/download-resource`** — GeoJSON/CSV file downloads (for collection schedules)
- **`domains/transit`** — STM bus/metro, BIXI details, Exo commuter rail
- **`domains/safety`** — Crime, 311 requests, fire/police data
- **`domains/permits-and-planning`** — Construction permits, zoning
- **`meta/error-recovery`** — 403, 409, timeout handling patterns
- **`meta/bilingual-handling`** — French/English field mapping, output formatting

---

*Last Updated: 2026-03-15 | CKAN Portal: https://donnees.montreal.ca*
