"""Canonical URLs, dataset IDs, and static source metadata.

Single registry for open-data portals and domain APIs used by this MCP.
Runtime env overrides live in ``helpers.common.config`` (defaults come from here).

Prefer importing ``SOURCES`` / helpers from this module for citations and docs;
prefer ``helpers.common.config`` when you need env-overridable values.
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class SourceInfo(TypedDict):
    """Static description of an upstream data source."""

    key: str
    label: str
    portal_url: str
    source: str  # value used in response `_meta.source`
    api_url: NotRequired[str]
    dataset_id: NotRequired[str]
    resource_id: NotRequired[str]
    viewer_url: NotRequired[str]
    license: NotRequired[str]
    notes: NotRequired[str]


# ── Portal bases (defaults) ──────────────────────────────────────────────────

DQ_API = "https://www.donneesquebec.ca/recherche/api/3/action"
DQ_BASE = "https://www.donneesquebec.ca/recherche"

MTL_API = "https://donnees.montreal.ca/api/3/action"
MTL_BASE = "https://donnees.montreal.ca"

GEO_OGC = "https://geoegl.msp.gouv.qc.ca/ws/igo_gouvouvert.fcgi"
GEOCODER = "https://geoegl.msp.gouv.qc.ca/apis/icherche"

VITRINE_BASE = "https://vitrinelinguistique.oqlf.gouv.qc.ca"
NOSORIGINES_BASE = "https://www.nosorigines.qc.ca"
LABICYCLETTE_BASE = "https://www.labicyclette.ca"
COLLECTEMTL_BASE = "https://collectemtl.ca"

HYDRO_INFOPANNES_API = "https://services-bs.solutions.hydroquebec.com/pan/web"
HYDRO_INFOPANNES_PORTAL = "https://infopannes.solutions.hydroquebec.com"

PIKNIC_BASE = "https://piknicelectronik.com"
PIKNIC_PROGRAM_PATH = "/fr/programmation"
JAZZFEST_BASE = "https://montrealjazzfest.com"
JAZZFEST_PROGRAM_PATH = "/fr/programmation/horaire"

# ── Montréal dataset / resource IDs ──────────────────────────────────────────

MURALES_DATASET_ID = "murales"
MURALES_RESOURCE_ID = "f02401c2-8336-4086-9955-4c5592ace72e"
MURALES_VIEWER = "https://www.mtlmurales.ca/fr"

AVIS_ALERTES_DATASET_ID = "avis-alertes"
AVIS_ALERTES_PACKAGE_UUID = "556c84af-aebf-4ca9-9a9c-2f246601674c"
AVIS_ALERTES_GEOJSON_RESOURCE_ID = "d249e452-46f5-422f-91ae-898c98eea6cc"
AVIS_ALERTES_VIEWER = "https://montreal.ca/avis-et-alertes"
AVIS_ALERTES_GEOJSON = (
    f"{MTL_BASE}/dataset/{AVIS_ALERTES_PACKAGE_UUID}"
    f"/resource/{AVIS_ALERTES_GEOJSON_RESOURCE_ID}/download/avis-alertes.geojson"
)

PARCS_DATASET_ID = "grands-parcs-parcs-d-arrondissements-et-espaces-publics"
PARCS_PACKAGE_UUID = "2e9e4d2f-173a-4c3d-a5e3-565d79baa27d"
PARCS_GEOJSON_RESOURCE_ID = "35796624-15df-4503-a569-797665f8768e"
PARCS_GEOJSON = (
    f"{MTL_BASE}/dataset/{PARCS_PACKAGE_UUID}/resource/{PARCS_GEOJSON_RESOURCE_ID}/download/espace_vert.json"
)

BIXI_DATASET_ID = "bixi-etat-des-stations"
BIXI_GBFS_BASE = "https://gbfs.velobixi.com/gbfs/en"
BIXI_STATION_INFO = f"{BIXI_GBFS_BASE}/station_information.json"
BIXI_STATION_STATUS = f"{BIXI_GBFS_BASE}/station_status.json"

QUALO_DATASET_ID = "rsma-qualite-de-l-eau-en-rive-qualo"
QUALO_RESOURCE_ID = "9136d84a-8273-4777-ad68-9ab05d270322"

EVENEMENTS_PACKAGE_ID = "vmtl-evenements-publics"
EVENEMENTS_CSV_RESOURCE_ID = "6decf611-6f11-4f34-bb36-324d804c9bad"

# IP geolocation (client IP only - never host egress). Template uses {ip}.
IP_GEO_URL_TEMPLATE = "https://ipapi.co/{ip}/json/"

MTL_OPEN_DATA_LICENSE = "CC BY 4.0 (Ville de Montréal open data)"
HTTP_USER_AGENT_DEFAULT = "donneesqc-mcp (https://github.com/Stefen-Taime/donneesqc-mcp)"
GITHUB_REPO = "https://github.com/Stefen-Taime/donneesqc-mcp"


def mtl_dataset_url(dataset_id: str, *, base: str = MTL_BASE) -> str:
    """Navigable dataset page on donnees.montreal.ca."""
    return f"{base.rstrip('/')}/dataset/{dataset_id}"


def dq_dataset_url(dataset_id: str, *, base: str = DQ_BASE) -> str:
    """Navigable dataset page on Données Québec."""
    return f"{base.rstrip('/')}/dataset/{dataset_id}"


def join_portal(base: str, path: str) -> str:
    """Join portal base + path (path should start with /)."""
    return f"{base.rstrip('/')}{path}"


PIKNIC_PORTAL = join_portal(PIKNIC_BASE, PIKNIC_PROGRAM_PATH)
JAZZFEST_PORTAL = join_portal(JAZZFEST_BASE, JAZZFEST_PROGRAM_PATH)


# ── Source registry (static info dicts) ──────────────────────────────────────

SOURCES: dict[str, SourceInfo] = {
    "donnees_quebec": {
        "key": "donnees_quebec",
        "label": "Données Québec (CKAN)",
        "portal_url": DQ_BASE,
        "api_url": DQ_API,
        "source": "donnees_quebec",
        "notes": "Catalogue provincial + municipalités partenaires",
    },
    "montreal": {
        "key": "montreal",
        "label": "Données Montréal (CKAN)",
        "portal_url": MTL_BASE,
        "api_url": MTL_API,
        "source": "montreal",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "igo": {
        "key": "igo",
        "label": "IGO / geoegl (WMS/WFS)",
        "portal_url": GEO_OGC,
        "api_url": GEO_OGC,
        "source": "igo",
        "notes": "Couches gouvernementales Québec",
    },
    "adresses_quebec": {
        "key": "adresses_quebec",
        "label": "Adresses Québec (ICherche)",
        "portal_url": GEOCODER,
        "api_url": GEOCODER,
        "source": "adresses_quebec",
    },
    "vitrine": {
        "key": "vitrine",
        "label": "Vitrine linguistique (OQLF)",
        "portal_url": VITRINE_BASE,
        "source": "vitrine_linguistique",
    },
    "nosorigines": {
        "key": "nosorigines",
        "label": "NosOrigines",
        "portal_url": NOSORIGINES_BASE,
        "source": "nosorigines",
        "notes": "Généalogie publique ; respecter affichages Privé",
    },
    "labicyclette": {
        "key": "labicyclette",
        "label": "La bicyclette (comptages vélo Montréal)",
        "portal_url": LABICYCLETTE_BASE,
        "source": "labicyclette",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "collectemtl": {
        "key": "collectemtl",
        "label": "Collecte MTL",
        "portal_url": COLLECTEMTL_BASE,
        "source": "collectemtl",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "murales": {
        "key": "murales",
        "label": "Murales financées Montréal",
        "portal_url": mtl_dataset_url(MURALES_DATASET_ID),
        "dataset_id": MURALES_DATASET_ID,
        "resource_id": MURALES_RESOURCE_ID,
        "viewer_url": MURALES_VIEWER,
        "source": "murales",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "avis_alertes": {
        "key": "avis_alertes",
        "label": "Avis et alertes Montréal",
        "portal_url": mtl_dataset_url(AVIS_ALERTES_DATASET_ID),
        "dataset_id": AVIS_ALERTES_DATASET_ID,
        "resource_id": AVIS_ALERTES_GEOJSON_RESOURCE_ID,
        "viewer_url": AVIS_ALERTES_VIEWER,
        "api_url": AVIS_ALERTES_GEOJSON,
        "source": "avis_alertes",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "parcs": {
        "key": "parcs",
        "label": "Grands parcs et espaces publics",
        "portal_url": mtl_dataset_url(PARCS_DATASET_ID),
        "dataset_id": PARCS_DATASET_ID,
        "resource_id": PARCS_GEOJSON_RESOURCE_ID,
        "api_url": PARCS_GEOJSON,
        "source": "parcs",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "bixi": {
        "key": "bixi",
        "label": "BIXI - état des stations (GBFS)",
        "portal_url": mtl_dataset_url(BIXI_DATASET_ID),
        "dataset_id": BIXI_DATASET_ID,
        "api_url": BIXI_STATION_INFO,
        "source": "bixi",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": f"Live GBFS: {BIXI_GBFS_BASE}",
    },
    "qualo": {
        "key": "qualo",
        "label": "RSMA QUALO - qualité de l'eau en rive",
        "portal_url": mtl_dataset_url(QUALO_DATASET_ID),
        "dataset_id": QUALO_DATASET_ID,
        "resource_id": QUALO_RESOURCE_ID,
        "source": "qualo",
        "license": MTL_OPEN_DATA_LICENSE,
    },
    "evenements_publics": {
        "key": "evenements_publics",
        "label": "Événements publics Montréal",
        "portal_url": dq_dataset_url(EVENEMENTS_PACKAGE_ID),
        "dataset_id": EVENEMENTS_PACKAGE_ID,
        "resource_id": EVENEMENTS_CSV_RESOURCE_ID,
        "source": "donnees_quebec",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": "Aussi sur donnees.montreal.ca (même CSV DataStore)",
    },
    "hydro_infopannes": {
        "key": "hydro_infopannes",
        "label": "Hydro-Québec Info-pannes",
        "portal_url": HYDRO_INFOPANNES_PORTAL,
        "api_url": HYDRO_INFOPANNES_API,
        "source": "hydro_quebec_infopannes",
        "notes": "Wrapper communautaire - données approximatives",
    },
    "piknic": {
        "key": "piknic",
        "label": "Piknic Électronik",
        "portal_url": PIKNIC_PORTAL,
        "source": "piknic",
    },
    "jazzfest": {
        "key": "jazzfest",
        "label": "Festival International de Jazz de Montréal",
        "portal_url": JAZZFEST_PORTAL,
        "source": "jazzfest",
        "notes": "Page souvent JS-only ; warning si HTML vide",
    },
}


def get_source(key: str) -> SourceInfo:
    """Lookup a source by key; raises KeyError if unknown."""
    return SOURCES[key]


def source_labels() -> list[str]:
    """Short labels for ``common_get_version`` / docs."""
    return [f"{info['label']} - {info['portal_url']}" for info in SOURCES.values()]


def source_capabilities() -> dict[str, bool]:
    """Capability flags derived from registered sources."""
    return {
        "donnees_quebec": True,
        "ville_montreal": True,
        "geospatial_igo": True,
        "geocoding": True,
        "coordinate_conversion": True,
        "non_datastore_download": True,
        "labicyclette": "labicyclette" in SOURCES,
        "collectemtl": "collectemtl" in SOURCES,
        "murales": "murales" in SOURCES,
        "avis_alertes": "avis_alertes" in SOURCES,
        "bixi": "bixi" in SOURCES,
        "parcs": "parcs" in SOURCES,
        "qualo": "qualo" in SOURCES,
        "hydro_infopannes": "hydro_infopannes" in SOURCES,
        "festivals": "piknic" in SOURCES and "jazzfest" in SOURCES,
    }


def as_flat_urls() -> dict[str, str]:
    """Flat map of every string constant (for debugging / docs dumps)."""
    out: dict[str, Any] = {
        "DQ_API": DQ_API,
        "DQ_BASE": DQ_BASE,
        "MTL_API": MTL_API,
        "MTL_BASE": MTL_BASE,
        "GEO_OGC": GEO_OGC,
        "GEOCODER": GEOCODER,
        "VITRINE_BASE": VITRINE_BASE,
        "NOSORIGINES_BASE": NOSORIGINES_BASE,
        "LABICYCLETTE_BASE": LABICYCLETTE_BASE,
        "COLLECTEMTL_BASE": COLLECTEMTL_BASE,
        "HYDRO_INFOPANNES_API": HYDRO_INFOPANNES_API,
        "HYDRO_INFOPANNES_PORTAL": HYDRO_INFOPANNES_PORTAL,
        "PIKNIC_PORTAL": PIKNIC_PORTAL,
        "JAZZFEST_PORTAL": JAZZFEST_PORTAL,
        "MURALES_VIEWER": MURALES_VIEWER,
        "AVIS_ALERTES_GEOJSON": AVIS_ALERTES_GEOJSON,
        "AVIS_ALERTES_VIEWER": AVIS_ALERTES_VIEWER,
        "PARCS_GEOJSON": PARCS_GEOJSON,
        "BIXI_STATION_INFO": BIXI_STATION_INFO,
        "BIXI_STATION_STATUS": BIXI_STATION_STATUS,
        "GITHUB_REPO": GITHUB_REPO,
    }
    return {k: str(v) for k, v in out.items()}
