"""Client GeoJSON pour les avis et alertes de la Ville de Montréal."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from helpers.common.config import AVIS_ALERTES_GEOJSON_URL
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.calendar_adapters import avis_alert_to_item, enrich_list_payload
from helpers.mtl.geo import nearest_distance_m
from helpers.qc.geo.icherche_client import geocode_features
from helpers.qc.geo.icherche_format import feature_to_geocode_result

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50


def parse_date(value: str) -> date:
    """Parse YYYY-MM-DD or raise ValueError."""
    raw = (value or "").strip()
    if not _DATE_RE.match(raw):
        msg = "Le parametre date doit etre au format YYYY-MM-DD."
        raise ValueError(msg)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        msg = "Le parametre date doit etre une date valide (YYYY-MM-DD)."
        raise ValueError(msg) from exc


def _parse_datetime_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    text = str(value).strip().replace("Z", "")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        if len(text) >= 10 and _DATE_RE.match(text[:10]):
            try:
                return date.fromisoformat(text[:10])
            except ValueError:
                return None
        return None


def active_on(target: date, date_debut: Any, date_fin: Any) -> bool:
    """True if target falls in [date_debut, date_fin] (inclusive)."""
    start = _parse_datetime_date(date_debut)
    end = _parse_datetime_date(date_fin)
    if start is None and end is None:
        return False
    if start is not None and target < start:
        return False
    return not (end is not None and target > end)


def filter_nearby(
    geojson: dict[str, Any],
    *,
    latitude: float,
    longitude: float,
    target: date,
    radius_m: float,
    limit: int,
    alert_type: str | None = None,
) -> list[dict[str, Any]]:
    """Filter GeoJSON features by date window + distance; sort by distance."""
    features = geojson.get("features") or []
    type_filter = alert_type.strip() if alert_type and alert_type.strip() else None
    hits: list[dict[str, Any]] = []

    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties") or {}
        if not isinstance(props, dict):
            continue
        if type_filter is not None and (props.get("type") or "") != type_filter:
            continue
        if not active_on(target, props.get("date_debut"), props.get("date_fin")):
            continue
        geom = feat.get("geometry")
        nearest = nearest_distance_m(latitude, longitude, geom if isinstance(geom, dict) else None)
        if nearest is None:
            continue
        dist, near_lat, near_lon = nearest
        if dist > radius_m:
            continue
        hits.append(
            {
                "titre": props.get("titre") or "",
                "type": props.get("type") or "",
                "date_debut": props.get("date_debut"),
                "date_fin": props.get("date_fin"),
                "lien": props.get("lien") or "",
                "service_publieur": props.get("service_publieur") or "",
                "distance_m": round(dist, 1),
                "geom_type": (geom or {}).get("type") if isinstance(geom, dict) else None,
                "nearest_lat": round(near_lat, 6),
                "nearest_lon": round(near_lon, 6),
            }
        )

    hits.sort(key=lambda row: row["distance_m"])
    return hits[:limit]


async def fetch_avis_geojson() -> dict[str, Any]:
    """Download avis/alertes GeoJSON (cached in-memory via http_client)."""
    data = await fetch_json(AVIS_ALERTES_GEOJSON_URL)
    if not isinstance(data, dict):
        msg = "Reponse GeoJSON avis/alertes inattendue (objet attendu)."
        raise TypeError(msg)
    return data


async def geocode_address(address: str) -> tuple[float, float, str]:
    """Geocode via iCherche; return (lat, lon, resolved_address)."""
    cleaned = address.strip()
    if not cleaned:
        msg = "Le parametre address est requis (ou latitude/longitude)."
        raise ValueError(msg)
    features = await geocode_features(cleaned, limit=1)
    if not features:
        msg = f"Adresse introuvable: '{cleaned}'."
        raise ValueError(msg)
    result = feature_to_geocode_result(features[0])
    lat = result.get("latitude")
    lon = result.get("longitude")
    if lat is None or lon is None:
        msg = f"Geocodage sans coordonnees pour '{cleaned}'."
        raise ValueError(msg)
    return float(lat), float(lon), str(result.get("address") or cleaned)


async def list_nearby(
    *,
    date: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 1000.0,
    limit: int = 20,
    alert_type: str | None = None,
) -> dict[str, Any]:
    """Avis actifs a une date, dans un rayon autour d'une adresse ou d'un point."""
    from helpers.common.context import resolve_now

    date_str = (date or "").strip() or resolve_now()["date"]
    target = parse_date(date_str)

    if not (_MIN_RADIUS_M <= radius_m <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M:g} et {_MAX_RADIUS_M:g}."
        raise ValueError(msg)
    limit = max(1, min(int(limit), _MAX_LIMIT))

    resolved_address: str | None = address.strip() if address and address.strip() else None

    from helpers.mtl.nearby import resolve_user_point

    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
    query_lat = loc["latitude"]
    query_lon = loc["longitude"]
    resolved_address = loc.get("resolved_address") or resolved_address

    geojson = await fetch_avis_geojson()
    alerts = filter_nearby(
        geojson,
        latitude=query_lat,
        longitude=query_lon,
        target=target,
        radius_m=radius_m,
        limit=limit,
        alert_type=alert_type,
    )
    alerts, nearest_directions = attach_nearby_maps(
        alerts,
        query_lat=query_lat,
        query_lon=query_lon,
        lat_key="nearest_lat",
        lon_key="nearest_lon",
    )
    payload = {
        "query": {
            "address": resolved_address,
            "latitude": query_lat,
            "longitude": query_lon,
            "date": target.isoformat(),
            "radius_m": radius_m,
            "type": alert_type.strip() if alert_type and alert_type.strip() else None,
            "location_source": loc.get("location_source"),
        },
        "total": len(alerts),
        "alerts": alerts,
        "nearest_google_maps_directions_url": nearest_directions,
    }
    return enrich_list_payload(payload, list_key="alerts", mapper=avis_alert_to_item)
