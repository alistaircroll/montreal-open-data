---
name: error-recovery
description: |
  Patterns for recovering from common API failures when querying Montréal's
  open data: timeouts, field name mismatches, encoding issues, rate limits,
  and missing resources.
  / Stratégies de récupération après les erreurs courantes de l'API de
  données ouvertes de Montréal : délais, noms de champs, encodage, limites.
triggers:
  - error, fail, timeout, 404, 500, encoding, broken, not working
  - erreur, échec, délai, encodage, ne fonctionne pas
---

# Error Recovery / Récupération d'erreurs

## Error Decision Tree / Arbre de décision

When an API call fails, follow this sequence:

```
1. HTTP error?
   ├─ 404 → Resource ID may have changed. Use package_show to get current IDs.
   ├─ 400 → SQL syntax error or bad field name. Run field-inspector.py.
   ├─ 403 → Auth required (STM real-time) or IP blocked. Check config.
   ├─ 500 → Server error. Wait 30s, retry once. If persists, try simpler query.
   └─ Timeout → Query too large. Add LIMIT, reduce date range, or paginate.

2. Empty results?
   ├─ Check field name case (case-sensitive in DataStore SQL)
   ├─ Check borough name format (spaces, dashes, accents vary)
   ├─ Check date format (some fields use ISO, others use DD/MM/YYYY)
   └─ Try broader LIKE pattern instead of exact match

3. Unexpected data?
   ├─ Numeric field returns text → CAST("field" AS FLOAT/INTEGER)
   ├─ Encoding garbled → Field uses Latin-1, not UTF-8 (rare, older datasets)
   ├─ Coordinates wrong → Check if NAD83 MTM8 instead of WGS84
   └─ Borough name mismatch → Use LIKE '%keyword%' pattern
```

---

## Pattern 1: Resource ID Changed / ID de ressource modifié

The most common silent failure. A resource UUID in a skill may no longer exist.

**Recovery:**
```bash
# Get current resource IDs for a dataset
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=DATASET_SLUG' | \
  python3 -c "
import json, sys
for r in json.load(sys.stdin)['result']['resources']:
    ds = '✓ DataStore' if r.get('datastore_active') else '  File only'
    print(f'{ds}  {r[\"id\"]}  {r.get(\"name\",\"\")[:50]}')
"
```

**Prevention:** Run `scripts/catalog-refresh.py` periodically. The generated `reference/endpoint-registry.json` has all current UUIDs.

---

## Pattern 2: Field Name Mismatch / Nom de champ incorrect

DataStore SQL is **case-sensitive**. `"ARROND_NOM"` ≠ `"arrond_nom"` ≠ `"Arrond_Nom"`.

**Recovery:**
```bash
# Discover actual field names
python3 scripts/field-inspector.py RESOURCE_UUID
```

**Or via API:**
```bash
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=RESOURCE_UUID&limit=0' | \
  python3 -c "
import json, sys
for f in json.load(sys.stdin)['result']['fields']:
    print(f'{f[\"id\"]:<30} {f.get(\"type\",\"?\")}')
"
```

---

## Pattern 3: Borough Name Variations / Variantes de noms d'arrondissements

Borough names are inconsistent across datasets. The same borough may appear as:

```
"Ville-Marie"                    ← hyphen, no spaces
"Ville - Marie"                  ← hyphen with spaces
"Mercier–Hochelaga-Maisonneuve"  ← en-dash between first two, hyphen in third
"CDN-NDG"                        ← abbreviation
```

**Recovery:** Always use LIKE patterns:
```sql
WHERE "ARROND_NOM" LIKE '%Plateau%Royal%'
WHERE "ARROND_NOM" LIKE '%Mercier%Hochelaga%'
WHERE "ARROND_NOM" LIKE '%Notre-Dame%Gr_ce%'
```

The underscore `_` in SQL LIKE matches any single character (handles accent variants).

---

## Pattern 4: Query Too Large / Requête trop volumineuse

DataStore has a **32,000-row default limit** per response. Large datasets will silently truncate.

**Recovery:**
```sql
-- Always paginate large result sets
SELECT * FROM "UUID" WHERE ... ORDER BY "_id" LIMIT 1000 OFFSET 0
SELECT * FROM "UUID" WHERE ... ORDER BY "_id" LIMIT 1000 OFFSET 1000
-- ... continue until fewer than LIMIT rows returned
```

**For aggregations**, use SQL GROUP BY to reduce result size server-side.

---

## Pattern 5: Numeric Fields Stored as Text

Many datasets store numbers as text. Comparisons and math will fail silently.

**Recovery:**
```sql
-- Cast before comparing
WHERE CAST("DHP" AS INTEGER) > 50
ORDER BY CAST("COUT_ESTIME" AS FLOAT) DESC
```

---

## Pattern 6: Rate Limiting, 403s, and 409s

The CKAN API has undocumented rate limits and query complexity limits:

- **403 Forbidden:** Too many rapid requests. Wait 10-30 seconds and retry.
- **409 Conflict:** SQL query too complex or dataset too large for server-side processing. Common with large datasets (311 has 2.7M+ rows, crime has 344K+) when doing GROUP BY without date filtering.
- Rapid sequential SQL queries (>5 in quick succession) trigger 403s.

**Recovery:**
- Add `LIMIT` to all queries (even if you want all rows — paginate instead)
- Wait 2-3 seconds between sequential API calls
- **Always add date filters** on large datasets before GROUP BY
- For 409: narrow the date range (e.g., last 3 months instead of all time)
- For 403: wait 10s and retry, or use `datastore_search` (non-SQL) as fallback
- For large exports, use the CSV download URL instead of DataStore API
- **Fallback to filter API:** `datastore_search?filters={"field":"value"}` is more reliable than SQL for simple queries on large datasets

---

## Pattern 7: Non-CKAN Endpoints

Some endpoints are not CKAN (BIXI GBFS, STM GTFS, Planif-Neige SOAP). Each has its own failure modes:

| Endpoint | Common Failure | Recovery |
|----------|---------------|----------|
| BIXI GBFS | Seasonal (Apr-Nov) | Check `station_status` first; 0 bikes in winter is normal |
| STM GTFS-RT | Missing API key | Direct user to register at portail.developpeurs.stm.info |
| Planif-Neige | SOAP format | Use `zeep` library; raw HTTP won't work |
| Données Québec | Different CKAN instance | Same API pattern but different base URL |

---

## Pattern 8: Encoding Issues / Problèmes d'encodage

Montréal data uses French characters (é, è, ê, ë, ç, à, î, ô, etc.). Most data is UTF-8, but:

**If you see garbled characters:**
1. Check if the response was decoded as Latin-1 instead of UTF-8
2. For CSV downloads, try `encoding='utf-8-sig'` (handles BOM)
3. In SQL queries, accented characters work: `WHERE "Essence_fr" = 'Érable argenté'`

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — agent-side error handling patterns |
| **Applies to** | All Montréal open data endpoints |
| **Last verified** | March 2026 |

---

## Related Skills / Compétences connexes

- `query-dataset` — Query patterns and pagination
- `bilingual-handling` — French character handling
- `borough-context` — Borough name lookups
- `data-freshness` — Detecting stale data
