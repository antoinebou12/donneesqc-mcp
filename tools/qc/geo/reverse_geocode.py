"""Geocodage inverse : coordonnees (lat/lng) -> adresse quebecoise."""

from helpers.common.config import GEOCODER_URL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.qc.geo.icherche_client import reverse_features
from helpers.qc.geo.icherche_format import feature_to_reverse_result
from tools import mcp


@mcp.tool(name="qc_geo_reverse_geocode")
async def reverse_geocode(latitude: float, longitude: float, limit: int = 1) -> str:
    """Convertit des coordonnees geographiques en adresse quebecoise.

    Utilise le service ICherche (Adresses Quebec) du gouvernement du Quebec.
    Si l'API reverse est indisponible, preferez qc_geo_geocode avec une adresse.

    Parameters:
        latitude: Latitude en degres decimaux (ex: 45.5017).
        longitude: Longitude en degres decimaux (ex: -73.5673).
        limit: Nombre maximal de resultats (defaut 1, max 5).
    """

    async def _run() -> str:
        size = max(1, min(limit, 5))
        features = await reverse_features(latitude, longitude, limit=size)
        results = [feature_to_reverse_result(feat) for feat in features]
        return ok(
            {
                "query": {"latitude": latitude, "longitude": longitude},
                "total": len(results),
                "results": results,
            },
            source="adresses_quebec",
            portal_url=GEOCODER_URL,
        )

    return await run_tool(
        "reverse_geocode",
        _run,
        generic_error=f"Impossible de geocoder les coordonnees ({latitude}, {longitude}).",
    )
