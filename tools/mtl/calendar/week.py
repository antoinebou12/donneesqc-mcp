"""Agenda semaine Montreal (festivals, evenements publics, avis)."""

from __future__ import annotations

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.mtl import calendar_week
from tools import mcp


@mcp.tool(name="mtl_calendar_week")
async def calendar_week_tool(
    week_start: str = "",
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 1000.0,
    include_festivals: bool = True,
    include_evenements: bool = True,
    include_avis: bool = True,
    limit_per_source: int = 25,
) -> str:
    """Agenda de la semaine: festivals, evenements publics, avis a proximite.

    Retourne items unifies avec google_calendar_url et calendar_ascii (agenda jour).
    Les avis ne sont inclus que si address ou latitude/longitude sont fournis.

    Parameters:
        week_start: Lundi de la semaine (YYYY-MM-DD); vide = semaine courante (America/Toronto).
        address: Adresse pour les avis (geocodage).
        latitude: Latitude WGS84 (avis).
        longitude: Longitude WGS84 (avis).
        radius_m: Rayon avis en metres (50-5000).
        include_festivals: Inclure Piknic + Jazz Fest.
        include_evenements: Inclure vmtl-evenements-publics.
        include_avis: Inclure avis/alertes (requiert geo).
        limit_per_source: Limite par source (1-50).
    """

    async def _run() -> str:
        data = await calendar_week.build_calendar_week(
            week_start=week_start,
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            include_festivals=include_festivals,
            include_evenements=include_evenements,
            include_avis=include_avis,
            limit_per_source=limit_per_source,
        )
        return ok(
            data,
            source="mtl_calendar",
            portal_url="https://www.donneesquebec.ca/recherche/?q=evenements",
        )

    return await run_tool(
        "calendar_week",
        _run,
        generic_error="Impossible de construire l'agenda de la semaine.",
    )
