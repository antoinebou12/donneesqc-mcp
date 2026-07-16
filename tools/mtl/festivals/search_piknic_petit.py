"""Recherche programmation Petit Piknic."""

from helpers.mtl import piknic_api
from helpers.mtl.events_common import run_festival_tool
from tools import mcp


@mcp.tool(name="mtl_piknic_search_petit")
async def search_piknic_petit(
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> str:
    """Liste ou filtre les evenements Petit Piknic.

    Source: https://piknicelectronik.com/fr/programmation

    Parameters:
        query: Filtre sous-chaine artiste / scene / titre (vide = tout lister).
        date: Filtre optionnel YYYY-MM-DD.
        limit: Nombre max d'evenements (1-50).
    """
    return await run_festival_tool(
        "search_piknic_petit",
        lambda: piknic_api.search_events(category="petit", query=query, date=date, limit=limit),
        source="piknic",
        portal_url=piknic_api.PORTAL_URL,
        generic_error="Impossible de joindre Piknic Électronik.",
    )
