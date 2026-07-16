"""Briefing de quartier Montréal (Hydro + avis + QUALO + parcs + BIXI)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import neighborhood_api
from helpers.mtl.citations import neighborhood_ok
from tools import mcp


@mcp.tool(name="mtl_neighborhood_briefing")
async def neighborhood_briefing(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    date: str | None = None,
    avis_radius_m: float = 1000.0,
    parks_radius_m: float = 300.0,
    bixi_radius_m: float = 400.0,
    qualo_radius_m: float = 1500.0,
    limit: int = 10,
) -> str:
    """Briefing de quartier Montreal: Hydro, avis, QUALO, parcs et BIXI.

    Un seul appel pour un point (adresse et/ou lat/lng). Chaque section peut
    echouer independamment (cle ``error``) sans faire echouer le briefing.
    Presentation agent: verdict court puis tableaux markdown (Dist. en 1re colonne)
    avec source sous chaque section.

    Parameters:
        address: Adresse (ex. '275 Rue Notre-Dame Est, Montreal').
        latitude: Latitude WGS84 (avec longitude; prioritaire si fournie).
        longitude: Longitude WGS84.
        date: Date avis YYYY-MM-DD (defaut: aujourd'hui America/Toronto).
        avis_radius_m: Rayon avis/alertes (50-5000, defaut 1000).
        parks_radius_m: Rayon parcs / espaces verts (50-5000, defaut 300).
        bixi_radius_m: Rayon stations BIXI (50-5000, defaut 400).
        qualo_radius_m: Rayon stations QUALO (50-15000, defaut 1500).
        limit: Max d'elements par liste (1-50, defaut 10).
    """

    async def _run() -> str:
        data = await neighborhood_api.build_briefing(
            address=address,
            latitude=latitude,
            longitude=longitude,
            date=date,
            avis_radius_m=avis_radius_m,
            parks_radius_m=parks_radius_m,
            bixi_radius_m=bixi_radius_m,
            qualo_radius_m=qualo_radius_m,
            limit=limit,
        )
        return neighborhood_ok(data)

    return await run_tool(
        "neighborhood_briefing",
        _run,
        generic_error="Impossible de produire le briefing de quartier.",
    )
