"""Volumes par arrondissement - contrat MCP boroughs."""

import logging

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import labicyclette_api, labicyclette_format
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="mtl_labicyclette_boroughs")
async def get_labicyclette_boroughs() -> str:
    """Volumes velo par arrondissement (bar chart MCP).

    Totaux all-time: l'API amont ignore les filtres de dates.
    Retourne ranks, volumeSharePct et chart bar.
    """
    try:
        rows = await labicyclette_api.get_boroughs()
        formatted = labicyclette_format.format_boroughs(rows)
        return ok(
            {
                "view": "boroughs",
                "note": "All-time totals; upstream ignores date filters",
                **formatted,
            },
            source="labicyclette",
            portal_url=LABICYCLETTE_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans get_labicyclette_boroughs")
        return error("Impossible de recuperer les volumes par arrondissement.")
