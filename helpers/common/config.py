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

# PlanHub (comparateur forfaits internet — non officiel)
PLANHUB_BASE_URL: str = _env("PLANHUB_BASE_URL", urls.PLANHUB_BASE)

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

# STM GTFS-RT / i3 (clé gratuite : stm.info/developers)
STM_API_KEY: str = _env("STM_API_KEY", "")
STM_GTFS_RT_BASE_URL: str = _env("STM_GTFS_RT_BASE_URL", urls.STM_GTFS_RT_BASE)
STM_VEHICLE_POSITIONS_URL: str = _env(
    "STM_VEHICLE_POSITIONS_URL",
    f"{STM_GTFS_RT_BASE_URL.rstrip('/')}/vehiclePositions",
)
STM_TRIP_UPDATES_URL: str = _env(
    "STM_TRIP_UPDATES_URL",
    f"{STM_GTFS_RT_BASE_URL.rstrip('/')}/tripUpdates",
)
STM_SERVICE_ALERTS_URL: str = _env("STM_SERVICE_ALERTS_URL", urls.STM_SERVICE_ALERTS_URL)
STM_DEVELOPERS_PORTAL_URL: str = _env("STM_DEVELOPERS_PORTAL_URL", urls.STM_DEVELOPERS_PORTAL)
STM_GTFS_STATIC_ZIP_URL: str = _env("STM_GTFS_STATIC_ZIP_URL", urls.STM_GTFS_STATIC_ZIP)
STM_TRACES_DATASET_ID: str = _env("STM_TRACES_DATASET_ID", urls.STM_TRACES_DATASET_ID)

# REM (pas de clé API)
REM_PORTAL_URL: str = _env("REM_PORTAL_URL", urls.REM_PORTAL)
REM_STATUS_URL_FR: str = _env("REM_STATUS_URL_FR", urls.REM_STATUS_URL_FR)
REM_STATUS_URL_EN: str = _env("REM_STATUS_URL_EN", urls.REM_STATUS_URL_EN)
REM_NEWS_URL_FR: str = _env("REM_NEWS_URL_FR", urls.REM_NEWS_URL_FR)
REM_NEWS_URL_EN: str = _env("REM_NEWS_URL_EN", urls.REM_NEWS_URL_EN)
REM_RSS_URL_FR: str = _env("REM_RSS_URL_FR", urls.REM_RSS_URL_FR)
REM_RSS_URL_EN: str = _env("REM_RSS_URL_EN", urls.REM_RSS_URL_EN)
REM_GTFS_STATIC_ZIP_URL: str = _env("REM_GTFS_STATIC_ZIP_URL", urls.REM_GTFS_STATIC_ZIP)
REM_GTFS_RT_ALERTS_URL: str = _env("REM_GTFS_RT_ALERTS_URL", urls.REM_GTFS_RT_ALERTS_URL)

# RSMA QUALO
QUALO_DATASET_ID: str = _env("QUALO_DATASET_ID", urls.QUALO_DATASET_ID)
QUALO_RESOURCE_ID: str = _env("QUALO_RESOURCE_ID", urls.QUALO_RESOURCE_ID)

# Événements publics
EVENEMENTS_PACKAGE_ID: str = _env("EVENEMENTS_PACKAGE_ID", urls.EVENEMENTS_PACKAGE_ID)
EVENEMENTS_CSV_RESOURCE_ID: str = _env("EVENEMENTS_CSV_RESOURCE_ID", urls.EVENEMENTS_CSV_RESOURCE_ID)

PERMIS_DATASET_ID: str = _env("PERMIS_DATASET_ID", urls.PERMIS_DATASET_ID)
PERMIS_RESOURCE_ID: str = _env("PERMIS_RESOURCE_ID", urls.PERMIS_RESOURCE_ID)
PERMIS_VIEWER_URL: str = _env("PERMIS_VIEWER_URL", urls.PERMIS_VIEWER)

PARKING_SIGNALISATION_DATASET_ID: str = _env(
    "PARKING_SIGNALISATION_DATASET_ID",
    urls.PARKING_SIGNALISATION_DATASET_ID,
)
PARKING_SIGNALISATION_RESOURCE_ID: str = _env(
    "PARKING_SIGNALISATION_RESOURCE_ID",
    urls.PARKING_SIGNALISATION_RESOURCE_ID,
)

# Stationnements déneigement (GeoJSON saisonnier)
PARKING_DENEIGEMENT_DATASET_ID: str = _env(
    "PARKING_DENEIGEMENT_DATASET_ID",
    urls.PARKING_DENEIGEMENT_DATASET_ID,
)
PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID: str = _env(
    "PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID",
    urls.PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID,
)
PARKING_DENEIGEMENT_GEOJSON_URL: str = _env(
    "PARKING_DENEIGEMENT_GEOJSON_URL",
    urls.PARKING_DENEIGEMENT_GEOJSON,
)

# Entraves circulation (CIFS)
ENTRAVES_DATASET_ID: str = _env("ENTRAVES_DATASET_ID", urls.ENTRAVES_DATASET_ID)
ENTRAVES_CIFS_JSON_URL: str = _env("ENTRAVES_CIFS_JSON_URL", urls.ENTRAVES_CIFS_JSON)

# Info Neige (HTML)
INFONEIGE_BASE_URL: str = _env("INFONEIGE_BASE_URL", urls.INFONEIGE_BASE)

# Open-Meteo (live weather)
OPEN_METEO_FORECAST_URL: str = _env(
    "OPEN_METEO_FORECAST_URL",
    urls.OPEN_METEO_FORECAST_URL,
)

# CinemaClock (HTML theatres near me)
CINEMACLOCK_BASE_URL: str = _env("CINEMACLOCK_BASE_URL", urls.CINEMACLOCK_BASE)
CINEMACLOCK_THEATERS_URL: str = _env(
    "CINEMACLOCK_THEATERS_URL",
    urls.CINEMACLOCK_THEATERS_URL,
)

# SIT Québec restauration
SIT_RESTAURATION_DATASET_ID: str = _env(
    "SIT_RESTAURATION_DATASET_ID",
    urls.SIT_RESTAURATION_DATASET_ID,
)
SIT_RESTAURATION_RESOURCE_ID: str = _env(
    "SIT_RESTAURATION_RESOURCE_ID",
    urls.SIT_RESTAURATION_RESOURCE_ID,
)

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
