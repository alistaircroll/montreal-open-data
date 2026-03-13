---
name: address-geocoding
description: |
  Patterns for converting Montréal addresses to coordinates and vice versa,
  using open data sources. Includes geocoding strategies, address format
  normalization, and fallback approaches.
  / Stratégies de géocodage à Montréal : conversion d'adresses en
  coordonnées, normalisation des formats d'adresse, approches de repli.
triggers:
  - address, geocode, coordinates, location, where is, find address
  - adresse, géocodage, coordonnées, localisation, où est, trouver
---

# Address Geocoding / Géocodage d'adresses

## Strategy Overview / Vue d'ensemble

Montréal's CKAN portal does NOT have a dedicated geocoding API. Instead, use these approaches in order of preference:

1. **Reverse lookup from datasets** — Many datasets already have coordinates. Find the record by address, extract lat/lon.
2. **Nominatim (OpenStreetMap)** — Free, open geocoding API. Rate limit: 1 request/second.
3. **Dataset addresses as proxy** — Use building permits or tree inventory addresses to approximate locations.

---

## Approach 1: Extract Coordinates from Existing Data

If the user asks about a specific location and a relevant dataset has that address with coordinates:

```sql
-- Find coordinates for a street address from permits
SELECT "longitude", "latitude", "emplacement", "arrondissement"
FROM "5232a72d-2355-4e8c-8e1c-a3a0b4e1b867"
WHERE "emplacement" LIKE '%Mont-Royal%350%'
LIMIT 5

-- Find coordinates from tree inventory (has street + civic number)
SELECT "Latitude", "Longitude", "No_civique", "Rue", "ARROND_NOM"
FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
WHERE "Rue" LIKE '%Saint-Denis%'
  AND "No_civique" = '4200'
LIMIT 5
```

This is imprecise but often good enough for borough-level analysis.

---

## Approach 2: Nominatim (OpenStreetMap)

Free geocoding with good Montréal coverage. **Rate limit: 1 request per second.**

```python
import urllib.request, json, time

def geocode_nominatim(address, city="Montréal"):
    """Geocode an address using Nominatim. Respect rate limits."""
    query = urllib.parse.quote(f"{address}, {city}, QC, Canada")
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'MontrealOpenData/1.0 (research)')
    with urllib.request.urlopen(req, timeout=10) as resp:
        results = json.loads(resp.read())
    time.sleep(1)  # MANDATORY: 1 request per second
    if results:
        return float(results[0]['lat']), float(results[0]['lon'])
    return None, None

# Example
lat, lon = geocode_nominatim("3575 Parc Avenue")
# Returns: (45.5156, -73.5774)
```

```python
def reverse_geocode(lat, lon):
    """Reverse geocode coordinates to an address."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'MontrealOpenData/1.0 (research)')
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    time.sleep(1)
    return result.get('display_name', '')
```

---

## Address Format in Montréal / Format d'adresse

Montréal addresses follow Quebec conventions:

```
[civic number] [street name], [borough/city]
3575 avenue du Parc, Le Plateau-Mont-Royal
1000 rue De La Gauchetière Ouest, Ville-Marie
```

**Street type placement varies:**
- French style: `avenue du Parc` (type before name)
- English style: `Park Avenue` (type after name)
- Mixed: `rue Sherbrooke` vs `Sherbrooke Street`

**Common abbreviations in datasets:**
| Full | Abbreviation |
|------|-------------|
| avenue | av. |
| boulevard | boul. |
| rue | (often omitted) |
| chemin | ch. |
| place | pl. |
| Ouest/West | O. / W. |
| Est/East | E. |
| Nord/North | N. |
| Sud/South | S. |

---

## Borough from Address / Arrondissement à partir d'une adresse

When the user provides an address and you need the borough:

```python
# Quick approach: geocode, then find nearest borough center
import json
from pathlib import Path

boroughs = json.load(open('reference/borough-lookup.json'))

def find_borough(lat, lon):
    """Find nearest borough by center distance."""
    best = None
    best_dist = float('inf')
    for b in boroughs['boroughs']:
        dist = ((b['lat'] - lat)**2 + (b['lon'] - lon)**2)**0.5
        if dist < best_dist:
            best_dist = dist
            best = b['name']
    return best
```

**This is approximate.** Boroughs have irregular boundaries. For precise matching, download the borough boundaries GeoJSON from the portal:
- Dataset: `limites-administratives-agglomeration`
- Use `shapely` library for point-in-polygon test (requires `pip install shapely`)

---

## Coordinate Systems / Systèmes de coordonnées

| System | Usage | Fields |
|--------|-------|--------|
| WGS84 (EPSG:4326) | GPS, web maps | `Latitude`, `Longitude` |
| NAD83 MTM8 (EPSG:32188) | Quebec surveys | `Coord_X`, `Coord_Y`, `MTM8_X`, `MTM8_Y` |

**Always prefer WGS84** for cross-dataset work. Some older datasets only have MTM8. To convert:

```python
# MTM8 to WGS84 (approximate — for precise conversion use pyproj)
# This is a rough linear approximation valid for Montréal only
def mtm8_to_wgs84(x, y):
    lon = -73.0 + (x - 300000) / 111320 / 0.7193  # very approximate
    lat = y / 111320
    return lat, lon

# For precise conversion: pip install pyproj
# from pyproj import Transformer
# t = Transformer.from_crs("EPSG:32188", "EPSG:4326")
# lat, lon = t.transform(x, y)
```

---

## Gotchas / Pièges

1. **No official municipal geocoder.** The city doesn't expose a geocoding API.
2. **Nominatim rate limit.** 1 request/second. Batch geocoding needs patience.
3. **Street names are in French.** Search for "rue Saint-Denis", not "Saint Denis Street".
4. **Accents matter.** "Côte-des-Neiges" ≠ "Cote-des-Neiges" in some contexts.
5. **Civic numbers can be ranges.** Some datasets use "3575-3577" format.
6. **Intersections.** Datasets may store locations as intersections: "Saint-Laurent / Sainte-Catherine".
7. **MTM8 coordinates.** If lat/lon are missing but `Coord_X`/`Coord_Y` exist, they're NAD83 MTM8.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Geocoding source** | Nominatim (OpenStreetMap) — ODbL license |
| **Address data** | Montréal CKAN portal — CC BY 4.0 |
| **Last verified** | March 2026 |

## Related Skills / Compétences connexes

- `spatial-queries` — Proximity and bounding box calculations
- `borough-context` — Borough lookup from coordinates
- `cross-dataset-joins` — Joining datasets by coordinates
