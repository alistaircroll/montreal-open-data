#!/usr/bin/env python3
"""
Montreal Open Data — MCP Read Server
======================================
A Model Context Protocol server that gives AI agents deterministic, tool-based
access to Montréal's 397+ open datasets.

This is the Phase 5 execution layer: skills provide documentation and context,
this server provides the actual tools agents call.

Tools:
  search_datasets     — Find datasets by keyword (bilingual FR/EN)
  query_dataset       — SQL query against any DataStore resource
  get_dataset_fields  — Inspect field names/types for a resource
  get_borough_info    — Look up borough by name, alias, or code
  find_nearby         — Find records near a lat/lon point
  bixi_stations       — Real-time BIXI station availability
  dataset_stats       — Quick stats for a resource
  list_datasets_by_topic — Browse by category
  health_check        — Test endpoint connectivity

Usage:
  # stdio transport (for Claude Code, Cursor, etc.)
  python3 mcp/read-server/server.py

  # Or register in Claude Code:
  # claude mcp add montreal-data python3 mcp/read-server/server.py

Requires: pip install mcp
"""

import json
import math
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server Setup
# ---------------------------------------------------------------------------
mcp = FastMCP("montreal-open-data")

CKAN_BASE = "https://donnees.montreal.ca/api/3/action"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REF_DIR = REPO_ROOT / "reference"
USER_AGENT = "MontrealOpenData-MCP/0.5"
REQUEST_TIMEOUT = 20

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """Fetch JSON from a URL with standard headers."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url[:200]}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}", "url": url[:200]}
    except TimeoutError:
        return {"error": "Request timed out", "url": url[:200]}


def _ckan_action(action: str, params: dict = None) -> dict:
    """Call a CKAN API action."""
    url = f"{CKAN_BASE}/{action}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return _fetch_json(url)


def _ckan_sql(sql: str) -> dict:
    """Execute a DataStore SQL query."""
    url = f"{CKAN_BASE}/datastore_search_sql?sql={urllib.parse.quote(sql)}"
    return _fetch_json(url, timeout=30)


def _load_reference(filename: str) -> Optional[dict]:
    """Load a reference JSON file if it exists."""
    path = REF_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in meters between two WGS84 points."""
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bbox(lat: float, lon: float, radius_km: float) -> dict:
    """Bounding box for a radius around a point."""
    dlat = radius_km / 111.32
    dlon = radius_km / (111.32 * math.cos(math.radians(lat)))
    return {
        "lat_min": lat - dlat, "lat_max": lat + dlat,
        "lon_min": lon - dlon, "lon_max": lon + dlon,
    }


# Bilingual keyword translation for search (EN → FR)
# All CKAN metadata is French. See: skills/meta/bilingual-handling
FR_KEYWORDS = {
    # Infrastructure municipale
    "tree": "arbre", "trees": "arbres", "park": "parc", "parks": "parcs",
    "road": "route", "roads": "routes", "street": "rue", "bridge": "pont",
    "sidewalk": "trottoir", "bike path": "piste cyclable",
    "building": "bâtiment", "water main": "aqueduc",
    # Gouvernement & services
    "permit": "permis", "permits": "permis", "budget": "budget",
    "contract": "contrat", "contracts": "contrats", "tax": "taxation",
    "election": "élection", "elections": "élections", "bylaw": "règlement",
    "complaint": "plainte", "request": "requête",
    "snow removal": "déneigement", "snow": "neige",
    "garbage": "déchet", "waste": "déchet",
    # Environnement
    "air quality": "qualité air", "water quality": "qualité eau",
    "green space": "espace vert", "canopy": "canopée",
    "pollution": "pollution", "garden": "jardin",
    "heat island": "îlot chaleur",
    # Transport
    "bus": "autobus", "metro": "métro", "subway": "métro",
    "transit": "transport", "bike": "vélo", "bicycle": "vélo",
    "parking": "stationnement", "traffic": "circulation",
    "collision": "collision", "accident": "accident",
    # Sécurité
    "crime": "criminalité", "fire": "incendie", "police": "police",
    # Culture & loisirs
    "library": "bibliothèque", "pool": "piscine", "swimming": "piscine",
    "rink": "patinoire", "arena": "aréna", "mural": "murale",
    "sport": "sport", "culture": "culture",
    # Construction
    "construction": "construction", "zoning": "zonage",
}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_datasets(query: str, limit: int = 10) -> str:
    """Search Montréal's open data catalog by keyword. / Chercher dans le catalogue de données ouvertes par mot-clé.

    Automatically translates English keywords to French for better results,
    since all dataset metadata is in French.
    Traduit automatiquement les mots-clés anglais en français, puisque
    toutes les métadonnées sont en français.

    Args:
        query: Search term (English or French) / Terme de recherche (anglais ou français). Ex: "trees", "arbres", "crime", "vélo"
        limit: Maximum results (default 10, max 50) / Résultats max (défaut 10, max 50)
    """
    limit = min(limit, 50)

    # Translate English keywords to French
    q = query.lower().strip()
    for en, fr in FR_KEYWORDS.items():
        if en in q:
            q = q.replace(en, fr)

    data = _ckan_action("package_search", {"q": q, "rows": limit})
    if "error" in data:
        return json.dumps(data)

    if not data.get("success"):
        return json.dumps({"error": "Search failed", "detail": data})

    results = []
    for ds in data["result"]["results"]:
        resources = []
        for r in ds.get("resources", []):
            if r.get("datastore_active"):
                resources.append({
                    "id": r["id"],
                    "name": r.get("name", ""),
                    "format": r.get("format", ""),
                })

        results.append({
            "slug": ds["name"],
            "title": ds.get("title", ""),
            "organization": ds.get("organization", {}).get("title", ""),
            "num_resources": len(ds.get("resources", [])),
            "queryable_resources": resources,
            "tags": [t["name"] for t in ds.get("tags", [])],
        })

    return json.dumps({
        "total_matches": data["result"]["count"],
        "showing": len(results),
        "results": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def query_dataset(resource_id: str, sql_where: str = "", columns: str = "*",
                  group_by: str = "", order_by: str = "", limit: int = 100) -> str:
    """Query a Montréal open data resource using SQL. / Interroger une ressource avec SQL.

    Builds and executes a SQL query against the CKAN DataStore. All fields are
    text — use CAST() for numeric comparisons.
    Construit et exécute une requête SQL. Tous les champs sont texte —
    utiliser CAST() pour les comparaisons numériques.

    Args:
        resource_id: UUID de la ressource DataStore (from search_datasets / de search_datasets)
        sql_where: Clause WHERE (sans 'WHERE'). Ex: '"ARROND_NOM" LIKE '%Plateau%''
        columns: Colonnes SELECT. Défaut "*". Ex: '"ARROND_NOM", COUNT(*) as n'
        group_by: Clause GROUP BY (sans 'GROUP BY'). Ex: '"ARROND_NOM"'
        order_by: Clause ORDER BY (sans 'ORDER BY'). Ex: 'n DESC'
        limit: Lignes max (défaut 100, max 5000) / Max rows (default 100, max 5000)
    """
    limit = min(limit, 5000)

    sql = f'SELECT {columns} FROM "{resource_id}"'
    if sql_where:
        sql += f" WHERE {sql_where}"
    if group_by:
        sql += f" GROUP BY {group_by}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    sql += f" LIMIT {limit}"

    data = _ckan_sql(sql)
    if "error" in data:
        # Provide helpful error context / Contexte d'erreur utile
        return json.dumps({
            "error": data["error"],
            "sql": sql,
            "hint": "Field names are case-sensitive, numeric fields need CAST(), 409 = query too complex (add date filter). / Les noms de champs sont sensibles à la casse, les champs numériques nécessitent CAST(), 409 = requête trop complexe (ajouter un filtre de date)."
        })

    if not data.get("success"):
        return json.dumps({"error": "Query failed", "sql": sql, "detail": str(data)[:500]})

    records = data["result"]["records"]
    # Remove internal _id and _full_text fields
    for r in records:
        r.pop("_id", None)
        r.pop("_full_text", None)

    return json.dumps({
        "sql": sql,
        "record_count": len(records),
        "records": records,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_dataset_fields(resource_id: str) -> str:
    """Get field names, types, and sample values for a DataStore resource. / Obtenir les noms, types et exemples de champs d'une ressource.

    Essential for building correct queries — field names are case-sensitive
    and types are often 'text' even for numeric data.
    Essentiel pour construire des requêtes correctes — les noms de champs
    sont sensibles à la casse et les types sont souvent 'text' même pour les nombres.

    Args:
        resource_id: UUID de la ressource DataStore
    """
    data = _ckan_action("datastore_search", {
        "resource_id": resource_id,
        "limit": 3,
    })
    if "error" in data:
        return json.dumps(data)

    if not data.get("success"):
        return json.dumps({"error": "Cannot access resource", "resource_id": resource_id})

    fields = []
    samples = data["result"].get("records", [])
    for f in data["result"].get("fields", []):
        if f["id"] == "_id":
            continue
        field_info = {
            "name": f["id"],
            "type": f.get("type", "unknown"),
            "samples": [str(s.get(f["id"], ""))[:80] for s in samples if s.get(f["id"]) is not None][:3],
        }
        fields.append(field_info)

    return json.dumps({
        "resource_id": resource_id,
        "total_records": data["result"].get("total", 0),
        "field_count": len(fields),
        "fields": fields,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_borough_info(name: str) -> str:
    """Look up a Montréal borough by name, alias, or code. / Chercher un arrondissement par nom, alias ou code.

    Handles common aliases: "downtown" → Ville-Marie, "HoMa" →
    Mercier–Hochelaga-Maisonneuve, "the Plateau" → Le Plateau-Mont-Royal,
    "centre-ville" → Ville-Marie, "le Plateau" → Le Plateau-Mont-Royal.

    Args:
        name: Nom, alias ou code. Ex: "Plateau", "downtown", "centre-ville", "AHU", "Mile End"
    """
    lookup = _load_reference("borough-lookup.json")
    if not lookup:
        return json.dumps({"error": "borough-lookup.json not found. Run: python3 scripts/catalog-refresh.py"})

    search = name.lower().strip()

    # Check aliases first
    aliases = lookup.get("aliases", {})
    if search in aliases:
        code = aliases[search]
        if isinstance(code, list):
            # Multiple boroughs (e.g., "west island")
            matches = [b for b in lookup["boroughs"] if b["code"] in code]
            return json.dumps({"query": name, "matches": matches, "note": "Multiple boroughs match this alias"}, ensure_ascii=False, indent=2)
        else:
            for b in lookup["boroughs"]:
                if b["code"] == code:
                    return json.dumps({"query": name, "borough": b}, ensure_ascii=False, indent=2)

    # Check code
    for b in lookup["boroughs"]:
        if b["code"].lower() == search:
            return json.dumps({"query": name, "borough": b}, ensure_ascii=False, indent=2)

    # Check name (fuzzy)
    for b in lookup["boroughs"]:
        if search in b["name"].lower() or search in b.get("short", "").lower():
            return json.dumps({"query": name, "borough": b}, ensure_ascii=False, indent=2)

    # Check municipalities
    for m in lookup.get("municipalities", []):
        if search in m["name"].lower():
            return json.dumps({"query": name, "municipality": m, "note": "This is a reconstituted municipality, not a borough"}, ensure_ascii=False, indent=2)

    return json.dumps({"query": name, "error": "Borough not found / Arrondissement non trouvé", "hint": "Try a shorter name or alias / Essayez un nom plus court ou un alias"})


@mcp.tool()
def find_nearby(resource_id: str, latitude: float, longitude: float,
                radius_km: float = 1.0, lat_field: str = "Latitude",
                lon_field: str = "Longitude", limit: int = 100) -> str:
    """Find records within a radius of a point. / Trouver les enregistrements dans un rayon autour d'un point.

    Uses bounding box server-side + Haversine client-side for precision.
    Utilise un filtre par boîte englobante côté serveur + Haversine côté client.

    Args:
        resource_id: UUID de la ressource DataStore
        latitude: Latitude du point central (WGS84)
        longitude: Longitude du point central (WGS84)
        radius_km: Rayon en km (défaut 1.0, max 10) / Radius in km (default 1.0, max 10)
        lat_field: Nom du champ latitude (défaut "Latitude")
        lon_field: Nom du champ longitude (défaut "Longitude")
        limit: Résultats max (défaut 100, max 1000)
    """
    radius_km = min(radius_km, 10.0)
    limit = min(limit, 1000)
    b = _bbox(latitude, longitude, radius_km)

    sql = f'''SELECT * FROM "{resource_id}"
        WHERE CAST("{lat_field}" AS FLOAT) BETWEEN {b["lat_min"]} AND {b["lat_max"]}
          AND CAST("{lon_field}" AS FLOAT) BETWEEN {b["lon_min"]} AND {b["lon_max"]}
          AND "{lat_field}" IS NOT NULL
        LIMIT {limit}'''

    data = _ckan_sql(sql)
    if "error" in data:
        return json.dumps({
            "error": data["error"],
            "hint": "Check field names / Vérifiez les noms de champs. Common: Latitude/Longitude, LOC_LAT/LOC_LONG. Use get_dataset_fields / Utilisez get_dataset_fields."
        })

    if not data.get("success"):
        return json.dumps({"error": "Query failed", "detail": str(data)[:500]})

    # Calculate actual distances and filter to circle
    records = data["result"]["records"]
    results = []
    for r in records:
        try:
            rlat = float(r[lat_field])
            rlon = float(r[lon_field])
            dist = _haversine_m(latitude, longitude, rlat, rlon)
            if dist <= radius_km * 1000:
                r.pop("_id", None)
                r.pop("_full_text", None)
                r["_distance_m"] = round(dist)
                results.append(r)
        except (ValueError, TypeError, KeyError):
            continue

    results.sort(key=lambda x: x["_distance_m"])

    return json.dumps({
        "center": {"lat": latitude, "lon": longitude},
        "radius_km": radius_km,
        "found": len(results),
        "records": results[:limit],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def bixi_stations(latitude: float = 45.508, longitude: float = -73.561,
                  radius_km: float = 1.0, min_bikes: int = 0) -> str:
    """Real-time BIXI bike availability near a location. / Disponibilité BIXI en temps réel près d'un lieu.

    BIXI operates April–November. Returns 0 bikes in winter (normal).
    BIXI opère d'avril à novembre. Retourne 0 vélo en hiver (normal).

    Args:
        latitude: Latitude (défaut : centre-ville de Montréal)
        longitude: Longitude (défaut : centre-ville de Montréal)
        radius_km: Rayon en km (défaut 1.0, max 5) / Radius in km (default 1.0, max 5)
        min_bikes: Vélos min disponibles (défaut 0) / Min bikes available (default 0)
    """
    radius_km = min(radius_km, 5.0)

    info = _fetch_json("https://gbfs.velobixi.com/gbfs/en/station_information.json")
    status = _fetch_json("https://gbfs.velobixi.com/gbfs/en/station_status.json")

    if "error" in info or "error" in status:
        return json.dumps({"error": "Cannot reach BIXI GBFS feed / Impossible d'accéder au flux BIXI", "hint": "BIXI operates April–November / BIXI opère d'avril à novembre."})

    # Build availability lookup
    avail = {}
    for s in status.get("data", {}).get("stations", []):
        avail[s["station_id"]] = {
            "bikes": s.get("num_bikes_available", 0),
            "docks": s.get("num_docks_available", 0),
            "ebikes": s.get("num_ebikes_available", 0),
        }

    # Find nearby stations
    stations = []
    for s in info.get("data", {}).get("stations", []):
        dist = _haversine_m(latitude, longitude, s["lat"], s["lon"])
        if dist <= radius_km * 1000:
            a = avail.get(s["station_id"], {"bikes": 0, "docks": 0, "ebikes": 0})
            if a["bikes"] >= min_bikes:
                stations.append({
                    "name": s["name"],
                    "lat": s["lat"],
                    "lon": s["lon"],
                    "distance_m": round(dist),
                    "bikes_available": a["bikes"],
                    "ebikes_available": a["ebikes"],
                    "docks_available": a["docks"],
                    "capacity": s.get("capacity", 0),
                })

    stations.sort(key=lambda x: x["distance_m"])

    return json.dumps({
        "center": {"lat": latitude, "lon": longitude},
        "radius_km": radius_km,
        "total_stations_found": len(stations),
        "stations": stations[:20],
        "last_updated": status.get("last_updated", "unknown"),
        "note": "BIXI operates April-November. 0 bikes in winter is normal.",
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def dataset_stats(resource_id: str) -> str:
    """Quick stats for a resource: record count, fields, sample. / Stats rapides : nombre d'enregistrements, champs, exemple.

    Args:
        resource_id: UUID de la ressource DataStore
    """
    data = _ckan_action("datastore_search", {
        "resource_id": resource_id,
        "limit": 1,
    })
    if "error" in data:
        return json.dumps(data)

    if not data.get("success"):
        return json.dumps({"error": "Cannot access resource", "resource_id": resource_id})

    result = data["result"]
    fields = [{"name": f["id"], "type": f.get("type", "?")} for f in result.get("fields", []) if f["id"] != "_id"]

    return json.dumps({
        "resource_id": resource_id,
        "total_records": result.get("total", 0),
        "field_count": len(fields),
        "fields": fields,
        "sample": result.get("records", [{}])[0] if result.get("records") else {},
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def list_datasets_by_topic(topic: str) -> str:
    """Browse datasets by topic. / Parcourir les jeux de données par thème.

    EN topics: transit, trees, crime, permits, 311, fire, budget,
    contracts, parks, culture, infrastructure, environment, elections, health.
    FR thèmes: transport, arbres, criminalité, permis, 311, incendie, budget,
    contrats, parcs, culture, infrastructure, environnement, élections, santé.

    Args:
        topic: Topic / Thème (English or French / anglais ou français)
    """
    topic_keywords = {
        # English keys
        "transit": "transport OR autobus OR métro OR vélo OR bixi OR stm",
        "trees": "arbre",
        "crime": "criminalité OR actes criminels OR police",
        "permits": "permis OR construction OR bâtiment",
        "311": "requête 311 OR demande service",
        "fire": "incendie OR pompier OR caserne",
        "budget": "budget OR dépense OR financ",
        "contracts": "contrat OR fournisseur",
        "parks": "parc OR espace vert",
        "culture": "culture OR bibliothèque OR art OR murale",
        "infrastructure": "chaussée OR trottoir OR pont OR aqueduc OR égout",
        "environment": "environnement OR arbre OR qualité air OR canopée",
        "elections": "élection OR scrutin OR district",
        "health": "santé OR alimentaire",
        # French keys → same CKAN queries
        "transport": "transport OR autobus OR métro OR vélo OR bixi OR stm",
        "arbres": "arbre",
        "criminalité": "criminalité OR actes criminels OR police",
        "permis": "permis OR construction OR bâtiment",
        "incendie": "incendie OR pompier OR caserne",
        "contrats": "contrat OR fournisseur",
        "parcs": "parc OR espace vert",
        "environnement": "environnement OR arbre OR qualité air OR canopée",
        "élections": "élection OR scrutin OR district",
        "santé": "santé OR alimentaire",
        "sécurité": "criminalité OR incendie OR collision OR police",
        "vélo": "vélo OR cyclable OR bixi",
        "logement": "logement OR habitation OR propriété",
        "eau": "eau OR aqueduc OR égout",
        "déneigement": "neige OR déneigement OR sel",
        "déchet": "déchet OR collecte OR ordure OR recyclage",
    }

    q = topic_keywords.get(topic.lower().strip(), topic)
    data = _ckan_action("package_search", {"q": q, "rows": 20})

    if "error" in data or not data.get("success"):
        return json.dumps({"error": "Search failed", "topic": topic})

    results = []
    for ds in data["result"]["results"]:
        has_ds = any(r.get("datastore_active") for r in ds.get("resources", []))
        results.append({
            "slug": ds["name"],
            "title": ds.get("title", ""),
            "queryable": has_ds,
        })

    return json.dumps({
        "topic": topic,
        "total_matches": data["result"]["count"],
        "datasets": results,
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def health_check() -> str:
    """Test connectivity to all Montréal data endpoints. / Tester la connectivité aux points d'accès de données.

    Returns status of CKAN portal, DataStore, BIXI, STM, and Données Québec.
    Retourne l'état du portail CKAN, DataStore, BIXI, STM et Données Québec.
    """
    endpoints = [
        ("ckan_portal", f"{CKAN_BASE}/site_read", True),
        ("ckan_search", f"{CKAN_BASE}/package_search?rows=0", True),
        ("datastore", f"{CKAN_BASE}/datastore_search?resource_id=64e28fe6-ef37-437a-972d-d1d3f1f7d891&limit=0", True),
        ("bixi_gbfs", "https://gbfs.velobixi.com/gbfs/gbfs.json", False),
        ("donnees_quebec", "https://www.donneesquebec.ca/recherche/api/3/action/site_read", False),
    ]

    results = []
    for name, url, critical in endpoints:
        start = datetime.now(timezone.utc)
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", USER_AGENT)
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                results.append({"name": name, "status": "ok", "latency_s": round(elapsed, 2), "critical": critical})
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            results.append({"name": name, "status": "error", "error": str(e)[:80], "latency_s": round(elapsed, 2), "critical": critical})

    ok_count = sum(1 for r in results if r["status"] == "ok")
    crit_fail = sum(1 for r in results if r["status"] != "ok" and r["critical"])

    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "ok": ok_count,
        "critical_failures": crit_fail,
        "endpoints": results,
    }, indent=2)


# ---------------------------------------------------------------------------
# Resources (static context for agents)
# ---------------------------------------------------------------------------

@mcp.resource("montreal://boroughs")
def get_boroughs() -> str:
    """List all 19 Montréal boroughs with codes and coordinates. / Les 19 arrondissements avec codes et coordonnées."""
    lookup = _load_reference("borough-lookup.json")
    if lookup:
        return json.dumps(lookup["boroughs"], ensure_ascii=False, indent=2)
    return json.dumps({"error": "borough-lookup.json not found"})


@mcp.resource("montreal://catalog-stats")
def get_catalog_stats() -> str:
    """Summary statistics about the Montréal open data catalog. / Statistiques sommaires du catalogue de données ouvertes."""
    stats = _load_reference("catalog-stats.json")
    if stats:
        return json.dumps(stats, ensure_ascii=False, indent=2)
    return json.dumps({"error": "catalog-stats.json not found. Run: python3 scripts/catalog-refresh.py"})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
