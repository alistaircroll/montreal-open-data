---
name: spatial-queries
description: |
  Patterns for location-based queries: "near me", "within X km",
  bounding boxes, and proximity calculations across Montréal datasets.
  All coordinates are WGS84 unless noted.
  / Stratégies pour requêtes spatiales : « près de moi », « dans un rayon
  de X km », boîtes englobantes et calculs de proximité.
triggers:
  - near, nearby, within, radius, distance, closest, km, meters, around
  - près, proche, dans un rayon, distance, plus proche, km, mètres, autour
---

# Spatial Queries / Requêtes spatiales

## The SQL Proximity Pattern / Patron de proximité SQL

CKAN DataStore doesn't have PostGIS, so you can't use `ST_DWithin`. Instead, use a **bounding box filter in SQL** followed by **Haversine client-side**.

### Step 1: Bounding Box (server-side, fast)

Convert "within X km" to a lat/lon bounding box:

```python
def bbox(lat, lon, radius_km):
    """Approximate bounding box for a radius around a point."""
    # 1 degree latitude ≈ 111.32 km
    # 1 degree longitude ≈ 111.32 * cos(lat) km at Montreal's latitude
    import math
    dlat = radius_km / 111.32
    dlon = radius_km / (111.32 * math.cos(math.radians(lat)))
    return {
        'lat_min': lat - dlat,
        'lat_max': lat + dlat,
        'lon_min': lon - dlon,
        'lon_max': lon + dlon,
    }

# Example: 2km around Mile End (45.524, -73.596)
b = bbox(45.524, -73.596, 2.0)
# → lat: 45.506 to 45.542, lon: -73.622 to -73.570
```

### Step 2: SQL with Bounding Box

```sql
SELECT "Essence_fr", "DHP", "Latitude", "Longitude"
FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
WHERE CAST("Latitude" AS FLOAT) BETWEEN 45.506 AND 45.542
  AND CAST("Longitude" AS FLOAT) BETWEEN -73.622 AND -73.570
LIMIT 5000
```

### Step 3: Haversine Filter (client-side, precise)

```python
import math

def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in meters between two WGS84 points."""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Filter bbox results to exact radius
center_lat, center_lon, radius_m = 45.524, -73.596, 2000
results = [
    r for r in bbox_results
    if haversine_m(center_lat, center_lon,
                   float(r['Latitude']), float(r['Longitude'])) <= radius_m
]
```

---

## Common Spatial Queries / Requêtes spatiales courantes

### "Trees near me" / "Arbres près de moi"

```python
b = bbox(user_lat, user_lon, 0.5)  # 500m radius
trees = ckan_sql(f'''
    SELECT "Essence_fr", "Essence_ang", "DHP",
           "Latitude", "Longitude", "ARROND_NOM"
    FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
    WHERE CAST("Latitude" AS FLOAT) BETWEEN {b['lat_min']} AND {b['lat_max']}
      AND CAST("Longitude" AS FLOAT) BETWEEN {b['lon_min']} AND {b['lon_max']}
    LIMIT 5000
''')
```

### "Crime near this address" / "Criminalité près de cette adresse"

```python
# First geocode the address (see address-geocoding skill)
addr_lat, addr_lon = geocode_nominatim("3575 Parc Avenue")
b = bbox(addr_lat, addr_lon, 1.0)  # 1km radius

crimes = ckan_sql(f'''
    SELECT "CATEGORIE", "DATE", "QUART", "LATITUDE", "LONGITUDE"
    FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
    WHERE CAST("LATITUDE" AS FLOAT) BETWEEN {b['lat_min']} AND {b['lat_max']}
      AND CAST("LONGITUDE" AS FLOAT) BETWEEN {b['lon_min']} AND {b['lon_max']}
      AND "DATE" >= '2025-01-01'
    LIMIT 5000
''')
```

### "Nearest BIXI station" / "Station BIXI la plus proche"

```python
import requests

stations = requests.get('https://gbfs.velobixi.com/gbfs/en/station_information.json').json()
status = requests.get('https://gbfs.velobixi.com/gbfs/en/station_status.json').json()

# Build lookup for bike availability
avail = {s['station_id']: s['num_bikes_available']
         for s in status['data']['stations']}

# Find nearest with bikes
nearest = sorted(
    stations['data']['stations'],
    key=lambda s: haversine_m(user_lat, user_lon, s['lat'], s['lon'])
)

for s in nearest[:5]:
    dist = haversine_m(user_lat, user_lon, s['lat'], s['lon'])
    bikes = avail.get(s['station_id'], 0)
    print(f"  {s['name']}: {dist:.0f}m away, {bikes} bikes")
```

### "Fire stations within 3km" / "Casernes dans un rayon de 3 km"

```python
b = bbox(user_lat, user_lon, 3.0)
casernes = ckan_sql(f'''
    SELECT * FROM "RESOURCE_UUID_FOR_CASERNES"
    WHERE CAST("LATITUDE" AS FLOAT) BETWEEN {b['lat_min']} AND {b['lat_max']}
      AND CAST("LONGITUDE" AS FLOAT) BETWEEN {b['lon_min']} AND {b['lon_max']}
''')
```

---

## Montréal Geographic Constants / Constantes géographiques

| Reference | Latitude | Longitude |
|-----------|----------|-----------|
| City Hall (Hôtel de Ville) | 45.5088 | -73.5538 |
| Mont-Royal summit | 45.5048 | -73.5874 |
| Olympic Stadium | 45.5579 | -73.5516 |
| Pierre-Elliott-Trudeau Airport | 45.4706 | -73.7408 |
| Old Port (Vieux-Port) | 45.5033 | -73.5540 |
| Jean-Talon Market | 45.5365 | -73.6148 |
| McGill University | 45.5048 | -73.5772 |

**Island bounds (approximate):**
- North: 45.71
- South: 45.40
- West: -73.99
- East: -73.47

---

## Performance Tips / Conseils de performance

1. **Always use bbox first.** The CAST + BETWEEN filter happens server-side, reducing data transfer.
2. **Set reasonable LIMIT.** A 500m radius in downtown has thousands of trees. Limit to 1000-5000.
3. **Avoid full-table scans.** Never download all 333,556 trees to find nearby ones.
4. **Cache BIXI data.** Station locations rarely change. Cache `station_information.json` for a session.
5. **Pre-compute for common areas.** Borough centers from `borough-lookup.json` avoid geocoding.

---

## Gotchas / Pièges

1. **CAST is required.** Lat/lon fields are stored as text. `WHERE "Latitude" > 45.5` won't work without CAST.
2. **Some records have null coordinates.** Always add `AND "Latitude" IS NOT NULL`.
3. **Bounding box is a square, not a circle.** Corner results may be > radius. Filter client-side.
4. **MTM8 coordinates.** If only `Coord_X`/`Coord_Y` exist, convert to WGS84 first.
5. **BIXI is seasonal.** April to November only. Stations exist but show 0 bikes in winter.
6. **Crime coordinates are approximate.** Deliberately offset for privacy. Don't treat as exact.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side spatial query patterns |
| **Applies to** | All geolocated Montréal datasets |
| **Last verified** | March 2026 |

## Related Skills / Compétences connexes

- `address-geocoding` — Convert addresses to coordinates
- `borough-context` — Borough lookup by name or coordinate
- `cross-dataset-joins` — Proximity joins across datasets
- `transit` — BIXI station proximity queries
