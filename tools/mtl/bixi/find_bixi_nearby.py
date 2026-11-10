"""Stations BIXI a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import bixi_api
from helpers.mtl.citations import bixi_ok
from tools import mcp


@mcp.tool(name="mtl_bixi_nearby")
async def find_bixi_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 600.0,
    limit: int = 15,
) -> str:
    """Stations BIXI proches d'une adresse ou d'un point (GBFS live).

    Donnees: https://donnees.montreal.ca/dataset/bixi-etat-des-stations
    Flux: gbfs.velobixi.com (station_information + station_status).

    Parameters:
        address: Adresse a geocoder (ex. 'Hôtel de Ville de Montréal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 600).
        limit: Nombre max de stations (1-50, defaut 15).
    """

    async def _run() -> str:
        data = await bixi_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return bixi_ok(data)

    return await run_tool(
        "find_bixi_nearby",
        _run,
        generic_error="Impossible de lister les stations BIXI a proximite.",
    )
