"""Tests BIXI nearby (fixtures GBFS)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import bixi_api

_INFO = {
    "data": {
        "stations": [
            {
                "station_id": "1",
                "name": "de la Commune / Berri",
                "lat": 45.5106,
                "lon": -73.5501,
                "capacity": 45,
            },
            {
                "station_id": "2",
                "name": "Far away",
                "lat": 45.6,
                "lon": -73.7,
                "capacity": 10,
            },
        ]
    }
}
_STATUS = {
    "data": {
        "stations": [
            {
                "station_id": "1",
                "num_bikes_available": 10,
                "num_docks_available": 35,
                "is_renting": True,
                "is_returning": True,
            },
            {
                "station_id": "2",
                "num_bikes_available": 0,
                "num_docks_available": 10,
                "is_renting": True,
                "is_returning": True,
            },
        ]
    }
}


def test_merge_stations_radius():
    rows = bixi_api.merge_stations(
        _INFO,
        _STATUS,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=400,
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "de la Commune / Berri"
    assert rows[0]["bikes_available"] == 10


@pytest.mark.asyncio
async def test_find_bixi_nearby_tool():
    with (
        patch(
            "helpers.mtl.nearby.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": None,
                "location_source": "agent",
            },
        ),
        patch(
            "helpers.mtl.bixi_api.fetch_json",
            new_callable=AsyncMock,
            side_effect=[_INFO, _STATUS],
        ),
    ):
        from tools.mtl.bixi.find_bixi_nearby import find_bixi_nearby

        result = json.loads(await find_bixi_nearby(latitude=45.5088, longitude=-73.5541))
        assert "error" not in result
        assert result["total"] == 1
        assert result["_meta"]["source"] == "bixi"
