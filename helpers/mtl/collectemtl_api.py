"""Client HTTP pour l'API JSON publique de Collecte MTL."""

from __future__ import annotations

from typing import Any

import httpx

from helpers.common.config import COLLECTEMTL_BASE_URL
from helpers.common.http_client import fetch_json
from helpers.common.maps_format import attach_nearby_maps


async def _resolve_civic_address(address: str) -> str:
    """Normalize landmarks to a civic address Collecte MTL accepts."""
    from helpers.mtl.avis_api import geocode_address

    _lat, _lon, resolved = await geocode_address(address.strip())
    return (resolved or address).strip()


async def _fetch_address_endpoint(path: str, address: str, *, expect_label: str) -> dict[str, Any]:
    """GET Collecte MTL address endpoint; geocode and retry on HTTP 404."""
    cleaned = address.strip()
    url = f"{COLLECTEMTL_BASE_URL}{path}"
    try:
        data = await fetch_json(url, params={"address": cleaned})
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        resolved = await _resolve_civic_address(cleaned)
        if resolved == cleaned:
            raise
        data = await fetch_json(url, params={"address": resolved})
    if not isinstance(data, dict):
        msg = f"Réponse inattendue de {path} ({expect_label})."
        raise TypeError(msg)
    return data


async def get_collections(address: str) -> dict[str, Any]:
    """GET /api/collections?address= - calendrier de collecte par adresse."""
    return await _fetch_address_endpoint(
        "/api/collections",
        address,
        expect_label="objet JSON attendu",
    )


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
    return await _fetch_address_endpoint(
        "/api/borough",
        address,
        expect_label="objet JSON attendu",
    )
