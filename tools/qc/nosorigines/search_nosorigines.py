"""Recherche genealogique publique sur NosOrigines."""

import logging

from helpers.common.config import NOSORIGINES_BASE_URL
from helpers.common.response import error, ok
from helpers.qc.nosorigines import nosorigines_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_nosorigines_search")
async def search_nosorigines(
    last_name: str = "",
    first_name: str = "",
    spouse_last_name: str = "",
    spouse_first_name: str = "",
    year_from: str = "",
    match_mode: str = "starting",
    limit: int = 20,
) -> str:
    """Recherche des personnes ou couples sur NosOrigines.qc.ca.

    Source: https://www.nosorigines.qc.ca/genealogieSearch.aspx?lng=fr

    Sans epoux/epouse: recherche personnes (txbNameChild / txbFirstNameChild).
    Avec spouse_*: recherche de mariage (individu + epouse).

    Parameters:
        last_name: Nom de famille (individu ou epoux).
        first_name: Prenom.
        spouse_last_name: Nom de l'epouse (active la recherche couple).
        spouse_first_name: Prenom de l'epouse.
        year_from: Annee minimale (optionnel).
        match_mode: starting | exact | alias | soundex.
        limit: Nombre max de resultats (1-50).
    """
    try:
        if not any([last_name, first_name, spouse_last_name, spouse_first_name]):
            return error("Indiquez au moins un nom ou prenom.")
        limit = max(1, min(limit, 50))
        data = await nosorigines_api.search_nosorigines(
            last_name=last_name.strip(),
            first_name=first_name.strip(),
            spouse_last_name=spouse_last_name.strip(),
            spouse_first_name=spouse_first_name.strip(),
            year_from=year_from.strip(),
            match_mode=match_mode.strip() or "starting",
            limit=limit,
        )
        return ok(
            data,
            source="nosorigines",
            portal_url=NOSORIGINES_BASE_URL,
        )
    except Exception:
        logger.exception("Erreur dans search_nosorigines")
        return error("Impossible de rechercher sur NosOrigines.")
