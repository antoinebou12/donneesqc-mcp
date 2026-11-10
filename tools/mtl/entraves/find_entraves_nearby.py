"""Entraves a la circulation (CIFS) a proximite."""

from __future__ import annotations

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.mtl import entraves_api
from helpers.mtl.citations import entraves_ok
from tools import mcp


@mcp.tool(name="mtl_entraves_nearby")
async def find_entraves_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800.0,
    limit: int = 15,
    type_filter: str | None = None,
    subtype: str | None = None,
    active_only: bool = True,
) -> str:
    """Entraves a la circulation en temps reel a Montreal (standard CIFS).

    Flux public JSON (pas de cle API). Dataset:
    https://donnees.montreal.ca/dataset/entraves-circulation
    Donnees Quebec: https://www.donneesquebec.ca/recherche/dataset/vmtl-entraves-circulation

    Parameters:
        address: Adresse a geocoder.
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        radius_m: Rayon en metres (50-5000, defaut 800).
        limit: Nombre max de resultats (1-50, defaut 15).
        type_filter: Filtre sous-chaine sur le type CIFS (optionnel).
        subtype: Filtre sous-chaine sur le sous-type (optionnel).
        active_only: Si true, filtre starttime/endtime vs maintenant (defaut true).
    """

    async def _run() -> str:
        data = await entraves_api.list_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            radius_m=radius_m,
            limit=limit,
            type_filter=type_filter,
            subtype_filter=subtype,
            active_only=active_only,
        )
        if data.get("fallback"):
            return ok(
                data,
                source=data["source_url"],
                portal_url=data["source_url"],
                dataset_id=data["dataset_id"],
                resource_id=data["resource_id"],
            )
        return entraves_ok(data)

    return await run_tool(
        "find_entraves_nearby",
        _run,
        generic_error="Impossible de lister les entraves a proximite.",
    )
