"""Tests briefing de quartier (fan-out partiel)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import neighborhood_api


@pytest.mark.asyncio
async def test_build_briefing_partial_success():
    hydro = {
        "total": 1,
        "lieux": [{"has_outage": False, "etat": "A"}],
        "source": "https://infopannes.solutions.hydroquebec.com",
    }
    avis = {"total": 2, "alerts": [{"titre": "A", "distance_m": 10}], "source": "avis"}
    parks = {"total": 1, "items": [{"nom": "Square", "type": "Place", "distance_m": 50}], "source": "parcs"}
    bixi = {
        "total": 1,
        "stations": [{"name": "Berri", "num_bikes_available": 10, "num_docks_available": 5, "distance_m": 100}],
        "source": "bixi",
    }

    with (
        patch(
            "helpers.mtl.neighborhood_api.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": "Hôtel de Ville / 275 Rue Notre-Dame Est",
                "location_source": "agent",
            },
        ),
        patch(
            "helpers.mtl.neighborhood_api._hydro_section",
            new_callable=AsyncMock,
            return_value=hydro,
        ),
        patch(
            "helpers.mtl.neighborhood_api._avis_section",
            new_callable=AsyncMock,
            return_value=avis,
        ),
        patch(
            "helpers.mtl.neighborhood_api._qualo_section",
            new_callable=AsyncMock,
            side_effect=RuntimeError("QUALO down"),
        ),
        patch(
            "helpers.mtl.neighborhood_api._parks_section",
            new_callable=AsyncMock,
            return_value=parks,
        ),
        patch(
            "helpers.mtl.neighborhood_api._bixi_section",
            new_callable=AsyncMock,
            return_value=bixi,
        ),
    ):
        data = await neighborhood_api.build_briefing(
            latitude=45.5088,
            longitude=-73.5541,
            date="2026-07-16",
        )

    assert data["summary"]["hydro_ok"] is True
    assert data["summary"]["avis_count"] == 2
    assert data["summary"]["parks_count"] == 1
    assert data["summary"]["bixi_stations"] == 1
    assert data["summary"]["qualo_bathing_ok"] is None
    assert "error" in data["water_quality"]
    assert "QUALO down" in data["water_quality"]["error"]
    assert data["hydro"]["total"] == 1
    assert data["parks"]["items"][0]["nom"] == "Square"


@pytest.mark.asyncio
async def test_build_briefing_requires_point():
    with pytest.raises(ValueError, match=r"GPS|address"):
        await neighborhood_api.build_briefing()


@pytest.mark.asyncio
async def test_neighborhood_briefing_tool():
    payload = {
        "query": {"latitude": 45.5088, "longitude": -73.5541, "date": "2026-07-16"},
        "summary": {
            "hydro_ok": True,
            "avis_count": 0,
            "qualo_bathing_ok": True,
            "parks_count": 0,
            "bixi_stations": 0,
        },
        "hydro": {"total": 0, "lieux": [], "source": "hydro"},
        "avis": {"total": 0, "alerts": [], "source": "avis"},
        "water_quality": {"total": 0, "stations": [], "source": "qualo"},
        "parks": {"total": 0, "items": [], "source": "parcs"},
        "bixi": {"total": 0, "stations": [], "source": "bixi"},
    }
    with patch(
        "helpers.mtl.neighborhood_api.build_briefing",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.neighborhood.briefing import neighborhood_briefing

        result = json.loads(await neighborhood_briefing(latitude=45.5088, longitude=-73.5541, date="2026-07-16"))
        assert "error" not in result
        assert result["_meta"]["source"] == "mtl_neighborhood_briefing"
        assert result["summary"]["hydro_ok"] is True
