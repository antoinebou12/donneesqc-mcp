"""KPIs agreges La bicyclette - contrat MCP overview."""

import logging

from helpers.common.config import LABICYCLETTE_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import labicyclette_api, labicyclette_format
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="mtl_labicyclette_overview")
async def get_labicyclette_overview() -> str:
    """Vue d'ensemble MCP des comptages velo Montreal (La bicyclette).

    Retourne un contrat agent-first: view, kpis (cartes), totals, dashboard_url.
    Source amont: https://www.labicyclette.ca/api/stats/overview (non filtrable par date).
    """
    try:
        raw = await labicyclette_api.get_overview()
        total_volume = int(raw.get("totalVolume") or 0)
        active_counters = int(raw.get("activeCounters") or 0)
        unique_days = int(raw.get("uniqueDays") or 0)
        total_records = int(raw.get("totalRecords") or 0)
        daily_average = round(total_volume / unique_days) if unique_days > 0 else 0

        payload = {
            "view": "overview",
            "period": {
                "minDate": raw.get("minDate"),
                "maxDate": raw.get("maxDate"),
            },
            "kpis": labicyclette_format.build_overview_kpis(
                total_volume,
                active_counters,
                daily_average,
            ),
            "totals": {
                "totalVolume": total_volume,
                "activeCounters": active_counters,
                "uniqueDays": unique_days,
                "totalRecords": total_records,
            },
            "dashboard_url": f"{LABICYCLETTE_BASE_URL.rstrip('/')}/en",
        }
        return ok(
            payload,
            source="labicyclette",
            portal_url=LABICYCLETTE_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans get_labicyclette_overview")
        return error("Impossible de recuperer les statistiques La bicyclette.")
