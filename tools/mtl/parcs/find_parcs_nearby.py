"""Parcs et espaces verts Montreal a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import parcs_api
from helpers.mtl.citations import parcs_ok
from tools import mcp


@mcp.tool(name="mtl_parcs_nearby")
async def find_parcs_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
    parks_only: bool = True,
) -> str:
    """Parcs / places publiques proches d'une adresse ou d'un point a Montreal.

    Donnees: GeoJSON Espaces verts (fichier) â€” pas le DataStore ligne-par-ligne.
    Dataset: https://donnees.montreal.ca/dataset/grands-parcs-parcs-d-arrondissements-et-espaces-publics

    Parameters:
        address: Adresse a geocoder (ex. 'Hôtel de Ville de Montréal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 800).
        limit: Nombre max de resultats (1-50, defaut 15).
        parks_only: Si true, filtre TYPO1 contenant 'Parc' (defaut true).
    """

    async def _run() -> str:
        data = await parcs_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
            parks_only=parks_only,
        )
        return parcs_ok(data)

    return await run_tool(
        "find_parcs_nearby",
        _run,
        generic_error="Impossible de lister les parcs a proximite.",
    )
