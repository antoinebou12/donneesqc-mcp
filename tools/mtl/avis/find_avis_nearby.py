"""Avis et alertes Montréal à proximité d'une adresse / d'un point."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import avis_api
from helpers.mtl.citations import avis_ok
from tools import mcp


@mcp.tool(name="mtl_avis_nearby")
async def find_avis_nearby(
    date: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 1000.0,
    limit: int = 20,
    type: str | None = None,  # noqa: A002 - MCP param name matches dataset field
) -> str:
    """Avis et alertes Montreal actifs a une date, proches d'une adresse.

    Donnees: GeoJSON Donnees Montreal (geometries Point / LineString).
    Dataset: https://donnees.montreal.ca/dataset/avis-alertes
    Viewer: https://montreal.ca/avis-et-alertes
    Fenetre temporelle amont: environ les 12 dernieres semaines.

    Parameters:
        date: Date cible YYYY-MM-DD (defaut: aujourd'hui America/Toronto / GPS agent).
        address: Adresse a geocoder (ex. '800 Rue De La Gauchetiere Ouest, Montreal').
        latitude: Latitude WGS84 GPS telephone/PC (prioritaire).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 1000).
        limit: Nombre max de resultats (1-50, defaut 20).
        type: Filtre exact sur le type (ex. 'Urgence', 'Circulation et transport').
    """

    async def _run() -> str:
        data = await avis_api.list_nearby(
            date=date,
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
            alert_type=type,
        )
        return avis_ok(data)

    return await run_tool(
        "find_avis_nearby",
        _run,
        generic_error="Impossible de lister les avis a proximite.",
    )
