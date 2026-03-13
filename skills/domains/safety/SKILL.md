---
name: safety
description: |
  Access public safety and security data for Montréal: criminal incidents,
  emergency service interventions (fire, police), 311 citizen requests,
  traffic collisions, fire stations, police stations, coyote sightings, and
  fire hydrant locations.
  / Accéder aux données de sécurité publique de Montréal : incidents criminels,
  interventions des services d'urgence (incendies, police), demandes 311,
  collisions routières, casernes de pompiers, postes de police, signalements
  de coyotes et emplacements des bornes fontaines.
triggers:
  - crime, criminal, police, fire, emergency, 911, collision, accident, safety, security, coyote
  - crime, criminalité, police, incendie, urgence, collision, accident, sécurité, coyote
---

# Public Safety Data / Données de sécurité publique

## Available Datasets / Jeux de données disponibles

| Dataset | Slug | Format | Update Frequency | Records (approx) |
|---------|------|--------|------------------|------------------|
| Criminal acts | `actes-criminels` | CSV (DataStore) | Daily | 500K+ |
| 311 Service requests | `requete-311` | CSV (DataStore) | Real-time | 1M+ |
| Road collisions | `collisions-routieres` | CSV (DataStore) | Daily | 100K+ |
| Fire department interventions | `interventions-service-securite-incendie-montreal` | CSV (DataStore) | Daily | 500K+ |
| Fire stations | `casernes-pompiers` | CSV + GeoJSON | Static | 42 stations |
| Police stations | `carte-postes-quartier` | GeoJSON | Static | 42 stations |
| Police district boundaries | `limites-pdq-spvm` | GeoJSON | Static | 42 districts |
| Coyote sightings | `signalements-de-coyotes` | CSV (DataStore) | Real-time | 5K+ |
| Fire hydrants | `geolocalisation-des-bornes-fontaines` | CSV + GeoJSON | Monthly | 8K+ |

---

## 1. Criminal Acts / Actes criminels

**Slug:** `actes-criminels`
**Coverage:** All incidents reported to SPVM (Service de police de la Ville de Montréal)
**Records:** 500,000+ since ~2010

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `DATE` | datetime | Date/time of incident |
| `CATEGORIE` | text | Major crime category (FR) |
| `SOUS_CATEGORIE` | text | Crime subcategory (FR) |
| `X` | float | NAD 83 MTM Zone 8 coordinate |
| `Y` | float | NAD 83 MTM Zone 8 coordinate |
| `Latitude` | float | WGS84 latitude |
| `Longitude` | float | WGS84 longitude |
| `QUARTIER` | text | Neighborhood name (FR) |

### Common Queries

```bash
# Count crimes by category (last year)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"CATEGORIE",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+WHERE+"DATE">%272025-01-01%27+GROUP+BY+"CATEGORIE"+ORDER+BY+total+DESC'

# Crimes near a location
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"DATE","CATEGORIE","SOUS_CATEGORIE","Latitude","Longitude"+FROM+"RESOURCE_UUID"+WHERE+("Latitude"-45.5171)^2+("Longitude"-(-73.5629))^2<0.001+LIMIT+100'

# Crimes by neighborhood (month)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"QUARTIER",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+WHERE+DATE_TRUNC(%27month%27,"DATE")=%272026-03-01%27+GROUP+BY+"QUARTIER"+ORDER+BY+total+DESC'
```

---

## 2. 311 Citizen Service Requests / Demandes de services 311

**Slug:** `requete-311`
**Coverage:** All non-emergency requests to City services (potholes, noise, graffiti, street cleaning, etc.)
**Records:** 1M+ entries

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `RequestID` | text | Unique request ID |
| `CreatedDate` | datetime | Request submission date |
| `Status` | text | Open, Closed, In Progress (EN) |
| `Category` | text | Service category |
| `Description` | text | Citizen description |
| `Latitude` | float | WGS84 |
| `Longitude` | float | WGS84 |
| `Ward` | text | Borough/Ward (EN) |

### Common Queries

```bash
# Total requests by category
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"Category",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+GROUP+BY+"Category"+ORDER+BY+total+DESC'

# Open requests in a location
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=RESOURCE_UUID&filters={"Status":"Open"}&limit=50'
```

---

## 3. Road Collisions / Collisions routières

**Slug:** `collisions-routieres`
**Coverage:** Police-reported traffic collisions (injury, property damage)
**Records:** 100,000+ incidents

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `NO_ACCIDENT` | text | Collision ID |
| `DT_ACCIDENT` | datetime | Date/time of collision |
| `NOM_RUE_1` | text | First street (FR) |
| `NOM_RUE_2` | text | Second street (FR) |
| `GRAVITE` | text | Severity: Fatal, Injury, Property damage (FR) |
| `LATITUDE` | float | WGS84 |
| `LONGITUDE` | float | WGS84 |
| `NB_MORTS` | int | Fatalities |
| `NB_BLESSES_GRAVES` | int | Serious injuries |
| `NB_BLESSES_LEGERS` | int | Minor injuries |

### Common Queries

```bash
# Collisions by severity (current year)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"GRAVITE",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+WHERE+YEAR("DT_ACCIDENT")=2026+GROUP+BY+"GRAVITE"'

# Fatal collisions
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=RESOURCE_UUID&filters={"GRAVITE":"Décès"}&limit=100'
```

---

## 4. Fire Department Interventions / Interventions du service de sécurité incendie

**Slug:** `interventions-service-securite-incendie-montreal`
**Coverage:** All SSIM (Service de sécurité incendie de Montréal) emergency responses
**Records:** 500,000+ calls annually

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `NumIntervention` | text | Intervention ID |
| `DateDebut` | datetime | Response start time |
| `CodeIncident` | text | Incident type code |
| `DescriptionIncident` | text | Description (FR) |
| `Arrondissement` | text | Borough (FR) |
| `Longitude` | float | WGS84 |
| `Latitude` | float | WGS84 |
| `TempsReaction` | int | Response time (minutes) |

### Common Queries

```bash
# Incidents by type
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"CodeIncident","DescriptionIncident",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+GROUP+BY+"CodeIncident","DescriptionIncident"+ORDER+BY+total+DESC+LIMIT+20'

# Average response time by borough
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"Arrondissement",AVG("TempsReaction")+as+avg_response+FROM+"RESOURCE_UUID"+GROUP+BY+"Arrondissement"+ORDER+BY+avg_response'
```

---

## 5. Fire Stations / Casernes de pompiers

**Slug:** `casernes-pompiers`
**Format:** CSV + GeoJSON
**Coverage:** 42 fire stations across Montréal
**Update:** Static (stations don't move frequently)

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `Station_ID` | text | SSIM station code |
| `Nom` | text | Station name (FR) |
| `Adresse` | text | Street address |
| `Telephone` | text | Station phone |
| `Latitude` | float | WGS84 |
| `Longitude` | float | WGS84 |

---

## 6. Police Stations / Postes de police

**Slug:** `carte-postes-quartier`
**Format:** GeoJSON
**Coverage:** 42 police stations (PDQ = Poste de quartier)
**Update:** Static

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `name` | text | Station name (FR) |
| `address` | text | Street address |
| `phone` | text | Contact number |
| `geometry` | GeoJSON | Point coordinates (WGS84) |

---

## 7. Police District Boundaries / Limites des PDQ

**Slug:** `limites-pdq-spvm`
**Format:** GeoJSON (Polygon)
**Coverage:** 42 district boundaries
**Use for:** Spatial joins with crime data

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `PDQ_Name` | text | District name (e.g., "Centre") |
| `PDQ_Number` | text | District code (e.g., "01") |
| `geometry` | GeoJSON | Polygon boundary (WGS84) |

---

## 8. Coyote Sightings / Signalements de coyotes

**Slug:** `signalements-de-coyotes`
**Coverage:** Public coyote sightings reported to Ville de Montréal
**Records:** 5,000+ sightings (growing dataset)

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `DateSignalement` | datetime | Sighting date |
| `Adresse` | text | Location (street address) |
| `Description` | text | What was observed (FR) |
| `Latitude` | float | WGS84 |
| `Longitude` | float | WGS84 |
| `Arrondissement` | text | Borough (FR) |

### Common Queries

```bash
# Coyote sightings by borough (last month)
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+"Arrondissement",COUNT(*)+as+total+FROM+"RESOURCE_UUID"+WHERE+"DateSignalement">%272026-02-13%27+GROUP+BY+"Arrondissement"+ORDER+BY+total+DESC'

# Sightings near a location
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=RESOURCE_UUID&limit=50&sort=DateSignalement+desc'
```

---

## 9. Fire Hydrants / Bornes fontaines

**Slug:** `geolocalisation-des-bornes-fontaines`
**Format:** CSV + GeoJSON
**Coverage:** 8,000+ fire hydrants across Montréal
**Update:** Monthly

### Key Fields

| Field | Type | Notes |
|-------|------|-------|
| `HydrantID` | text | Unique hydrant ID |
| `Adresse` | text | Street location |
| `RuePrincipale` | text | Primary street (FR) |
| `RueSecondaire` | text | Cross street (FR) |
| `Latitude` | float | WGS84 |
| `Longitude` | float | WGS84 |
| `Arrondissement` | text | Borough (FR) |
| `TypeBorne` | text | Hydrant type (above/below ground) |

---

## Common Questions / Questions fréquentes

| Question | Dataset | Query Approach |
|----------|---------|----------------|
| "How many crimes in [neighborhood] last year?" | `actes-criminels` | SQL GROUP BY QUARTIER, DATE range |
| "What's the most common crime?" | `actes-criminels` | SQL GROUP BY CATEGORIE |
| "How many collisions on [street]?" | `collisions-routieres` | SQL filter on street name |
| "Nearest fire station to my address?" | `casernes-pompiers` | Distance calculation (spatial) |
| "Police station serving my area?" | `carte-postes-quartier` + `limites-pdq-spvm` | Point-in-polygon GeoJSON |
| "Any 311 requests for potholes?" | `requete-311` | Filter by Category |
| "Recent coyote sightings?" | `signalements-de-coyotes` | Sort by DateSignalement DESC |
| "Fire hydrant locations for [street]?" | `geolocalisation-des-bornes-fontaines` | Filter by street name |

---

## Gotchas & Edge Cases / Pièges et cas limites

1. **Coordinate systems:** `Latitude`/`Longitude` = WGS84 (standard). Some datasets also have `X`/`Y` = NAD 83 MTM Zone 8. Always check.

2. **Crime data lag:** Criminal acts data is updated daily but may have a 24–48 hour lag.

3. **311 requests do not have precise categories in all versions.** Categories may be abbreviated (e.g., "POT" for pothole). Check the resource schema.

4. **Collision severity field is bilingual.** Values: "Décès", "Blessés graves", "Dommages matériels" (FR). Do not hard-code English values.

5. **Fire station phone numbers may change.** Always call 911 for emergencies; use phone field for non-emergency queries only.

6. **Coyote sightings are self-reported.** Data quality varies; not all sightings are confirmed by wildlife experts.

7. **Fire hydrants include both above-ground and below-ground types.** Check `TypeBorne` field to filter if needed.

8. **Large datasets (crimes, 311, collisions, fire interventions).** Always use `LIMIT` and pagination. Avoid fetching entire datasets.

9. **Police district boundaries are GeoJSON (Polygon).** Requires GIS library for point-in-polygon queries; consider spatial index for performance.

---

## Provenance / Provenance

| Source | Publisher | Gov Level | License | Contact |
|--------|-----------|-----------|---------|---------|
| Criminal acts | SPVM (Police de Montréal) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| 311 Requests | Ville de Montréal | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Road collisions | SPVM + MTQ | Municipal/Provincial | CC BY 4.0 | donneesouvertes@montreal.ca |
| Fire interventions | SSIM (Montréal Fire Service) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Fire stations | SSIM | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Police stations | SPVM | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Police districts | SPVM | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Coyote sightings | Ville de Montréal (Public Health) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |
| Fire hydrants | Ville de Montréal (Infrastructure) | Municipal | CC BY 4.0 | donneesouvertes@montreal.ca |

**All datasets:** Published by Ville de Montréal. License: CC BY 4.0 (Creative Commons Attribution 4.0 International).

---

## Related Skills / Compétences connexes

- `query-dataset` — SQL patterns for DataStore queries
- `spatial-queries` — Geographic proximity and point-in-polygon searches
- `borough-context` — Neighborhood names, district codes, boundaries
- `bilingual-handling` — French/English crime categories, incident types
- `geojson-handling` — Working with fire stations, police boundaries as GeoJSON
