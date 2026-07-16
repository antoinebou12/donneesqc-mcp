"""Geocodage : adresse -> coordonnees (lat/lng) via Adresses Quebec / ICherche."""

from helpers.common.config import GEOCODER_URL
from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.qc.geo.icherche_client import geocode_features
from helpers.qc.geo.icherche_format import feature_to_geocode_result
from tools import mcp


@mcp.tool(name="qc_geo_geocode")
async def geocode(address: str, limit: int = 5) -> str:
    """Convertit une adresse quebecoise en coordonnees geographiques (lat/lng).

    Utilise le service ICherche (Adresses Quebec) du gouvernement du Quebec.
    Demande toujours geometry=true (sinon les features n'ont pas de coordonnees).

    Parameters:
        address: Adresse a geocoder (ex: '900 Boulevard Rene-Levesque, Quebec').
        limit: Nombre maximal de resultats (defaut 5, max 10).
    """

    async def _run() -> str:
        size = max(1, min(limit, 10))
        features = await geocode_features(address, limit=size)
        results = [feature_to_geocode_result(feat) for feat in features]
        return ok(
            {"query": address, "total": len(results), "results": results},
            source="adresses_quebec",
            portal_url=GEOCODER_URL,
        )

    return await run_tool(
        "geocode",
        _run,
        generic_error=f"Impossible de geocoder l'adresse '{address}'. Verifiez le format.",
    )
