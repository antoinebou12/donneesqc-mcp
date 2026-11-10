"""Public 311 requests around a Montréal location."""

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.common.urls import MTL_311_DATASET_ID, MTL_311_RESOURCE_ID, MTL_311_SOURCE_URL
from helpers.mtl import requests311_api
from tools import mcp


@mcp.tool(name="mtl_311_nearby")
async def requests311_nearby(
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 800,
    days: int = 30,
    limit: int = 10,
    use_latest_available: bool = False,
) -> str:
    """Recent public 311 requests near a location (1-90 days, 100-3000 m).

    Published requests do not prove a municipal intervention. Only geolocated
    records are included; results are bounded and sorted by creation date.
    use_latest_available anchors the window to the latest published geolocated
    date and labels historical data explicitly; otherwise the window ends today.
    Source: https://donnees.montreal.ca/dataset/requete-311
    """

    async def run() -> str:
        data = await requests311_api.list_nearby(
            address, latitude, longitude, radius_m, days, limit, use_latest_available
        )
        return ok(
            data,
            source=MTL_311_SOURCE_URL,
            portal_url=MTL_311_SOURCE_URL,
            dataset_id=MTL_311_DATASET_ID,
            resource_id=MTL_311_RESOURCE_ID,
        )

    return await run_tool("requests311_nearby", run, generic_error="Les demandes 311 sont indisponibles.")
