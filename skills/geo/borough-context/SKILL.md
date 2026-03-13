---
name: borough-context
description: |
  Reference data for Montréal's 19 boroughs and 15 reconstituted municipalities.
  Names (FR/EN), codes, approximate boundaries, and how they appear in datasets.
  / Données de référence pour les 19 arrondissements et 15 municipalités
  reconstituées de Montréal. Noms (FR/AN), codes, limites et leur apparence
  dans les jeux de données.
triggers:
  - borough, arrondissement, neighborhood, district, area, zone, CDN, Plateau
  - arrondissement, quartier, district, secteur, zone
---

# Borough Context / Contexte des arrondissements

## Overview / Aperçu

The Montréal agglomeration is composed of:
- **19 boroughs** (arrondissements) that are part of the City of Montréal
- **15 reconstituted municipalities** that share some agglomeration services

L'agglomération de Montréal comprend 19 arrondissements et 15 municipalités reconstituées.

---

## The 19 Boroughs / Les 19 arrondissements

| # | Full Name | Code | Common Short Name | Approx. Center (lat, lon) |
|---|-----------|------|------------------|--------------------------|
| 1 | Ahuntsic-Cartierville | AHU | Ahuntsic | 45.548, -73.662 |
| 2 | Anjou | ANJ | Anjou | 45.601, -73.558 |
| 3 | Côte-des-Neiges–Notre-Dame-de-Grâce | CDN | CDN-NDG | 45.479, -73.625 |
| 4 | Lachine | LAC | Lachine | 45.437, -73.680 |
| 5 | LaSalle | LAS | LaSalle | 45.432, -73.632 |
| 6 | Le Plateau-Mont-Royal | PLA | The Plateau | 45.523, -73.574 |
| 7 | Le Sud-Ouest | LSO | Sud-Ouest / SW | 45.476, -73.580 |
| 8 | L'Île-Bizard–Sainte-Geneviève | IBI | Île-Bizard | 45.498, -73.866 |
| 9 | Mercier–Hochelaga-Maisonneuve | MHM | Mercier-HM / HoMa | 45.558, -73.537 |
| 10 | Montréal-Nord | MTN | Mtl-Nord | 45.596, -73.614 |
| 11 | Outremont | OUT | Outremont | 45.518, -73.610 |
| 12 | Pierrefonds-Roxboro | PRF | Pierrefonds | 45.489, -73.834 |
| 13 | Rivière-des-Prairies–Pointe-aux-Trembles | RDP | RDP-PAT | 45.631, -73.524 |
| 14 | Rosemont–La Petite-Patrie | RPP | Rosemont / RPP | 45.542, -73.585 |
| 15 | Saint-Laurent | STL | Saint-Laurent | 45.503, -73.709 |
| 16 | Saint-Léonard | SLE | Saint-Léonard | 45.581, -73.595 |
| 17 | Verdun | VER | Verdun | 45.454, -73.571 |
| 18 | Ville-Marie | VIM | Downtown / Centre-ville | 45.508, -73.561 |
| 19 | Villeray–Saint-Michel–Parc-Extension | VSE | VSP / Villeray | 45.558, -73.616 |

## The 15 Reconstituted Municipalities / Municipalités reconstituées

These are independent municipalities within the agglomeration. They share some services (police, fire, water, transit) but have their own councils:

| Municipality | On Island? | Notes |
|---|---|---|
| Baie-D'Urfé | Yes | West island |
| Beaconsfield | Yes | West island |
| Côte-Saint-Luc | Yes | Near CDN-NDG |
| Dollard-Des Ormeaux | Yes | West island |
| Dorval | Yes | Airport area |
| Hampstead | Yes | Near CDN-NDG |
| Kirkland | Yes | West island |
| L'Île-Dorval | Yes | Tiny island municipality |
| Montréal-Est | Yes | East end |
| Montréal-Ouest | Yes | Near Lachine |
| Mont-Royal | Yes | Surrounded by MTL |
| Pointe-Claire | Yes | West island |
| Sainte-Anne-de-Bellevue | Yes | Western tip |
| Senneville | Yes | Western tip |
| Westmount | Yes | Near VIM/CDN |

---

## How Boroughs Appear in Datasets / Apparence dans les jeux de données

**The big problem:** Borough names are inconsistent across datasets.

### In dataset metadata (the `territoire` field):
Uses short codes: `["AHU", "CDN", "VIM"]`

### In data records (`ARROND_NOM` or similar fields):
Uses full names, but formatting varies:

```
"Ville-Marie"                              ← most common
"Ville - Marie"                            ← spaces around dash (some datasets)
"Mercier - Hochelaga-Maisonneuve"          ← mixed dash styles
"Mercier–Hochelaga-Maisonneuve"            ← en-dash
"Côte-des-Neiges - Notre-Dame-de-Grâce"   ← with spaces
"CDN-NDG"                                  ← abbreviated
```

### In numeric fields (`ARROND` field):
Some datasets use a borough number (1-19). The numbering is:
```
1 = Ahuntsic-Cartierville
2 = Anjou (confirm — numbering varies by dataset)
...
```
**Do not assume consistent numbering.** Always check the specific dataset's values.

### Best practice for filtering:
Use `LIKE` patterns that are robust to formatting differences:
```sql
-- More robust than exact match
WHERE "ARROND_NOM" LIKE '%Plateau%Royal%'
WHERE "ARROND_NOM" LIKE '%Mercier%Hochelaga%'
WHERE "ARROND_NOM" LIKE '%Notre-Dame%Gr_ce%'  -- underscore matches any char (accent variants)
```

---

## Natural Language to Borough Mapping / Correspondance langage naturel

Users often refer to boroughs informally. Map common terms:

| User says... | Borough |
|---|---|
| "downtown", "centre-ville" | Ville-Marie |
| "the Plateau", "le Plateau" | Le Plateau-Mont-Royal |
| "Mile End" | Le Plateau-Mont-Royal (neighborhood) |
| "Old Montreal", "Vieux-Montréal" | Ville-Marie (neighborhood) |
| "the Village" | Ville-Marie (neighborhood) |
| "Griffintown" | Le Sud-Ouest (neighborhood) |
| "Little Italy", "Petite-Italie" | Rosemont–La Petite-Patrie |
| "HoMa" | Mercier–Hochelaga-Maisonneuve |
| "NDG" | Côte-des-Neiges–Notre-Dame-de-Grâce |
| "the West Island" | Multiple: Pierrefonds-Roxboro, L'Île-Bizard–Sainte-Geneviève, Dorval, etc. |
| "Verdun" | Verdun |
| "Westmount" | NOT a borough — reconstituted municipality |
| "Mont-Royal" / "TMR" | NOT a borough — reconstituted municipality (Ville de Mont-Royal) |

**Important:** Neighborhoods (like Mile End, Griffintown, Old Montréal) are NOT official boroughs. They are informal areas within boroughs. Datasets are indexed by borough, not neighborhood. An agent may need to look up which borough contains the user's neighborhood.

---

## Provenance / Provenance

| Field | Value |
|-------|-------|
| **Publisher** | Ville de Montréal |
| **Government level** | Municipal |
| **Jurisdiction** | Montréal agglomeration |
| **License** | CC BY 4.0 |
| **Contact** | donneesouvertes@montreal.ca |
| **Last verified** | March 2026 |

**Note:** Borough boundaries occasionally change (most recently with the 2002 mergers and 2006 de-mergers). The current 19-borough + 15-municipality structure has been stable since 2006.

---

## Related Skills / Compétences connexes

- `bilingual-handling` — Borough names in both languages
- `spatial-queries` — Point-in-polygon lookups
- `discover-datasets` — Filter datasets by territory/borough
