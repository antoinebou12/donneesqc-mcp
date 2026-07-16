"""Stations BIXI - proximité via GBFS."""

from __future__ import annotations

from typing import Any

from helpers.common.config import (
    BIXI_DATASET_ID,
    BIXI_STATION_INFO_URL,
    BIXI_STATION_STATUS_URL,
)
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import haversine_m

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50


def merge_stations(
    info: dict[str, Any],
    status: dict[str, Any],
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> list[dict[str, Any]]:
    """Fusionne information + status GBFS et filtre par distance."""
    stations = ((info.get("data") or {}).get("stations")) or []
    statuses = {
        str(s.get("station_id")): s for s in (((status.get("data") or {}).get("stations")) or []) if isinstance(s, dict)
    }
    nearby: list[dict[str, Any]] = []
    for station in stations:
        if not isinstance(station, dict):
            continue
        try:
            slat = float(station["lat"])
            slon = float(station["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        dist = haversine_m(latitude, longitude, slat, slon)
        if dist > radius_m:
            continue
        sid = str(station.get("station_id") or "")
        st = statuses.get(sid) or {}
        nearby.append(
            {
                "station_id": sid,
                "name": station.get("name"),
                "capacity": station.get("capacity"),
                "bikes_available": st.get("num_bikes_available"),
                "docks_available": st.get("num_docks_available"),
                "num_bikes_available": st.get("num_bikes_available"),
                "num_docks_available": st.get("num_docks_available"),
                "is_renting": st.get("is_renting"),
                "is_returning": st.get("is_returning"),
                "distance_m": round(dist, 1),
                "latitude": slat,
                "longitude": slon,
            }
        )
    nearby.sort(key=lambda row: row["distance_m"])
    return nearby[:limit]


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 400.0,
    limit: int = 15,
) -> dict[str, Any]:
    """Stations BIXI proches d'une adresse ou d'un point."""
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
    info = await fetch_json(BIXI_STATION_INFO_URL)
    status = await fetch_json(BIXI_STATION_STATUS_URL)
    stations = merge_stations(
        info,
        status,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=float(radius_m),
        limit=lim,
    )
    stations, nearest_directions = attach_nearby_maps(
        stations,
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
            "location_source": loc.get("location_source"),
        },
        "total": len(stations),
        "stations": stations,
        "nearest_google_maps_directions_url": nearest_directions,
        "dataset_id": BIXI_DATASET_ID,
        "gbfs_info_url": BIXI_STATION_INFO_URL,
        "gbfs_status_url": BIXI_STATION_STATUS_URL,
    }
