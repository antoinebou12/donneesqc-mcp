"""Arrêts STM a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import stm_api
from helpers.mtl.citations import stm_ok
from tools import mcp


@mcp.tool(name="mtl_stm_stops_nearby")
async def find_stm_stops_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 400.0,
    limit: int = 15,
) -> str:
    """Arrets STM proches d'une adresse ou d'un point (index GTFS static bundlé).

    Pas de cle API requise. Enchaine avec mtl_stm_next_arrivals(stop_id=...).
    Sources: GTFS STM + https://donnees.montreal.ca/dataset/stm-traces-des-lignes-de-bus-et-de-metro

    Parameters:
        address: Adresse a geocoder (ex. 'Hôtel de Ville de Montréal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 400).
        limit: Nombre max d'arrets (1-50, defaut 15).
    """

    async def _run() -> str:
        data = await stm_api.list_stops_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return stm_ok(data)

    return await run_tool(
        "find_stm_stops_nearby",
        _run,
        generic_error="Impossible de lister les arrets STM a proximite.",
    )
