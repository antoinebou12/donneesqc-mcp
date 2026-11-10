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
MTL_311_DATASET_ID = "requete-311"
MTL_311_RESOURCE_ID = "2cfa0e06-9be4-49a6-b7f1-ee9f2363a872"
MTL_311_SOURCE_URL = "https://donnees.montreal.ca/dataset/requete-311"
DQ_311_SOURCE_URL = "https://www.donneesquebec.ca/recherche/dataset/vmtl-requete-311"
MTL_PLANNED_WORKS_RESOURCE_ID = "cc41b532-f12d-40fb-9f55-eb58c9a2b12b"
MTL_PLANNED_WORKS_SOURCE_URL = "https://www.donneesquebec.ca/recherche/dataset/vmtl-info-travaux"
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

LA_PRESSE_BASE = "https://www.lapresse.ca"
LE_DEVOIR_BASE = "https://www.ledevoir.com"
JOURNAL_DE_MONTREAL_BASE = "https://www.journaldemontreal.com"
JOURNAL_DE_QUEBEC_BASE = "https://www.journaldequebec.com"
RADIO_CANADA_BASE = "https://ici.radio-canada.ca"
GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"

PLANHUB_BASE = "https://www.planhub.ca"
PLANHUB_COMPARE_PATH = "/quebec/compare-internet-plan"
PLANHUB_PROVIDERS_PATH = "/internet-providers-information"

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

# STM GTFS-RT / i3 (requires free API key from stm.info/developers)
STM_DEVELOPERS_PORTAL = "https://www.stm.info/fr/a-propos/developpeurs"
STM_GTFS_STATIC_ZIP = "https://www.stm.info/sites/default/files/gtfs/gtfs_stm.zip"
STM_GTFS_RT_BASE = "https://api.stm.info/pub/od/gtfs-rt/ic/v2"
STM_VEHICLE_POSITIONS_URL = f"{STM_GTFS_RT_BASE}/vehiclePositions"
STM_TRIP_UPDATES_URL = f"{STM_GTFS_RT_BASE}/tripUpdates"
STM_I3_BASE = "https://api.stm.info/pub/od/i3/v2/messages"
STM_SERVICE_ALERTS_URL = f"{STM_I3_BASE}/etatservice"
STM_TRACES_DATASET_ID = "stm-traces-des-lignes-de-bus-et-de-metro"
STM_OPEN_DATA_LICENSE = "CC BY 4.0 (STM / données ouvertes)"

# REM (Réseau express métropolitain) — GTFS static + GTFS-RT alerts (no API key)
REM_PORTAL = "https://rem.info"
REM_STATUS_URL_FR = f"{REM_PORTAL}/fr/se-deplacer/etat-du-service"
REM_STATUS_URL_EN = f"{REM_PORTAL}/en/travelling/network-status"
REM_NEWS_URL_FR = f"{REM_PORTAL}/fr/actualites"
REM_NEWS_URL_EN = f"{REM_PORTAL}/en/news"
REM_RSS_URL_FR = f"{REM_PORTAL}/fr/rss.xml"
REM_RSS_URL_EN = f"{REM_PORTAL}/en/rss.xml"
REM_GTFS_STATIC_ZIP = "https://gtfs.gpmmom.ca/gtfs/gtfs.zip"
REM_GTFS_RT_ALERTS_URL = "https://storage.googleapis.com/transit-terminal-alerts-bucket-production/rem_montreal.pb"
REM_OPEN_DATA_LICENSE = "CC BY 4.0 (REM / Données Québec)"

QUALO_DATASET_ID = "rsma-qualite-de-l-eau-en-rive-qualo"
QUALO_RESOURCE_ID = "9136d84a-8273-4777-ad68-9ab05d270322"

EVENEMENTS_PACKAGE_ID = "vmtl-evenements-publics"
EVENEMENTS_CSV_RESOURCE_ID = "6decf611-6f11-4f34-bb36-324d804c9bad"

PERMIS_DATASET_ID = "permis-construction"
PERMIS_RESOURCE_ID = "5232a72d-235a-48eb-ae20-bb9d501300ad"
PERMIS_VIEWER = (
    "https://app.powerbi.com/view?r="
    # Public Power BI report identifier, not a credential.
    "eyJrIjoiYjAxYzI1M2UtMjA0MC00ODM5LWI2ODMtMzVjNjNiNjU2NmZhIiwidCI6IjlmMTVkMmRjLTg3NTMtNGY4My1hYWMyLWE1ODI4OGQzYTRiYyJ9"  # pragma: allowlist secret  # noqa: E501
)

# Stationnements gratuits/payants (déneigement) — saisonnier GeoJSON
PARKING_DENEIGEMENT_DATASET_ID = "stationnements-deneigement"
PARKING_DENEIGEMENT_DQ_DATASET_ID = "vmtl-stationnements-deneigement"
PARKING_DENEIGEMENT_PACKAGE_UUID = "575ecf37-9097-44cd-817f-a2fbd8de314b"
PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID = "def63739-6295-4745-97e9-74755ee0bf92"
PARKING_DENEIGEMENT_GEOJSON = (
    f"{MTL_BASE}/dataset/{PARKING_DENEIGEMENT_PACKAGE_UUID}"
    f"/resource/{PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID}"
    "/download/stationnements-h-2025-2026.geojson"
)

# Entraves à la circulation (CIFS temps réel)
ENTRAVES_DATASET_ID = "entraves-circulation"
ENTRAVES_DQ_DATASET_ID = "vmtl-entraves-circulation"
ENTRAVES_PACKAGE_UUID = "3df48f53-10a4-424d-bfbc-9aea3feac402"
ENTRAVES_CIFS_JSON = "https://api.montreal.ca/api/transportation/traffic-events-api/v1/export-cifs?type=json"

# Info Neige (viewer citoyen Planif-Neige — HTML, pas d'API jeton Ville)
INFONEIGE_BASE = "https://www.infoneige.ca"
INFONEIGE_SEARCH_PATH = "/vdm/recherche.php"
INFONEIGE_MAP_PATH = "/vdm/map.php"
INFONEIGE_AIDE_URL = f"{INFONEIGE_BASE}/vdm/aide.php"

# Open-Meteo (live weather — no API key; CC BY 4.0 attribution required)
OPEN_METEO_BASE = "https://api.open-meteo.com"
OPEN_METEO_FORECAST_URL = f"{OPEN_METEO_BASE}/v1/forecast"
OPEN_METEO_DOCS_URL = "https://open-meteo.com/en/docs"
OPEN_METEO_LICENSE = "CC BY 4.0 (Open-Meteo)"
OPEN_METEO_ATTRIBUTION = "Weather data by Open-Meteo.com (CC BY 4.0)"

# CinemaClock (showtimes / theatres — unofficial HTML scrape)
# Near-me SSR lives on /cinemas (canonical); /movie-theaters alone often has no blocks.
CINEMACLOCK_BASE = "https://www.cinemaclock.com"
CINEMACLOCK_THEATERS_PATH = "/cinemas"
CINEMACLOCK_THEATERS_URL = f"{CINEMACLOCK_BASE}{CINEMACLOCK_THEATERS_PATH}"
CINEMACLOCK_MONTREAL_FR = f"{CINEMACLOCK_BASE}/montreal-qc/fr"

CRIME_DATASET_ID = "actes-criminels"
CRIME_RESOURCE_ID = "c6f482bf-bf0f-4960-8b2f-9982c211addd"

# Signalisation stationnement sur rue (panneaux RPA courants)
PARKING_SIGNALISATION_DATASET_ID = "stationnement-sur-rue-signalisation-courant"
PARKING_SIGNALISATION_RESOURCE_ID = "7f1d4ae9-1a12-46d7-953e-6b9c18c78680"

# SIT Québec (Système d'information touristique) — restauration
SIT_RESTAURATION_DATASET_ID = "sit-quebec-restauration"
SIT_RESTAURATION_RESOURCE_ID = "64d52e5a-5cc5-40ce-a0c4-96c318087e97"
DQ_OPEN_DATA_LICENSE = "Licence ouverte / Creative Commons (Données Québec — vérifier sur le jeu)"

# IP geolocation (client IP only - never host egress). Template uses {ip}.
IP_GEO_URL_TEMPLATE = "https://ipapi.co/{ip}/json/"

MTL_OPEN_DATA_LICENSE = "CC BY 4.0 (Ville de Montréal open data)"
HTTP_USER_AGENT_DEFAULT = "mtl-mcp (https://github.com/Stefen-Taime/mtl-mcp)"
GITHUB_REPO = "https://github.com/Stefen-Taime/mtl-mcp"


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
PLANHUB_PORTAL = join_portal(PLANHUB_BASE, PLANHUB_COMPARE_PATH)


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
    "stm": {
        "key": "stm",
        "label": "STM - transport en commun (GTFS-RT / i3)",
        "portal_url": STM_DEVELOPERS_PORTAL,
        "dataset_id": STM_TRACES_DATASET_ID,
        "api_url": STM_GTFS_RT_BASE,
        "source": "stm",
        "license": STM_OPEN_DATA_LICENSE,
        "notes": (
            f"GTFS-RT + i3 nécessitent STM_API_KEY ; arrêts bundlés depuis GTFS static ; "
            f"traces/arrêts aussi sur {mtl_dataset_url(STM_TRACES_DATASET_ID)}"
        ),
    },
    "rem": {
        "key": "rem",
        "label": "REM - Réseau express métropolitain",
        "portal_url": REM_PORTAL,
        "api_url": REM_GTFS_RT_ALERTS_URL,
        "source": "rem",
        "license": REM_OPEN_DATA_LICENSE,
        "notes": (
            f"GTFS-RT alertes (pas de clé) ; état réseau/ascenseurs via {REM_STATUS_URL_FR} ; "
            f"arrêts bundlés depuis {REM_GTFS_STATIC_ZIP} ; pas de tripUpdates/vehiclePositions publics"
        ),
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
    "permis": {
        "key": "permis",
        "label": "Permis de construction, transformation et démolition",
        "portal_url": mtl_dataset_url(PERMIS_DATASET_ID),
        "dataset_id": PERMIS_DATASET_ID,
        "resource_id": PERMIS_RESOURCE_ID,
        "viewer_url": PERMIS_VIEWER,
        "source": "permis",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": "Row-level CSV has no cout_travaux_estimes; use nb_logements for scale",
    },
    "parking_deneigement": {
        "key": "parking_deneigement",
        "label": "Stationnements gratuits et payants (déneigement)",
        "portal_url": mtl_dataset_url(PARKING_DENEIGEMENT_DATASET_ID),
        "dataset_id": PARKING_DENEIGEMENT_DATASET_ID,
        "resource_id": PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID,
        "api_url": PARKING_DENEIGEMENT_GEOJSON,
        "source": "parking_deneigement",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": (
            f"Aussi sur Données Québec: {dq_dataset_url(PARKING_DENEIGEMENT_DQ_DATASET_ID)} ; "
            "GeoJSON saisonnier (rafraîchir l'URL chaque novembre)"
        ),
    },
    "entraves": {
        "key": "entraves",
        "label": "Entraves à la circulation en temps réel (CIFS)",
        "portal_url": mtl_dataset_url(ENTRAVES_DATASET_ID),
        "dataset_id": ENTRAVES_DATASET_ID,
        "api_url": ENTRAVES_CIFS_JSON,
        "source": "entraves",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": f"Aussi sur Données Québec: {dq_dataset_url(ENTRAVES_DQ_DATASET_ID)}",
    },
    "infoneige": {
        "key": "infoneige",
        "label": "Info Neige (stationnement / déneigement)",
        "portal_url": INFONEIGE_BASE,
        "viewer_url": INFONEIGE_AIDE_URL,
        "source": "infoneige",
        "notes": (
            "Viewer citoyen de Planif-Neige + données ouvertes MTL ; "
            "pas d'API jeton Ville ; la signalisation sur rue prévaut toujours"
        ),
    },
    "open_meteo": {
        "key": "open_meteo",
        "label": "Open-Meteo (conditions / prévisions)",
        "portal_url": OPEN_METEO_DOCS_URL,
        "api_url": OPEN_METEO_FORECAST_URL,
        "source": "open_meteo",
        "license": OPEN_METEO_LICENSE,
        "notes": OPEN_METEO_ATTRIBUTION,
    },
    "cinemaclock": {
        "key": "cinemaclock",
        "label": "CinemaClock (cinémas / horaires)",
        "portal_url": CINEMACLOCK_BASE,
        "viewer_url": CINEMACLOCK_THEATERS_URL,
        "source": "cinemaclock",
        "notes": ("Wrapper HTML non officiel ; cookie userlon = abs(lon) ; les mises en page peuvent changer"),
    },
    "crime": {
        "key": "crime",
        "label": "Actes criminels (SPVM)",
        "portal_url": mtl_dataset_url(CRIME_DATASET_ID),
        "dataset_id": CRIME_DATASET_ID,
        "resource_id": CRIME_RESOURCE_ID,
        "source": "crime",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": "Coordonnées approximatives; pas un indice de danger en temps réel",
    },
    "parking_signalisation": {
        "key": "parking_signalisation",
        "label": "Signalisation stationnement sur rue",
        "portal_url": mtl_dataset_url(PARKING_SIGNALISATION_DATASET_ID),
        "dataset_id": PARKING_SIGNALISATION_DATASET_ID,
        "resource_id": PARKING_SIGNALISATION_RESOURCE_ID,
        "source": "parking_signalisation",
        "license": MTL_OPEN_DATA_LICENSE,
        "notes": (
            "Sous-ensemble interdiction / arrêt-stationnement interdit / remorquage "
            "(pas un moteur tarifaire Agence mobilité)"
        ),
    },
    "sit_restauration": {
        "key": "sit_restauration",
        "label": "SIT Québec - restauration",
        "portal_url": dq_dataset_url(SIT_RESTAURATION_DATASET_ID),
        "dataset_id": SIT_RESTAURATION_DATASET_ID,
        "resource_id": SIT_RESTAURATION_RESOURCE_ID,
        "api_url": DQ_API,
        "source": "sit_restauration",
        "license": DQ_OPEN_DATA_LICENSE,
        "notes": "Établissements touristiques (restaurants, cafés, etc.) — SIT Québec",
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
    "planhub": {
        "key": "planhub",
        "label": "PlanHub (comparateur forfaits internet)",
        "portal_url": PLANHUB_PORTAL,
        "source": "planhub",
        "notes": (
            "Wrapper communautaire non officiel ; ToS PlanHub interdisent la collecte "
            "systématique — vérifier sur le site ; Cloudflare peut bloquer certains hôtes"
        ),
    },
    "la_presse": {
        "key": "la_presse",
        "label": "La Presse",
        "portal_url": LA_PRESSE_BASE,
        "source": "la_presse",
        "notes": "Agrégation RSS communautaire ; usage personnel des fils RSS",
    },
    "le_devoir": {
        "key": "le_devoir",
        "label": "Le Devoir",
        "portal_url": LE_DEVOIR_BASE,
        "source": "le_devoir",
        "notes": "Agrégation RSS communautaire ; usage personnel des fils RSS",
    },
    "journal_de_montreal": {
        "key": "journal_de_montreal",
        "label": "Le Journal de Montréal",
        "portal_url": JOURNAL_DE_MONTREAL_BASE,
        "source": "journal_de_montreal",
        "notes": "Agrégation RSS communautaire ; usage personnel des fils RSS",
    },
    "journal_de_quebec": {
        "key": "journal_de_quebec",
        "label": "Le Journal de Québec",
        "portal_url": JOURNAL_DE_QUEBEC_BASE,
        "source": "journal_de_quebec",
        "notes": "Agrégation RSS communautaire ; usage personnel des fils RSS",
    },
    "radio_canada": {
        "key": "radio_canada",
        "label": "Radio-Canada",
        "portal_url": RADIO_CANADA_BASE,
        "source": "radio_canada",
        "notes": "Fils RSS ICI Radio-Canada — usage personnel seulement",
    },
    "qc_news": {
        "key": "qc_news",
        "label": "Presse québécoise (agrégateur)",
        "portal_url": LA_PRESSE_BASE,
        "source": "qc_news",
        "notes": (
            "Agrégateur communautaire de manchettes (La Presse, Le Devoir, JdeM, JdeQ, "
            "Radio-Canada) — pas un service officiel des médias"
        ),
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
        "stm": "stm" in SOURCES,
        "rem": "rem" in SOURCES,
        "parcs": "parcs" in SOURCES,
        "qualo": "qualo" in SOURCES,
        "hydro_infopannes": "hydro_infopannes" in SOURCES,
        "festivals": "piknic" in SOURCES and "jazzfest" in SOURCES,
        "planhub": "planhub" in SOURCES,
        "qc_news": "qc_news" in SOURCES,
        "sit_restauration": "sit_restauration" in SOURCES,
        "permis": "permis" in SOURCES,
        "parking_deneigement": "parking_deneigement" in SOURCES,
        "entraves": "entraves" in SOURCES,
        "infoneige": "infoneige" in SOURCES,
        "open_meteo": "open_meteo" in SOURCES,
        "crime": "crime" in SOURCES,
        "parking_signalisation": "parking_signalisation" in SOURCES,
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
        "PLANHUB_BASE": PLANHUB_BASE,
        "PLANHUB_PORTAL": PLANHUB_PORTAL,
        "LA_PRESSE_BASE": LA_PRESSE_BASE,
        "LE_DEVOIR_BASE": LE_DEVOIR_BASE,
        "JOURNAL_DE_MONTREAL_BASE": JOURNAL_DE_MONTREAL_BASE,
        "JOURNAL_DE_QUEBEC_BASE": JOURNAL_DE_QUEBEC_BASE,
        "RADIO_CANADA_BASE": RADIO_CANADA_BASE,
        "MURALES_VIEWER": MURALES_VIEWER,
        "PERMIS_VIEWER": PERMIS_VIEWER,
        "PARKING_DENEIGEMENT_GEOJSON": PARKING_DENEIGEMENT_GEOJSON,
        "ENTRAVES_CIFS_JSON": ENTRAVES_CIFS_JSON,
        "INFONEIGE_BASE": INFONEIGE_BASE,
        "OPEN_METEO_FORECAST_URL": OPEN_METEO_FORECAST_URL,
        "CINEMACLOCK_BASE": CINEMACLOCK_BASE,
        "CINEMACLOCK_THEATERS_URL": CINEMACLOCK_THEATERS_URL,
        "AVIS_ALERTES_GEOJSON": AVIS_ALERTES_GEOJSON,
        "AVIS_ALERTES_VIEWER": AVIS_ALERTES_VIEWER,
        "PARCS_GEOJSON": PARCS_GEOJSON,
        "BIXI_STATION_INFO": BIXI_STATION_INFO,
        "BIXI_STATION_STATUS": BIXI_STATION_STATUS,
        "GITHUB_REPO": GITHUB_REPO,
    }
    return {k: str(v) for k, v in out.items()}
