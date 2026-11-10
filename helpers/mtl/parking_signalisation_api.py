"""Signalisation stationnement sur rue — interdictions proches (DataStore MTL)."""

from __future__ import annotations

import math
import re
from typing import Any

import httpx

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL, MTL_API_URL, PARKING_SIGNALISATION_RESOURCE_ID
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import haversine_m, validate_wgs84
from helpers.mtl.nearby import resolve_user_point

PARKING_SIGNALISATION_DATASET_ID = "stationnement-sur-rue-signalisation-courant"

_MAX_NEARBY = 50
_MAX_BBOX = 5000

# SIGNALEC: \A = arrêt interdit, \P = stationnement interdit; plus texte FR.
_BAD_RE = re.compile(
    r"(?:interdit|interdiction|remorqu|no[\s\-]?parking|\\+a\b|\\+p\b)",
    re.IGNORECASE,
)


def _bbox(
    latitude: float,
    longitude: float,
    radius_m: float,
) -> tuple[float, float, float, float]:
    lat_delta = radius_m / 111_320.0
    cos_lat = max(0.2, abs(math.cos(math.radians(latitude))))
    lon_delta = radius_m / (111_320.0 * cos_lat)
    return (
        latitude - lat_delta,
        latitude + lat_delta,
        longitude - lon_delta,
        longitude + lon_delta,
    )


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_restriction_sign(description: str | None, code_rpa: str | None = None) -> bool:
    """True for no-parking / no-stopping / tow-risk panels (not paid-only)."""
    text = str(description or "")
    if _BAD_RE.search(text):
        return True
    code = str(code_rpa or "").strip().upper()
    return code.startswith(("AD-", "SD-", "SLR-", "AR-"))


def normalize_sign(raw: dict[str, Any]) -> dict[str, Any]:
    """Slim row with WGS84 floats."""
    lat = _to_float(raw.get("Latitude") if "Latitude" in raw else raw.get("latitude"))
    lon = _to_float(raw.get("Longitude") if "Longitude" in raw else raw.get("longitude"))
    return {
        "description": str(raw.get("DESCRIPTION_RPA") or "").strip() or None,
        "code_rpa": str(raw.get("CODE_RPA") or "").strip() or None,
        "category": str(raw.get("DESCRIPTION_CAT") or "").strip() or None,
        "arrondissement": str(raw.get("NOM_ARROND") or "").strip() or None,
        "toponyme": str(raw.get("TOPONYME_PAN") or "").strip() or None,
        "latitude": lat,
        "longitude": lon,
    }


async def list_restrictions_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 300.0,
    limit: int = 20,
) -> dict[str, Any]:
    """Panneaux d'interdiction / stationnement interdit dans un rayon."""
    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
    lat = float(loc["latitude"])
    lon = float(loc["longitude"])
    validate_wgs84(lat, lon)
    if radius_m <= 0:
        msg = "radius_m doit etre positif."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_NEARBY))

    lat_min, lat_max, lon_min, lon_max = _bbox(lat, lon, float(radius_m))
    table = f'"{PARKING_SIGNALISATION_RESOURCE_ID}"'
    sql = (
        f'SELECT "DESCRIPTION_RPA", "CODE_RPA", "DESCRIPTION_CAT", "TOPONYME_PAN", '  # noqa: S608
        f'"NOM_ARROND", "Latitude", "Longitude" '
        f"FROM {table} "
        f'WHERE "Latitude" IS NOT NULL AND "Longitude" IS NOT NULL '
        f'AND "Latitude"::float >= {lat_min} AND "Latitude"::float <= {lat_max} '
        f'AND "Longitude"::float >= {lon_min} AND "Longitude"::float <= {lon_max} '
        f"LIMIT {_MAX_BBOX}"
    )
    try:
        result = await ckan_api.datastore_search_sql(MTL_API_URL, sql)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 409:
            raise
        # The provincial mirror exposes the same published resource and columns.
        result = await ckan_api.datastore_search_sql(DQ_API_URL, sql)

    nearby: list[dict[str, Any]] = []
    for raw in result.get("records") or []:
        if not isinstance(raw, dict):
            continue
        if not is_restriction_sign(raw.get("DESCRIPTION_RPA"), raw.get("CODE_RPA")):
            continue
        item = normalize_sign(raw)
        plat, plon = item.get("latitude"), item.get("longitude")
        if plat is None or plon is None:
            continue
        distance = haversine_m(lat, lon, float(plat), float(plon))
        if distance <= float(radius_m):
            nearby.append({**item, "distance_m": round(distance, 1)})

    nearby.sort(key=lambda r: r["distance_m"])
    signs, nearest = attach_nearby_maps(
        nearby[:lim],
        query_lat=lat,
        query_lon=lon,
    )
    return {
        "query": {
            "address": address,
            "resolved_address": loc.get("resolved_address"),
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "location_source": loc.get("location_source"),
            "limit": lim,
        },
        "total": len(nearby),
        "restrictions": signs,
        "nearest_google_maps_directions_url": nearest,
        "note": (
            "Sous-ensemble « mauvais stationnement » (interdiction / \\A / \\P / remorquage). "
            "Pas un moteur tarifaire; la signalisation sur place prévaut."
        ),
    }
