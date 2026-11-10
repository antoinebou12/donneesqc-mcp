"""Stations REM a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import rem_api
from helpers.mtl.citations import rem_ok
from tools import mcp


@mcp.tool(name="mtl_rem_stops_nearby")
async def find_rem_stops_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
) -> str:
    """Stations / quais REM proches d'une adresse ou d'un point (index GTFS bundlé).

    Pas de cle API. Pas d'arrivees live (tripUpdates/vehiclePositions non publics).
    Sources: GTFS REM (gtfs.gpmmom.ca) + https://rem.info

    Parameters:
        address: Adresse libre (geocodee via Adresses Quebec).
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84 (avec latitude).
        radius_m: Rayon de recherche en metres (50-5000, defaut 800).
        limit: Nombre max de resultats (1-50, defaut 15).
    """

    async def _run() -> str:
        data = await rem_api.list_stops_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return rem_ok(data)

    return await run_tool(
        "find_rem_stops_nearby",
        _run,
        generic_error="Impossible de lister les stations REM a proximite.",
    )
