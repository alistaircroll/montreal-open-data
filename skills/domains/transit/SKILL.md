---
name: transit
description: |
  Access transit data for the Montréal metropolitan area: STM bus and metro
  schedules, real-time positions, BIXI bike sharing, Exo commuter trains,
  and regional transit feeds.
  / Accéder aux données de transport de la région métropolitaine de Montréal :
  horaires STM bus et métro, positions en temps réel, vélopartage BIXI,
  trains de banlieue Exo et données de transport régional.
triggers:
  - bus, metro, subway, transit, STM, BIXI, bike, commute, train, Exo
  - autobus, métro, transport, vélo, trajet, train, banlieue
---

# Transit Data / Données de transport

## Overview / Aperçu

Montréal's transit data comes from **multiple agencies on separate platforms** — not a single portal. This skill covers all of them:

| Agency | What | Data Platform | Auth Required? |
|--------|------|--------------|----------------|
| **STM** | Bus + Metro | GTFS / GTFS-RT / Developer portal | Free registration for real-time |
| **BIXI** | Bike sharing | GBFS (REST/JSON) | None |
| **Exo** | Commuter trains + regional buses | GTFS / GTFS-RT | Request form for real-time |
| **STL** | Laval buses | GTFS | None |
| **ARTM** | Metropolitan coordination | Via member agencies | N/A |

Les données de transport de Montréal proviennent de **plusieurs agences sur des plateformes séparées**.

---

## 1. STM — Bus & Metro / Autobus et métro

### Static Schedules (GTFS)

**No auth required.** Download the static GTFS feed:

```bash
# Download current schedule (ZIP containing stops.txt, routes.txt, trips.txt, etc.)
curl -LO 'https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip'
```

**GTFS files inside the ZIP:**
- `agency.txt` — STM agency info
- `stops.txt` — All bus/metro stops with coordinates
- `routes.txt` — All bus and metro routes
- `trips.txt` — Individual trip instances
- `stop_times.txt` — Arrival/departure times at each stop
- `calendar.txt` / `calendar_dates.txt` — Service dates
- `shapes.txt` — Route geometries
- `feed_info.txt` — Feed validity dates

**Schedule change dates (2025-2026):** Jan 5, Mar 23, Jun 15, Aug 24, Oct 26. Current feed valid until ~Mar 22, 2026.

**Also on CKAN (donnees.montreal.ca):**
- Bus lines and stops as Shapefiles (MTM NAD83 Zone 8)

### Real-Time Feeds (GTFS-Realtime)

**Requires free registration** at the STM developer portal.

**Developer portal:** `https://portail.developpeurs.stm.info`
**Contact:** `dev@stm.info`
**Forum:** Open data forum available for developer questions

Once registered, you get an API key for:

| Feed | Content | Format | Update Rate |
|------|---------|--------|-------------|
| Vehicle Positions | Live GPS of all active buses | GTFS-RT (Protocol Buffers) | Multiple times/minute |
| Trip Updates | Predicted arrival times at upcoming stops | GTFS-RT (Protocol Buffers) | Multiple times/minute |
| Service Alerts | Disruptions, detours, planned changes | GTFS-RT (Protocol Buffers) | As needed |
| Occupancy (v2) | Passenger load per bus | GTFS-RT v2 | Real-time |

**GTFS-Realtime format:** These are Protocol Buffer (protobuf) feeds, not JSON. To consume them:

```python
# Python example using gtfs-realtime-bindings
# pip install gtfs-realtime-bindings requests
from google.transit import gtfs_realtime_pb2
import requests

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get(
    'https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions',
    headers={'apiKey': 'YOUR_API_KEY'}
)
feed.ParseFromString(response.content)

for entity in feed.entity:
    vehicle = entity.vehicle
    print(f"Route {vehicle.trip.route_id}: "
          f"lat={vehicle.position.latitude}, "
          f"lon={vehicle.position.longitude}")
```

**Answering "When is the next bus?":**
1. Find the stop_id from `stops.txt` (or CKAN dataset) nearest to the user's location
2. Query the Trip Updates feed for predictions at that stop
3. Fall back to the static schedule if real-time feed is unavailable

### Metro

**Metro has 4 lines and 68 stations:**
- Green (Verte): Angrignon ↔ Honoré-Beaugrand
- Orange: Côte-Vertu ↔ Montmorency
- Blue (Bleue): Snowdon ↔ Saint-Michel
- Yellow (Jaune): Berri-UQAM ↔ Longueuil

Metro schedules are included in the GTFS static feed. Real-time metro arrival predictions are available through the GTFS-RT Trip Updates feed.

---

## 2. BIXI — Bike Sharing / Vélopartage

### Station Data (GBFS — fully public)

**No auth required.** BIXI uses the General Bikeshare Feed Specification (GBFS).

**Entry point:** `https://gbfs.velobixi.com/gbfs/gbfs.json`

| Feed | URL | Content | Update Rate |
|------|-----|---------|-------------|
| System info | `/gbfs/en/system_information.json` | System name, operator, URL | Static |
| Station info | `/gbfs/en/station_information.json` | Station ID, name, lat/lon, capacity | Rarely changes |
| Station status | `/gbfs/en/station_status.json` | Available bikes, available docks, per station | ~Every minute |

**Example: Find available bikes near a location:**

```python
import requests, math

# Get all station info and status
stations = requests.get('https://gbfs.velobixi.com/gbfs/en/station_information.json').json()
status = requests.get('https://gbfs.velobixi.com/gbfs/en/station_status.json').json()

# Build status lookup
status_map = {s['station_id']: s for s in status['data']['stations']}

# User's location (example: Place des Arts)
user_lat, user_lon = 45.5081, -73.5664

# Find 5 nearest stations with bikes
def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)

results = []
for stn in stations['data']['stations']:
    st = status_map.get(stn['station_id'], {})
    bikes = st.get('num_bikes_available', 0)
    docks = st.get('num_docks_available', 0)
    dist = distance(user_lat, user_lon, stn['lat'], stn['lon'])
    results.append((dist, stn['name'], bikes, docks))

results.sort()
for dist, name, bikes, docks in results[:5]:
    print(f"{name}: {bikes} bikes, {docks} docks available")
```

**Coverage:** 8,000+ bikes, 610+ stations across Montréal, Laval, Longueuil, Westmount, Ville de Mont-Royal, Montréal-Est.

**Seasonal:** BIXI typically operates April–November. Winter data shows stations with 0 availability.

### Historical Trip Data (on CKAN)

**Dataset:** `bixi-historique-des-deplacements`
**Content:** Every trip taken — start/end station, start/end time, duration.
**Format:** CSV, updated annually.
**Use for:** Usage patterns, demand analysis, station sizing.

---

## 3. Exo — Commuter Trains & Regional Buses

### Static Schedules

**Portal:** `https://exo.quebec/en/about/open-data`

```bash
# Download Exo GTFS feed
curl -LO 'https://exo.quebec/xdata/citl/google_transit.zip'
```

**Coverage:** 6 commuter train lines (Candiac, Mascouche, Mont-Saint-Hilaire, Saint-Jérôme, Vaudreuil-Hudson, Deux-Montagnes/REM) plus regional bus networks in suburbs.

### Real-Time (Limited)

**Available for:** Commuter trains only (not buses)
**Access:** Submit request via form on Exo website
**Formats:** GTFS-Realtime + TCIP

---

## 4. STL — Société de transport de Laval

**Portal:** `https://stlaval.ca/about-us/public-information/open-data`
**Coverage:** Laval (adjacent to Montréal, connected via metro Orange line to Montmorency)
**Feeds:** GTFS static (public download)
**Real-time:** Not publicly available as of March 2026

---

## Common Questions / Questions fréquentes

### "When is the next bus at my stop?"
1. Identify the stop (by name, stop_id, or nearest to coordinates)
2. If you have a real-time API key → query GTFS-RT Trip Updates
3. If no API key → parse static GTFS `stop_times.txt` for the current service day

### "How do I get from A to B?"
This requires a trip planner, which combines GTFS from multiple agencies. Recommend users use:
- **Transit app** (transitapp.com) — uses all Montréal agencies
- **Google Maps / Apple Maps** — integrated GTFS
- **Chrono** (ARTM's app) — metropolitan scope

Building a trip planner from raw GTFS is complex (requires graph algorithms). The skill covers data access, not routing.

### "Is my bus delayed?"
Requires real-time GTFS-RT feed (STM API key needed). Compare scheduled arrival (`stop_times.txt`) with predicted arrival (Trip Updates feed).

### "How busy is BIXI station X?"
Query GBFS `station_status.json` — fully public, no auth needed. Compare `num_bikes_available` to the station's total capacity from `station_information.json`.

### "What metro lines are affected by construction?"
Query STM GTFS-RT Service Alerts feed (API key required). Or check `donnees.montreal.ca` for `stm-perturbations` dataset if available.

---

## Gotchas & Edge Cases / Pièges et cas limites

1. **GTFS-Realtime is Protocol Buffers, not JSON.** You need `gtfs-realtime-bindings` or equivalent library. Cannot be consumed with `curl` alone.

2. **STM API key is free but not instant.** Registration on the developer portal may take a business day. Plan accordingly.

3. **Exo GTFS URLs change.** The download URL pattern includes an agency code (`citl`, `citpi`, etc.) that may shift. Always start from the Exo portal page.

4. **BIXI is seasonal.** April–November typically. Winter queries will return 0 bikes everywhere.

5. **Stop IDs are agency-specific.** STM stop 51234 and Exo stop 51234 are different stops. Always include agency context.

6. **Coordinate systems:** GTFS uses WGS84 (lat/lon). The CKAN Shapefile of bus stops uses NAD 83 MTM Zone 8. Convert if mixing sources.

7. **REM (Réseau express métropolitain):** The new automated light metro has been gradually opening. Its data may appear under Exo or a separate feed. Check for updates.

---

## Provenance / Provenance

This skill spans multiple data tiers and publishers:

| Source | Publisher | Gov Level | License | Contact |
|--------|-----------|-----------|---------|---------|
| STM GTFS static | Société de transport de Montréal | Municipal (para-municipal) | Open license | dev@stm.info |
| STM GTFS-RT | Société de transport de Montréal | Municipal (para-municipal) | Developer terms | dev@stm.info |
| BIXI GBFS | BIXI Montréal (OBNL) | Municipal (delegated) | CC BY 4.0 | Via donnees.montreal.ca |
| BIXI historical | BIXI Montréal | Municipal (delegated) | CC BY 4.0 | donneesouvertes@montreal.ca |
| Exo GTFS | Exo (regional transit) | Regional (ARTM) | Open license | Via exo.quebec |
| STL GTFS | Société de transport de Laval | Municipal (Laval) | Open license | Via stlaval.ca |

**When citing transit data:** Always specify which agency provided the data. "The STM reports..." or "According to BIXI station data..." — not "The city says..."

---

## Related Skills / Compétences connexes

- `discover-datasets` — Find transit datasets on CKAN
- `borough-context` — Map stops to boroughs
- `spatial-queries` — "Nearest bus stop to my location"
- `bilingual-handling` — Station names, route names
