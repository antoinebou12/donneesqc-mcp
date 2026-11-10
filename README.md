# Données Québec MCP

[Montréal MCP App](docs/montreal-app.md): `mtl_show_dashboard` · `ui://mtl-mcp/montreal.html`

[![CI](https://github.com/Stefen-Taime/donneesqc-mcp/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Stefen-Taime/donneesqc-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FStefen-Taime%2Fdonneesqc-mcp&project-name=donneesqc-mcp&repository-name=donneesqc-mcp)

Serveur [Model Context Protocol (MCP)](https://modelcontextprotocol.io) qui permet aux agents IA (Claude, ChatGPT, Gemini, etc.) de rechercher, explorer et analyser les jeux de données de [Données Québec](https://donneesquebec.ca), de la [Ville de Montréal](https://donnees.montreal.ca) et des services géospatiaux du gouvernement du Québec ([IGO](https://igouverte.org)), directement par conversation.

Au lieu de naviguer manuellement sur les portails, posez simplement vos questions :
_« Quels jeux de données existent sur la criminalité à Montréal ? »_ ou _« Combien d'actes criminels par arrondissement en 2025 ? »_ et obtenez des réponses instantanées, incluant des analyses SQL.

**Fonctionnalités clés :** Requêtes SQL sur le DataStore | Téléchargement de ressources non-DataStore (CSV, JSON, GeoJSON) | Recherche + interrogation en un appel | Géocodage québécois | Conversion EPSG:32198 ↔ 4326 | Intersection spatiale | Couches géospatiales OGC | Vitrine linguistique OQLF | NosOrigines | Info-pannes Hydro-Québec | Murales / Collecte MTL / La bicyclette / Festivals (Piknic, Jazz Fest) | Événements publics + agenda semaine (GCal) | Briefing de quartier | ~59 outils

> **Projet communautaire non officiel :** ce dépôt n'est pas exploité, approuvé ni certifié par le Gouvernement du Québec. Il sert à explorer des données ouvertes publiques; vérifiez toujours la source et la licence du jeu de données avant réutilisation.

| Approprié | Non approprié |
| --- | --- |
| Recherche et analyse de données ouvertes | Déclaration d'impôts ou démarches administratives authentifiées |
| Exploration géospatiale, WFS/WMS, intersections | Dossiers de santé, identité, permis ou prestations |
| Géocodage d'adresses québécoises publiques | Portails citoyens nécessitant une connexion |

Références : [déploiement](DEPLOY.md), [sécurité](SECURITY.md), [ADRs](docs/adr/), [architecture](docs/architecture/overview.md), [release checklist](docs/RELEASE.md), [contribution](CONTRIBUTING.md), [skill agents](skills/donneesqc-mcp/SKILL.md).

*[English version below](#english)*

---

## Exemples de requêtes

Voici ce que vous pouvez demander directement à votre agent IA :

### 1. Analyse SQL — criminalité par quartier

> « Quels sont les 10 postes de quartier avec le plus d'actes criminels à Montréal ? »

| Rang | PDQ | Total actes |
|------|-----|-------------|
| 1 | 38 (Plateau-Mont-Royal) | 25 787 |
| 2 | 21 (Centre-Sud / Ville-Marie Est) | 23 934 |
| 3 | 20 (Ville-Marie Ouest) | 20 700 |
| 4 | 48 (Mercier-Hochelaga-Maisonneuve) | 16 615 |
| 5 | 26 (Côte-des-Neiges / Outremont) | 16 573 |

*L'agent exécute une requête SQL `GROUP BY` et présente le classement en **tableau markdown** (pas d'histogramme ASCII).*

Sources : [Actes criminels](https://donnees.montreal.ca/dataset/actes-criminels) · [ressource](https://donnees.montreal.ca/dataset/actes-criminels/resource/c6f482bf-bf0f-4960-8b2f-9982c211addd)

### 2. Exploration multi-outils — arbres publics

> « Trouve les données sur les arbres publics de Montréal, explore la structure, puis dis-moi combien d'arbres par arrondissement. »

L'agent enchaîne `mtl_search_datasets` → `mtl_query_data` → `mtl_query_sql`. Instantané juillet 2026 : **~334 631 arbres** (fichier consolidé), Mercier–Hochelaga-Maisonneuve en tête.

### 3. Statistiques du catalogue

> « Combien d'organisations publient des données sur Données Québec ? »

**142 organisations**, **1 615 jeux de données** (`qc_get_catalog_stats`). Top organisations en tableau :

| Organisation | Jeux |
|-------------|------|
| Ville de Montréal | 389 |
| Ville de Laval | 130 |
| MELCCFP | 128 |
| MRNF | 121 |
| Ville de Gatineau | 52 |

### 4. Tendance temporelle

> « Quelle est la tendance mensuelle des actes criminels à Montréal ? »

L'agent identifie un pic au printemps/été et une baisse en hiver via un `GROUP BY` sur les dates, présenté en tableau.

### 5. Données géospatiales — patrimoine culturel

> « Quelles couches géospatiales sont disponibles pour le patrimoine culturel du Québec ? »

L'agent interroge le WFS IGO avec `query="MCC"` et trouve 7 couches du Ministère de la Culture (sites patrimoniaux, immeubles classés/cités).

### 6. Pistes cyclables — multi-sources

> « Trouve les données sur les pistes cyclables à Montréal via les deux portails et via IGO. »

- **DQ / Montréal :** [Réseau cyclable](https://donnees.montreal.ca/dataset/pistes-cyclables) (GeoJSON/SHP) + REV
- **IGO WFS :** aucune couche « pistes » ; WMS `convi_velo_glv` (convivialité MTQ, pas le réseau municipal)

**[Voir tous les exemples avec réponses complètes](EXAMPLES.md)**

---

## Connecter votre agent IA au serveur MCP

Déployez votre instance ([Deploy with Vercel](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FStefen-Taime%2Fdonneesqc-mcp&project-name=donneesqc-mcp&repository-name=donneesqc-mcp) ou [guide complet](DEPLOY.md)), puis utilisez `https://YOUR_PROJECT.vercel.app/mcp` — ou `http://localhost:8000/mcp` en local.

[Claude Code](#claude-code) | [Claude Desktop](#claude-desktop) | [ChatGPT](#chatgpt) | [Cursor](#cursor) | [VS Code](#vs-code) | [Gemini CLI](#gemini-cli) | [Le Chat (Mistral)](#le-chat-mistral) | [Windsurf](#windsurf)

### Claude Code

```bash
# Local
claude mcp add --transport http donneesqc http://localhost:8000/mcp

# Après déploiement Vercel
claude mcp add --transport http donneesqc https://YOUR_PROJECT.vercel.app/mcp
```

> **Note :** Si Claude Code bloque les appels réseau vers les API externes, ajoutez les domaines à la whitelist dans votre `.claude/settings.json` :
>
> ```json
> {
>   "permissions": {
>     "allow": [
>       "WebFetch(domain:registreentreprises.gouv.qc.ca)",
>       "WebFetch(domain:www.donneesquebec.ca)"
>     ]
>   }
> }
> ```

### Claude Desktop

Ajoutez dans votre fichier de configuration Claude Desktop :

```json
{
  "mcpServers": {
    "donneesqc": {
      "command": "npx",
      "args": ["mcp-remote", "https://YOUR_PROJECT.vercel.app/mcp"]
    }
  }
}
```

Remplacez l’URL par `http://localhost:8000/mcp` pour un serveur local.

### ChatGPT

*Forfaits payants seulement.* Allez dans `Settings` > `Apps and connectors` > activez le **Developer mode** > `Add new connector` avec l'URL `https://YOUR_PROJECT.vercel.app/mcp` (ou `http://localhost:8000/mcp` en local).

### Cursor

Avec Docker (`docker compose up -d`), le serveur écoute sur `http://127.0.0.1:8000/mcp`.

Ajoutez dans `~/.cursor/mcp.json` (ou `.cursor/mcp.json` du projet) :

```json
{
  "mcpServers": {
    "donneesqc": {
      "url": "http://127.0.0.1:8000/mcp",
      "transport": "http"
    }
  }
}
```

Pour une instance hébergée (Vercel) :

```json
{
  "mcpServers": {
    "donneesqc": {
      "url": "https://YOUR_PROJECT.vercel.app/mcp",
      "transport": "http"
    }
  }
}
```

Puis rechargez les serveurs MCP dans Cursor (Settings → MCP, ou redémarrer Cursor).

### VS Code

Ajoutez dans `mcp.json` (lancez **MCP: Open User Configuration** depuis la palette de commandes) :

```json
{
  "servers": {
    "donneesqc": {
      "url": "https://YOUR_PROJECT.vercel.app/mcp",
      "type": "http"
    }
  }
}
```

### Gemini CLI

Ajoutez dans `~/.gemini/settings.json` :

```json
{
  "mcpServers": {
    "donneesqc": {
      "httpUrl": "https://YOUR_PROJECT.vercel.app/mcp"
    }
  }
}
```

### Le Chat (Mistral)

`Intelligence` > `Connectors` > `Add connector` > `Custom MCP Connector` > URL : `https://YOUR_PROJECT.vercel.app/mcp`.

### Windsurf

Ajoutez dans `~/.codeium/windsurf/mcp_config.json` :

```json
{
  "mcpServers": {
    "donneesqc": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://YOUR_PROJECT.vercel.app/mcp"]
    }
  }
}
```

## Héberger

Guide détaillé : **[DEPLOY.md](DEPLOY.md)**.

### Vercel (one-click)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FStefen-Taime%2Fdonneesqc-mcp&project-name=donneesqc-mcp&repository-name=donneesqc-mcp)

Après le déploiement : `GET /health` puis configurez vos clients sur `https://YOUR_PROJECT.vercel.app/mcp`. Aucune écriture disque — caches et téléchargements en mémoire uniquement (plafond 5 Mo sur Vercel).

### Docker

```bash
git clone https://github.com/Stefen-Taime/donneesqc-mcp.git
cd donneesqc-mcp
docker compose up -d
```

### Smithery

Voir [`smithery.yaml`](smithery.yaml) et `make smithery`.

## Développement local

### Makefile

```bash
make sync          # uv sync --extra dev
make check         # lint + format --check + types + tests
make security      # pip-audit
make run           # serveur local
make docker-up     # build + compose
make smithery      # infos de déploiement Smithery
```

Si votre environnement propose un conteneur de développement, utilisez **Open in Dev Container** pour obtenir une configuration reproductible sans polluer votre machine locale.

### Installation manuelle

```bash
git clone https://github.com/Stefen-Taime/donneesqc-mcp.git
cd donneesqc-mcp
uv sync --extra dev
cp .env.example .env
# chargez .env selon votre shell, puis :
uv run python main.py
```

**Variables d'environnement :**

| Variable | Défaut | Description |
|---|---|---|
| `MCP_HOST` | `0.0.0.0` | Adresse d'écoute. Utilisez `127.0.0.1` en développement local. |
| `MCP_PORT` | `8000` | Port du serveur HTTP. |
| `MCP_ENV` | `local` | Nom de l'environnement (Sentry). |
| `MCP_STATELESS_HTTP` | `false` (auto `true` sur Vercel) | Mode Streamable HTTP sans session (serverless). |
| `MCP_JSON_RESPONSE` | `false` (auto `true` sur Vercel) | Réponses JSON (recommandé avec stateless). |
| `DQ_API_URL` | `https://www.donneesquebec.ca/recherche/api/3/action` | API CKAN de Données Québec. |
| `MTL_API_URL` | `https://donnees.montreal.ca/api/3/action` | API CKAN de Montréal. |
| `GEO_WFS_URL` | `https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi` | Endpoint WFS IGO. |
| `GEO_WMS_URL` | `https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi` | Endpoint WMS IGO. |
| `GEOCODER_URL` | `https://geoegl.msp.gouv.qc.ca/apis/icherche` | API de géocodage Adresses Québec (ICherche). |
| `VITRINE_BASE_URL` | `https://vitrinelinguistique.oqlf.gouv.qc.ca` | Vitrine linguistique OQLF. |
| `NOSORIGINES_BASE_URL` | `https://www.nosorigines.qc.ca` | Recherche NosOrigines. |
| `HYDRO_INFOPANNES_API_URL` | `https://services-bs.solutions.hydroquebec.com/pan/web` | API Info-pannes. |
| `HYDRO_INFOPANNES_PORTAL_URL` | `https://infopannes.solutions.hydroquebec.com` | Portail Info-pannes. |
| `HTTP_TIMEOUT` | `30.0` | Timeout HTTP en secondes. |
| `HTTP_MAX_RETRIES` | `3` | Nombre de tentatives en cas d'erreur réseau ou 5xx. |
| `DOWNLOAD_MAX_BYTES` | `52428800` local / `5242880` sur Vercel | Taille max téléchargement **en mémoire** (pas de disque). |
| `SQL_MAX_LENGTH` | `10000` | Longueur maximale d'une requête SQL DataStore. |
| `HTTP_RATE_LIMIT_RPS` | `5.0` | Débit sortant par hôte pour le token bucket HTTP. |
| `HTTP_RATE_LIMIT_BURST` | `10.0` | Rafale maximale par hôte avant attente. |
| `HTTP_CACHE_TTL_SECONDS` | `60` local / `30` sur Vercel | TTL du cache GET en mémoire. |
| `HTTP_CACHE_MAX_ENTRIES` | `256` local / `64` sur Vercel | Entrées max du cache GET en mémoire. |
| `LOG_LEVEL` | `INFO` | Niveau de journalisation Python. |
| `SENTRY_DSN` | _(non défini)_ | DSN Sentry pour le monitoring. |

## Transport

Construit avec le [SDK Python MCP officiel](https://github.com/modelcontextprotocol/python-sdk). **Streamable HTTP uniquement** — STDIO et SSE ne sont pas supportés.

**Endpoints :**
- `POST /mcp` — Messages JSON-RPC
- `GET /health` — Sonde de santé (Docker HEALTHCHECK, Vercel, load balancers)

**Hébergement :** point d'entrée ASGI [`asgi.py`](asgi.py) (`asgi:app`) pour Vercel ; [`main.py`](main.py) pour Docker / local. Config : [`vercel.json`](vercel.json), [`smithery.yaml`](smithery.yaml). Voir [DEPLOY.md](DEPLOY.md).

Mises à jour de dépendances : [Renovate](https://docs.renovatebot.com/) via [`renovate.json`](renovate.json).

Les réponses réussies ajoutent une enveloppe `_meta` additive avec la source, l'horodatage de récupération, un avertissement communautaire et, quand disponible, les identifiants de jeu/ressource et la licence. Les erreurs n'ajoutent pas de citation factice.

## Outils disponibles (44)

Les noms MCP sont **préfixés par domaine** (`qc_*`, `mtl_*`, `common_*`) pour faciliter la découverte. Structure du code : `tools/qc/`, `tools/mtl/` (avec `murales/`, `labicyclette/`, `collecte/`, `avis/`), `tools/common/`.

### Migration (breaking)

Unprefixed tool names (`search_datasets`, `geocode`, `search_murales`, …) are gone. Call `common_list_tools_with_examples` (optionally with `category`) or use the tables below to pick the new `qc_*` / `mtl_*` / `common_*` names.

### `qc` — Données Québec (15 outils)

| Outil | Description |
|---|---|
| `qc_search_datasets` | Recherche par mots-clés, organisation, tags |
| `qc_get_dataset_info` | Métadonnées complètes d'un jeu de données |
| `qc_list_dataset_resources` | Liste les fichiers/ressources d'un jeu |
| `qc_get_resource_info` | Détail d'une ressource spécifique |
| `qc_query_resource_data` | Interroge le DataStore avec filtres et pagination |
| `qc_query_resource_sql` | **SQL direct** — agrégations, jointures, sous-requêtes |
| `qc_list_organizations` | Ministères, villes, organismes |
| `qc_get_organization_info` | Détail d'une organisation |
| `qc_get_catalog_stats` | Statistiques globales du catalogue |
| `qc_download_resource` | Télécharge et lit des ressources **non-DataStore** (CSV, JSON, GeoJSON, XLSX) |
| `qc_preview_resource` | Aperçu intelligent — schéma (colonnes + types) et 5 premières lignes |
| `qc_find_and_query` | **Composite** — enchaîne search → resources → query en un seul appel |
| `qc_suggest_sql` | Génère des squelettes SQL à partir du schéma d'une ressource |
| `qc_compare_datasets` | Diff entre 2 jeux (colonnes, volumes, tags, organisations) |
| `qc_auto_detect_resource` | Trouve automatiquement le meilleur `resource_id` à partir d'un nom |

### `qc/geo` — Géospatial (8 outils)

| Outil | Description |
|---|---|
| `qc_geo_list_layers` | Couches WFS/WMS depuis IGO |
| `qc_geo_get_features` | Entités GeoJSON depuis le WFS |
| `qc_geo_describe_layer` | Schéma d'une couche (champs, types) |
| `qc_geo_get_map_url` | URL d'image cartographique WMS |
| `qc_geo_geocode` | Adresse québécoise → coordonnées lat/lng (via Adresses Québec) |
| `qc_geo_reverse_geocode` | Coordonnées lat/lng → adresse québécoise |
| `qc_geo_convert_coordinates` | Conversion EPSG:32198 (Lambert MTQ) ↔ EPSG:4326 (WGS84) |
| `qc_geo_spatial_intersection` | Quelle région / MRC / municipalité / arrondissement contient un point |

### `qc/oqlf`, `qc/nosorigines` et `qc/hydro` (6 outils)

| Outil | Description |
|---|---|
| `qc_oqlf_search` | Recherche BDL/GDT sur la [Vitrine linguistique](https://vitrinelinguistique.oqlf.gouv.qc.ca/) |
| `qc_oqlf_get_entry` | Titre + extrait d'une fiche Vitrine |
| `qc_nosorigines_search` | Recherche personnes/couples sur [NosOrigines](https://www.nosorigines.qc.ca/genealogieSearch.aspx?lng=fr) |
| `qc_nosorigines_get_person` | Fiche personne (parents, conjoint, enfants) via [GenealogieQuebec](https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=781) |
| `qc_nosorigines_get_ancestors` | Remonte parents / grands-parents (1–3 générations) |
| `qc_hydro_outage_status` | État du service à une adresse via [Info-pannes](https://infopannes.solutions.hydroquebec.com) (adresse ou lat/lng) |

### `mtl` — Ville de Montréal catalogue (3 outils)

| Outil | Description |
|---|---|
| `mtl_search_datasets` | Recherche sur donnees.montreal.ca |
| `mtl_query_data` | Interroge le DataStore montréalais |
| `mtl_query_sql` | SQL sur les données montréalaises |

### `mtl/murales` (5 outils)

| Outil | Description |
|---|---|
| `mtl_murales_search` | Recherche murales financées (artiste, arrondissement, année, texte) |
| `mtl_murales_get` | Détail d'une murale par id |
| `mtl_murales_nearby` | Murales à proximité d'un point GPS |
| `mtl_murales_random` | Tirage aléatoire (filtres optionnels) |
| `mtl_murales_facet` | Facettes artiste / arrondissement / année |

### `mtl/labicyclette` (5 outils)

| Outil | Description |
|---|---|
| `mtl_labicyclette_overview` | KPIs overview (Total / Active / Daily avg) |
| `mtl_labicyclette_list_counters` | Liste des compteurs |
| `mtl_labicyclette_get_counter` | Série volume d'un compteur |
| `mtl_labicyclette_boroughs` | Volumes par arrondissement |
| `mtl_labicyclette_list_construction` | Chantiers actifs |

### `mtl/collecte` (3 outils)

| Outil | Description |
|---|---|
| `mtl_collecte_find_waste` | Calendrier de collecte des déchets par adresse |
| `mtl_collecte_find_ecocentres` | Écocentres les plus proches |
| `mtl_collecte_borough_waste_stats` | Bilan massique / taux de récupération par arrondissement |

### `mtl/avis` (1 outil)

| Outil | Description |
|---|---|
| `mtl_avis_nearby` | Avis/alertes actifs à une date, près d'une adresse (GeoJSON) |

### `mtl/parcs` / `mtl/bixi` / `mtl/qualo` / neighborhood

| Outil | Description |
|---|---|
| `mtl_parcs_nearby` | Parcs / espaces verts proches (GeoJSON) |
| `mtl_bixi_nearby` | Stations BIXI proches (GBFS live) |
| `mtl_qualo_nearby` | Mesures QUALO (qualité de l'eau en rive) proches |
| `mtl_neighborhood_briefing` | Briefing de quartier : Hydro + avis + QUALO + parcs + BIXI |

### `mtl/festivals` (5 outils)

| Outil | Description |
|---|---|
| `mtl_piknic_search_off` | Programmation OfF Piknic (+ GCal / `calendar_ascii`) |
| `mtl_piknic_search` | Programmation Piknic (série principale) |
| `mtl_piknic_search_petit` | Programmation Petit Piknic |
| `mtl_jazzfest_search_free` | Concerts gratuits Festival de Jazz de Montréal |
| `mtl_jazzfest_search_paid` | Concerts payants Festival de Jazz de Montréal |

### `mtl/evenements` / `mtl/calendar` (2 outils)

| Outil | Description |
|---|---|
| `mtl_evenements_search` | Événements publics (`vmtl-evenements-publics`, Données Québec CKAN) |
| `mtl_calendar_week` | Agenda de la semaine (festivals + événements + avis) |

### `common` — Système (2 outils)

| Outil | Description |
|---|---|
| `common_get_version` | Version du serveur, Python, capacités disponibles |
| `common_list_tools_with_examples` | Meta-introspection — liste tous les outils avec exemples (filtre `category`) |

## Tests

```bash
make test
# ou (hors ligne par défaut)
uv run pytest -v

# CKAN live (optionnel)
make test-network

# Test interactif avec MCP Inspector
npx @modelcontextprotocol/inspector --http-url "http://127.0.0.1:8000/mcp"
```

## Contribuer

- **1 fonctionnalité = 1 PR**
- Tout le code doit être révisé et testé par un humain avant soumission.
- Guide complet : [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
make check
make security
uv run pre-commit install
```

### Releases

Checklist : [docs/RELEASE.md](docs/RELEASE.md)

```bash
./tag_version.sh 1.0.0            # Créer une release
./tag_version.sh 1.0.0 --dry-run  # Aperçu
```

## Sources de données

- **[Données Québec](https://www.donneesquebec.ca/)** — Portail provincial (gouvernement + municipalités), CKAN
- **[donnees.montreal.ca](https://donnees.montreal.ca/)** — Portail municipal de Montréal
- **[IGO](https://igouverte.org)** — Infrastructure Géomatique Ouverte (WMS/WFS)
- **[Adresses Québec (ICherche)](https://geoegl.msp.gouv.qc.ca/apis/icherche)** — Géocodage
- **[Vitrine linguistique (OQLF)](https://vitrinelinguistique.oqlf.gouv.qc.ca/)** — BDL et GDT
- **[NosOrigines](https://www.nosorigines.qc.ca/genealogieSearch.aspx?lng=fr)** — Généalogie publique
- **[Info-pannes (Hydro-Québec)](https://infopannes.solutions.hydroquebec.com)** — État du service / pannes (wrapper communautaire)
- **[Murales subventionnées](https://donnees.montreal.ca/dataset/murales)** — Art public financé depuis 2007 ([viewer MTL Murales](https://www.mtlmurales.ca/fr))

Vérifiez la licence propre à chaque jeu de données avant redistribution, publication ou usage commercial. La licence du code ne remplace pas les licences des données consultées.

## Licence

MIT — voir [LICENSE](LICENSE).

---

## English

MCP server that lets AI agents (Claude, ChatGPT, Gemini, etc.) search, explore, and analyze open datasets from [Données Québec](https://donneesquebec.ca), [Ville de Montréal](https://donnees.montreal.ca), and Quebec's geospatial services ([IGO](https://igouverte.org)) through conversation.

Instead of manually browsing portals, simply ask questions like _"What datasets exist about crime in Montreal?"_ or _"How many criminal acts per borough in 2025?"_ and get instant answers — including SQL-powered analytics.

This is a community project, not an official Gouvernement du Québec service. It is suitable for open data, geospatial exploration and geocoding; it is not suitable for tax filing, health records or authenticated government portals. Always check each dataset licence before reuse.

Useful docs: [Deploy](DEPLOY.md), [Security](SECURITY.md), [ADRs](docs/adr/), [Architecture](docs/architecture/overview.md), [Release checklist](docs/RELEASE.md), [Contributing](CONTRIBUTING.md).

All setup instructions, tool descriptions, and environment variables are documented in the French section above. The configuration snippets (JSON, bash) are language-independent and apply as-is.

### Quick start

**One-click host:** [Deploy with Vercel](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FStefen-Taime%2Fdonneesqc-mcp&project-name=donneesqc-mcp&repository-name=donneesqc-mcp) — then use `https://YOUR_PROJECT.vercel.app/mcp`.

```bash
git clone https://github.com/Stefen-Taime/donneesqc-mcp.git
cd donneesqc-mcp
docker compose up -d
```

Then connect your AI client to `http://localhost:8000/mcp` — see the [connection section above](#connecter-votre-agent-ia-au-serveur-mcp) for client-specific configs.

### Available tools (~50)

- **Données Québec** : recherche, métadonnées, DataStore, SQL, organisations, catalog stats (top orgs en tableau)
- **Ville de Montréal** : recherche, DataStore, SQL
- **Intelligence** : find-and-query, suggest SQL, compare, auto-detect, download/preview
- **Géospatial** : WFS/WMS, features, géocodage, EPSG:32198↔4326, intersection
- **Linguistique & généalogie** : OQLF Vitrine, NosOrigines
- **Hydro-Québec** : Info-pannes (état du service à une adresse)
- **MTL domaines** : murales, Collecte MTL, La bicyclette, avis/alertes, festivals (Piknic / Jazz Fest)
- **Système** : version, catalogue d'outils avec exemples

Prefer `common_list_tools_with_examples` at runtime for the exact count. Agent workflows: [skills/donneesqc-mcp/SKILL.md](skills/donneesqc-mcp/SKILL.md).

---

*Un projet [mcsÉdition](https://mcsedition.org/fr) — Montréal, Québec*
