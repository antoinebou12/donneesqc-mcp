"""Recherche de murales subventionnées (Montréal / MTL Murales)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import murales_api
from helpers.mtl.citations import murales_ok
from tools import mcp


@mcp.tool(name="mtl_murales_search")
async def search_murales(
    query: str | None = None,
    artiste: str | None = None,
    arrondissement: str | None = None,
    annee: str | None = None,
    annee_min: str | None = None,
    annee_max: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Recherche les murales financees par Montreal depuis 2007.

    Donnees: DataStore CKAN donnees.montreal.ca (jeu murales).
    Viewer: https://www.mtlmurales.ca/fr

    Parameters:
        query: Texte libre (artiste, adresse, arrondissement, organisme).
        artiste: Filtre partiel sur le nom d'artiste.
        arrondissement: Filtre partiel sur l'arrondissement.
        annee: Annee exacte (ex: '2019').
        annee_min: Annee minimale inclusive (ex: '2015').
        annee_max: Annee maximale inclusive (ex: '2020').
        page: Page (defaut 1).
        page_size: Resultats par page (1-200, defaut 20).
    """

    async def _run() -> str:
        data = await murales_api.search_murales(
            query=query,
            artiste=artiste,
            arrondissement=arrondissement,
            annee=annee,
            annee_min=annee_min,
            annee_max=annee_max,
            page=page,
            page_size=page_size,
        )
        return murales_ok(data)

    return await run_tool(
        "search_murales",
        _run,
        generic_error="Impossible de rechercher les murales.",
    )
