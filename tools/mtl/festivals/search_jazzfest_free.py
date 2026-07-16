"""Recherche concerts gratuits Festival de Jazz de Montréal."""

from helpers.mtl import jazzfest_api
from helpers.mtl.events_common import run_festival_tool
from tools import mcp


@mcp.tool(name="mtl_jazzfest_search_free")
async def search_jazzfest_free(
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> str:
    """Liste ou filtre les concerts gratuits du Festival International de Jazz de Montreal.

    Source: https://montrealjazzfest.com/fr/programmation/horaire
    Note: la page officielle est souvent rendue en JS; v1 peut renvoyer une liste vide + warning.

    Parameters:
        query: Filtre sous-chaine artiste / titre / scene (vide = tout lister).
        date: Filtre optionnel YYYY-MM-DD.
        limit: Nombre max d'evenements (1-50).
    """
    return await run_festival_tool(
        "search_jazzfest_free",
        lambda: jazzfest_api.search_events(ticket_kind="free", query=query, date=date, limit=limit),
        source="jazzfest",
        portal_url=jazzfest_api.PORTAL_URL,
        generic_error="Impossible de joindre le Festival de Jazz de Montréal.",
    )
