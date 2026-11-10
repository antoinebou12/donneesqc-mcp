"""Prochaines arrivees STM a un arret."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import stm_api
from helpers.mtl.citations import stm_ok
from tools import mcp


@mcp.tool(name="mtl_stm_next_arrivals")
async def get_stm_next_arrivals(
    stop_id: str,
    limit: int = 15,
) -> str:
    """Prochaines arrivees bus STM (GTFS-RT tripUpdates) pour un stop_id.

    Necessite STM_API_KEY (cle gratuite sur stm.info/developers).
    Obtenir un stop_id via mtl_stm_stops_nearby.

    Parameters:
        stop_id: Identifiant d'arret STM (ex. '51543').
        limit: Nombre max d'arrivees (1-30, defaut 15).
    """

    async def _run() -> str:
        data = await stm_api.list_next_arrivals(stop_id=stop_id, limit=limit)
        return stm_ok(data)

    return await run_tool(
        "get_stm_next_arrivals",
        _run,
        generic_error="Impossible d'obtenir les prochaines arrivees STM.",
    )
