"""Tests météo Open-Meteo (sans réseau)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import weather_api

_FIXTURE = json.loads(Path("tests/fixtures/mtl/open_meteo_forecast.json").read_text(encoding="utf-8"))


def test_weather_label_fr_known_and_unknown():
    assert weather_api.weather_label_fr(0) == "Ciel dégagé"
    assert weather_api.weather_label_fr(1) == "Principalement clair"
    assert weather_api.weather_label_fr(999).startswith("Code météo")
    assert weather_api.weather_label_fr(None) == "Inconnu"


def test_parse_open_meteo_fixture():
    data = weather_api.parse_open_meteo(
        _FIXTURE,
        latitude=45.5088,
        longitude=-73.5541,
        resolved_address="Hôtel de Ville",
        timezone_name="America/Toronto",
    )
    assert data["current"]["temperature_c"] == 22.1
    assert data["current"]["weather_label_fr"] == "Principalement clair"
    assert data["weather_summary"] == "22°C, Principalement clair"
    assert len(data["daily"]) == 3
    assert data["daily"][2]["weather_label_fr"] == "Pluie faible"
    assert data["google_maps_url"]
    assert "Open-Meteo" in data["attribution"]


@pytest.mark.asyncio
async def test_get_weather_nearby_uses_resolve_and_fetch():
    with (
        patch(
            "helpers.mtl.weather_api.resolve_point",
            new_callable=AsyncMock,
            return_value=(45.5088, -73.5541, "Hôtel de Ville"),
        ),
        patch(
            "helpers.mtl.weather_api.fetch_json",
            new_callable=AsyncMock,
            return_value=_FIXTURE,
        ) as fetch,
    ):
        data = await weather_api.get_weather_nearby(
            address="Hôtel de Ville de Montréal",
            timezone="America/Toronto",
        )

    assert data["current"]["temperature_c"] == 22.1
    assert data["resolved_address"] == "Hôtel de Ville"
    fetch.assert_awaited_once()
    kwargs = fetch.await_args
    assert kwargs is not None
    assert "forecast" in kwargs.args[0] or "open-meteo" in kwargs.args[0]
    params = kwargs.kwargs.get("params") or kwargs.args[1]
    assert params["timezone"] == "America/Toronto"
    assert params["forecast_days"] == 3
