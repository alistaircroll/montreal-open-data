---
name: environment
description: |
  Access environmental data for Montréal: public tree inventory (333,556 trees),
  air quality monitoring, green spaces, canopy coverage, water quality, and
  urban heat islands.
  / Accéder aux données environnementales de Montréal : inventaire des arbres
  publics (333 556 arbres), qualité de l'air, espaces verts, canopée,
  qualité de l'eau et îlots de chaleur.
triggers:
  - tree, trees, air quality, environment, green space, canopy, water, pollution
  - arbre, arbres, qualité air, environnement, espace vert, canopée, eau, pollution
---

# Environment Data / Données environnementales

## Available Datasets / Jeux de données disponibles

### Trees / Arbres

| Dataset | Slug | Records | Format | Update |
|---------|------|---------|--------|--------|
| Public tree inventory | `arbres` | 333,556 | CSV (DataStore) | Monthly |
| Tree DHP history | `arbres` (resource 2) | Large | CSV (DataStore) | Weekly |
| Inventory status by borough | `arbres` (resource 3) | 19 rows | CSV (DataStore) | Stable |
| Tree chronology | `chronologie-des-arbres-de-montreal` | Varies | CSV | Periodic |
| Tree felling | `abattage-arbres-publics` | Varies | CSV | Monthly |
| Canopy coverage | `canopee` | GeoJSON | GeoJSON | Periodic |

**Tree inventory — key resource ID:** `64e28fe6-ef37-437a-972d-d1d3f1f7d891`

**Fields (bilingual where noted):**

| Field | Type | Description |
|-------|------|-------------|
| `INV_TYPE` | text | H = Hors rue (off-street/park), R = Rue (street) |
| `EMP_NO` | int | Unique tree placement ID (within type) |
| `ARROND_NOM` | text | Borough name (FR) |
| `Rue` | text | Street name (street trees only) |
| `No_civique` | int | Civic number (nearest building) |
| `Emplacement` | text | Physical location type (FR) |
| `Essence_latin` | text | Latin species name |
| `Essence_fr` | text | French common name ✅ bilingual |
| `Essence_ang` | text | English common name ✅ bilingual |
| `DHP` | text (cast to int) | Diameter at Breast Height (cm) |
| `Date_Releve` | datetime | Last survey date |
| `Date_Plantation` | datetime | Planting date (when known) |
| `Latitude` | float | WGS84 latitude |
| `Longitude` | float | WGS84 longitude |
| `Coord_X` / `Coord_Y` | float | NAD 83 MTM Zone 8 |
| `Arbre_remarquable` | text | O/N — remarkable tree designation |
| `NOM_PARC` | text | Park name (for park trees) |

**Common queries:**

```bash
# Count trees by borough
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"ARROND_NOM",COUNT(*)+as+total+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"+GROUP+BY+"ARROND_NOM"+ORDER+BY+total+DESC'

# Top 10 species
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"Essence_fr","Essence_ang",COUNT(*)+as+total+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"+GROUP+BY+"Essence_fr","Essence_ang"+ORDER+BY+total+DESC+LIMIT+10'

# Trees near a location (approximate)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"Essence_fr","Essence_ang","DHP","Latitude","Longitude",(("Latitude"-45.5236)^2+("Longitude"-(-73.5826))^2)+as+dist_sq+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"+WHERE+"Latitude"+IS+NOT+NULL+ORDER+BY+dist_sq+ASC+LIMIT+10'

# Remarkable trees
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&filters={"Arbre_remarquable":"O"}&limit=50'
```

### Air Quality / Qualité de l'air

| Dataset | Slug | Format | Update |
|---------|------|--------|--------|
| RSQA pollutants | `rsqa-polluants` | CSV (DataStore) | Hourly |
| RSQA stations | On CKAN | CSV | Static |

**Network:** 11 permanent monitoring stations + 1 nomadic station across the island.
**Real-time map:** `carte-qualite-air.montreal.ca`
**Provincial feed:** RSQAQ (Réseau de surveillance de la qualité de l'air du Québec) — hourly IQA (Air Quality Index).

**Pollutants monitored:** PM2.5, PM10, O₃ (ozone), NO₂, SO₂, CO.

### Green Spaces / Espaces verts

| Dataset | Slug | Format |
|---------|------|--------|
| Parks | Various park datasets | GeoJSON, CSV |
| Dog parks | `parcs-canins` | CSV |
| Community gardens | On CKAN | CSV |
| Protected natural areas | `bilan-repertoire-des-milieux-naturels-proteges-contributifs-a-la-biodiversite` | CSV |

### Water / Eau

| Dataset | Slug | Format |
|---------|------|--------|
| Aquatic monitoring network | `carte-du-reseau-de-suivi-du-milieu-aquatique-rsma` | Various |
| Wastewater treatment concentration | `concentration-mes-station-epuration` | CSV |
| Streams and ditches | `cours-d-eau-et-fosse` | GeoJSON |

### Urban Heat Islands / Îlots de chaleur

**Available through:** INSPQ Géoportail de santé publique
**On CKAN:** Check for related datasets tagged with "chaleur" or "température"
**Note:** This is provincial (INSPQ) data, not municipal.

---

## Common Questions / Questions fréquentes

| Question | Dataset | Query Approach |
|----------|---------|---------------|
| "How many trees in [borough]?" | `arbres` | SQL GROUP BY ARROND_NOM |
| "What species is most common?" | `arbres` | SQL GROUP BY Essence_fr |
| "What trees are near my address?" | `arbres` | SQL ORDER BY distance |
| "What's the air quality right now?" | `rsqa-polluants` | Latest DataStore record |
| "Where are the dog parks?" | `parcs-canins` | DataStore search |
| "Any remarkable trees nearby?" | `arbres` | Filter Arbre_remarquable=O |
| "Tree canopy by neighborhood?" | `canopee` | GeoJSON download |

---

## Gotchas / Pièges

1. **DHP is stored as text.** Use `CAST("DHP" AS INTEGER)` for numeric operations.
2. **Not all boroughs have complete inventories.** Check the inventory status resource for coverage.
3. **Coordinate systems.** `Latitude`/`Longitude` = WGS84. `Coord_X`/`Coord_Y` = NAD 83 MTM Zone 8. Some records have one but not the other.
4. **Tree records are large.** 333,556 rows × 34 fields. Always use `LIMIT` and pagination. Don't try to fetch all at once.
5. **Air quality data latency.** Approximately 50 minutes after each hour.
6. **Canopy data is GeoJSON** — not in DataStore. Must download and parse locally.

---

## Provenance / Provenance

| Source | Publisher | Gov Level | License | Contact |
|--------|-----------|-----------|---------|---------|
| Tree inventory | Ville de Montréal (Arrondissements) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Air quality (RSQA) | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Air quality (RSQAQ) | Min. Environnement du Québec | Provincial | Open license | Via province |
| Heat islands | INSPQ | Provincial | Varies | Via inspq.qc.ca |
| Parks, green spaces | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |

**Data collection method (trees):** Field inspectors in each borough collect and update data. They record species, diameter, location, and other attributes. Data is uploaded to the GDV (Gestion des végétaux) database.

---

## Related Skills / Compétences connexes

- `query-dataset` — SQL patterns for DataStore queries
- `spatial-queries` — Geographic proximity searches
- `borough-context` — Borough names and codes
- `bilingual-handling` — Tree species names, field translations
- `cross-dataset-joins` — Correlate trees with heat islands, crime, etc.
