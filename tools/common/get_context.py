"""Contexte utilisateur - date/heure, GPS agent, IP client approx."""

from __future__ import annotations

from helpers.common.context import build_user_context
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from tools import mcp


@mcp.tool(name="common_get_context")
async def get_context(
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    date: str | None = None,
    timezone: str | None = None,
    include_client_ip: bool = True,
) -> str:
    """Contexte utilisateur pour nearby / evenements (GPS telephone + heure systeme).

    Preferez passer latitude/longitude (GPS appareil) et date/timezone systeme.
    Si omis : date = maintenant America/Toronto ; localisation = IP client
    (X-Forwarded-For) si publique. L'IP du serveur MCP n'est JAMAIS utilisee.

    Parameters:
        latitude: Latitude WGS84 du telephone/PC (prioritaire).
        longitude: Longitude WGS84.
        address: Adresse a geocoder si pas de GPS.
        date: Date YYYY-MM-DD (sinon aujourd'hui fuseau).
        timezone: Fuseau IANA (defaut America/Toronto).
        include_client_ip: Inclure l'IP client detectee dans la reponse.
    """

    async def _run() -> str:
        # Geo via IP seulement si agent n'a fourni ni GPS ni adresse
        has_coords = latitude is not None and longitude is not None
        has_address = bool(address and address.strip())
        data = await build_user_context(
            latitude=latitude,
            longitude=longitude,
            address=address,
            date=date,
            timezone_name=timezone,
            include_client_ip=include_client_ip,
            allow_client_ip_geo=not (has_coords or has_address),
        )
        return ok(data, source="donneesqc_mcp")

    return await run_tool(
        "get_context",
        _run,
        generic_error="Impossible de resoudre le contexte utilisateur.",
    )
