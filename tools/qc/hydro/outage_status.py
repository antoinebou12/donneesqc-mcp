"""État du service électrique Hydro-Québec (Info-pannes) pour une adresse."""

from __future__ import annotations

from helpers.common.config import HYDRO_INFOPANNES_PORTAL_URL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.qc.hydro import address_resolve, infopannes_api
from tools import mcp


@mcp.tool(name="qc_hydro_outage_status")
async def outage_status(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    appartement: str | None = None,
) -> str:
    """Etat du service electrique Hydro-Quebec (Info-pannes) pour une adresse.

    Accepte soit une adresse libre, soit latitude+longitude (reverse via
    Adresses Quebec). Consulte l'API publique Info-pannes (lieux-conso puis etats).
    Portail: https://infopannes.solutions.hydroquebec.com
    Wrapper communautaire - non affilie a Hydro-Quebec; donnees approximatives.

    Parameters:
        address: Adresse quebecoise (ex. '1 Place Ville-Marie, Montreal').
        latitude: Latitude WGS84 (avec longitude; alternative a address).
        longitude: Longitude WGS84.
        appartement: Numero d'appartement / unite (optionnel).
    """

    async def _run() -> str:
        civic = await address_resolve.resolve_civic(
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        status = await infopannes_api.outage_status_for_civic(
            street_number=str(civic["street_number"]),
            street=str(civic["street"]),
            postal_code=str(civic["postal_code"]),
            appartement=appartement,
        )
        payload = {
            "query": {
                "address": address,
                "latitude": latitude,
                "longitude": longitude,
                "appartement": appartement,
            },
            "resolved_address": {
                "street_number": civic["street_number"],
                "street": civic["street"],
                "postal_code": civic["postal_code"],
                "municipality": civic.get("municipality"),
                "address": civic.get("address"),
                "latitude": civic.get("latitude"),
                "longitude": civic.get("longitude"),
            },
            **status,
        }
        return ok(
            payload,
            source="hydro_quebec_infopannes",
            portal_url=HYDRO_INFOPANNES_PORTAL_URL,
        )

    return await run_tool(
        "outage_status",
        _run,
        generic_error="Impossible de recuperer l'etat du service Info-pannes.",
    )
