---
name: bilingual-handling
description: |
  Patterns for navigating French and English content in Montréal's open data.
  Field name mappings, search strategies, and output formatting for bilingual use.
  / Stratégies pour naviguer le contenu bilingue dans les données ouvertes de Montréal.
  Correspondances de noms de champs, stratégies de recherche et formatage bilingue.
triggers:
  - bilingual, French, English, translate, field names, language
  - bilingue, français, anglais, traduire, noms de champs, langue
---

# Bilingual Data Handling / Gestion des données bilingues

## The Reality / La réalité

Montréal's open data is **predominantly French**. This is not a bug — it reflects the legal and cultural context of Québec. To work with this data effectively, an AI agent must:

1. **Search in French** — dataset titles, descriptions, tags, and most field names are French
2. **Recognize bilingual fields** — some datasets have paired FR/EN columns
3. **Present results in the user's language** — regardless of the source language

Les données ouvertes de Montréal sont **principalement en français**. Pour travailler efficacement, un agent IA doit chercher en français, reconnaître les champs bilingues et présenter les résultats dans la langue de l'utilisateur.

---

## Pattern 1: Search Term Translation / Traduction des termes de recherche

When a user asks in English, translate to French before searching:

### Municipal Infrastructure

| English | French (search term) |
|---------|---------------------|
| tree(s) | arbre(s) |
| road, street | rue, route, chaussée |
| bridge | pont |
| water main | aqueduc, conduite d'eau |
| building | bâtiment |
| sidewalk | trottoir |
| bike path | piste cyclable, réseau cyclable |
| park | parc |
| fire station | caserne (de pompiers) |
| library | bibliothèque |
| pool, swimming | piscine |
| arena, rink | aréna, patinoire |

### Government & Services

| English | French (search term) |
|---------|---------------------|
| budget | budget |
| contract | contrat |
| permit | permis |
| election | élection |
| voting | vote, scrutin |
| borough | arrondissement |
| council | conseil |
| bylaw, regulation | règlement |
| complaint, request | plainte, requête |
| snow removal | déneigement |
| garbage, waste | déchet, collecte, ordure |

### Environment

| English | French (search term) |
|---------|---------------------|
| air quality | qualité de l'air |
| water quality | qualité de l'eau |
| green space | espace vert |
| canopy | canopée |
| garden | jardin |
| contaminated soil | terrain contaminé |
| heat island | îlot de chaleur |

### Transportation

| English | French (search term) |
|---------|---------------------|
| bus | autobus, bus |
| metro, subway | métro |
| transit | transport (en commun) |
| bike sharing | vélopartage, vélo-partage |
| parking | stationnement |
| road closure | entrave, fermeture |
| construction | travaux |
| traffic | circulation |
| accident, collision | accident, collision |

---

## Pattern 2: Bilingual Field Recognition / Reconnaissance des champs bilingues

Some datasets include explicit bilingual field pairs. The common patterns:

### Suffix pattern: `_fr` / `_ang` or `_en`
```
Essence_fr → "Érable argenté"
Essence_ang → "Silver Maple"
```

### Prefix pattern: `NOM_FR` / `NOM_AN`
```
NOM_FR → "Parc La Fontaine"
NOM_AN → "La Fontaine Park"
```

### No bilingual pair (most common)
Most fields are French-only. The field name itself is in French:
```
ARROND_NOM → "Ville-Marie"         (borough name, FR only)
Emplacement → "Banquette gazonnée"  (location type, FR only)
Rue → "Rue Sainte-Catherine"        (street name, bilingual by nature)
```

### How to handle French-only fields

1. **Proper nouns** (street names, park names, borough names) — use as-is in both languages. "Rue Sainte-Catherine" stays "Rue Sainte-Catherine" in English output.

2. **Category values** — translate when presenting to English users:
   ```
   INV_TYPE: "H" = "Hors rue" (English: "Off-street")
   INV_TYPE: "R" = "Rue" (English: "Street")
   ```

3. **Data dictionary terms** — translate column descriptions:
   ```
   DHP = "Diamètre à Hauteur de Poitrine"
       → "Diameter at Breast Height" (DBH, standard forestry term)
   ```

---

## Pattern 3: Borough Names / Noms d'arrondissements

Borough names are proper nouns — they are the same in both languages but must be matched exactly (including accents and special characters):

| Code | Full Name |
|------|-----------|
| AHU | Ahuntsic-Cartierville |
| ANJ | Anjou |
| CDN | Côte-des-Neiges–Notre-Dame-de-Grâce |
| LAC | Lachine |
| LAS | LaSalle |
| PLA | Le Plateau-Mont-Royal |
| LSO | Le Sud-Ouest |
| IBI | L'Île-Bizard–Sainte-Geneviève |
| MHM | Mercier–Hochelaga-Maisonneuve |
| MTN | Montréal-Nord |
| OUT | Outremont |
| PRF | Pierrefonds-Roxboro |
| RDP | Rivière-des-Prairies–Pointe-aux-Trembles |
| RPP | Rosemont–La Petite-Patrie |
| STL | Saint-Laurent |
| SLE | Saint-Léonard |
| VER | Verdun |
| VIM | Ville-Marie |
| VSE | Villeray–Saint-Michel–Parc-Extension |

**Watch out:** The `territoire` field in dataset metadata uses these short codes. The `ARROND_NOM` field in data records uses the full name. Capitalization and accent usage may vary between datasets.

**Dash types matter:** Some datasets use en-dash (–) between compound borough names, others use hyphen (-). When filtering, try both or use `LIKE '%Mercier%Hochelaga%'`.

---

## Pattern 4: Output Formatting / Formatage de sortie

### Detecting user language

Determine the user's language from their query. If ambiguous, default to the language they wrote in.

### Presenting results bilingually

When bilingual fields are available:
```
🌳 Silver Maple / Érable argenté
   Diameter: 45cm | Borough: Ville-Marie
```

When only French data available, present it naturally:
```
📍 Location: Banquette gazonnée (grassy median)
   Street: Rue Sainte-Catherine
```

### Units and conventions
- Distances: metric (km, m) — Montréal uses metric
- Coordinates: WGS84 (latitude, longitude) preferred; some datasets use NAD 83 MTM Zone 8
- Dates: ISO 8601 (`2024-01-15`) or Montréal convention (`15 janvier 2024` / `January 15, 2024`)
- Currency: Canadian dollars (CAD / $)

---

## Pattern 5: API Metadata Language / Langue des métadonnées API

### Dataset metadata
- `title` — French (always)
- `notes` — French (always), often includes detailed data dictionary
- `tags` — French (always)
- `resources[].name` — French (always)
- `resources[].description` — French (always)
- `groups[].title` — French (always)
- `organization.title` — French (proper name)

### The portal itself
- `donnees.montreal.ca` — French interface
- `donnees.montreal.ca/en` — English interface
- API responses are language-independent (same JSON regardless of language)

### Practical implication
When using `package_search`, always compose queries in French for best results. If the user asks in English, translate the search terms to French, run the query, then present results in English.

---

## Common Translation Table: Dataset Field Names

These are recurring field names across multiple datasets:

| French Field | English Meaning | Notes |
|---|---|---|
| NOM | Name | Often a proper noun |
| ARROND / ARROND_NOM | Borough / Borough name | |
| Rue | Street | |
| No_civique | Civic number (house #) | |
| Latitude / Longitude | Same in both languages | WGS84 |
| Coord_X / Coord_Y | X/Y Coordinates | NAD 83 MTM8 |
| Date_debut / Date_fin | Start date / End date | |
| Date_Releve | Survey date | |
| Date_Plantation | Planting date | |
| Statut | Status | |
| Type | Type | |
| Description | Description | Usually in French |
| Adresse | Address | |
| Code_postal | Postal code | |
| Superficie | Area (m²) | |
| Population | Population | |

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | N/A — this is an agent-side skill, not a data source |
| **Government level** | Applies across all tiers (municipal, provincial, federal) |
| **Jurisdiction** | Montréal / Québec |
| **Legal context** | Québec's Charter of the French Language (Bill 101) makes French the official language. All government data is published in French first; English availability varies. |
| **Last verified** | March 2026 |

**Accountability note:** When presenting translated field names or values, the agent should indicate when it is providing its own translation vs. using an official bilingual field (e.g., `Essence_fr` / `Essence_ang`). Never present an agent translation as official government content.

---

## Related Skills / Compétences connexes

- `understand-ckan` — API conventions
- `discover-datasets` — Search in the right language
- `borough-context` — Full borough reference with boundaries
- `error-recovery` — Handle encoding and accent issues
