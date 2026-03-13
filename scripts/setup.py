#!/usr/bin/env python3
"""
Montreal Open Data — Setup & Onboarding / Configuration et intégration
=======================================================================
Run this script after installing the skill to:
  1. Verify your Python environment has required packages
  2. Test connectivity to all data endpoints
  3. Optionally configure API keys for premium feeds (STM real-time, etc.)
  4. Generate a local config file for the agent to read

Exécutez ce script après l'installation pour vérifier la connectivité,
configurer les clés API optionnelles et générer la configuration locale.

Usage:
  python3 scripts/setup.py              # Interactive setup
  python3 scripts/setup.py --check      # Health check only (no prompts)
  python3 scripts/setup.py --lang fr    # Force language to French
  python3 scripts/setup.py --lang en    # Force language to English
"""

import json
import os
import sys
import urllib.request
import urllib.error
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.local.json"

ENDPOINTS = {
    "ckan_portal": {
        "url": "https://donnees.montreal.ca/api/3/action/site_read",
        "required": True,
        "description_en": "Montreal Open Data portal (CKAN API)",
        "description_fr": "Portail de données ouvertes de Montréal (API CKAN)",
    },
    "ckan_dataset_count": {
        "url": "https://donnees.montreal.ca/api/3/action/package_search?rows=0",
        "required": True,
        "description_en": "Dataset catalog search",
        "description_fr": "Recherche dans le catalogue",
    },
    "datastore_sql": {
        "url": 'https://donnees.montreal.ca/api/3/action/datastore_search_sql?sql=SELECT+COUNT(*)+FROM+"64e28fe6-ef37-437a-972d-d1d3f1f7d891"',
        "required": True,
        "description_en": "DataStore SQL queries (tree inventory)",
        "description_fr": "Requêtes SQL DataStore (inventaire des arbres)",
    },
    "bixi_gbfs": {
        "url": "https://gbfs.velobixi.com/gbfs/gbfs.json",
        "required": False,
        "description_en": "BIXI bike-sharing stations (GBFS)",
        "description_fr": "Stations BIXI vélo-partage (GBFS)",
    },
    "stm_gtfs_static": {
        "url": "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip",
        "required": False,
        "description_en": "STM transit schedules (GTFS static)",
        "description_fr": "Horaires STM (GTFS statique)",
        "method": "HEAD",
    },
    "donnees_quebec": {
        "url": "https://www.donneesquebec.ca/recherche/api/3/action/site_read",
        "required": False,
        "description_en": "Données Québec provincial portal",
        "description_fr": "Portail provincial Données Québec",
    },
}

API_KEYS = {
    "stm_realtime": {
        "description_en": "STM real-time bus/metro positions (free registration at portail.developpeurs.stm.info)",
        "description_fr": "Positions en temps réel STM (inscription gratuite sur portail.developpeurs.stm.info)",
        "url": "https://portail.developpeurs.stm.info",
        "env_var": "STM_API_KEY",
        "required": False,
    },
}

# ---------------------------------------------------------------------------
# Strings (bilingual)
# ---------------------------------------------------------------------------
STRINGS = {
    "en": {
        "welcome": "\n🏙️  Montreal Open Data — Setup\n" + "=" * 42,
        "checking": "Checking endpoints...",
        "ok": "✅ OK",
        "fail": "❌ FAIL",
        "skip": "⚠️  SKIP (optional)",
        "results": "\nResults:",
        "all_ok": "✅ All required endpoints are reachable.",
        "some_fail": "❌ Some required endpoints failed. Check your network connection.",
        "optional_fail": "⚠️  Some optional endpoints are unreachable (features will be limited).",
        "api_keys_header": "\n🔑 Optional API Keys",
        "api_key_prompt": "  Enter your {} key (or press Enter to skip): ",
        "api_key_saved": "  ✅ Saved.",
        "api_key_skipped": "  ⏭️  Skipped. You can add it later in config.local.json",
        "config_saved": "\n✅ Config saved to {}",
        "done": "\n🎉 Setup complete! Your agent can now query Montreal's open data.",
        "dataset_count": "   📊 {} datasets available in the catalog",
        "tree_count": "   🌳 {} trees in the inventory",
        "lang_detect": "Language detected: English (override with --lang fr)",
    },
    "fr": {
        "welcome": "\n🏙️  Données ouvertes de Montréal — Configuration\n" + "=" * 52,
        "checking": "Vérification des points d'accès...",
        "ok": "✅ OK",
        "fail": "❌ ÉCHEC",
        "skip": "⚠️  PASSÉ (optionnel)",
        "results": "\nRésultats :",
        "all_ok": "✅ Tous les points d'accès requis sont disponibles.",
        "some_fail": "❌ Certains points d'accès requis ont échoué. Vérifiez votre connexion.",
        "optional_fail": "⚠️  Certains points d'accès optionnels sont indisponibles (fonctionnalités limitées).",
        "api_keys_header": "\n🔑 Clés API optionnelles",
        "api_key_prompt": "  Entrez votre clé {} (ou Entrée pour passer) : ",
        "api_key_saved": "  ✅ Enregistrée.",
        "api_key_skipped": "  ⏭️  Passé. Vous pouvez l'ajouter plus tard dans config.local.json",
        "config_saved": "\n✅ Config enregistrée dans {}",
        "done": "\n🎉 Configuration terminée! Votre agent peut maintenant interroger les données ouvertes.",
        "dataset_count": "   📊 {} jeux de données disponibles dans le catalogue",
        "tree_count": "   🌳 {} arbres dans l'inventaire",
        "lang_detect": "Langue détectée : français (changer avec --lang en)",
    },
}


def detect_language():
    """Detect system language from LANG environment variable."""
    lang = os.environ.get("LANG", "en_US.UTF-8")
    return "fr" if lang.startswith("fr") else "en"


def test_endpoint(name, info):
    """Test a single endpoint. Returns (ok: bool, detail: str)."""
    try:
        method = info.get("method", "GET")
        req = urllib.request.Request(info["url"], method=method)
        req.add_header("User-Agent", "MontrealOpenData-Setup/1.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            if method == "HEAD":
                return True, f"HTTP {resp.status}"
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body) if body.startswith("{") else {}

            # Extract useful counts from known endpoints
            detail = f"HTTP {resp.status}"
            if "result" in data:
                result = data["result"]
                if isinstance(result, dict) and "count" in result:
                    detail += f" ({result['count']} results)"
                elif isinstance(result, dict) and "records" in result:
                    records = result["records"]
                    if records and "count" in records[0]:
                        detail += f" ({records[0]['count']} records)"
            return True, detail
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        return False, str(e)[:80]


def run_health_check(lang, verbose=True):
    """Test all endpoints. Returns (required_ok, optional_ok, details)."""
    s = STRINGS[lang]
    if verbose:
        print(s["checking"])
        print()

    results = {}
    required_ok = True
    optional_ok = True

    for name, info in ENDPOINTS.items():
        ok, detail = test_endpoint(name, info)
        desc = info[f"description_{lang}"]
        results[name] = {"ok": ok, "detail": detail}

        if verbose:
            status = s["ok"] if ok else (s["fail"] if info["required"] else s["skip"])
            print(f"  {status}  {desc}")
            if not ok and verbose:
                print(f"       → {detail}")

        if not ok:
            if info["required"]:
                required_ok = False
            else:
                optional_ok = False

    if verbose:
        print(s["results"])
        if required_ok:
            print(s["all_ok"])
        else:
            print(s["some_fail"])
        if not optional_ok:
            print(s["optional_fail"])

    return required_ok, optional_ok, results


def prompt_api_keys(lang, config):
    """Interactively collect optional API keys."""
    s = STRINGS[lang]
    print(s["api_keys_header"])
    print()

    for key_name, info in API_KEYS.items():
        desc = info[f"description_{lang}"]
        print(f"  {desc}")
        print(f"  🔗 {info['url']}")

        # Check environment variable first
        env_val = os.environ.get(info["env_var"], "")
        if env_val:
            print(f"  ✅ Found in environment variable ${info['env_var']}")
            config["api_keys"][key_name] = env_val
            continue

        # Check existing config
        existing = config.get("api_keys", {}).get(key_name, "")
        if existing:
            print(f"  ✅ Already configured (starts with {existing[:8]}...)")
            continue

        try:
            val = input(s["api_key_prompt"].format(key_name)).strip()
        except (EOFError, KeyboardInterrupt):
            val = ""

        if val:
            config["api_keys"][key_name] = val
            print(s["api_key_saved"])
        else:
            print(s["api_key_skipped"])
        print()


def save_config(config, lang):
    """Save config to config.local.json."""
    s = STRINGS[lang]
    config["last_setup"] = datetime.now(timezone.utc).isoformat()
    config["language"] = lang

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(s["config_saved"].format(CONFIG_PATH.name))


def load_config():
    """Load existing config or create default."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "language": "auto",
        "api_keys": {},
        "endpoints": {},
        "last_setup": None,
        "last_health_check": None,
    }


def main():
    parser = argparse.ArgumentParser(description="Montreal Open Data Setup")
    parser.add_argument("--lang", choices=["en", "fr"], help="Force language")
    parser.add_argument("--check", action="store_true", help="Health check only (no prompts)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON (for agents)")
    args = parser.parse_args()

    # Language
    lang = args.lang or detect_language()

    if args.json:
        # Machine-readable output for agents
        _, _, results = run_health_check(lang, verbose=False)
        config = load_config()
        output = {
            "language": lang,
            "endpoints": results,
            "has_stm_key": bool(config.get("api_keys", {}).get("stm_realtime")),
            "config_exists": CONFIG_PATH.exists(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    s = STRINGS[lang]
    print(s["welcome"])
    print(s["lang_detect"] if lang == "en" else s["lang_detect"])
    print()

    # Load or create config
    config = load_config()

    # Health check
    required_ok, optional_ok, results = run_health_check(lang)
    config["endpoints"] = results
    config["last_health_check"] = datetime.now(timezone.utc).isoformat()

    if not required_ok:
        save_config(config, lang)
        sys.exit(1)

    # API keys (interactive only)
    if not args.check:
        prompt_api_keys(lang, config)

    # Save
    save_config(config, lang)
    print(s["done"])


if __name__ == "__main__":
    main()
