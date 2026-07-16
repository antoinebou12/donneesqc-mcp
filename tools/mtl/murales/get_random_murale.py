"""Tirage aleatoire de murales subventionnees."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import murales_api
from helpers.mtl.citations import murales_ok
from tools import mcp


@mcp.tool(name="mtl_murales_random")
async def get_random_murale(
    artiste: str | None = None,
    arrondissement: str | None = None,
    annee: str | None = None,
    count: int = 1,
) -> str:
    """Tire une ou plusieurs murales au hasard (filtres optionnels).

    Donnees: https://donnees.montreal.ca/dataset/murales
    Viewer: https://www.mtlmurales.ca/fr

    Parameters:
        artiste: Filtre partiel optionnel sur l'artiste.
        arrondissement: Filtre partiel optionnel sur l'arrondissement.
        annee: Annee exacte optionnelle (ex: '2024').
        count: Nombre de murales a tirer (1-20, defaut 1).
    """

    async def _run() -> str:
        data = await murales_api.get_random(
            artiste=artiste,
            arrondissement=arrondissement,
            annee=annee,
            count=count,
        )
        return murales_ok(data)

    return await run_tool(
        "get_random_murale",
        _run,
        generic_error="Impossible de tirer une murale au hasard.",
    )
