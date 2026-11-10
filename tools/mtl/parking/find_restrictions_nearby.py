"""Restrictions de stationnement (signalisation interdiction) a proximite."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import parking_signalisation_api
from helpers.mtl.citations import parking_signalisation_ok
from tools import mcp


@mcp.tool(name="mtl_parking_restrictions_nearby")
async def find_parking_restrictions_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 300.0,
    limit: int = 20,
) -> str:
    """Panneaux d'interdiction / stationnement interdit / remorquage a proximite.

    Donnees: DataStore CKAN donnees.montreal.ca
    (jeu stationnement-sur-rue-signalisation-courant). Filtre les panneaux
    a risque de contravention (\\A, \\P, interdit, remorquage); pas un moteur tarifaire.

    Parameters:
        address: Adresse a geocoder (ex. 'Hotel de Ville de Montreal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (defaut 300).
        limit: Nombre max de panneaux (1-50, defaut 20).
    """

    async def _run() -> str:
        data = await parking_signalisation_api.list_restrictions_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
        )
        return parking_signalisation_ok(data)

    return await run_tool(
        "find_parking_restrictions_nearby",
        _run,
        generic_error="Impossible de lister les restrictions de stationnement.",
    )
