"""Client HTTP pour l'API JSON publique de Collecte MTL."""

from __future__ import annotations

from typing import Any

from helpers.common.config import COLLECTEMTL_BASE_URL
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import attach_nearby_maps


async def get_collections(address: str) -> dict[str, Any]:
    """GET /api/collections?address= - calendrier de collecte par adresse."""
    data = await fetch_json(
        f"{COLLECTEMTL_BASE_URL}/api/collections",
        params={"address": address},
    )
    if not isinstance(data, dict):
        msg = "Réponse inattendue de /api/collections (objet JSON attendu)."
        raise TypeError(msg)
    return data


async def get_ecocentres(lat: float, lng: float, limit: int = 3) -> dict[str, Any]:
    """GET /api/ecocentres?lat=&lng=&limit= - écocentres les plus proches."""
    data = await fetch_json(
        f"{COLLECTEMTL_BASE_URL}/api/ecocentres",
        params={"lat": lat, "lng": lng, "limit": limit},
    )
    if not isinstance(data, dict):
        msg = "Réponse inattendue de /api/ecocentres (objet JSON attendu)."
        raise TypeError(msg)
    raw_items = data.get("ecocentres")
    items = [row for row in raw_items if isinstance(row, dict)] if isinstance(raw_items, list) else []
    enriched, nearest_directions = attach_nearby_maps(
        items,
        query_lat=float(lat),
        query_lon=float(lng),
        lat_key="lat",
        lon_key="lng",
    )
    out = dict(data)
    out["ecocentres"] = enriched
    out["nearest_google_maps_directions_url"] = nearest_directions
    return out


async def get_borough_stats(address: str) -> dict[str, Any]:
    """GET /api/borough?address= - bilan massique d'arrondissement."""
    data = await fetch_json(
        f"{COLLECTEMTL_BASE_URL}/api/borough",
        params={"address": address},
    )
    if not isinstance(data, dict):
        msg = "Réponse inattendue de /api/borough (objet JSON attendu)."
        raise TypeError(msg)
    return data
