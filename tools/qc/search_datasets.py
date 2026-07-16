"""Recherche de jeux de données sur Données Québec."""

from helpers.common import ckan_format
from helpers.common.portals import DQ_PORTAL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="qc_search_datasets")
async def search_datasets(
    query: str,
    page: int = 1,
    page_size: int = 20,
    organization: str | None = None,
    tags: str | None = None,
) -> str:
    """Recherche de jeux de données sur Données Québec par mots-clés.

    Le portail contient des données du gouvernement du Québec et de
    nombreuses municipalités (Montréal, Québec, Laval, Sherbrooke, Gatineau, etc.).

    Parameters:
        query: Termes de recherche (ex: 'transport', 'criminalité montréal').
        page: Numéro de page (défaut 1).
        page_size: Résultats par page (1-100, défaut 20).
        organization: Filtrer par organisation (ex: 'ville-de-montreal').
        tags: Filtrer par tags séparés par des virgules.
    """

    async def _run() -> str:
        result = await ckan_format.search_packages(
            DQ_PORTAL,
            query=query,
            page=page,
            page_size=page_size,
            organization=organization,
            tags=tags,
            include_tags=True,
        )
        return ok(
            {
                "count": result["count"],
                "page": result["page"],
                "page_size": result["page_size"],
                "datasets": result["datasets"],
            },
            source=DQ_PORTAL.source,
            portal_url=DQ_PORTAL.base_url,
        )

    return await run_tool(
        "search_datasets",
        _run,
        generic_error="Impossible de rechercher les jeux de données. Vérifiez les paramètres et réessayez.",
    )
