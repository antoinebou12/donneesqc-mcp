"""Conditions et previsions meteo a proximite (Open-Meteo)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl.citations import weather_ok
from helpers.mtl.weather_api import get_weather_nearby
from tools import mcp


@mcp.tool(name="mtl_weather_nearby")
async def find_weather_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    timezone: str | None = None,
    forecast_days: int = 3,
) -> str:
    """Meteo live (conditions + 3 jours) pour une adresse ou un point GPS.

    Source: Open-Meteo Forecast API (pas de cle, CC BY 4.0).
    https://open-meteo.com/en/docs

    Resolve GPS agent -> adresse -> IP client (jamais l'IP du serveur MCP).

    Parameters:
        address: Adresse a geocoder (ex. 'Hotel de Ville de Montreal').
        latitude: Latitude WGS84 (avec longitude).
        longitude: Longitude WGS84.
        timezone: Fuseau IANA (defaut America/Toronto).
        forecast_days: Jours de prevision quotidienne (1-7, defaut 3).
    """

    async def _run() -> str:
        data = await get_weather_nearby(
            address=address,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            forecast_days=forecast_days,
        )
        return weather_ok(data)

    return await run_tool(
        "find_weather_nearby",
        _run,
        generic_error="Impossible d'obtenir la meteo pour ce point.",
    )
