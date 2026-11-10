"""Alertes d'etat du service REM (GTFS-RT)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import rem_api
from helpers.mtl.citations import rem_ok
from tools import mcp


@mcp.tool(name="mtl_rem_service_alerts")
async def get_rem_service_alerts(
    lang: str = "fr",
) -> str:
    """Alertes d'etat du service REM (GTFS-RT, sans cle API).

    Couvre interruptions planifiees, ouvertures tardives, etc.
    Pour le detail reseau/ascenseurs, utiliser aussi mtl_rem_network_status.

    Parameters:
        lang: Langue des textes 'fr', 'en' ou 'all' (defaut fr).
    """

    async def _run() -> str:
        data = await rem_api.list_service_alerts(lang=lang)
        return rem_ok(data)

    return await run_tool(
        "get_rem_service_alerts",
        _run,
        generic_error="Impossible d'obtenir les alertes REM.",
    )
