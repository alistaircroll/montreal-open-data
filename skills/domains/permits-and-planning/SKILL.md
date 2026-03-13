---
name: permits-and-planning
description: |
  Access building permit data, zoning information, urban planning, property
  assessments, and land use data for Montréal.
  / Accéder aux données de permis de construction, zonage, urbanisme,
  évaluations foncières et affectation du sol pour Montréal.
triggers:
  - permit, building permit, construction, zoning, urban plan, property, assessment
  - permis, construction, zonage, urbanisme, évaluation foncière, affectation
---

# Permits & Urban Planning / Permis et urbanisme

## Available Datasets / Jeux de données disponibles

### Building Permits / Permis de construction

**Dataset:** `permis-construction`
**Resources:**
- CSV (DataStore-active ✓) — Permits for construction, transformation, and demolition
- GeoJSON — Same data with geographic coordinates
- Web visualization tool

```bash
# Find the resource ID
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=permis-construction' | \
  python3 -c "
import json, sys
for r in json.load(sys.stdin)['result']['resources']:
    if r.get('datastore_active'):
        print(f'DataStore resource: {r[\"id\"]}')
        print(f'Name: {r[\"name\"][:80]}')
"
```

**Typical fields:**
- Permit number, type (construction, transformation, demolition)
- Project address, borough
- Estimated project cost
- Permit issue date, status
- Type of work (residential, commercial, institutional)
- Geographic coordinates

**Common queries:**
```sql
-- Permits in a specific borough
SELECT * FROM "RESOURCE_UUID"
WHERE "ARROND" = 'Le Plateau-Mont-Royal'
ORDER BY "DATE_EMISSION" DESC
LIMIT 20

-- Total permit value by borough
SELECT "ARROND", COUNT(*) as count, SUM(CAST("COUT_ESTIME" AS FLOAT)) as total_cost
FROM "RESOURCE_UUID"
GROUP BY "ARROND"
ORDER BY total_cost DESC

-- Recent demolition permits
SELECT * FROM "RESOURCE_UUID"
WHERE "TYPE_PERMIS" LIKE '%démolition%'
ORDER BY "DATE_EMISSION" DESC
LIMIT 10
```

### Property Assessment / Évaluation foncière

**Dataset:** `unites-evaluation-fonciere` (or search for "évaluation foncière")
**Resources:** CSV + GeoJSON
**Content:** Property assessment units for all 16 cities of the Montréal agglomeration.

**Key fields:**
- CUBF code (Code d'utilisation des biens-fonds) — property use classification
- Assessed land value, building value, total value
- Approximate dimensions
- Registration number
- Geographic position

**Important:** This data has **no legal value** for cadastral purposes. It's the city's assessment for tax purposes, not the legal property boundary (which is the provincial Cadastre du Québec).

### Land Use / Affectation du sol

**Dataset:** `affectation-du-sol`
**Format:** GeoJSON (download only — not in DataStore)
**Content:** Zoning and land use designations across the city.

### Urban Plan / Plan d'urbanisme

**Related datasets:**
- `schema-transport` — Transportation schema
- `vision-2050-reseau-transport-collectif-structurant-plan-urbanisme-mobilite-2050` — 2050 transit vision
- `cartes-reglement-metropole-mixte` — Mixed-use regulation maps

### Building Data

| Dataset | Slug | Format |
|---------|------|--------|
| 2D building footprints | `batiment-2d` | GeoJSON/Shapefile |
| 3D building maquette | `batiment-3d-2016-maquette-citygml-lod2-avec-textures2` | CityGML |
| Municipal buildings | `batiments-municipaux` | CSV |
| Vacant buildings (Ville-Marie) | `batiments-vacants-ville-marie` | CSV |
| Family-certified buildings | `batiments-certifies-qualite-famille` | CSV |

---

## Common Questions / Questions fréquentes

| Question | Dataset | Approach |
|----------|---------|----------|
| "Were any permits issued on my street?" | `permis-construction` | Filter by address/street name |
| "How much construction in my borough?" | `permis-construction` | Group by ARROND, count/sum |
| "What's the assessed value of a property?" | `unites-evaluation-fonciere` | Filter by address or registration # |
| "Is this area zoned residential?" | `affectation-du-sol` | GeoJSON spatial lookup |
| "Any demolitions nearby?" | `permis-construction` | Filter TYPE_PERMIS + coordinates |
| "3D model of a neighborhood?" | `batiment-3d-*` | CityGML download |

---

## Gotchas / Pièges

1. **Permit field names vary.** Check actual field names via `datastore_info` — they may differ from what's described here.
2. **Cost is estimated, not actual.** `COUT_ESTIME` is the applicant's estimate at permit time.
3. **Assessment ≠ market value.** Property assessments are done every 3 years and may not reflect current sale prices.
4. **GeoJSON files can be large.** Building footprints for all of Montréal is a substantial download.
5. **CityGML is specialized.** 3D building data requires GIS tools (QGIS, FME, CesiumJS) — not standard data analysis tools.

---

## Provenance / Provenance

| Source | Publisher | Gov Level | License | Contact |
|--------|-----------|-----------|---------|---------|
| Building permits | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Property assessment | Ville de Montréal (Direction de l'évaluation foncière) | Municipal (agglomeration) | CC BY 4.0 | donneesouvertes@montreal.ca |
| Land use / zoning | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Building footprints | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Cadastre (legal boundaries) | Registre foncier du Québec | **Provincial** | Provincial terms | registrefoncier.gouv.qc.ca |

**Important distinction:** Property assessment data is from the **city** (for tax purposes). The legal property registry (cadastre) is from the **province**. They overlap but are not the same thing. When a citizen asks about property boundaries in a legal context, direct them to the provincial Registre foncier.

---

## Related Skills / Compétences connexes

- `query-dataset` — DataStore query patterns
- `borough-context` — Borough names and boundaries
- `spatial-queries` — Geographic filtering
- `budget-and-finance` — Contract and spending data
