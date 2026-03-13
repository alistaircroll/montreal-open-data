---
name: Culture and Recreation
description: |
  EN: Access Montreal's parks, cultural facilities, programming, public art, and recreational infrastructure through CKAN datasets.
  FR: Accédez aux parcs, installations culturelles, programmation, art public et infrastructures récréatives de Montréal via les données CKAN.
triggers:
  - culture
  - recreation
  - parks
  - facilities
  - sports
  - arts
  - murals
  - patinoires
  - skating rinks
  - programming
  - parcs
  - installations
  - programmation
  - art public
---

# Culture and Recreation / Culture et Loisirs

Access Montreal's parks, recreational facilities, cultural programming, public art installations, and seasonal conditions through the CKAN open data portal.

## Available Datasets / Ensembles de données disponibles

| Dataset | Format | Real-time? | Description |
|---------|--------|-----------|-------------|
| `grands-parcs-parcs-d-arrondissements-et-espaces-publics` | DataStore SQL | No | Major parks, district parks, and public spaces |
| `installations-recreatives-sportives-et-culturelles` | DataStore SQL | No | Sports, recreational, and cultural facility locations |
| `programmation-sports-loisirs-montreal` | DataStore SQL | No | Sports and leisure activity programming schedule |
| `murales` | DataStore SQL | No | Subsidized public art murals with locations |
| `parcours-riverain` | DataStore SQL | No | Riverside walking and cycling trails |
| `patinoires` | JSON Feed | **Yes** | Current skating rink conditions (separate feed, not DataStore) |
| `patinoires-historique` | DataStore SQL | No | Historical skating rink conditions data |
| `conditions-ski` | JSON Feed | **Yes** | Ski hill conditions (separate feed, not DataStore) |
| `recipiendaires-du-prix-paul-buissonneau` | DataStore SQL | No | Annual cultural excellence award recipients |
| `soutien-artistes-organismes-culturels` | DataStore SQL | No | Artist and cultural organization funding records |
| `batiments-certifies-qualite-famille` | DataStore SQL | No | Family-certified community buildings |

## Real-time Condition Feeds / Flux temps réel

**Note:** Skating rink (`patinoires`) and ski (`conditions-ski`) real-time conditions are **NOT in DataStore**. They are available as separate JSON feeds updated throughout the day. Query these directly via their feed endpoints rather than through standard DataStore SQL queries.

## Common SQL Queries / Requêtes SQL courantes

### Find all parks in a specific borough
```sql
SELECT name, borough, type, address
FROM "grands-parcs-parcs-d-arrondissements-et-espaces-publics"
WHERE borough = 'Plateau-Mont-Royal'
ORDER BY name;
```

### List cultural facilities with type filtering
```sql
SELECT name, address, borough, facility_type, phone
FROM "installations-recreatives-sportives-et-culturelles"
WHERE facility_type ILIKE '%cultural%'
  OR facility_type ILIKE '%art%'
ORDER BY borough, name;
```

### Find murals near a location (requires lat/lon)
```sql
SELECT title, artist, address, coordinates
FROM "murales"
WHERE ST_DWithin(
  coordinates::geography,
  ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326)::geography,
  500
)
ORDER BY title;
```

### Search programming by activity type
```sql
SELECT activity_name, schedule, location, borough
FROM "programmation-sports-loisirs-montreal"
WHERE activity_name ILIKE '%swimming%'
  OR activity_name ILIKE '%natation%'
LIMIT 20;
```

## Common Questions / Questions fréquentes

| Question | Query | Notes |
|----------|-------|-------|
| Which parks are in my neighbourhood? | `grands-parcs-parcs-d-arrondissements-et-espaces-publics` + borough filter | Use exact borough name (proper nouns) |
| What sports classes are available? | `programmation-sports-loisirs-montreal` | Includes schedules and locations |
| Where can I find a skating rink? | `patinoires` (real-time feed) | Check real-time conditions separately |
| Is there public art nearby? | `murales` + geospatial query | Include artist and funding year |
| What cultural facilities exist? | `installations-recreatives-sportives-et-culturelles` | Filter by facility_type |
| Which artists received funding? | `soutien-artistes-organismes-culturels` | Year-based filtering available |

## Gotchas / Pièges

1. **Real-time condition feeds** — `patinoires` and `conditions-ski` update throughout the day via separate JSON feeds, NOT through DataStore. Standard SQL queries won't capture live updates.

2. **Park names are proper nouns** — Always match exact capitalization and accents when filtering by park name (e.g., "Parc La Fontaine", not "parc la fontaine").

3. **Borough filtering** — Borough names are specific and case-sensitive. Use exact values like "Plateau-Mont-Royal", "Rosemont–La Petite-Patrie", "Ville-Marie".

4. **Seasonal data** — Programming and facility availability vary by season. Filter results by date ranges if querying historical or future schedules.

5. **Coordinates format** — Some datasets use PostGIS geometry; others use text coordinates. Check schema before performing spatial queries.

6. **Funding records** — Support datasets (`soutien-artistes-organismes-culturels`) may have annual publication delays. Current year data may not be available.

## Provenance / Provenance

| Attribute | Value |
|-----------|-------|
| Publisher | Ville de Montréal / City of Montreal |
| Portal | CKAN Open Data Portal |
| License | Creative Commons Attribution 4.0 (CC BY 4.0) |
| Update Frequency | Quarterly (most datasets); Daily (real-time feeds) |
| Contact | Montreal Open Data Team |

## Related Skills / Compétences connexes

- **Permits & Buildings** — `batiments-certifies-qualite-famille` overlaps with family-certified facility queries
- **Events & Programming** — Complements `programmation-sports-loisirs-montreal` scheduling
- **Geography & Boundaries** — Required for borough filtering and spatial queries
- **Arts & Heritage** — Connects to public art and cultural funding datasets
