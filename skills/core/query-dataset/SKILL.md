---
name: query-dataset
description: |
  Query tabular data from Montréal's open data using the CKAN DataStore API.
  Supports filtered searches, SQL queries, aggregation, and pagination.
  / Interroger les données tabulaires de Montréal via l'API DataStore de CKAN.
  Supporte les recherches filtrées, requêtes SQL, agrégation et pagination.
triggers:
  - query, search records, filter data, SQL, datastore, count, aggregate
  - requête, chercher enregistrements, filtrer données, compter, agréger
---

# Query Datasets / Interroger les jeux de données

## Prerequisites / Prérequis

Before querying, you need a **resource ID** (UUID). Get it from `package_show`:

```bash
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=DATASET_SLUG' | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)['result']
for r in d['resources']:
    active = '✓ DataStore' if r.get('datastore_active') else '✗ Download only'
    print(f'{r[\"id\"]} | {r.get(\"format\",\"?\")} | {active} | {r.get(\"name\",\"\")[:60]}')
"
```

**Only resources with `datastore_active: true` can be queried via DataStore.** Others must be downloaded directly.

---

## Method 1: Simple Filtered Query / Requête filtrée simple

**Endpoint:** `https://donnees.montreal.ca/api/3/action/datastore_search`

### Basic query
```bash
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=RESOURCE_UUID&limit=10'
```

### With filters (exact match)
```bash
# Trees in Ville-Marie borough
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&filters={"ARROND_NOM":"Ville-Marie"}&limit=10'
```

### Select specific fields
```bash
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&fields=Essence_fr,Essence_ang,DHP,Latitude,Longitude&limit=10'
```

### Full-text search across all fields
```bash
# Find trees with "Érable" (maple) anywhere
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&q=Érable&limit=10'
```

### Sort results
```bash
# Trees sorted by diameter (largest first)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&sort=DHP desc&limit=10'
```

### Pagination
```bash
# Page 1 (rows 0-99)
curl -s '...&limit=100&offset=0'
# Page 2 (rows 100-199)
curl -s '...&limit=100&offset=100'
```

The response includes `"total"` which tells you the total number of matching records.

### All parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `resource_id` | string (required) | UUID of the resource |
| `limit` | int | Max rows to return (default 100, max 32000) |
| `offset` | int | Number of rows to skip |
| `fields` | string | Comma-separated list of column names to return |
| `filters` | JSON | Exact-match filters: `{"FIELD":"VALUE"}` |
| `q` | string | Full-text search across all fields |
| `sort` | string | Field name + `asc` or `desc` |
| `distinct` | bool | `true` to return unique rows |
| `include_total` | bool | `true` (default) to include total count |

---

## Method 2: SQL Query / Requête SQL

**Endpoint:** `https://donnees.montreal.ca/api/3/action/datastore_search_sql`

For anything beyond simple filtering — aggregation, complex WHERE clauses, date ranges, LIKE patterns.

### Count records
```sql
SELECT COUNT(*) FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
```

### Group by with count
```sql
SELECT "ARROND_NOM", COUNT(*) as total
FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
GROUP BY "ARROND_NOM"
ORDER BY total DESC
```

### Filter with LIKE (pattern matching)
```sql
SELECT "Essence_fr", "Essence_ang", "DHP"
FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
WHERE "Essence_fr" LIKE '%Érable%'
LIMIT 20
```

### Date range queries
```sql
SELECT *
FROM "RESOURCE_UUID"
WHERE "Date_Plantation" >= '2020-01-01'
  AND "Date_Plantation" < '2021-01-01'
LIMIT 100
```

### Aggregate functions
```sql
SELECT
  "ARROND_NOM",
  COUNT(*) as tree_count,
  AVG(CAST("DHP" AS FLOAT)) as avg_diameter,
  MAX(CAST("DHP" AS FLOAT)) as max_diameter
FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891"
GROUP BY "ARROND_NOM"
ORDER BY tree_count DESC
```

### URL encoding for curl
```bash
# URL-encode the SQL query
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"ARROND_NOM",+COUNT(*)+as+total+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"+GROUP+BY+"ARROND_NOM"+ORDER+BY+total+DESC'
```

Or use POST with JSON body:
```bash
curl -s -X POST 'https://donnees.montreal.ca/api/3/action/datastore_search_sql' \
  -H 'Content-Type: application/json' \
  -d '{"sql": "SELECT \"ARROND_NOM\", COUNT(*) as total FROM \"64e28fe6-ef37-437a-972d-d1d3f1f7d891\" GROUP BY \"ARROND_NOM\" ORDER BY total DESC"}'
```

### SQL rules and limits

1. **Table name = resource UUID in double quotes:** `FROM "64e28fe6-..."`
2. **Column names with accents/spaces must be double-quoted:** `SELECT "Essence_fr"`
3. **String values in single quotes:** `WHERE "ARROND_NOM" = 'Ville-Marie'`
4. **No JOINs across resources** — each query hits one resource only
5. **Max 32,000 rows** per query result
6. **CAST for numeric operations** — some numeric fields are stored as text: `CAST("DHP" AS FLOAT)`
7. **Date format:** `'YYYY-MM-DD'` or `'YYYY-MM-DDTHH:MM:SS'`
8. **NULL handling:** Use `IS NULL` / `IS NOT NULL`

---

## Method 3: Direct Download / Téléchargement direct

For non-DataStore resources (GeoJSON, Shapefile, PDF, GBFS):

```bash
# Get the download URL from package_show
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=SLUG' | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)['result']
for r in d['resources']:
    print(f'{r.get(\"format\",\"?\")} | {r[\"url\"][:120]}')
"
```

Then download:
```bash
curl -O 'URL_FROM_ABOVE'
```

---

## Recipes: Common Query Patterns / Recettes : Requêtes courantes

### Count total records in a dataset
```python
import requests
url = 'https://donnees.montreal.ca/api/3/action/datastore_search'
r = requests.get(url, params={'resource_id': 'UUID', 'limit': 0})
print(r.json()['result']['total'])
```

### Get all unique values in a column
```sql
SELECT DISTINCT "COLUMN_NAME" FROM "RESOURCE_UUID" ORDER BY "COLUMN_NAME"
```

### Find records near a location (if lat/lon available)
```sql
SELECT *,
  (("Latitude" - 45.5017)^2 + ("Longitude" - (-73.5673))^2) as dist_sq
FROM "RESOURCE_UUID"
WHERE "Latitude" IS NOT NULL
ORDER BY dist_sq ASC
LIMIT 10
```
Note: This is approximate Euclidean distance, not geodesic. Adequate for city-scale proximity queries.

### Paginate through entire dataset
```python
import requests

resource_id = 'UUID'
offset = 0
limit = 5000
all_records = []

while True:
    r = requests.get('https://donnees.montreal.ca/api/3/action/datastore_search',
                      params={'resource_id': resource_id, 'limit': limit, 'offset': offset})
    data = r.json()['result']
    records = data['records']
    all_records.extend(records)
    if len(records) < limit:
        break
    offset += limit

print(f'Retrieved {len(all_records)} records')
```

---

## Response Structure / Structure de la réponse

### datastore_search response
```json
{
  "success": true,
  "result": {
    "resource_id": "64e28fe6-...",
    "fields": [
      {"id": "_id", "type": "int"},
      {"id": "Essence_fr", "type": "text"},
      {"id": "DHP", "type": "text"}
    ],
    "records": [
      {"_id": 1, "Essence_fr": "Févier Skyline", "DHP": "25"},
      ...
    ],
    "total": 333556,
    "_links": {
      "start": "/api/3/action/datastore_search?...",
      "next": "/api/3/action/datastore_search?...&offset=100"
    }
  }
}
```

### datastore_search_sql response
```json
{
  "success": true,
  "result": {
    "records": [...],
    "fields": [...]
  }
}
```
Note: SQL responses do NOT include `total` — you must use `COUNT(*)` if you need it.

---

## Gotchas / Pièges

1. **Numeric fields stored as text.** Many datasets store numbers as strings. Use `CAST("field" AS FLOAT)` or `CAST("field" AS INTEGER)` in SQL.
2. **Empty strings vs NULL.** Some fields use `""` instead of `null` for missing data.
3. **Encoding.** All data is UTF-8. French accents (é, è, ê, ô, etc.) work natively.
4. **Large datasets.** The tree inventory has 333,556 records. Always use `limit` to avoid overwhelming responses.
5. **Date formats vary.** Some use `2024-01-15`, others `2024-01-15T00:00:00`. Be flexible in parsing.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | Ville de Montréal + partner organizations |
| **Government level** | Municipal |
| **Jurisdiction** | Montréal agglomeration |
| **License** | CC BY 4.0 International |
| **Contact** | donneesouvertes@montreal.ca |
| **Portal** | https://donnees.montreal.ca |
| **Last verified** | March 2026 |

**Data accuracy:** The city publishes data as-is. Update frequencies vary by dataset (daily to yearly). Always check `metadata_modified` and `update_frequency` before presenting data as current. When citing results to citizens, include the dataset name and last-modified date.

---

## Related Skills / Compétences connexes

- `understand-ckan` — Full API reference and conventions
- `discover-datasets` — Find the right dataset first
- `bilingual-handling` — Decode French field names
- `cross-dataset-joins` — Combine data from multiple datasets
