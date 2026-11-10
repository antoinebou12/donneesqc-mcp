"""Stationnements gratuits/payants (déneigement) a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import parking_api
from helpers.mtl.citations import parking_deneigement_ok
from tools import mcp


@mcp.tool(name="mtl_parking_deneigement_nearby")
async def find_parking_deneigement_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
    free_only: bool = False,
) -> str:
    """Stationnements incitatifs (gratuits/payants) pour le deneigement a Montreal.

    Donnees ouvertes saisonnieres (GeoJSON) — pas d'API jeton.
    Dataset: https://donnees.montreal.ca/dataset/stationnements-deneigement
    Donnees Quebec: https://www.donneesquebec.ca/recherche/dataset/vmtl-stationnements-deneigement

    La signalisation sur place prevalt toujours.

    Parameters:
        address: Adresse a geocoder (ex. 'Hotel de Ville de Montreal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 800).
        limit: Nombre max de resultats (1-50, defaut 15).
        free_only: Si true, ne garde que les stationnements gratuits.
    """

    async def _run() -> str:
        data = await parking_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
            free_only=free_only,
        )
        return parking_deneigement_ok(data)

    return await run_tool(
        "find_parking_deneigement_nearby",
        _run,
        generic_error="Impossible de lister les stationnements deneigement.",
    )
