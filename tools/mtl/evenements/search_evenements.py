"""Recherche evenements publics Montreal (vmtl-evenements-publics)."""

from __future__ import annotations

from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.mtl import evenements_api
from tools import mcp


@mcp.tool(name="mtl_evenements_search")
async def search_evenements(
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> str:
    """Liste ou filtre les evenements publics Montreal (calendrier civique).

    Source principale: Donnees Quebec (dataset vmtl-evenements-publics),
    avec bascule Donnees Montreal si besoin.
    Chaque evenement date inclut google_calendar_url; la reponse inclut calendar_ascii.

    Parameters:
        query: Filtre sous-chaine titre / type / emplacement (vide = lister).
        date: Filtre optionnel YYYY-MM-DD (evenement actif ce jour).
        limit: Nombre max d'evenements (1-50).
    """

    async def _run() -> str:
        data = await evenements_api.search_evenements(query=query, date=date, limit=limit)
        portal_info = data.pop("_portal", {})
        return ok(
            data,
            source=str(portal_info.get("source") or "donnees_quebec"),
            portal_url=str(
                portal_info.get("portal_url")
                or portal_info.get("dq_dataset_url")
                or DQ_PORTAL.dataset_url(evenements_api.PACKAGE_ID)
            ),
            dataset_id=evenements_api.PACKAGE_ID,
            resource_id=data.get("resource_id"),
            license=portal_info.get("license"),
        )

    return await run_tool(
        "search_evenements",
        _run,
        generic_error="Impossible de joindre le calendrier des evenements publics.",
    )
