"""Entraves à la circulation Montréal (CIFS JSON temps réel)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from helpers.common.config import ENTRAVES_CIFS_JSON_URL, ENTRAVES_DATASET_ID
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import nearest_distance_m

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50
_TZ = ZoneInfo("America/Toronto")


def polyline_to_linestring(polyline: str | None) -> dict[str, Any] | None:
    """Parse CIFS space-separated 'lat lon lat lon...' into GeoJSON LineString (lon, lat)."""
    if not polyline or not str(polyline).strip():
        return None
    parts = str(polyline).replace(",", " ").split()
    if len(parts) < 2:
        return None
    coords: list[list[float]] = []
    i = 0
    while i + 1 < len(parts):
        try:
            lat = float(parts[i])
            lon = float(parts[i + 1])
        except ValueError:
            i += 1
            continue
        coords.append([lon, lat])
        i += 2
    if not coords:
        return None
    if len(coords) == 1:
        return {"type": "Point", "coordinates": coords[0]}
    return {"type": "LineString", "coordinates": coords}


def _parse_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_TZ)
    return dt


def is_active(incident: dict[str, Any], *, now: datetime | None = None) -> bool:
    """True if now is within [starttime, endtime] when those fields exist."""
    current = now or datetime.now(_TZ)
    start = _parse_dt(incident.get("starttime"))
    end = _parse_dt(incident.get("endtime"))
    if start is not None and current < start:
        return False
    return not (end is not None and current > end)


def _incident_location(incident: dict[str, Any]) -> dict[str, Any]:
    loc = incident.get("location")
    return loc if isinstance(loc, dict) else {}


def _matches_filter(value: Any, needle: str | None) -> bool:
    if not needle or not needle.strip():
        return True
    return needle.strip().lower() in str(value or "").lower()


def extract_incidents(payload: Any) -> list[dict[str, Any]]:
    """Normalize CIFS root to a list of incident dicts."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("incidents", "incident", "events", "trafficEvents"):
        raw = payload.get(key)
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
        if isinstance(raw, dict):
            return [raw]
    # Some feeds wrap under incidents.incident
    incidents = payload.get("incidents")
    if isinstance(incidents, dict):
        inner = incidents.get("incident")
        if isinstance(inner, list):
            return [x for x in inner if isinstance(x, dict)]
        if isinstance(inner, dict):
            return [inner]
    return []


def filter_nearby(
    payload: Any,
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
    type_filter: str | None = None,
    subtype_filter: str | None = None,
    active_only: bool = True,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Filter CIFS incidents by distance to polyline."""
    hits: list[dict[str, Any]] = []
    for inc in extract_incidents(payload):
        if active_only and not is_active(inc, now=now):
            continue
        if not _matches_filter(inc.get("type"), type_filter):
            continue
        if not _matches_filter(inc.get("subtype"), subtype_filter):
            continue
        loc = _incident_location(inc)
        geom = polyline_to_linestring(loc.get("polyline"))
        nearest = nearest_distance_m(latitude, longitude, geom)
        if nearest is None:
            continue
        dist, near_lat, near_lon = nearest
        if dist > radius_m:
            continue
        hits.append(
            {
                "id": inc.get("id"),
                "type": inc.get("type"),
                "subtype": inc.get("subtype"),
                "description": inc.get("description"),
                "street": loc.get("street"),
                "direction": loc.get("direction"),
                "starttime": inc.get("starttime"),
                "endtime": inc.get("endtime"),
                "updatetime": inc.get("updatetime"),
                "distance_m": round(dist, 1),
                "latitude": round(near_lat, 6),
                "longitude": round(near_lon, 6),
            }
        )
    hits.sort(key=lambda row: row["distance_m"])
    return hits[:limit]


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
    type_filter: str | None = None,
    subtype_filter: str | None = None,
    active_only: bool = True,
) -> dict[str, Any]:
    """Entraves proches d'une adresse ou d'un point."""
    if not (_MIN_RADIUS_M <= radius_m <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M} et {_MAX_RADIUS_M}."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_LIMIT))
    from helpers.mtl.nearby import resolve_user_point

    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    query_lat = loc["latitude"]
    query_lon = loc["longitude"]
    resolved = loc.get("resolved_address")
    try:
        payload = await fetch_json(ENTRAVES_CIFS_JSON_URL, use_cache=False)
    except (httpx.HTTPError, TimeoutError):
        from helpers.mtl.planned_works_api import list_nearby as planned_nearby

        if type_filter or subtype_filter:
            raise
        return await planned_nearby(query_lat, query_lon, float(radius_m), lim, active_only)
    items = filter_nearby(
        payload,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=float(radius_m),
        limit=lim,
        type_filter=type_filter,
        subtype_filter=subtype_filter,
        active_only=active_only,
    )
    items, nearest_directions = attach_nearby_maps(
        items,
        query_lat=query_lat,
        query_lon=query_lon,
    )
    return {
        "query": {
            "address": address,
            "resolved_address": resolved,
            "latitude": query_lat,
            "longitude": query_lon,
            "radius_m": radius_m,
            "type": type_filter,
            "subtype": subtype_filter,
            "active_only": active_only,
            "location_source": loc.get("location_source"),
        },
        "total": len(items),
        "entraves": items,
        "items": items,
        "nearest_google_maps_directions_url": nearest_directions,
        "dataset_id": ENTRAVES_DATASET_ID,
        "source_url": ENTRAVES_CIFS_JSON_URL,
    }
