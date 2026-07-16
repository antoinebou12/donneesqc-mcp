"""Detail d'une murale subventionnee par id."""

from __future__ import annotations

from helpers.common.response import error
from helpers.common.tool_call import run_tool
from helpers.mtl import murales_api
from helpers.mtl.citations import murales_ok
from tools import mcp


@mcp.tool(name="mtl_murales_get")
async def get_murale(murale_id: str) -> str:
    """Detail d'une murale financee par Montreal (id DataStore).

    Donnees: https://donnees.montreal.ca/dataset/murales
    Viewer: https://www.mtlmurales.ca/fr

    Parameters:
        murale_id: Identifiant sequentiel de la murale (ex: '307', '1').
    """

    async def _run() -> str:
        if not murale_id or not str(murale_id).strip():
            return error("Le parametre murale_id est requis.")
        murale = await murales_api.get_murale(murale_id)
        if murale is None:
            return error(f"Aucune murale trouvee pour id '{murale_id}'.")
        return murales_ok({"murale": murale})

    return await run_tool(
        "get_murale",
        _run,
        generic_error=f"Impossible de recuperer la murale '{murale_id}'.",
    )
