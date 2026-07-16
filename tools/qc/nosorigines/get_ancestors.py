"""Arbre d'ancetres NosOrigines (wrapper mince sur get_person)."""

import logging

from helpers.common.config import NOSORIGINES_BASE_URL
from helpers.common.response import error, ok
from helpers.qc.nosorigines import nosorigines_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_nosorigines_get_ancestors")
async def get_ancestors(pid: str, generations: int = 2) -> str:
    """Remonte les parents / grands-parents via les fiches NosOrigines.

    Source: https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=

    Recurse uniquement sur le pere/mere de la personne (pas les beaux-parents).
    Le grand-pere paternel est ``father.father`` (ou ``father.person`` si
    generations=1 puis un second appel). Les noms « Privé » restent proteges.

    Parameters:
        pid: Identifiant numerique NosOrigines.
        generations: Profondeur 1-3 (defaut 2 = parents + grands-parents).
    """
    try:
        if not pid or not str(pid).strip():
            return error("Le parametre pid est requis.")
        data = await nosorigines_api.get_ancestors(
            str(pid).strip(),
            generations=generations,
        )
        return ok(
            data,
            source="nosorigines",
            portal_url=f"{NOSORIGINES_BASE_URL}/GenealogieQuebec.aspx?pid={data['pid']}",
        )
    except ValueError as exc:
        return error(str(exc))
    except Exception:
        logger.exception("Erreur dans get_ancestors NosOrigines")
        return error(f"Impossible de remonter les ancetres pour pid={pid}.")
