---
name: cross-dataset-joins
description: |
  Patterns for combining data from multiple Montréal datasets. Includes
  borough-based joins, proximity joins, temporal joins, and strategies for
  working around CKAN's single-table SQL limitation.
  / Stratégies pour combiner des données de plusieurs jeux de données :
  jointures par arrondissement, par proximité, par période, et contournement
  de la limitation SQL mono-table de CKAN.
triggers:
  - join, combine, merge, correlate, compare, cross, relationship, together
  - joindre, combiner, fusionner, corréler, comparer, relation, ensemble
---

# Cross-Dataset Joins / Jointures inter-jeux de données

## The Core Problem / Le problème fondamental

CKAN's DataStore SQL **cannot join across tables**. Each `datastore_search_sql` call queries ONE resource. To combine data, the agent must:

1. Query each dataset separately
2. Join results client-side (in Python or in the agent's reasoning)

This skill documents the **join keys** that exist across datasets, the **naming inconsistencies** to normalize, and **recipes** for the most common multi-dataset analyses.

---

## Join Keys Across Major Datasets / Clés de jointure

### Borough Name (most common join)

Every major dataset has a borough field, but they use **different field names and formats**:

| Dataset | Field Name | Example Value | Records |
|---------|-----------|---------------|---------|
| Trees | `ARROND_NOM` | `Ahuntsic - Cartierville` | 333,556 |
| Crime | `PDQ` | `12` (police district, not borough!) | 344,406 |
| Permits | `arrondissement` | `Ahuntsic-Cartierville` | 548,352 |
| 311 Requests | `ARRONDISSEMENT` | `Ahuntsic-Cartierville` | 2,768,711 |
| Fire | `NOM_ARROND` | `Ahuntsic - Cartierville` | 147,889 |
| Collisions | *(no borough field)* | — | 218,272 |

**Critical:** Borough names are NOT consistent. Trees use spaces around dashes (`Ahuntsic - Cartierville`), permits don't (`Ahuntsic-Cartierville`). Always use `LIKE '%Ahuntsic%Cartierville%'` for matching, or normalize in code.

**Crime data uses PDQ (police districts), NOT boroughs.** PDQ boundaries don't align with boroughs. You need the `limites-pdq-spvm` dataset to map between them, or use coordinate-based proximity instead.

### Coordinates (universal join)

All major datasets have latitude/longitude:

| Dataset | Lat Field | Lon Field | Coordinate System |
|---------|-----------|-----------|-------------------|
| Trees | `Latitude` | `Longitude` | WGS84 |
| Crime | `LATITUDE` | `LONGITUDE` | WGS84 |
| Permits | `latitude` | `longitude` | WGS84 |
| 311 | `LOC_LAT` | `LOC_LONG` | WGS84 |
| Fire | `LATITUDE` | `LONGITUDE` | WGS84 |
| Collisions | `LOC_LAT` | `LOC_LONG` | WGS84 |

All WGS84. Some datasets also have MTM8 (NAD83) coordinates (`Coord_X`/`Coord_Y`, `MTM8_X`/`MTM8_Y`). Always prefer WGS84 for joins.

### Date Fields (temporal join)

| Dataset | Date Field | Format |
|---------|-----------|--------|
| Trees | `Date_Releve` | `2018-06-26T00:00:00` |
| Crime | `DATE` | `2024-01-15` |
| Permits | `date_emission` | `2024-01-15` |
| 311 | `DDS_DATE_CREATION` | `2024-01-15 08:30:00` |
| Fire | `CREATION_DATE_TIME` | `2024-01-15T08:30:00` |
| Collisions | `DT_ACCDN` | `2023-01-15` |

---

## Recipe 1: Borough Comparison / Comparaison par arrondissement

**Question:** "Which borough has the most trees per capita? Per crime incident?"

**Strategy:** Query each dataset with GROUP BY borough, then join client-side.

```python
import json, urllib.request

def ckan_sql(sql):
    url = f'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql={urllib.parse.quote(sql)}'
    return json.loads(urllib.request.urlopen(url).read())['result']['records']

# Trees per borough
trees = ckan_sql('''
    SELECT "ARROND_NOM" as borough, COUNT(*) as tree_count
    FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
    GROUP BY "ARROND_NOM" ORDER BY tree_count DESC
''')

# 311 requests per borough (last 12 months)
requests_311 = ckan_sql('''
    SELECT "ARRONDISSEMENT" as borough, COUNT(*) as request_count
    FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
    WHERE "DDS_DATE_CREATION" >= '2025-03-01'
    GROUP BY "ARRONDISSEMENT" ORDER BY request_count DESC
''')

# Normalize and join
def normalize_borough(name):
    """Remove spaces around dashes, lowercase for matching."""
    if not name: return ''
    return name.replace(' - ', '-').replace(' – ', '-').strip().lower()

tree_map = {normalize_borough(t['borough']): t['tree_count'] for t in trees}
for r in requests_311:
    key = normalize_borough(r['borough'])
    r['tree_count'] = tree_map.get(key, 0)
    r['trees_per_request'] = round(r['tree_count'] / max(r['request_count'], 1), 2)
```

---

## Recipe 2: Proximity Join / Jointure par proximité

**Question:** "What crimes happened within 500m of the most trees?"

**Strategy:** Use the Haversine formula on coordinates from two datasets.

```python
import math

def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two WGS84 points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Get trees in a specific area (limit to a small bbox first!)
trees_nearby = ckan_sql('''
    SELECT "Latitude", "Longitude", "Essence_fr"
    FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
    WHERE CAST("Latitude" AS FLOAT) BETWEEN 45.51 AND 45.53
      AND CAST("Longitude" AS FLOAT) BETWEEN -73.58 AND -73.56
    LIMIT 5000
''')

# Get crimes in the same bbox
crimes_nearby = ckan_sql('''
    SELECT "CATEGORIE", "DATE", "LATITUDE", "LONGITUDE"
    FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
    WHERE CAST("LATITUDE" AS FLOAT) BETWEEN 45.51 AND 45.53
      AND CAST("LONGITUDE" AS FLOAT) BETWEEN -73.58 AND -73.56
      AND "DATE" >= '2025-01-01'
    LIMIT 5000
''')

# Count crimes within 200m of each tree
# (Agent: optimize by pre-filtering with bbox, not scanning all pairs)
```

**Performance tip:** Always pre-filter both datasets to a small bounding box using SQL `BETWEEN` before doing client-side proximity. Never download full datasets for proximity joins.

---

## Recipe 3: Temporal Pattern / Patron temporel

**Question:** "Do 311 requests increase after construction permits are issued?"

```python
# Monthly permit count by borough
permits_monthly = ckan_sql('''
    SELECT "arrondissement" as borough,
           SUBSTRING("date_emission", 1, 7) as month,
           COUNT(*) as permit_count
    FROM "5232a72d-2355-4e8c-8e1c-a3a0b4e1b867"
    WHERE "date_emission" >= '2024-01-01'
    GROUP BY "arrondissement", SUBSTRING("date_emission", 1, 7)
    ORDER BY month
''')

# Monthly 311 count by borough (same period)
requests_monthly = ckan_sql('''
    SELECT "ARRONDISSEMENT" as borough,
           SUBSTRING("DDS_DATE_CREATION", 1, 7) as month,
           COUNT(*) as request_count
    FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
    WHERE "DDS_DATE_CREATION" >= '2024-01-01'
    GROUP BY "ARRONDISSEMENT", SUBSTRING("DDS_DATE_CREATION", 1, 7)
    ORDER BY month
''')

# Agent: merge on (normalized borough, month) and compute correlation
```

---

## Recipe 4: Safety Profile / Profil de sécurité

**Question:** "Build a safety profile for Rosemont."

Combine: crime stats + fire interventions + 311 requests + road collisions for one borough.

```python
borough_like = '%Rosemont%Petite%'

crime_count = ckan_sql(f'''
    SELECT COUNT(*) as n FROM "c6f482bf-bf0f-4960-8b2f-9ca22b2d4e88"
    WHERE "DATE" >= '2025-01-01'
    AND "LATITUDE" IS NOT NULL
''')
# Note: crime uses PDQ, not borough. Use coordinate bbox for Rosemont instead.
# Rosemont approximate bbox: lat 45.53-45.56, lon -73.61--73.55

fire = ckan_sql(f'''
    SELECT "INCIDENT_TYPE_DESC", COUNT(*) as n
    FROM "71e86320-e354-4665-8de8-e97a62b23bac"
    WHERE "NOM_ARROND" LIKE '{borough_like}'
    AND "CREATION_DATE_TIME" >= '2025-01-01'
    GROUP BY "INCIDENT_TYPE_DESC" ORDER BY n DESC LIMIT 10
''')

requests = ckan_sql(f'''
    SELECT "NATURE", COUNT(*) as n
    FROM "2cfa0e06-9be7-46f1-9b3d-fee3f9174754"
    WHERE "ARRONDISSEMENT" LIKE '{borough_like}'
    AND "DDS_DATE_CREATION" >= '2025-01-01'
    GROUP BY "NATURE" ORDER BY n DESC LIMIT 10
''')
```

---

## Borough Name Normalization Function

Use this in every cross-dataset join:

```python
BOROUGH_ALIASES = {
    'ahuntsic': 'Ahuntsic-Cartierville',
    'cartierville': 'Ahuntsic-Cartierville',
    'cdnndg': 'Côte-des-Neiges–Notre-Dame-de-Grâce',
    'cdn-ndg': 'Côte-des-Neiges–Notre-Dame-de-Grâce',
    'plateau': 'Le Plateau-Mont-Royal',
    'homa': 'Mercier–Hochelaga-Maisonneuve',
    'rosemont': 'Rosemont–La Petite-Patrie',
    'villeray': 'Villeray–Saint-Michel–Parc-Extension',
    'downtown': 'Ville-Marie',
    'sud-ouest': 'Le Sud-Ouest',
}

def normalize_borough(raw):
    """Normalize borough name for cross-dataset matching."""
    if not raw:
        return None
    clean = raw.strip().replace(' - ', '-').replace(' – ', '-').replace('–', '-').lower()
    for alias, canonical in BOROUGH_ALIASES.items():
        if alias in clean:
            return canonical
    return raw.strip()
```

---

## Gotchas / Pièges

1. **No server-side joins.** Every join is two API calls + client-side merge.
2. **Borough names differ across datasets.** Always normalize.
3. **Crime uses PDQ, not boroughs.** Use coordinates or the PDQ boundary dataset.
4. **Collisions have no borough field.** Must join by coordinates only.
5. **Date formats vary.** Always parse dates, don't compare as strings.
6. **Large datasets need pre-filtering.** Use SQL WHERE with bbox or date range before downloading.
7. **32K row limit per API call.** Paginate or aggregate server-side.
8. **Numeric fields are text.** Always CAST before math operations.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side join patterns |
| **Applies to** | All DataStore-active Montréal datasets |
| **Last verified** | March 2026 |

## Related Skills / Compétences connexes

- `borough-context` — Borough name mappings and aliases
- `query-dataset` — SQL query patterns and pagination
- `error-recovery` — Handling API failures during multi-query joins
- `spatial-queries` — Coordinate-based proximity calculations
