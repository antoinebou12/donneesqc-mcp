"""MCP App registration, packaging and partial-source behavior."""

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from helpers.mtl.dashboard import build_dashboard


async def test_dashboard_resolves_once_and_retains_partial_results(monkeypatch):
    resolve = AsyncMock(return_value=(45.508, -73.554, "Hôtel de Ville de Montréal"))
    monkeypatch.setattr("helpers.mtl.dashboard.resolve_point", resolve)
    for module, name in (
        ("bixi.find_bixi_nearby", "find_bixi_nearby"),
        ("parcs.find_parcs_nearby", "find_parcs_nearby"),
        ("stm.find_stops_nearby", "find_stm_stops_nearby"),
        ("requests311", "requests311_nearby"),
        ("parking.find_restrictions_nearby", "find_parking_restrictions_nearby"),
        ("parking.find_parking_deneigement_nearby", "find_parking_deneigement_nearby"),
        ("entraves.find_entraves_nearby", "find_entraves_nearby"),
        ("avis.find_avis_nearby", "find_avis_nearby"),
        ("murales.list_murales_nearby", "list_murales_nearby"),
        ("rem.find_stops_nearby", "find_rem_stops_nearby"),
        ("collecte.find_montreal_ecocentres", "find_montreal_ecocentres"),
        ("events.events_soon", "events_soon_tool"),
    ):
        monkeypatch.setattr(
            f"tools.mtl.{module}.{name}",
            AsyncMock(return_value=json.dumps({"items": [], "source": "https://donnees.montreal.ca"})),
        )
    monkeypatch.setattr(
        "tools.mtl.weather.find_weather_nearby.find_weather_nearby", AsyncMock(side_effect=TimeoutError)
    )
    for name in ("qc_sit_restaurants_nearby", "qc_sit_tourist_nearby"):
        monkeypatch.setattr(f"tools.qc.sit.restaurants_nearby.{name}", AsyncMock(return_value='{"places": []}'))
    result = await build_dashboard("Hôtel de Ville de Montréal", 800)
    resolve.assert_awaited_once()
    assert "error" in result["sections"]["weather"]
    assert result["sections"]["bixi"]["source"] == "https://donnees.montreal.ca"
    assert result["sections"]["parks"]["items"] == []
    assert len(result["sections"]) == 15
    assert result["openstreetmap_embed_url"].startswith("https://www.openstreetmap.org/export/embed.html?")
    assert result["sections"]["snowparking"]["search_radius_m"] == 5000
    assert result["sections"]["snowparking"]["expanded_from_radius_m"] == 800


@pytest.mark.parametrize(("address", "radius"), [("", 800), ("x" * 301, 800), ("Place des Arts", 99)])
async def test_invalid_dashboard_input(address, radius):
    with pytest.raises(ValueError, match=r"caractères|rayon"):
        await build_dashboard(address, radius)


async def test_dashboard_app_resource_and_tool():
    from tools import mcp, register_all_tools
    from tools.mtl.dashboard import RESOURCE_URI

    register_all_tools()
    tool = next(t for t in await mcp.list_tools() if t.name == "mtl_show_dashboard")
    assert tool.meta is not None
    assert tool.meta["ui"]["resourceUri"] == RESOURCE_URI
    assert tool.outputSchema is not None
    resource = next(iter(await mcp.read_resource(RESOURCE_URI)))
    assert isinstance(resource.content, str)
    assert resource.meta is not None
    assert resource.mime_type == "text/html;profile=mcp-app"
    assert "ui/initialize" in resource.content
    assert "ui/notifications/initialized" in resource.content
    assert "<script src=" not in resource.content
    assert resource.meta["ui"]["csp"]["frameDomains"] == ["https://www.openstreetmap.org"]


@pytest.mark.parametrize("body", [[], {"radius_m": "invalid"}, {"view": "unknown"}])
async def test_browser_dashboard_rejects_invalid_arguments(body, monkeypatch):
    from asgi import app

    build = AsyncMock()
    monkeypatch.setattr("tools.mtl.dashboard.build_dashboard", build)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/montreal/api", json=body)
    assert response.status_code == 400
    build.assert_not_awaited()


async def test_browser_and_mcp_use_same_dashboard_arguments(monkeypatch):
    from asgi import app

    build = AsyncMock(return_value={"sections": {}, "view": "move"})
    monkeypatch.setattr("tools.mtl.dashboard.build_dashboard", build)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/montreal/api", json={"address": "Place des Arts", "radius_m": 1500, "view": "move"}
        )
    assert response.status_code == 200
    assert response.json()["view"] == "move"
    build.assert_awaited_once_with("Place des Arts", 1500, "move")
