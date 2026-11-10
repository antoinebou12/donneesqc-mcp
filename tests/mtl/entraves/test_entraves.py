"""Tests entraves CIFS nearby."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from helpers.mtl import entraves_api

_FIXTURE = json.loads(Path("tests/fixtures/mtl/entraves_cifs_sample.json").read_text(encoding="utf-8"))
_NOW = datetime(2026, 7, 16, 12, 0, tzinfo=ZoneInfo("America/Toronto"))


def test_polyline_to_linestring():
    geom = entraves_api.polyline_to_linestring("45.5088 -73.5541 45.5090 -73.5535")
    assert geom is not None
    assert geom["type"] == "LineString"
    assert geom["coordinates"][0] == [-73.5541, 45.5088]


def test_filter_nearby_active():
    rows = entraves_api.filter_nearby(
        _FIXTURE,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=500,
        limit=10,
        active_only=True,
        now=_NOW,
    )
    ids = {r["id"] for r in rows}
    assert "EVT-1" in ids
    assert "EVT-FAR" not in ids
    assert "EVT-EXPIRED" not in ids
    assert rows[0]["street"] == "rue Notre-Dame Est"


@pytest.mark.asyncio
async def test_list_nearby_mocked():
    with (
        patch(
            "helpers.mtl.nearby.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": "Hôtel de Ville",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.mtl.entraves_api.fetch_json",
            new_callable=AsyncMock,
            return_value=_FIXTURE,
        ),
    ):
        data = await entraves_api.list_nearby(address="Hôtel de Ville", radius_m=800, limit=5)
    assert data["total"] >= 1
    assert data["entraves"][0]["id"] == "EVT-1"
