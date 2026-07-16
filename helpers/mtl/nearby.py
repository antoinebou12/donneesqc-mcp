"""Résolution adresse / lat-lng partagée pour les outils « nearby » Montréal."""

from __future__ import annotations

from typing import Any

from helpers.mtl.avis_api import geocode_address
from helpers.mtl.geo import validate_wgs84


async def resolve_point(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    allow_client_ip: bool = True,
) -> tuple[float, float, str | None]:
    """Retourne (lat, lon, resolved_address|None).

    Priorité : GPS agent → address → IP client (si ``allow_client_ip``).
    Ne géolocalise jamais l'IP egress du serveur MCP.
    """
    loc = await resolve_user_point(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=allow_client_ip,
    )
    return loc["latitude"], loc["longitude"], loc.get("resolved_address")


async def resolve_user_point(
    *,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    allow_client_ip: bool = True,
) -> dict[str, Any]:
    """Comme ``resolve_point`` mais avec ``location_source`` et métadonnées."""
    from helpers.common.context import resolve_user_location

    # Strict path without IP: keep local validation for tests that patch geocode only
    if not allow_client_ip:
        resolved_address: str | None = address.strip() if address and address.strip() else None
        if latitude is not None and longitude is not None:
            lat = float(latitude)
            lon = float(longitude)
            validate_wgs84(lat, lon)
            return {
                "latitude": lat,
                "longitude": lon,
                "resolved_address": resolved_address,
                "location_source": "agent",
                "city": None,
                "label": resolved_address,
                "client_ip": None,
            }
        if resolved_address:
            lat, lon, geocoded = await geocode_address(resolved_address)
            return {
                "latitude": lat,
                "longitude": lon,
                "resolved_address": geocoded,
                "location_source": "address",
                "city": None,
                "label": geocoded,
                "client_ip": None,
            }
        msg = "Fournissez address ou latitude et longitude."
        raise ValueError(msg)

    return await resolve_user_location(
        address=address,
        latitude=latitude,
        longitude=longitude,
        allow_client_ip=True,
    )
