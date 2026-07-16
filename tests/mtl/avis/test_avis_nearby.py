"""Tests unitaires pour avis/alertes nearby."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import avis_api

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "mtl" / "avis_alertes_sample.geojson"


def _sample_geojson() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_parse_date_rejects_bad_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        avis_api.parse_date("16/07/2026")


def test_active_on_inclusive_window():
    assert avis_api.active_on(
        date(2026, 7, 16),
        "2026-06-01T12:00:00",
        "2026-08-01T12:00:00",
    )
    assert not avis_api.active_on(
        date(2026, 7, 16),
        "2026-01-01T12:00:00",
        "2026-01-31T12:00:00",
    )


def test_filter_nearby_linestring_beats_far_point():
    hits = avis_api.filter_nearby(
        _sample_geojson(),
        latitude=45.5010,
        longitude=-73.5636,
        target=date(2026, 7, 16),
        radius_m=800.0,
        limit=20,
    )
    titres = [h["titre"] for h in hits]
    assert "Entrave proche — Beaver Hall / Gauchetiere" in titres
    assert "Urgence proche" in titres
    assert "Point loin - hors rayon" not in titres
    assert "Hors fenetre de dates" not in titres
    assert hits[0]["geom_type"] == "LineString"
    assert hits[0]["distance_m"] < hits[-1]["distance_m"]


def test_filter_nearby_type_exact():
    hits = avis_api.filter_nearby(
        _sample_geojson(),
        latitude=45.5010,
        longitude=-73.5636,
        target=date(2026, 7, 16),
        radius_m=2000.0,
        limit=20,
        alert_type="Urgence",
    )
    assert len(hits) == 1
    assert hits[0]["type"] == "Urgence"


def test_filter_nearby_respects_radius():
    hits = avis_api.filter_nearby(
        _sample_geojson(),
        latitude=45.5010,
        longitude=-73.5636,
        target=date(2026, 7, 16),
        radius_m=50.0,
        limit=20,
    )
    assert all(h["distance_m"] <= 50.0 for h in hits)


@pytest.mark.asyncio
async def test_list_nearby_requires_point():
    with pytest.raises(ValueError, match=r"GPS|address"):
        await avis_api.list_nearby(date="2026-07-16")


@pytest.mark.asyncio
async def test_list_nearby_rejects_radius():
    with pytest.raises(ValueError, match="radius_m"):
        await avis_api.list_nearby(
            date="2026-07-16",
            latitude=45.5,
            longitude=-73.5,
            radius_m=10.0,
        )


@pytest.mark.asyncio
async def test_list_nearby_with_coords_uses_geojson():
    with patch(
        "helpers.mtl.avis_api.fetch_avis_geojson",
        new=AsyncMock(return_value=_sample_geojson()),
    ):
        result = await avis_api.list_nearby(
            date="2026-07-16",
            latitude=45.5010,
            longitude=-73.5636,
            radius_m=800.0,
            limit=10,
        )
    assert result["query"]["date"] == "2026-07-16"
    assert result["total"] >= 1
    assert result["alerts"][0]["lien"].startswith("https://montreal.ca/alertes/")
    assert result["alerts"][0]["google_calendar_url"]
    assert result["alerts"][0]["google_maps_url"]
    assert result["alerts"][0]["google_maps_directions_url"]
    assert result["nearest_google_maps_directions_url"]
    assert "calendar_ascii" in result
    assert result["calendar_ascii"]


@pytest.mark.asyncio
async def test_find_avis_nearby_tool_ok():
    with patch(
        "helpers.mtl.avis_api.fetch_avis_geojson",
        new=AsyncMock(return_value=_sample_geojson()),
    ):
        from tools.mtl.avis.find_avis_nearby import find_avis_nearby

        raw = await find_avis_nearby(
            date="2026-07-16",
            latitude=45.5010,
            longitude=-73.5636,
            radius_m=800.0,
        )
    payload = json.loads(raw)
    assert payload["_meta"]["source"] == "avis_alertes"
    assert "avis-alertes" in payload["_meta"]["portal_url"]
    assert payload["_meta"]["dataset_id"] == "avis-alertes"
    assert payload["total"] >= 1
    assert payload["alerts"][0]["google_calendar_url"]
    assert payload["calendar_ascii"]


@pytest.mark.asyncio
async def test_find_avis_nearby_validation_error():
    from tools.mtl.avis.find_avis_nearby import find_avis_nearby

    raw = await find_avis_nearby(date="not-a-date", latitude=45.5, longitude=-73.5)
    payload = json.loads(raw)
    assert "error" in payload or payload.get("ok") is False or "YYYY-MM-DD" in raw
