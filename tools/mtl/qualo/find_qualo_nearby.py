"""RSMA QUALO - qualite de l'eau en rive a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import qualo_api
from helpers.mtl.citations import qualo_ok
from tools import mcp


@mcp.tool(name="mtl_qualo_nearby")
async def find_qualo_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 5000.0,
    limit: int = 10,
) -> str:
    """Dernieres mesures QUALO (qualite de l'eau en rive) proches d'un point.

    Dataset: https://donnees.montreal.ca/dataset/rsma-qualite-de-l-eau-en-rive-qualo
    Une mesure la plus recente par station d'echantillonnage, triee par distance.

    Parameters:
        address: Adresse a geocoder (ex. '275 Rue Notre-Dame Est, Montreal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-15000, defaut 5000).
        limit: Nombre max de stations (1-50, defaut 10).
    """

    async def _run() -> str:
        data = await qualo_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return qualo_ok(data)

    return await run_tool(
        "find_qualo_nearby",
        _run,
        generic_error="Impossible de lister les mesures QUALO a proximite.",
    )
