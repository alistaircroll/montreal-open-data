---
name: understand-ckan
description: |
  Reference guide for the CKAN API powering Montréal's open data portal.
  Covers authentication, endpoints, pagination, error handling, and conventions.
  / Guide de référence pour l'API CKAN du portail de données ouvertes de Montréal.
  Couvre l'authentification, les points d'accès, la pagination, la gestion d'erreurs et les conventions.
triggers:
  - CKAN, API, endpoint, donnees.montreal.ca, open data, données ouvertes
  - API, point d'accès, données ouvertes, portail
---

# CKAN API Reference / Référence API CKAN

## Overview / Aperçu

Montréal's open data portal at `donnees.montreal.ca` runs on **CKAN** (Comprehensive Knowledge Archive Network), an open-source data management system. All data access is through CKAN's Action API v3.

**Base URL:** `https://donnees.montreal.ca/api/3/action/`

No authentication is required for read operations. All endpoints accept GET or POST.

Le portail de données ouvertes de Montréal à `donnees.montreal.ca` fonctionne sur **CKAN**. Tout l'accès aux données se fait via l'API Action v3 de CKAN.

**URL de base :** `https://donnees.montreal.ca/api/3/action/`

Aucune authentification n'est requise pour les opérations de lecture.

---

## Response Format / Format de réponse

Every CKAN API response returns JSON with this structure:

```json
{
  "help": "https://donnees.montreal.ca/api/3/action/help_show?name=...",
  "success": true,
  "result": { ... }
}
```

On error:
```json
{
  "help": "...",
  "success": false,
  "error": {
    "__type": "Not Found Error",
    "message": "Not found"
  }
}
```

**Always check `success` before accessing `result`.**

---

## Three API Layers / Trois couches d'API

### 1. Action API (Catalog Metadata)

For discovering and browsing datasets. CKAN calls datasets "packages."

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `package_list` | List all dataset IDs | `?limit=50&offset=0` |
| `package_search` | Search datasets by keyword | `?q=arbres&rows=10` |
| `package_show` | Get full metadata for one dataset | `?id=arbres` |
| `organization_list` | List publishing organizations | `?all_fields=true` |
| `group_list` | List thematic categories | `?all_fields=true` |
| `tag_list` | List all tags | (no params needed) |
| `tag_show` | Show datasets with a specific tag | `?id=Transport` |

**Search syntax for `package_search`:**
- Simple keyword: `?q=transport`
- Phrase: `?q="vélo libre-service"`
- Field-specific: `?q=title:budget`
- Organization filter: `?q=organization:ville-de-montreal`
- Tag filter: `?q=tags:Transport`
- Multiple filters: `?q=tags:Transport+organization:bixi`
- Sort: `?q=arbres&sort=metadata_modified desc`
- Facets: `?q=*:*&facet=true&facet.field=["organization","tags"]`

**Pagination:** Use `rows` (page size) and `start` (offset):
```
?q=transport&rows=20&start=0   # first 20
?q=transport&rows=20&start=20  # next 20
```

### 2. DataStore API (Tabular Data)

For querying structured data (CSV, XLSX files that CKAN has imported into its database). This is the most powerful API for data retrieval.

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `datastore_search` | Query a resource with filters | `?resource_id=ID&limit=100` |
| `datastore_search_sql` | Full SQL queries | `?sql=SELECT...` |
| `datastore_info` | Get field names and types | `?id=RESOURCE_ID` |

**`datastore_search` parameters:**
- `resource_id` (required): The resource UUID
- `limit`: Max rows to return (default 100, max 32000)
- `offset`: Skip N rows (for pagination)
- `fields`: Comma-separated list of columns to return
- `filters`: JSON object for exact-match filtering
- `q`: Full-text search across all fields
- `sort`: Field name + `asc` or `desc`
- `distinct`: `true` to return unique rows only

**Example — filtered query:**
```
https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&filters={"ARROND_NOM":"Ville-Marie"}&limit=10&fields=Essence_fr,Essence_ang,DHP,Latitude,Longitude
```

**`datastore_search_sql` — full SQL:**
```
https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT "Essence_fr", COUNT(*) as total FROM "64e28fe6-ef37-437a-972d-d1d3f1f7d891" GROUP BY "Essence_fr" ORDER BY total DESC LIMIT 10
```

**SQL rules:**
- Table name is the resource UUID in double quotes
- Column names with special chars must be double-quoted
- Standard SQL functions work: COUNT, SUM, AVG, MIN, MAX, GROUP BY, ORDER BY
- JOINs across resources are NOT supported
- Maximum result size: 32,000 rows

### 3. FileStore API (Raw File Downloads)

For downloading entire files. URL pattern:
```
https://donnees.montreal.ca/dataset/{PACKAGE_ID}/resource/{RESOURCE_ID}/download/{FILENAME}
```

Available formats vary by dataset: CSV, XLSX, GeoJSON, Shapefile (ZIP), PDF, KML, GBFS (for BIXI).

---

## Key Concepts / Concepts clés

### Dataset (Package) vs Resource

- A **dataset** (CKAN calls it a "package") is a collection of related data files with shared metadata.
- A **resource** is a single file or API endpoint within a dataset.
- One dataset can have multiple resources (e.g., CSV, GeoJSON, and PDF versions of the same data).

Un **jeu de données** (CKAN l'appelle « package ») est une collection de fichiers avec des métadonnées partagées. Une **ressource** est un fichier ou point d'accès unique au sein d'un jeu de données.

### Important Metadata Fields

From `package_show` response:
- `name`: URL-friendly slug (e.g., `arbres`)
- `title`: Human-readable title (usually in French)
- `notes`: Description (usually in French, may contain data dictionary)
- `organization.name`: Publishing org slug
- `update_frequency`: How often updated (daily, weekly, monthly, yearly)
- `territoire`: Array of borough codes (e.g., `["AHU","CDN","VIM"]`)
- `groups`: Thematic categories
- `resources[]`: Array of available files/APIs
- `metadata_modified`: Last update timestamp

From each resource:
- `id`: UUID (use this for DataStore queries)
- `format`: File format (CSV, XLSX, GeoJSON, GBFS, etc.)
- `datastore_active`: `true` if queryable via DataStore API
- `last_modified`: When file was last updated
- `name`: Human-readable resource name

### Organizations on the Portal

As of March 2026, the portal has 6 publishing organizations:

| Organization | Slug | Datasets |
|---|---|---|
| Ville de Montréal | `ville-de-montreal` | ~383 |
| Société de transport de Montréal | `societe-de-transport-de-montreal` | 7 |
| Bixi Montréal | `bixi` | 2 |
| Agence de mobilité durable | `agence-de-mobilite-durable-montreal` | 2 |
| 211 Grand Montréal | `211-grand-montreal` | 1 |
| Regroupement des éco-quartiers | `regroupement-eco-quartiers` | 2 |

**Total datasets: 436** (as of March 2026)

---

## Gotchas & Edge Cases / Pièges et cas limites

1. **CKAN says "package" not "dataset."** The API endpoint is `package_show`, not `dataset_show`.

2. **Resource IDs are UUIDs, dataset IDs are slugs.** Dataset: `arbres`. Resource: `64e28fe6-ef37-437a-972d-d1d3f1f7d891`.

3. **Not all resources are in the DataStore.** Check `datastore_active: true` before attempting DataStore queries. GeoJSON, Shapefile, PDF, and GBFS resources are NOT in the DataStore — you must download them directly.

4. **SQL column names need double-quoting.** Many field names contain accents, spaces, or mixed case. Always quote: `SELECT "Essence_fr" FROM "uuid"`.

5. **32,000 row limit.** DataStore queries return at most 32,000 rows. For larger datasets (like the 333,556 tree records), you must paginate with `offset` and `limit`.

6. **Metadata is predominantly in French.** Dataset titles, descriptions, field names, and tag names are primarily in French. Some datasets include bilingual fields (e.g., `Essence_fr` and `Essence_ang` in the tree data), but this is not universal.

7. **Coordinate systems vary.** Some datasets use NAD 83 MTM Zone 8 (e.g., `Coord_X`, `Coord_Y`), others use WGS84 (`Latitude`, `Longitude`). Check the data dictionary in the dataset's `notes` field or PDF documentation.

8. **Rate limiting.** No official rate limit is documented, but be courteous — batch queries instead of making thousands of individual calls. Add a short delay between paginated requests.

9. **The portal also federates to Données Québec** (`donneesquebec.ca`), which shares the same CKAN infrastructure. The same API patterns work there, but with different base URL and potentially more datasets.

10. **GBFS (General Bikeshare Feed Specification)** is used for BIXI data. This is NOT a CKAN format — it's a separate REST API at `https://gbfs.velobixi.com/gbfs/gbfs.json`.

---

## Quick Reference: Common Workflows / Flux de travail courants

### "I want to find a dataset about X"
```bash
curl 'https://donnees.montreal.ca/api/3/action/package_search?q=X&rows=5'
```

### "I want to see what's in a dataset"
```bash
curl 'https://donnees.montreal.ca/api/3/action/package_show?id=SLUG'
# Then check resources[] for available files and their IDs
```

### "I want to query data with filters"
```bash
curl 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=UUID&filters={"FIELD":"VALUE"}&limit=100'
```

### "I want to run a SQL query"
```bash
curl 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+*+FROM+"UUID"+LIMIT+10'
```

### "I want to download a raw file"
```bash
curl -O 'https://donnees.montreal.ca/dataset/PACKAGE_ID/resource/RESOURCE_ID/download/FILENAME.csv'
```

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | Ville de Montréal (primary); 5 partner organizations |
| **Government level** | Municipal |
| **Jurisdiction** | Montréal agglomeration (19 boroughs + 15 reconstituted municipalities) |
| **License** | CC BY 4.0 International |
| **Contact** | donneesouvertes@montreal.ca |
| **Portal** | https://donnees.montreal.ca |
| **Platform** | CKAN (Open Knowledge Foundation) |
| **Last verified** | March 2026 |

**Accountability note:** Data on this portal is published and maintained by the organizations listed. When presenting data to citizens, always cite the publishing organization. For data quality issues, contact donneesouvertes@montreal.ca.

---

## Related Skills / Compétences connexes

- `discover-datasets` — Search and browse the full catalog
- `query-dataset` — Build DataStore queries with examples
- `bilingual-handling` — Navigate French/English field names
- `error-recovery` — Handle API failures gracefully
