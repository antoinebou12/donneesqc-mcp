"""RSMA QUALO - mesures de qualité de l'eau en rive à proximité."""

from __future__ import annotations

from typing import Any

from helpers.common import ckan_api
from helpers.common.config import QUALO_DATASET_ID, QUALO_RESOURCE_ID
from helpers.common.maps_format import attach_nearby_maps
from helpers.common.portals import MTL_PORTAL
from helpers.mtl.geo import haversine_m

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 15000.0
_MAX_LIMIT = 50
_FETCH_LIMIT = 400
BATHING_THRESHOLD_UFC = 200


def pick_nearby_latest(
    records: list[dict[str, Any]],
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
) -> list[dict[str, Any]]:
    """Une mesure la plus récente par station, dans le rayon, triées par distance."""
    by_station: dict[str, dict[str, Any]] = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        try:
            rlat = float(rec["latitude"])
            rlon = float(rec["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        dist = haversine_m(latitude, longitude, rlat, rlon)
        if dist > radius_m:
            continue
        station_nom = str(
            rec.get("nom") or rec.get("station_nom") or rec.get("point_echantillonnage") or f"{rlat},{rlon}"
        )
        stamped = {
            "station_nom": station_nom,
            "point_echantillonnage": rec.get("point_echantillonnage"),
            "plan_eau": rec.get("plan_eau"),
            "date_heure": rec.get("date_heure"),
            "temperature": rec.get("temperature"),
            "pH": rec.get("pH") if "pH" in rec else rec.get("ph"),
            "coliformes_fecaux": rec.get("coliformes_fecaux"),
            "latitude": rlat,
            "longitude": rlon,
            "distance_m": round(dist, 1),
        }
        prev = by_station.get(station_nom)
        if prev is None or str(stamped.get("date_heure") or "") > str(prev.get("date_heure") or ""):
            by_station[station_nom] = stamped
    nearby = sorted(by_station.values(), key=lambda row: row["distance_m"])
    return nearby[:limit]


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 1500.0,
    limit: int = 10,
) -> dict[str, Any]:
    """Dernières mesures QUALO proches d'une adresse ou d'un point."""
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
    result = await ckan_api.datastore_search(
        MTL_PORTAL.api_url,
        resource_id=QUALO_RESOURCE_ID,
        fields=[
            "point_echantillonnage",
            "plan_eau",
            "nom",
            "date_heure",
            "temperature",
            "pH",
            "coliformes_fecaux",
            "latitude",
            "longitude",
        ],
        sort="date_heure desc",
        limit=_FETCH_LIMIT,
    )
    records = result.get("records") or []
    if not isinstance(records, list):
        records = []
    stations = pick_nearby_latest(
        records,
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
        "measures": stations,
        "nearest_google_maps_directions_url": nearest_directions,
        "bathing_threshold_ufc": BATHING_THRESHOLD_UFC,
        "dataset_id": QUALO_DATASET_ID,
        "resource_id": QUALO_RESOURCE_ID,
        "note": (
            f"Seuil de baignade usuel ~{BATHING_THRESHOLD_UFC} UFC/100 mL pour "
            "coliformes_fecaux (indicateur; verifier les criteres officiels)."
        ),
    }
