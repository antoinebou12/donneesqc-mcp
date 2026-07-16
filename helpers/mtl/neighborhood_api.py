"""Briefing de quartier Montréal - fan-out Hydro + avis + QUALO + parcs + BIXI."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from helpers.common.config import (
    AVIS_ALERTES_DATASET_ID,
    AVIS_ALERTES_VIEWER_URL,
    BIXI_DATASET_ID,
    HYDRO_INFOPANNES_PORTAL_URL,
    MTL_BASE_URL,
    PARCS_DATASET_ID,
    QUALO_DATASET_ID,
)
from helpers.common.urls import mtl_dataset_url
from helpers.mtl import avis_api, bixi_api, parcs_api, qualo_api
from helpers.mtl.nearby import resolve_user_point
from helpers.qc.hydro import address_resolve, infopannes_api

logger = logging.getLogger(__name__)

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50

_SOURCE_AVIS = mtl_dataset_url(AVIS_ALERTES_DATASET_ID, base=MTL_BASE_URL)
_SOURCE_QUALO = mtl_dataset_url(QUALO_DATASET_ID, base=MTL_BASE_URL)
_SOURCE_PARCS = mtl_dataset_url(PARCS_DATASET_ID, base=MTL_BASE_URL)
_SOURCE_BIXI = mtl_dataset_url(BIXI_DATASET_ID, base=MTL_BASE_URL)


def _clamp_radius(value: float, *, name: str) -> float:
    if not (_MIN_RADIUS_M <= value <= _MAX_RADIUS_M):
        msg = f"{name} doit etre entre {_MIN_RADIUS_M:g} et {_MAX_RADIUS_M:g}."
        raise ValueError(msg)
    return float(value)


def _section_error(exc: BaseException) -> dict[str, str]:
    return {"error": str(exc) or exc.__class__.__name__}


def default_date() -> str:
    """Date locale Montréal (America/Toronto) au format YYYY-MM-DD."""
    from helpers.common.context import resolve_now

    return resolve_now()["date"]


async def _hydro_section(
    *,
    address: str | None,
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    if address and address.strip():
        civic = await address_resolve.resolve_civic(address=address.strip())
    else:
        civic = await address_resolve.resolve_civic(latitude=latitude, longitude=longitude)
    status = await infopannes_api.outage_status_for_civic(
        street_number=str(civic["street_number"]),
        street=str(civic["street"]),
        postal_code=str(civic["postal_code"]),
    )
    lieux = status.get("lieux") or []
    return {
        "total": status.get("total", len(lieux)),
        "lieux": lieux,
        "resolved_address": {
            "street_number": civic.get("street_number"),
            "street": civic.get("street"),
            "postal_code": civic.get("postal_code"),
            "municipality": civic.get("municipality"),
            "address": civic.get("address"),
            "latitude": civic.get("latitude"),
            "longitude": civic.get("longitude"),
        },
        "note": status.get("note"),
        "source": HYDRO_INFOPANNES_PORTAL_URL,
    }


async def _avis_section(
    *,
    date_str: str,
    address: str | None,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> dict[str, Any]:
    data = await avis_api.list_nearby(
        date=date_str,
        address=address,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
        limit=limit,
    )
    return {
        "total": data.get("total", 0),
        "alerts": data.get("alerts") or [],
        "nearest_google_maps_directions_url": data.get("nearest_google_maps_directions_url"),
        "source": _SOURCE_AVIS,
        "viewer_url": AVIS_ALERTES_VIEWER_URL,
    }


async def _qualo_section(
    *,
    address: str | None,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> dict[str, Any]:
    data = await qualo_api.list_nearby(
        address=address,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
        limit=limit,
    )
    return {
        "total": data.get("total", 0),
        "stations": data.get("stations") or data.get("measures") or [],
        "nearest_google_maps_directions_url": data.get("nearest_google_maps_directions_url"),
        "bathing_threshold_ufc": data.get("bathing_threshold_ufc", qualo_api.BATHING_THRESHOLD_UFC),
        "note": data.get("note"),
        "source": _SOURCE_QUALO,
    }


async def _parks_section(
    *,
    address: str | None,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> dict[str, Any]:
    data = await parcs_api.list_nearby(
        address=address,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
        limit=limit,
        parks_only=False,
    )
    items = [
        {
            "nom": p.get("nom") or p.get("name"),
            "type": p.get("type"),
            "distance_m": p.get("distance_m"),
            "google_maps_url": p.get("google_maps_url"),
            "google_maps_directions_url": p.get("google_maps_directions_url"),
        }
        for p in (data.get("items") or data.get("parks") or [])
    ]
    return {
        "total": data.get("total", len(items)),
        "items": items,
        "nearest_google_maps_directions_url": data.get("nearest_google_maps_directions_url"),
        "source": _SOURCE_PARCS,
    }


async def _bixi_section(
    *,
    address: str | None,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> dict[str, Any]:
    data = await bixi_api.list_nearby(
        address=address,
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
        limit=limit,
    )
    stations = [
        {
            "name": s.get("name"),
            "num_bikes_available": s.get("num_bikes_available", s.get("bikes_available")),
            "num_docks_available": s.get("num_docks_available", s.get("docks_available")),
            "distance_m": s.get("distance_m"),
            "google_maps_url": s.get("google_maps_url"),
            "google_maps_directions_url": s.get("google_maps_directions_url"),
        }
        for s in (data.get("stations") or [])
    ]
    return {
        "total": data.get("total", len(stations)),
        "stations": stations,
        "nearest_google_maps_directions_url": data.get("nearest_google_maps_directions_url"),
        "source": _SOURCE_BIXI,
    }


def _build_summary(
    hydro: dict[str, Any],
    avis: dict[str, Any],
    water: dict[str, Any],
    parks: dict[str, Any],
    bixi: dict[str, Any],
) -> dict[str, Any]:
    hydro_ok: bool | None = None
    if "error" not in hydro:
        lieux = hydro.get("lieux") or []
        hydro_ok = bool(lieux) and all(not lieu.get("has_outage") for lieu in lieux)

    avis_count: int | None = None if "error" in avis else int(avis.get("total") or 0)

    qualo_bathing_ok: bool | None = None
    if "error" not in water:
        stations = water.get("stations") or []
        threshold = float(water.get("bathing_threshold_ufc") or qualo_api.BATHING_THRESHOLD_UFC)
        if stations:
            vals: list[float] = []
            for st in stations:
                raw = st.get("coliformes_fecaux")
                try:
                    vals.append(float(raw))
                except (TypeError, ValueError):
                    continue
            qualo_bathing_ok = bool(vals) and all(v <= threshold for v in vals)
        else:
            qualo_bathing_ok = None

    parks_count: int | None = None if "error" in parks else int(parks.get("total") or 0)
    bixi_stations: int | None = None if "error" in bixi else int(bixi.get("total") or 0)

    return {
        "hydro_ok": hydro_ok,
        "avis_count": avis_count,
        "qualo_bathing_ok": qualo_bathing_ok,
        "parks_count": parks_count,
        "bixi_stations": bixi_stations,
    }


async def build_briefing(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    date: str | None = None,
    avis_radius_m: float = 1000.0,
    parks_radius_m: float = 300.0,
    bixi_radius_m: float = 400.0,
    qualo_radius_m: float = 1500.0,
    limit: int = 10,
) -> dict[str, Any]:
    """Assemble un briefing multi-sources avec succès partiel par section."""
    lim = max(1, min(int(limit), _MAX_LIMIT))
    avis_r = _clamp_radius(avis_radius_m, name="avis_radius_m")
    parks_r = _clamp_radius(parks_radius_m, name="parks_radius_m")
    bixi_r = _clamp_radius(bixi_radius_m, name="bixi_radius_m")
    # QUALO may go beyond 5 km; clamp with its own helper limits via list_nearby
    if qualo_radius_m < _MIN_RADIUS_M:
        msg = f"qualo_radius_m doit etre >= {_MIN_RADIUS_M:g}."
        raise ValueError(msg)
    if qualo_radius_m > 15000.0:
        msg = "qualo_radius_m doit etre <= 15000."
        raise ValueError(msg)
    qualo_r = float(qualo_radius_m)

    date_str = (date or "").strip() or default_date()
    avis_api.parse_date(date_str)  # validate early

    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    query_lat = loc["latitude"]
    query_lon = loc["longitude"]
    resolved = loc.get("resolved_address")
    addr_for_sections = resolved or (address.strip() if address and address.strip() else None)

    hydro_t = _hydro_section(address=addr_for_sections, latitude=query_lat, longitude=query_lon)
    avis_t = _avis_section(
        date_str=date_str,
        address=addr_for_sections,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=avis_r,
        limit=lim,
    )
    qualo_t = _qualo_section(
        address=addr_for_sections,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=qualo_r,
        limit=lim,
    )
    parks_t = _parks_section(
        address=addr_for_sections,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=parks_r,
        limit=lim,
    )
    bixi_t = _bixi_section(
        address=addr_for_sections,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=bixi_r,
        limit=lim,
    )

    results = await asyncio.gather(
        hydro_t,
        avis_t,
        qualo_t,
        parks_t,
        bixi_t,
        return_exceptions=True,
    )

    sections: list[dict[str, Any]] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("neighborhood section failed: %s", result)
            sections.append(_section_error(result))
        else:
            sections.append(result)

    hydro, avis, water, parks, bixi = sections
    return {
        "query": {
            "address": addr_for_sections,
            "latitude": query_lat,
            "longitude": query_lon,
            "date": date_str,
            "location_source": loc.get("location_source"),
            "radii": {
                "avis_m": avis_r,
                "parks_m": parks_r,
                "bixi_m": bixi_r,
                "qualo_m": qualo_r,
            },
            "limit": lim,
        },
        "summary": _build_summary(hydro, avis, water, parks, bixi),
        "hydro": hydro,
        "avis": avis,
        "water_quality": water,
        "parks": parks,
        "bixi": bixi,
    }
