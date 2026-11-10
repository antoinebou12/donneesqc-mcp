"""Tests stationnements déneigement nearby."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import parking_api

_FIXTURE = json.loads(Path("tests/fixtures/mtl/parking_deneigement_sample.geojson").read_text(encoding="utf-8"))


def test_parse_parking_geojson_nearby():
    rows = parking_api.parse_parking_geojson(
        _FIXTURE,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=2000,
        limit=10,
    )
    assert len(rows) >= 1
    assert rows[0]["distance_m"] <= rows[-1]["distance_m"]
    assert any("Hôtel" in (r.get("emplacement") or "") or r["id"] == "999" for r in rows)


def test_parse_parking_free_only():
    rows = parking_api.parse_parking_geojson(
        _FIXTURE,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=5000,
        limit=10,
        free_only=True,
    )
    assert all(r["free"] for r in rows)
    assert all(r["type_pay"] == "gratuit" for r in rows)


@pytest.mark.asyncio
async def test_list_nearby_mocked():
    with (
        patch(
            "helpers.mtl.parking_api.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": "Hôtel de Ville",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.mtl.parking_api.resolve_geojson_url",
            new_callable=AsyncMock,
            return_value=("https://example.test/parking.geojson", "res-1"),
        ),
        patch(
            "helpers.mtl.parking_api.fetch_text",
            new_callable=AsyncMock,
            return_value=json.dumps(_FIXTURE),
        ),
    ):
        data = await parking_api.list_nearby(address="Hôtel de Ville", radius_m=2000, limit=5)
    assert data["total"] >= 1
    assert data["lots"]
    assert data["dataset_id"] == "stationnements-deneigement"
