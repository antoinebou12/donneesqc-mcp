"""Fiche personne NosOrigines (GenealogieQuebec pid)."""

import logging

from helpers.common.config import NOSORIGINES_BASE_URL
from helpers.common.response import error, ok
from helpers.qc.nosorigines import nosorigines_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_nosorigines_get_person")
async def get_person(pid: str) -> str:
    """Recupere une fiche personne NosOrigines (parents, conjoint, enfants).

    Source: https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=

    Prefere un pid issu de qc_nosorigines_search. Les fiches vivantes peuvent
    afficher « Privé » / **** (ne pas inventer le nom).

    Parameters:
        pid: Identifiant numerique NosOrigines (ex. 781 pour Francois Boucher).
    """
    try:
        if not pid or not str(pid).strip():
            return error("Le parametre pid est requis.")
        data = await nosorigines_api.get_person(str(pid).strip())
        return ok(
            data,
            source="nosorigines",
            portal_url=data.get("url") or NOSORIGINES_BASE_URL,
        )
    except ValueError as exc:
        return error(str(exc))
    except Exception:
        logger.exception("Erreur dans get_person NosOrigines")
        return error(f"Impossible de recuperer la fiche pid={pid}.")
