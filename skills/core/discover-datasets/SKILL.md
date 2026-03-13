---
name: discover-datasets
description: |
  Search, browse, and explore the 436+ datasets on Montréal's open data portal.
  Find the right dataset for any question about the city.
  / Rechercher, parcourir et explorer les 436+ jeux de données du portail
  de données ouvertes de Montréal. Trouver le bon jeu de données pour toute
  question sur la ville.
triggers:
  - find dataset, search data, what data, which dataset, open data, catalog
  - trouver jeu de données, chercher données, quelles données, catalogue
---

# Discover Datasets / Découvrir les jeux de données

## Purpose / Objectif

When a user asks a question about Montréal, the first step is finding the right dataset. This skill teaches you to search the catalog effectively.

Lorsqu'un utilisateur pose une question sur Montréal, la première étape est de trouver le bon jeu de données.

---

## Step 1: Keyword Search / Recherche par mot-clé

**Endpoint:** `https://donnees.montreal.ca/api/3/action/package_search`

```bash
# Search for datasets about trees
curl -s 'https://donnees.montreal.ca/api/3/action/package_search?q=arbres&rows=5' | python3 -m json.tool
```

**Tips for effective searches:**
- Search in **French first** — most metadata is in French
- Try synonyms: `vélo` OR `cyclable` OR `bicyclette`
- Use the `notes` field for data dictionary details
- Use facets to narrow: `?q=*:*&facet=true&facet.field=["organization","tags"]&rows=0`

**Keyword translation table for common queries:**

| English | French (search term) | Example Dataset Slug |
|---------|---------------------|---------------------|
| Trees | arbres | `arbres` |
| Bus / Transit | transport, autobus, bus | `stm-bus-temps-reel-gtfs-realtime` |
| Bike sharing | vélo, bixi | `bixi-etat-des-stations` |
| Building permits | permis construction | `permis-construction` |
| Budget | budget | `budget` |
| Crime | criminalité, actes criminels | `actes-criminels` |
| Road closures | entraves, travaux | `entraves-travaux` |
| Parks | parcs | `parcs` |
| Elections | élections, vote | `bureaux-vote` |
| Water quality | eau, qualité | `carte-du-reseau-de-suivi-du-milieu-aquatique-rsma` |
| Snow removal | déneigement | `311-montreal-info-deneigement-alertes` |
| Fire stations | pompiers, casernes | `casernes-pompiers` |
| Libraries | bibliothèques | `bibliotheques-montreal-statistiques` |
| Public art | art public | `art-public-information-sur-les-oeuvres-de-la-collection-municipale` |
| Road conditions | chaussées, condition | `condition-chaussees-reseau-routier` |
| Bike paths | pistes cyclables, réseau cyclable | `condition-chaussees-reseau-cyclable` |
| Contracts | contrats | `contrats-comite-executif` |
| Air quality | qualité air | `rsqa-polluants` |
| Dog parks | chiens, canin | `parcs-canins` |

---

## Step 2: Browse by Category / Parcourir par catégorie

Datasets are organized into thematic groups:

```bash
curl -s 'https://donnees.montreal.ca/api/3/action/group_list?all_fields=true' | python3 -m json.tool
```

Main categories (groups):
- **Environnement, ressources naturelles et énergie** — Trees, air, water, green spaces
- **Gouvernement et finances** — Budget, contracts, elections, officials
- **Infrastructures** — Roads, buildings, water mains, geobase
- **Justice, sécurité et urgences** — Crime, fire, 311
- **Économie et entreprises** — Permits, businesses, commercial activity
- **Transport** — STM, BIXI, road closures, bike paths
- **Société et culture** — Heritage, public art, libraries
- **Santé** — Clinics, public health data
- **Éducation et recherche** — Schools, libraries, research
- **Agriculture et alimentation** — Community gardens, food inspections
- **Tourisme, sports et loisirs** — Parks, pools, events
- **Politiques sociales** — Housing, social services

---

## Step 3: Browse by Organization / Parcourir par organisme

```bash
curl -s 'https://donnees.montreal.ca/api/3/action/package_search?q=organization:societe-de-transport-de-montreal&rows=10'
```

| Organization | Focus | Datasets |
|---|---|---|
| `ville-de-montreal` | Everything municipal | ~383 |
| `societe-de-transport-de-montreal` | Bus & metro | 7 |
| `bixi` | Bike sharing | 2 |
| `agence-de-mobilite-durable-montreal` | Parking & mobility | 2 |
| `211-grand-montreal` | Community resources | 1 |
| `regroupement-eco-quartiers` | Eco-neighborhood programs | 2 |

---

## Step 4: Inspect a Dataset / Inspecter un jeu de données

Once you find a promising dataset, get its full details:

```bash
curl -s 'https://donnees.montreal.ca/api/3/action/package_show?id=arbres' | python3 -m json.tool
```

**Key things to check:**
1. `notes` — Description and data dictionary (often very detailed, in French)
2. `resources[]` — Available files and their formats
3. `resources[].datastore_active` — Can you query it via DataStore? (`true` = yes)
4. `update_frequency` — How fresh is the data? (daily, weekly, monthly, yearly)
5. `metadata_modified` — When was it last updated?
6. `territoire[]` — Which boroughs are covered? (borough codes like `AHU`, `CDN`, `VIM`)
7. `methodologie` — How the data was collected

**To see a resource's fields (columns):**
```bash
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_info?id=64e28fe6-ef37-437a-972d-d1d3f1f7d891' | python3 -m json.tool
```

Or peek at the first few rows:
```bash
curl -s 'https://donnees.montreal.ca/api/3/action/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&limit=2'
```

---

## Step 5: When You Can't Find It / Quand vous ne trouvez pas

1. **Try broader French terms.** The catalog is predominantly French.
2. **Search by tag:** `?q=tags:Transport`
3. **List all datasets:** `package_list` returns all 436 slugs — scan for relevant names.
4. **Check Données Québec:** Some Montréal data may only be on `donneesquebec.ca`.
5. **Check external partners:**
   - STM developer portal: `stm.info/en/about/developers`
   - BIXI GBFS feed: `gbfs.velobixi.com/gbfs/gbfs.json`
   - Info-Travaux (road closures): Check for `entraves-travaux` dataset
6. **The data may not exist as open data.** Some city services are not yet in the open data catalog.

---

## Quick Question → Dataset Mapping / Question rapide → Jeu de données

| User Question | Dataset to Use | Resource Type |
|---|---|---|
| "When is the next bus?" | `stm-bus-temps-reel-gtfs-realtime` | GTFS-RT |
| "How many trees in my borough?" | `arbres` | DataStore (CSV) |
| "Any construction on my street?" | `entraves-travaux` | DataStore |
| "Where can I park?" | Check agence-de-mobilite-durable | Various |
| "What's the crime rate?" | `actes-criminels` | DataStore (CSV) |
| "How much did the city spend?" | `budget` | DataStore (XLSX) |
| "Are there BIXI bikes nearby?" | `bixi-etat-des-stations` | GBFS (live) |
| "Where are the fire stations?" | `casernes-pompiers` | DataStore |
| "Any parks near me?" | `parcs` | GeoJSON |
| "Building permit status?" | `permis-construction` | DataStore |
| "Road conditions?" | `condition-chaussees-reseau-routier` | DataStore |
| "Where's the nearest library?" | `bibliotheques-montreal-statistiques` | DataStore |
| "Public art nearby?" | `art-public-...` | DataStore |
| "Snow removal schedule?" | `311-montreal-info-deneigement-alertes` | API |
| "Air quality today?" | `rsqa-polluants` | DataStore |
| "Election results?" | `resultats-elections` + `bureaux-vote` | DataStore |

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

**Scope limitation:** This skill searches the donnees.montreal.ca portal only (436 datasets). Other government data about Montréal exists on separate platforms — see the transit skill (STM developer portal, BIXI GBFS), the provincial skill (Données Québec, SOQUIJ, DGEQ), and the federal skill (Statistics Canada) for additional sources.

---

## Related Skills / Compétences connexes

- `understand-ckan` — Full CKAN API reference
- `query-dataset` — Build queries against DataStore
- `bilingual-handling` — Navigate French/English content
- `borough-context` — Map borough names and codes
