# Données ouvertes de Montréal pour agents IA

Une hiérarchie de compétences composable qui donne aux agents IA un accès natif aux 397 jeux de données et 918 ressources interrogeables de Montréal — arbres, transport, permis, criminalité, budget, et plus encore.

*A composable skill hierarchy that gives AI agents native access to Montréal's 397 open datasets and 918 queryable resources — trees, transit, permits, crime, budget, and more.*

---

## Démarrage rapide

### Claude Code

```bash
# 1. Cloner le dépôt
git clone https://github.com/alistaircroll/montreal-open-data.git
cd montreal-open-data

# 2. Installer la dépendance MCP
pip install mcp

# 3. Enregistrer le serveur MCP (9 outils d'accès aux données)
claude mcp add --transport stdio montreal-data -- python3 mcp/read-server/server.py

# 4. Installer les compétences (connaissances et contexte pour votre agent)
ln -s "$(pwd)/skills" ~/.claude/skills/montreal-open-data

# 5. Générer les fichiers de référence locaux
python3 scripts/setup.py
python3 scripts/catalog-refresh.py
```

### Claude Desktop

Ajouter à votre `claude_desktop_config.json` :
```json
{
  "mcpServers": {
    "montreal-data": {
      "command": "python3",
      "args": ["/chemin/vers/montreal-open-data/mcp/read-server/server.py"]
    }
  }
}
```

### Cursor / Autres clients MCP

```json
{
  "mcpServers": {
    "montreal-data": {
      "command": "python3",
      "args": ["mcp/read-server/server.py"],
      "cwd": "/chemin/vers/montreal-open-data"
    }
  }
}
```

### Vérifier l'installation

```bash
claude mcp list                     # Devrait afficher montreal-data
python3 scripts/health-check.py     # Devrait afficher tous les points d'accès OK
```

### Première requête

Une fois installé, posez vos questions naturellement :

> « Combien d'arbres y a-t-il dans le Plateau? »
> « Quels crimes ont été signalés près de chez moi? »
> « How many trees are there in the Plateau? »
> « Show me building permits in my neighborhood this month. »

L'agent utilise les compétences pour le contexte et les outils MCP pour l'accès aux données, présentant les résultats dans votre langue.

---

## Contenu

### 20 compétences dans 5 catégories

**Noyau** (4 compétences) — Fonctionne avec tout portail CKAN :
- `understand-ckan` — Référence API (points d'accès, pagination, conventions)
- `discover-datasets` — Recherche dans le catalogue (397 jeux de données)
- `query-dataset` — Requêtes SQL DataStore (filtres, agrégation, pagination)
- `download-resource` — Téléchargement de fichiers (CSV, GeoJSON, Shapefile, GBFS, GTFS)

**Domaines** (7 compétences) — Expertise spécifique à Montréal :
- `transit` — STM bus/métro, BIXI vélopartage, Exo trains de banlieue
- `environment` — 333 556 arbres, qualité de l'air, espaces verts, canopée
- `permits-and-planning` — Permis de construction, zonage, évaluation foncière
- `safety` — Criminalité, requêtes 311, interventions incendie, collisions routières
- `budget-and-finance` — Budget de fonctionnement, contrats, subventions, taux de taxation
- `culture-and-recreation` — Parcs, sports, murales, patinoires
- `infrastructure` — Chaussées, déneigement, collecte des déchets, API SOAP Planif-Neige

**Géographique** (3 compétences) :
- `borough-context` — 19 arrondissements + 15 municipalités, alias, coordonnées
- `address-geocoding` — Géocodage Nominatim, conversion NAD83 MTM8
- `spatial-queries` — Recherche par rayon (boîte englobante + Haversine)

**Analyse** (3 compétences) :
- `cross-dataset-joins` — Jointures entre jeux de données (arbres + 311 + incendie par arrondissement)
- `time-series` — Patrons temporels, saisonnalité montréalaise
- `visualization` — Tableaux texte, SVG, cartes, export CSV, React/Recharts

**Méta** (3 compétences) :
- `bilingual-handling` — Navigation français/anglais (toutes les métadonnées sont en français)
- `error-recovery` — Diagnostic et récupération d'erreurs API (403, 409, timeout)
- `data-freshness` — Calendriers de mise à jour, détection de données périmées

### 4 scripts

| Script | Description |
|--------|-------------|
| `scripts/setup.py` | Assistant d'intégration : vérification de santé + configuration des clés API |
| `scripts/health-check.py` | Valider les 9 points d'accès de données |
| `scripts/catalog-refresh.py` | Extraire le catalogue à jour → fichiers JSON de référence |
| `scripts/field-inspector.py` | Découvrir les noms de champs réels d'un jeu de données |

### 5 fichiers de référence (générés)

| Fichier | Contenu |
|---------|---------|
| `reference/dataset-catalog.json` | Les 397 jeux de données avec métadonnées |
| `reference/endpoint-registry.json` | Les 918 UUID de ressources DataStore |
| `reference/borough-lookup.json` | Codes, noms, alias et coordonnées des arrondissements |
| `reference/org-summary.json` | Jeux de données par organisation |
| `reference/catalog-stats.json` | Horodatage de rafraîchissement + sommaire |

---

## Architecture

```
montreal-open-data/
├── skills/
│   ├── core/           ← Charger en premier. Fonctionne avec tout portail CKAN.
│   ├── domains/        ← Charger par sujet. Expertise spécifique à Montréal.
│   ├── geo/            ← Charger pour les requêtes géographiques.
│   ├── analysis/       ← Jointures inter-données, séries temporelles, visualisation.
│   └── meta/           ← Langue, erreurs, fraîcheur des données.
├── mcp/read-server/    ← Serveur MCP : 9 outils bilingues.
├── reference/          ← JSON lisible par machine pour recherches rapides.
├── scripts/            ← Automatisation (installation, santé, catalogue, inspection).
├── plugin.json         ← Manifeste de plugin pour Claude Code.
├── SETUP.md            ← Guide d'intégration lisible par humain et agent.
└── .gitignore
```

Les compétences sont livrées sous forme de fichiers SKILL.md composables que les agents chargent à la demande.

---

## Sources de données

**Principale :** Portail de données ouvertes de la Ville de Montréal
- Portail : [donnees.montreal.ca](https://donnees.montreal.ca)
- API : CKAN Action API v3
- Licence : CC BY 4.0
- 397 jeux de données de 6 organisations

### Serveur MCP (9 outils bilingues)

`search_datasets` · `query_dataset` · `get_dataset_fields` · `get_borough_info` ·
`find_nearby` · `bixi_stations` · `dataset_stats` · `list_datasets_by_topic` · `health_check`

Voir `mcp/read-server/README.md` pour les détails et la configuration avancée.

---

**Aussi couvert :**
- BIXI vélopartage (GBFS — public, sans authentification)
- STM horaires bus/métro (GTFS statique — public) et temps réel (GTFS-RT — inscription gratuite)
- Exo trains de banlieue (GTFS — public)
- Planif-Neige déneigement (API SOAP — public)
- Données Québec portail provincial (CKAN — public)

---

## Feuille de route

- [x] Phase 1 : Compétences de base (CKAN, découverte, requête, bilingue)
- [x] Phase 2 : Compétences de domaine (transport, environnement, permis, sécurité, budget, culture, infrastructure)
- [x] Phase 3 : Scripts + données de référence (catalogue, santé, inspecteur de champs, arrondissements)
- [x] Phase 4 : Compétences d'analyse (jointures inter-données, séries temporelles, visualisation)
- [x] Phase 5 : Serveur MCP — 9 outils d'accès déterministe aux données (recherche, SQL, spatial, BIXI, arrondissements)
- [ ] Phase 6 : Délégation citoyen-agent (actions municipales authentifiées)

---

## Contribuer

Les contributions sont les bienvenues!

1. Faire un fork de ce dépôt
2. Ajouter ou améliorer un fichier SKILL.md
3. Tester avec l'API en direct : `python3 scripts/health-check.py`
4. Soumettre une demande de tirage (*pull request*)

Voir `SETUP.md` pour la spécification du format de compétence et le guide d'architecture.

---

## Licence

CC BY 4.0, correspondant à la licence de données ouvertes de la Ville de Montréal.

*Construit avec soin pour la ville que j'adore. / Built with care for the city I love.*
