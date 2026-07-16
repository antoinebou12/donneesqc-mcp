"""Recherche dans la Vitrine linguistique (OQLF) - BDL et GDT."""

import logging

from helpers.common.config import VITRINE_BASE_URL
from helpers.common.response import error, ok
from helpers.qc.oqlf import vitrine_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_oqlf_search")
async def search_vitrine_linguistique(
    query: str,
    include_bdl: bool = True,
    include_gdt: bool = True,
    limit: int = 10,
) -> str:
    """Recherche dans la Vitrine linguistique de l'OQLF (BDL et/ou GDT).

    Source: https://vitrinelinguistique.oqlf.gouv.qc.ca/

    Parameters:
        query: Terme ou expression a chercher (ex: 'Québec', 'tabanark').
        include_bdl: Inclure la Banque de depannage linguistique.
        include_gdt: Inclure le Grand dictionnaire terminologique.
        limit: Nombre max de resultats (1-25).
    """
    try:
        if not query or not query.strip():
            return error("Le parametre query est requis.")
        limit = max(1, min(limit, 25))
        data = await vitrine_api.search_vitrine(
            query.strip(),
            include_bdl=include_bdl,
            include_gdt=include_gdt,
            limit=limit,
        )
        return ok(
            data,
            source="vitrine_linguistique",
            portal_url=VITRINE_BASE_URL,
        )
    except Exception:
        logger.exception("Erreur dans search_vitrine_linguistique")
        return error(f"Impossible de rechercher '{query}' dans la Vitrine linguistique.")
