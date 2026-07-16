"""Facettes (artistes, arrondissements, annees) pour les murales."""

from __future__ import annotations

from typing import Literal

from helpers.common.tool_call import run_tool
from helpers.mtl import murales_api
from helpers.mtl.citations import murales_ok
from tools import mcp

FacetName = Literal["artiste", "arrondissement", "annee"]


@mcp.tool(name="mtl_murales_facet")
async def list_murales_facet(facet: FacetName) -> str:
    """Liste les valeurs distinctes d'une facette (artiste, arrondissement, annee).

    Utile pour peupler des filtres comme sur https://www.mtlmurales.ca/fr
    Donnees: https://donnees.montreal.ca/dataset/murales

    Parameters:
        facet: 'artiste' | 'arrondissement' | 'annee'
    """

    async def _run() -> str:
        data = await murales_api.list_facets(facet)
        return murales_ok(data)

    return await run_tool(
        "list_murales_facet",
        _run,
        generic_error=f"Impossible de lister la facette '{facet}'.",
    )
