"""Liste MCP des compteurs cyclistes permanents (La bicyclette)."""

import logging

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import labicyclette_api, labicyclette_format
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="mtl_labicyclette_list_counters")
async def list_labicyclette_counters(
    arrondissement: str | None = None,
    limit: int = 50,
) -> str:
    """Liste MCP des compteurs cyclistes Montreal (carte + sites).

    Retourne view=counters, sites slim (instance/name/borough/coords) et chart map_points.

    Parameters:
        arrondissement: Filtre partiel insensible a la casse (ex: 'Plateau').
        limit: Nombre max de sites (1-100, defaut 50).
    """
    try:
        limit = max(1, min(int(limit), 100))
        rows = await labicyclette_api.list_counters()
        if arrondissement and arrondissement.strip():
            needle = arrondissement.strip().casefold()
            rows = [c for c in rows if needle in str(c.get("arrondissement") or "").casefold()]

        slim = [labicyclette_format.slim_counter_site(c) for c in rows[:limit]]
        points = [
            {
                "lat": c["latitude"],
                "lon": c["longitude"],
                "label": c["name"],
                "instance": c["instance"],
            }
            for c in slim
            if c.get("latitude") is not None and c.get("longitude") is not None
        ]
        return ok(
            {
                "view": "counters",
                "count": len(slim),
                "counters": slim,
                "chart": labicyclette_format.map_points(points),
            },
            source="labicyclette",
            portal_url=LABICYCLETTE_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans list_labicyclette_counters")
        return error("Impossible de lister les compteurs La bicyclette.")
