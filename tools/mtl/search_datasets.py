"""Recherche dans le catalogue de données ouvertes de Montréal."""

from helpers.common import ckan_format
from helpers.common.portals import MTL_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="mtl_search_datasets")
async def search_montreal_datasets(query: str, page: int = 1, page_size: int = 20) -> str:
    """Recherche dans le catalogue de données ouvertes de la Ville de Montréal.

    Le portail donnees.montreal.ca contient des données spécifiques à la
    ville : actes criminels, travaux routiers, arbres publics, pistes
    cyclables, qualité de l'eau, contrats municipaux, etc.

    Parameters:
        query: Termes de recherche (ex: 'pistes cyclables', 'actes criminels').
        page: Numéro de page (défaut 1).
        page_size: Résultats par page (1-100, défaut 20).
    """

    async def _run() -> str:
        result = await ckan_format.search_packages(
            MTL_PORTAL,
            query=query,
            page=page,
            page_size=page_size,
            default_organization="Ville de Montréal",
        )
        return ok(
            {
                "count": result["count"],
                "page": result["page"],
                "page_size": result["page_size"],
                "datasets": result["datasets"],
            },
            source=MTL_PORTAL.source,
            portal_url=MTL_PORTAL.base_url,
        )

    return await run_tool(
        "search_montreal_datasets",
        _run,
        generic_error="Impossible de rechercher sur donnees.montreal.ca.",
    )
