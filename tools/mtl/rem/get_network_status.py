"""Etat live du reseau REM (HTML rem.info)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import rem_html
from helpers.mtl.citations import rem_ok
from tools import mcp


@mcp.tool(name="mtl_rem_network_status")
async def get_rem_network_status(
    lang: str = "fr",
) -> str:
    """Etat du reseau REM : service, ascenseurs et interruptions planifiees.

    Source HTML officielle rem.info (pas d'API JSON publique).
    Completer avec mtl_rem_service_alerts (GTFS-RT) pour les alertes machine-lisibles.

    Parameters:
        lang: 'fr' (defaut) ou 'en'.
    """

    async def _run() -> str:
        data = await rem_html.get_network_status(lang=lang)
        return rem_ok(data)

    return await run_tool(
        "get_rem_network_status",
        _run,
        generic_error="Impossible d'obtenir l'etat du reseau REM.",
    )
