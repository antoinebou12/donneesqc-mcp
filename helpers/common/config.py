"""Configuration runtime - variables d'environnement sur défauts ``urls``."""

from __future__ import annotations

import os

from helpers.common import urls


def _env_truthy(name: str) -> bool:
    """True si la variable d'environnement vaut 1/true/yes/on."""
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# Vercel définit VERCEL=1 ; MCP_STATELESS_HTTP force le mode sans session.
IS_VERCEL: bool = _env_truthy("VERCEL") or bool(os.environ.get("VERCEL_ENV"))
MCP_STATELESS_HTTP: bool = _env_truthy("MCP_STATELESS_HTTP") or IS_VERCEL
MCP_JSON_RESPONSE: bool = _env_truthy("MCP_JSON_RESPONSE") or IS_VERCEL

# Serveur MCP
MCP_HOST: str = _env("MCP_HOST", "0.0.0.0")
MCP_PORT: int = int(os.environ.get("MCP_PORT", "8000"))
MCP_ENV: str = _env("MCP_ENV", "local")
LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")

# Données Québec (CKAN)
DQ_API_URL: str = _env("DQ_API_URL", urls.DQ_API)
DQ_BASE_URL: str = _env("DQ_BASE_URL", urls.DQ_BASE)

# Ville de Montréal (CKAN)
MTL_API_URL: str = _env("MTL_API_URL", urls.MTL_API)
MTL_BASE_URL: str = _env("MTL_BASE_URL", urls.MTL_BASE)

# Géospatial - services OGC (IGO)
GEO_WMS_URL: str = _env("GEO_WMS_URL", urls.GEO_OGC)
GEO_WFS_URL: str = _env("GEO_WFS_URL", urls.GEO_OGC)

# Geocoding - Adresses Québec (API REST)
GEOCODER_URL: str = _env("GEOCODER_URL", urls.GEOCODER)

# Vitrine linguistique (OQLF)
VITRINE_BASE_URL: str = _env("VITRINE_BASE_URL", urls.VITRINE_BASE)

# NosOrigines (généalogie publique)
NOSORIGINES_BASE_URL: str = _env("NOSORIGINES_BASE_URL", urls.NOSORIGINES_BASE)

# La bicyclette (tableau de bord cyclisme Montréal)
LABICYCLETTE_BASE_URL: str = _env("LABICYCLETTE_BASE_URL", urls.LABICYCLETTE_BASE)

# Murales subventionnées (Données Montréal) + viewer MTL Murales
MURALES_DATASET_ID: str = _env("MURALES_DATASET_ID", urls.MURALES_DATASET_ID)
MURALES_RESOURCE_ID: str = _env("MURALES_RESOURCE_ID", urls.MURALES_RESOURCE_ID)
MURALES_VIEWER_URL: str = _env("MURALES_VIEWER_URL", urls.MURALES_VIEWER)

# Collecte MTL
COLLECTEMTL_BASE_URL: str = _env("COLLECTEMTL_BASE_URL", urls.COLLECTEMTL_BASE)

# Hydro-Québec Info-pannes
HYDRO_INFOPANNES_API_URL: str = _env("HYDRO_INFOPANNES_API_URL", urls.HYDRO_INFOPANNES_API)
HYDRO_INFOPANNES_PORTAL_URL: str = _env("HYDRO_INFOPANNES_PORTAL_URL", urls.HYDRO_INFOPANNES_PORTAL)

# Festivals Montréal
PIKNIC_BASE_URL: str = _env("PIKNIC_BASE_URL", urls.PIKNIC_BASE)
JAZZFEST_BASE_URL: str = _env("JAZZFEST_BASE_URL", urls.JAZZFEST_BASE)

# Avis et alertes
AVIS_ALERTES_DATASET_ID: str = _env("AVIS_ALERTES_DATASET_ID", urls.AVIS_ALERTES_DATASET_ID)
AVIS_ALERTES_GEOJSON_RESOURCE_ID: str = _env(
    "AVIS_ALERTES_GEOJSON_RESOURCE_ID",
    urls.AVIS_ALERTES_GEOJSON_RESOURCE_ID,
)
_AVIS_ALERTES_DEFAULT_GEOJSON_URL = (
    f"{MTL_BASE_URL}/dataset/{urls.AVIS_ALERTES_PACKAGE_UUID}"
    f"/resource/{AVIS_ALERTES_GEOJSON_RESOURCE_ID}/download/avis-alertes.geojson"
)
AVIS_ALERTES_GEOJSON_URL: str = _env("AVIS_ALERTES_GEOJSON_URL", _AVIS_ALERTES_DEFAULT_GEOJSON_URL)
AVIS_ALERTES_VIEWER_URL: str = _env("AVIS_ALERTES_VIEWER_URL", urls.AVIS_ALERTES_VIEWER)

# Parcs / espaces verts
PARCS_DATASET_ID: str = _env("PARCS_DATASET_ID", urls.PARCS_DATASET_ID)
PARCS_GEOJSON_RESOURCE_ID: str = _env("PARCS_GEOJSON_RESOURCE_ID", urls.PARCS_GEOJSON_RESOURCE_ID)
_PARCS_DEFAULT_GEOJSON_URL = (
    f"{MTL_BASE_URL}/dataset/{urls.PARCS_PACKAGE_UUID}/resource/{PARCS_GEOJSON_RESOURCE_ID}/download/espace_vert.json"
)
PARCS_GEOJSON_URL: str = _env("PARCS_GEOJSON_URL", _PARCS_DEFAULT_GEOJSON_URL)

# BIXI GBFS
BIXI_DATASET_ID: str = _env("BIXI_DATASET_ID", urls.BIXI_DATASET_ID)
BIXI_GBFS_BASE_URL: str = _env("BIXI_GBFS_BASE_URL", urls.BIXI_GBFS_BASE)
BIXI_STATION_INFO_URL: str = _env(
    "BIXI_STATION_INFO_URL",
    f"{BIXI_GBFS_BASE_URL.rstrip('/')}/station_information.json",
)
BIXI_STATION_STATUS_URL: str = _env(
    "BIXI_STATION_STATUS_URL",
    f"{BIXI_GBFS_BASE_URL.rstrip('/')}/station_status.json",
)

# RSMA QUALO
QUALO_DATASET_ID: str = _env("QUALO_DATASET_ID", urls.QUALO_DATASET_ID)
QUALO_RESOURCE_ID: str = _env("QUALO_RESOURCE_ID", urls.QUALO_RESOURCE_ID)

# Événements publics
EVENEMENTS_PACKAGE_ID: str = _env("EVENEMENTS_PACKAGE_ID", urls.EVENEMENTS_PACKAGE_ID)
EVENEMENTS_CSV_RESOURCE_ID: str = _env("EVENEMENTS_CSV_RESOURCE_ID", urls.EVENEMENTS_CSV_RESOURCE_ID)

# Géolocalisation IP client (jamais l'IP du serveur MCP)
IP_GEO_URL_TEMPLATE: str = _env("IP_GEO_URL_TEMPLATE", urls.IP_GEO_URL_TEMPLATE)
DEFAULT_TIMEZONE: str = _env("DEFAULT_TIMEZONE", "America/Toronto")

# Observabilité
SENTRY_DSN: str | None = os.environ.get("SENTRY_DSN")
SENTRY_SAMPLE_RATE: float = float(os.environ.get("SENTRY_SAMPLE_RATE", "1.0"))

# HTTP
HTTP_TIMEOUT: float = float(os.environ.get("HTTP_TIMEOUT", "30.0"))
HTTP_MAX_RETRIES: int = int(os.environ.get("HTTP_MAX_RETRIES", "3"))
HTTP_USER_AGENT: str = _env("HTTP_USER_AGENT", urls.HTTP_USER_AGENT_DEFAULT)

# Limites de téléchargement (mémoire uniquement - pas d'écriture disque)
_DEFAULT_DOWNLOAD_MAX_BYTES = 5 * 1024 * 1024 if IS_VERCEL else 50 * 1024 * 1024
DOWNLOAD_MAX_BYTES: int = int(os.environ.get("DOWNLOAD_MAX_BYTES", str(_DEFAULT_DOWNLOAD_MAX_BYTES)))

# SQL DataStore
SQL_MAX_LENGTH: int = int(os.environ.get("SQL_MAX_LENGTH", "10000"))

# Rate limiting HTTP sortant (token bucket par hôte)
HTTP_RATE_LIMIT_RPS: float = float(os.environ.get("HTTP_RATE_LIMIT_RPS", "5.0"))
HTTP_RATE_LIMIT_BURST: float = float(os.environ.get("HTTP_RATE_LIMIT_BURST", "10.0"))

# Cache HTTP GET (TTL + LRU en mémoire uniquement)
_DEFAULT_CACHE_TTL = 30.0 if IS_VERCEL else 60.0
_DEFAULT_CACHE_MAX_ENTRIES = 64 if IS_VERCEL else 256
HTTP_CACHE_TTL_SECONDS: float = float(os.environ.get("HTTP_CACHE_TTL_SECONDS", str(_DEFAULT_CACHE_TTL)))
HTTP_CACHE_MAX_ENTRIES: int = int(os.environ.get("HTTP_CACHE_MAX_ENTRIES", str(_DEFAULT_CACHE_MAX_ENTRIES)))
