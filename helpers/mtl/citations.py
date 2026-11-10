"""Citations / licence partagées pour les tools Montréal (murales, collecte, etc.)."""

from __future__ import annotations

from typing import Any

from helpers.common.config import (
    AVIS_ALERTES_DATASET_ID,
    AVIS_ALERTES_GEOJSON_RESOURCE_ID,
    AVIS_ALERTES_VIEWER_URL,
    BIXI_DATASET_ID,
    CINEMACLOCK_BASE_URL,
    CINEMACLOCK_THEATERS_URL,
    ENTRAVES_DATASET_ID,
    INFONEIGE_BASE_URL,
    LABICYCLETTE_BASE_URL,
    MTL_BASE_URL,
    MURALES_DATASET_ID,
    MURALES_RESOURCE_ID,
    MURALES_VIEWER_URL,
    PARCS_DATASET_ID,
    PARCS_GEOJSON_RESOURCE_ID,
    PARKING_DENEIGEMENT_DATASET_ID,
    PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID,
    PARKING_SIGNALISATION_DATASET_ID,
    PARKING_SIGNALISATION_RESOURCE_ID,
    PERMIS_DATASET_ID,
    PERMIS_RESOURCE_ID,
    PERMIS_VIEWER_URL,
    QUALO_DATASET_ID,
    QUALO_RESOURCE_ID,
    REM_PORTAL_URL,
    STM_DEVELOPERS_PORTAL_URL,
    STM_TRACES_DATASET_ID,
)
from helpers.common.response import ok
from helpers.common.urls import (
    MTL_OPEN_DATA_LICENSE,
    REM_OPEN_DATA_LICENSE,
    SourceInfo,
    get_source,
    mtl_dataset_url,
)

# Re-export for callers that imported the license from citations.
__all__ = [
    "MTL_OPEN_DATA_LICENSE",
    "REM_OPEN_DATA_LICENSE",
    "avis_ok",
    "bixi_ok",
    "cinemas_ok",
    "collecte_ok",
    "entraves_ok",
    "infoneige_ok",
    "labicyclette_ok",
    "mtl_open_ok",
    "murales_ok",
    "neighborhood_ok",
    "parcs_ok",
    "parking_deneigement_ok",
    "parking_signalisation_ok",
    "permis_ok",
    "qualo_ok",
    "rem_ok",
    "stm_ok",
    "weather_ok",
]


def _source_ok(
    payload: dict[str, Any],
    info: SourceInfo,
    *,
    portal_url: str | None = None,
    extra: dict[str, Any] | None = None,
    dataset_id: str | None = None,
    resource_id: str | None = None,
) -> str:
    """Build ok() from a SOURCES entry (+ optional runtime portal overrides)."""
    body = {**(extra or {}), **payload}
    ds_id = dataset_id if dataset_id is not None else info.get("dataset_id")
    res_id = resource_id if resource_id is not None else info.get("resource_id")
    portal = portal_url or info["portal_url"]
    if "dataset_url" not in body and ds_id and portal.startswith(MTL_BASE_URL):
        body.setdefault("dataset_url", portal)
    if info.get("viewer_url"):
        body.setdefault("viewer_url", info["viewer_url"])
    return ok(
        body,
        source=info["source"],
        portal_url=portal,
        dataset_id=ds_id,
        resource_id=res_id,
        license=info.get("license") or MTL_OPEN_DATA_LICENSE,
    )


def avis_ok(payload: dict[str, Any]) -> str:
    """ok() avec métadonnées avis/alertes Montréal."""
    info = get_source("avis_alertes")
    dataset_url = mtl_dataset_url(AVIS_ALERTES_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url, "viewer_url": AVIS_ALERTES_VIEWER_URL},
        dataset_id=AVIS_ALERTES_DATASET_ID,
        resource_id=AVIS_ALERTES_GEOJSON_RESOURCE_ID,
    )


def murales_ok(payload: dict[str, Any]) -> str:
    """ok() avec métadonnées murales (dataset + viewer)."""
    info = get_source("murales")
    dataset_url = mtl_dataset_url(MURALES_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url, "viewer_url": MURALES_VIEWER_URL},
        dataset_id=MURALES_DATASET_ID,
        resource_id=MURALES_RESOURCE_ID,
    )


def labicyclette_ok(payload: dict[str, Any]) -> str:
    """ok() avec citation La bicyclette."""
    return _source_ok(payload, get_source("labicyclette"), portal_url=LABICYCLETTE_BASE_URL)


def collecte_ok(
    payload: dict[str, Any],
    *,
    portal_url: str,
    dataset_id: str | None = None,
) -> str:
    """ok() avec citation Collecte MTL."""
    return _source_ok(
        payload,
        get_source("collectemtl"),
        portal_url=portal_url,
        dataset_id=dataset_id,
    )


def parcs_ok(payload: dict[str, Any]) -> str:
    """ok() pour parcs / espaces verts Montréal."""
    info = get_source("parcs")
    dataset_url = mtl_dataset_url(PARCS_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=PARCS_DATASET_ID,
        resource_id=PARCS_GEOJSON_RESOURCE_ID,
    )


def bixi_ok(payload: dict[str, Any]) -> str:
    """ok() pour stations BIXI (GBFS)."""
    info = get_source("bixi")
    dataset_url = mtl_dataset_url(BIXI_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=BIXI_DATASET_ID,
    )


def stm_ok(payload: dict[str, Any]) -> str:
    """ok() pour STM GTFS-RT / i3 / arrêts bundlés."""
    info = get_source("stm")
    traces_url = mtl_dataset_url(STM_TRACES_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=STM_DEVELOPERS_PORTAL_URL,
        extra={
            "developers_url": STM_DEVELOPERS_PORTAL_URL,
            "dataset_url": traces_url,
        },
        dataset_id=STM_TRACES_DATASET_ID,
    )


def rem_ok(payload: dict[str, Any]) -> str:
    """ok() pour REM GTFS-RT alertes / état réseau / actualités / arrêts bundlés."""
    info = get_source("rem")
    return ok(
        payload,
        source=info["source"],
        portal_url=REM_PORTAL_URL,
        license=info.get("license") or REM_OPEN_DATA_LICENSE,
    )


def qualo_ok(payload: dict[str, Any]) -> str:
    """ok() pour RSMA QUALO."""
    info = get_source("qualo")
    dataset_url = mtl_dataset_url(QUALO_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=QUALO_DATASET_ID,
        resource_id=QUALO_RESOURCE_ID,
    )


def permis_ok(payload: dict[str, Any]) -> str:
    """ok() pour permis de construction Montréal."""
    info = get_source("permis")
    dataset_url = mtl_dataset_url(PERMIS_DATASET_ID, base=MTL_BASE_URL)
    # Drop null note so JSON stays clean when unused.
    body = {k: v for k, v in payload.items() if k != "note" or v is not None}
    return _source_ok(
        body,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url, "viewer_url": PERMIS_VIEWER_URL},
        dataset_id=PERMIS_DATASET_ID,
        resource_id=PERMIS_RESOURCE_ID,
    )


def parking_deneigement_ok(payload: dict[str, Any]) -> str:
    """ok() pour stationnements déneigement Montréal."""
    info = get_source("parking_deneigement")
    dataset_url = mtl_dataset_url(PARKING_DENEIGEMENT_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=PARKING_DENEIGEMENT_DATASET_ID,
        resource_id=PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID,
    )


def parking_signalisation_ok(payload: dict[str, Any]) -> str:
    """ok() pour signalisation stationnement (interdictions)."""
    info = get_source("parking_signalisation")
    dataset_url = mtl_dataset_url(PARKING_SIGNALISATION_DATASET_ID, base=MTL_BASE_URL)
    body = {k: v for k, v in payload.items() if k != "note" or v is not None}
    return _source_ok(
        body,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=PARKING_SIGNALISATION_DATASET_ID,
        resource_id=PARKING_SIGNALISATION_RESOURCE_ID,
    )


def entraves_ok(payload: dict[str, Any]) -> str:
    """ok() pour entraves circulation CIFS."""
    info = get_source("entraves")
    dataset_url = mtl_dataset_url(ENTRAVES_DATASET_ID, base=MTL_BASE_URL)
    return _source_ok(
        payload,
        info,
        portal_url=dataset_url,
        extra={"dataset_url": dataset_url},
        dataset_id=ENTRAVES_DATASET_ID,
    )


def infoneige_ok(payload: dict[str, Any]) -> str:
    """ok() pour Info Neige (HTML citoyen)."""
    info = get_source("infoneige")
    return ok(
        payload,
        source=info["source"],
        portal_url=INFONEIGE_BASE_URL,
        license=info.get("license"),
    )


def weather_ok(payload: dict[str, Any]) -> str:
    """ok() pour météo Open-Meteo."""
    info = get_source("open_meteo")
    return ok(
        payload,
        source=info["source"],
        portal_url=info["portal_url"],
        license=info.get("license"),
    )


def cinemas_ok(payload: dict[str, Any]) -> str:
    """ok() pour CinemaClock (cinémas near-me, HTML non officiel)."""
    info = get_source("cinemaclock")
    body = {
        **payload,
        "theaters_url": payload.get("source_url") or CINEMACLOCK_THEATERS_URL,
    }
    return ok(
        body,
        source=info["source"],
        portal_url=payload.get("portal_url") or CINEMACLOCK_BASE_URL,
        license=info.get("license"),
    )


def neighborhood_ok(payload: dict[str, Any]) -> str:
    """ok() pour le briefing de quartier (sources multiples)."""
    return ok(
        payload,
        source="mtl_neighborhood_briefing",
        portal_url=MTL_BASE_URL,
        license=MTL_OPEN_DATA_LICENSE,
        dataset_id=(
            f"{AVIS_ALERTES_DATASET_ID};{QUALO_DATASET_ID};{PARCS_DATASET_ID};"
            f"{BIXI_DATASET_ID};{PERMIS_DATASET_ID};{PARKING_DENEIGEMENT_DATASET_ID};"
            f"{PARKING_SIGNALISATION_DATASET_ID};"
            f"{ENTRAVES_DATASET_ID};infoneige;actes-criminels;"
            f"sit-quebec-restauration;hydro_quebec_infopannes;vmtl-evenements-publics;"
            f"collectemtl;cinemaclock"
        ),
    )


def mtl_open_ok(
    payload: dict[str, Any],
    *,
    source: str,
    portal_url: str,
    dataset_id: str | None = None,
    resource_id: str | None = None,
) -> str:
    """ok() générique pour données ouvertes Montréal."""
    return ok(
        payload,
        source=source,
        portal_url=portal_url,
        dataset_id=dataset_id,
        resource_id=resource_id,
        license=MTL_OPEN_DATA_LICENSE,
    )
