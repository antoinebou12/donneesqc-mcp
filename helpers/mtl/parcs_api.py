"""Parcs / espaces verts Montréal - proximité (GeoJSON fichier)."""

from __future__ import annotations

import json
from typing import Any

from helpers.common.config import (
    PARCS_DATASET_ID,
    PARCS_GEOJSON_RESOURCE_ID,
    PARCS_GEOJSON_URL,
)
from helpers.common.http_client import fetch_text
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import nearest_distance_m

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50


def _type_label(props: dict[str, Any]) -> str:
    for key in ("TYPO2", "TYPO1", "Type"):
        val = props.get(key)
        if val:
            return str(val)
    return ""


def _is_parc(props: dict[str, Any], *, parks_only: bool) -> bool:
    if not parks_only:
        return True
    typo1 = str(props.get("TYPO1") or "")
    return "parc" in typo1.lower()


def parse_parcs_geojson(
    data: dict[str, Any],
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
    parks_only: bool = True,
) -> list[dict[str, Any]]:
    """Filtre features GeoJSON par distance (nearest vertex)."""
    features = data.get("features") or []
    nearby: list[dict[str, Any]] = []
    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties") or {}
        if not isinstance(props, dict):
            continue
        if not _is_parc(props, parks_only=parks_only):
            continue
        geom = feat.get("geometry") if isinstance(feat.get("geometry"), dict) else None
        nearest = nearest_distance_m(latitude, longitude, geom)
        if nearest is None:
            continue
        dist, near_lat, near_lon = nearest
        if dist > radius_m:
            continue
        nom = str(props.get("Nom") or props.get("name") or "").strip()
        if not nom:
            continue
        type_label = _type_label(props)
        nearby.append(
            {
                "name": nom,
                "nom": nom,
                "type": type_label,
                "typo1": props.get("TYPO1"),
                "typo2": props.get("TYPO2"),
                "gestion": props.get("GESTION"),
                "superficie_ha": props.get("SUPERFICIE"),
                "distance_m": round(dist, 1),
                "latitude": round(near_lat, 6),
                "longitude": round(near_lon, 6),
            }
        )
    nearby.sort(key=lambda row: row["distance_m"])
    return nearby[:limit]


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 300.0,
    limit: int = 15,
    parks_only: bool = True,
) -> dict[str, Any]:
    """Parcs / espaces verts proches d'une adresse ou d'un point."""
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
    text = await fetch_text(PARCS_GEOJSON_URL)
    data = json.loads(text)
    if not isinstance(data, dict):
        msg = "Reponse GeoJSON parcs inattendue."
        raise TypeError(msg)
    parks = parse_parcs_geojson(
        data,
        latitude=query_lat,
        longitude=query_lon,
        radius_m=float(radius_m),
        limit=lim,
        parks_only=parks_only,
    )
    parks, nearest_directions = attach_nearby_maps(
        parks,
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
            "parks_only": parks_only,
            "location_source": loc.get("location_source"),
        },
        "total": len(parks),
        "parks": parks,
        "items": parks,
        "nearest_google_maps_directions_url": nearest_directions,
        "dataset_id": PARCS_DATASET_ID,
        "resource_id": PARCS_GEOJSON_RESOURCE_ID,
        "source_url": PARCS_GEOJSON_URL,
    }
