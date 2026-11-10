"""Alertes d'etat du service STM."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import stm_api
from helpers.mtl.citations import stm_ok
from tools import mcp


@mcp.tool(name="mtl_stm_service_alerts")
async def get_stm_service_alerts(
    type: str = "all",  # noqa: A002 — MCP param name matches STM i3 filter
) -> str:
    """Alertes d'etat du service STM (API i3 etatservice).

    Necessite STM_API_KEY. Couvre metro, bus et trains de banlieue selon le flux i3.

    Parameters:
        type: Filtre 'metro', 'bus', 'train' ou 'all' (defaut).
    """

    async def _run() -> str:
        data = await stm_api.list_service_alerts(alert_type=type)
        return stm_ok(data)

    return await run_tool(
        "get_stm_service_alerts",
        _run,
        generic_error="Impossible d'obtenir les alertes STM.",
    )
