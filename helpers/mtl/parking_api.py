"""Stationnements gratuits/payants (déneigement) — GeoJSON saisonnier MTL."""

from __future__ import annotations

import json
import re
from contextlib import suppress
from typing import Any

from helpers.common import ckan_api
from helpers.common.config import (
    MTL_API_URL,
    PARKING_DENEIGEMENT_DATASET_ID,
    PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID,
    PARKING_DENEIGEMENT_GEOJSON_URL,
)
from helpers.common.http_client import fetch_text
from helpers.common.maps_format import attach_nearby_maps
from helpers.mtl.geo import haversine_m, validate_wgs84
from helpers.mtl.nearby import resolve_user_point

_MIN_RADIUS_M = 50.0
_MAX_RADIUS_M = 5000.0
_MAX_LIMIT = 50


def _published_text(value: Any) -> str | None:
    """Repair UTF-8 text decoded as Windows-1252 in the published GeoJSON."""
    text = str(value or "").strip()
    if "Ã" in text or "Â" in text:
        with suppress(UnicodeError):
            text = text.encode("cp1252").decode("utf-8")
    return text or None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _pay_label(raw: Any) -> tuple[str, bool]:
    """Return (type_pay label, is_free). TYPE_PAY 0 = gratuit, 1 = payant."""
    text = str(raw if raw is not None else "").strip().casefold()
    if text in {"0", "gratuit", "free", "g"}:
        return "gratuit", True
    if text in {"1", "payant", "paid", "p"}:
        return "payant", False
    if "gratuit" in text or "free" in text:
        return "gratuit", True
    if "payant" in text or "paid" in text:
        return "payant", False
    return (str(raw or "").strip() or "inconnu"), False


def parse_parking_geojson(
    data: dict[str, Any],
    *,
    latitude: float,
    longitude: float,
    radius_m: float,
    limit: int,
    free_only: bool = False,
) -> list[dict[str, Any]]:
    """Filtre features GeoJSON stationnements par distance haversine."""
    features = data.get("features") or []
    nearby: list[dict[str, Any]] = []
    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties") if isinstance(feat.get("properties"), dict) else {}
        type_pay, is_free = _pay_label(props.get("TYPE_PAY"))
        if free_only and not is_free:
            continue
        lat = _to_float(props.get("Latitude") or props.get("latitude"))
        lon = _to_float(props.get("Longitude") or props.get("longitude"))
        if lat is None or lon is None:
            geom = feat.get("geometry") if isinstance(feat.get("geometry"), dict) else None
            coords = (geom or {}).get("coordinates") if geom else None
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                lon = _to_float(coords[0])
                lat = _to_float(coords[1])
        if lat is None or lon is None:
            from helpers.mtl.geo import mtm8_to_wgs84

            x = _to_float(props.get("X"))
            y = _to_float(props.get("Y"))
            if x is not None and y is not None:
                lon, lat = mtm8_to_wgs84(x, y)
        if lat is None or lon is None:
            continue
        dist = haversine_m(latitude, longitude, lat, lon)
        if dist > radius_m:
            continue
        lot_id = str(props.get("ID_STA") or props.get("id") or "").strip() or None
        nearby.append(
            {
                "id": lot_id,
                "emplacement": _published_text(props.get("EMPLACEMENT") or props.get("LOCATION")),
                "arrondissement": _published_text(props.get("ARRONDISSEMENT") or props.get("BOROUGH")),
                "nbr_places": _to_float(props.get("NBR_PLA")) or props.get("NBR_PLA"),
                "heures": _published_text(props.get("HEURES") or props.get("HOURS")),
                "note_fr": _published_text(props.get("NOTE_FR")),
                "type_pay": type_pay,
                "free": is_free,
                "distance_m": round(dist, 1),
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
            }
        )
    nearby.sort(key=lambda row: row["distance_m"])
    return nearby[: max(1, min(int(limit), _MAX_LIMIT))]


async def resolve_geojson_url() -> tuple[str, str | None]:
    """URL GeoJSON saisonnier (env override, sinon CKAN package_show)."""
    configured = (PARKING_DENEIGEMENT_GEOJSON_URL or "").strip()
    if configured:
        return configured, PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID
    pkg = await ckan_api.package_show(MTL_API_URL, PARKING_DENEIGEMENT_DATASET_ID)
    resources = pkg.get("resources") or []
    geojsons = [
        r
        for r in resources
        if isinstance(r, dict)
        and (str(r.get("format") or "").upper() == "GEOJSON" or str(r.get("url") or "").lower().endswith(".geojson"))
    ]
    if not geojsons:
        msg = "Aucun resource GeoJSON pour stationnements-deneigement."
        raise RuntimeError(msg)
    # Prefer resource id match, else first GeoJSON
    preferred = next(
        (r for r in geojsons if str(r.get("id") or "") == PARKING_DENEIGEMENT_GEOJSON_RESOURCE_ID),
        geojsons[0],
    )
    url = str(preferred.get("url") or "").strip()
    if not url:
        msg = "URL GeoJSON stationnements-deneigement manquante."
        raise RuntimeError(msg)
    return url, str(preferred.get("id") or "") or None


async def list_nearby(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
    free_only: bool = False,
) -> dict[str, Any]:
    """Stationnements déneigement proches d'une adresse ou d'un point."""
    if not (_MIN_RADIUS_M <= radius_m <= _MAX_RADIUS_M):
        msg = f"radius_m doit etre entre {_MIN_RADIUS_M} et {_MAX_RADIUS_M}."
        raise ValueError(msg)
    lim = max(1, min(int(limit), _MAX_LIMIT))
    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
    lat = float(loc["latitude"])
    lon = float(loc["longitude"])
    validate_wgs84(lat, lon)

    url, resource_id = await resolve_geojson_url()
    text = await fetch_text(url)
    data = json.loads(text)
    if not isinstance(data, dict):
        msg = "Réponse GeoJSON stationnements inattendue."
        raise TypeError(msg)

    lots = parse_parking_geojson(
        data,
        latitude=lat,
        longitude=lon,
        radius_m=float(radius_m),
        limit=lim,
        free_only=free_only,
    )
    lots, nearest = attach_nearby_maps(lots, query_lat=lat, query_lon=lon)
    return {
        "query": {
            "address": address,
            "resolved_address": loc.get("resolved_address"),
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "location_source": loc.get("location_source"),
            "free_only": free_only,
            "limit": lim,
        },
        "total": len(lots),
        "lots": lots,
        "nearest_google_maps_directions_url": nearest,
        "dataset_id": PARKING_DENEIGEMENT_DATASET_ID,
        "resource_id": resource_id,
        "geojson_url": url,
        "source_season": next(iter(re.findall(r"20\d{2}-20\d{2}", url)), None),
        "note": ("GeoJSON saisonnier (déneigement). La signalisation sur place prévaut toujours."),
    }
