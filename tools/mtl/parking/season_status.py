"""Statut saison stationnement / deneigement Montreal."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl.citations import parking_deneigement_ok
from helpers.mtl.parking_season import build_parking_season_status
from tools import mcp


@mcp.tool(name="mtl_parking_season_status")
async def parking_season_status(
    date: str | None = None,
    timezone: str | None = None,
) -> str:
    """Saison de stationnement deneigement a Montreal (heuristic Nov 1 - Apr 15).

    Retourne season_label (ex. 2025-2026), in_season, bornes, et cite le jeu
    stationnements-deneigement. A appeler avant mtl_parking_deneigement_nearby.
    Pas d'HTTP — heuristique documentee (publication open data en novembre).

    Parameters:
        date: Date YYYY-MM-DD (sinon aujourd'hui fuseau).
        timezone: Fuseau IANA (defaut America/Toronto).
    """

    async def _run() -> str:
        data = build_parking_season_status(date=date, timezone_name=timezone)
        return parking_deneigement_ok(data)

    return await run_tool(
        "parking_season_status",
        _run,
        generic_error="Impossible de determiner la saison de stationnement deneigement.",
    )
