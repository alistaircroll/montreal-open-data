---
name: download-resource
description: |
  Download raw files (CSV, GeoJSON, Shapefile, PDF, GBFS) from Montréal's
  open data portal. Handles non-DataStore resources that require direct download.
  / Télécharger des fichiers bruts (CSV, GeoJSON, Shapefile, PDF, GBFS) du
  portail de données ouvertes de Montréal.
triggers:
  - download, file, GeoJSON, shapefile, CSV, export, raw data
  - télécharger, fichier, exporter, données brutes
---

# Download Resources / Télécharger des ressources

## When to Download vs Query / Quand télécharger vs interroger

| Scenario | Use DataStore API | Download File |
|----------|:-:|:-:|
| Tabular data with filters | ✓ | |
| SQL aggregation/counting | ✓ | |
| GeoJSON for mapping | | ✓ |
| Shapefile for GIS | | ✓ |
| PDF documentation | | ✓ |
| GBFS (BIXI) | | ✓ (live API) |
| Full dataset (all rows) | Sometimes* | ✓ |
| Dataset > 32,000 rows | Paginate | ✓ |

*DataStore has a 32,000 row limit per query. For large datasets, downloading the full CSV is often simpler.

---

## Step 1: Find the Download URL

```bash
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=DATASET_SLUG' | \
  python3 -c "
import json, sys
for r in json.load(sys.stdin)['result']['resources']:
    ds = '✓ DS' if r.get('datastore_active') else '✗'
    sz = r.get('size', 0)
    sz_mb = f'{sz/1048576:.1f}MB' if sz else '?'
    print(f'{r.get(\"format\",\"?\")} | {ds} | {sz_mb} | {r[\"url\"][:100]}')
"
```

## Step 2: Download

```bash
# Simple download
curl -LO 'URL_FROM_ABOVE'

# Download with a specific filename
curl -L -o trees.csv 'https://donnees.montreal.ca/dataset/b89fd27d-4b49-461b-8e54-fa2b34a628c4/resource/64e28fe6-ef37-437a-972d-d1d3f1f7d891/download/arbres-publics.csv'
```

**Always use `-L` (follow redirects).** Some URLs redirect.

---

## Format-Specific Handling

### CSV
- Encoding: UTF-8
- Separator: comma (standard)
- Load with pandas: `pd.read_csv('file.csv')`

### GeoJSON
- Standard GeoJSON (RFC 7946)
- Load with geopandas: `gpd.read_file('file.geojson')`
- Or parse with `json.load()`

### Shapefile (ZIP)
- Downloaded as `.zip` containing `.shp`, `.dbf`, `.prj`, `.shx`
- Unzip first, then load with geopandas: `gpd.read_file('file.shp')`
- Coordinate system is usually NAD 83 MTM Zone 8 (EPSG:32188)

### GBFS (BIXI)
- Not a downloadable file — it's a live REST API
- Entry point: `https://gbfs.velobixi.com/gbfs/gbfs.json`
- Returns URLs for station info, station status, system info
```bash
# Get station status (live availability)
curl -s 'https://gbfs.velobixi.com/gbfs/en/station_status.json'
# Get station info (locations, capacity)
curl -s 'https://gbfs.velobixi.com/gbfs/en/station_information.json'
```

### GTFS / GTFS-Realtime (STM)
- GTFS static: ZIP file with `stops.txt`, `routes.txt`, `trips.txt`, etc.
- GTFS-Realtime: Protocol Buffer format (requires `gtfs-realtime-bindings` library)
- STM developer registration may be required for real-time feeds
- See the `transit` domain skill for details

### PDF
- Documentation, data dictionaries, methodology descriptions
- Not machine-queryable — use for reference only

---

## Large File Considerations

Some datasets are substantial:
- Tree inventory CSV: ~135 MB (333,556 rows)
- Road condition data: large GeoJSON files
- Historical BIXI trips: multi-GB across years

For large files:
1. Download once and cache locally
2. Use `head` or `pandas.read_csv(nrows=100)` to preview before full load
3. For analysis, consider loading into a local SQLite database

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

**Note on non-CKAN downloads:** BIXI GBFS and STM GTFS feeds are hosted on separate infrastructure. See the `transit` domain skill for their specific URLs, auth requirements, and publishers.

---

## Related Skills / Compétences connexes

- `understand-ckan` — API reference and URL patterns
- `discover-datasets` — Find the right dataset first
- `query-dataset` — Query without downloading (DataStore API)
