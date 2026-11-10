"""Positions live des bus STM."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import stm_api
from helpers.mtl.citations import stm_ok
from tools import mcp


@mcp.tool(name="mtl_stm_bus_positions")
async def get_stm_bus_positions(
    route: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 50,
) -> str:
    """Positions live des autobus STM (GTFS-RT vehiclePositions).

    Necessite STM_API_KEY. Filtrer par ligne (route) et/ou proximite d'une adresse.

    Parameters:
        route: Numero de ligne (ex. '80', '24').
        address: Adresse pour filtrer par distance.
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres si adresse/GPS fournis (50-5000, defaut 800).
        limit: Nombre max de vehicules (1-100, defaut 50).
    """

    async def _run() -> str:
        data = await stm_api.list_bus_positions(
            route=route,
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return stm_ok(data)

    return await run_tool(
        "get_stm_bus_positions",
        _run,
        generic_error="Impossible d'obtenir les positions live STM.",
    )
