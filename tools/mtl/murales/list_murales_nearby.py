"""Murales a proximite d'un point GPS."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import murales_api
from helpers.mtl.citations import murales_ok
from helpers.mtl.nearby import resolve_user_point
from tools import mcp


@mcp.tool(name="mtl_murales_nearby")
async def list_murales_nearby(
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    radius_m: float = 1000.0,
    limit: int = 20,
) -> str:
    """Liste les murales a proximite d'un point (WGS84), triees par distance.

    Preferez latitude/longitude du GPS telephone/PC. Sinon address, sinon IP client.
    Donnees: https://donnees.montreal.ca/dataset/murales
    Viewer: https://www.mtlmurales.ca/fr

    Parameters:
        latitude: Latitude WGS84 GPS (ex: 45.5088).
        longitude: Longitude WGS84 (ex: -73.5617).
        address: Adresse a geocoder si pas de GPS.
        radius_m: Rayon de recherche en metres (defaut 1000).
        limit: Nombre max de resultats (1-100, defaut 20).
    """

    async def _run() -> str:
        loc = await resolve_user_point(
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        data = await murales_api.list_nearby(
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            radius_m=radius_m,
            limit=limit,
        )
        data["location_source"] = loc.get("location_source")
        data["resolved_address"] = loc.get("resolved_address")
        return murales_ok(data)

    return await run_tool(
        "list_murales_nearby",
        _run,
        generic_error="Impossible de lister les murales a proximite.",
    )
