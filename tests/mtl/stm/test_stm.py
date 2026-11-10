"""Tests STM GTFS-RT / arrêts / alertes."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import stm_api, stm_gtfs

_FIX = Path(__file__).resolve().parents[2] / "fixtures" / "mtl"
_VEH_BIN = (_FIX / "stm_vehicle_positions.bin").read_bytes()
_TRIP_BIN = (_FIX / "stm_trip_updates.bin").read_bytes()
_ALERTS = json.loads((_FIX / "stm_alerts.json").read_text(encoding="utf-8"))
_STOPS_SAMPLE = _FIX / "stm_stops_sample.json"


@pytest.fixture(autouse=True)
def _reload_stops(tmp_path, monkeypatch):
    """Point load_stops at the tiny fixture for unit tests."""
    dest = tmp_path / "stm_stops.json"
    dest.write_text(_STOPS_SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(stm_gtfs, "_DATA_PATH", dest)
    stm_gtfs.clear_stops_cache()
    yield
    stm_gtfs.clear_stops_cache()


def test_filter_stops_nearby_hotel_ville():
    stops = stm_gtfs.load_stops()
    rows = stm_gtfs.filter_stops_nearby(
        stops,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=400,
        limit=10,
    )
    assert len(rows) >= 1
    assert rows[0]["stop_id"] == "51543"
    assert rows[0]["distance_m"] == 0.0
    assert all(r["distance_m"] <= 400 for r in rows)


def test_load_compressed_stop_index(tmp_path, monkeypatch):
    compressed = tmp_path / "stops.json.gz"
    compressed.write_bytes(gzip.compress(_STOPS_SAMPLE.read_bytes(), mtime=0))
    monkeypatch.setattr(stm_gtfs, "_DATA_PATH", compressed)
    stm_gtfs.clear_stops_cache()
    stops = stm_gtfs.load_stops()
    assert stops
    assert stops[0]["stop_id"]
    assert isinstance(stops[0]["latitude"], float)


def test_parse_vehicle_positions_route_and_radius():
    feed = stm_api.parse_feed_message(_VEH_BIN)
    all_v = stm_api.parse_vehicle_positions(feed, limit=50)
    assert len(all_v) == 2
    route80 = stm_api.parse_vehicle_positions(feed, route="80", limit=50)
    assert len(route80) == 1
    assert route80[0]["vehicle_id"] == "29088"
    nearby = stm_api.parse_vehicle_positions(
        feed,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=500,
        limit=50,
    )
    assert len(nearby) == 1
    assert nearby[0]["route_id"] == "80"


def test_parse_arrivals_for_stop():
    feed = stm_api.parse_feed_message(_TRIP_BIN)
    rows = stm_api.parse_arrivals_for_stop(feed, "51543", limit=10, now_epoch=0)
    assert len(rows) == 1
    assert rows[0]["route_id"] == "80"
    assert rows[0]["delay_seconds"] == 60
    assert rows[0]["arrival_local"]


def test_parse_service_alerts_filter():
    all_alerts = stm_api.parse_service_alerts(_ALERTS, alert_type="all")
    assert len(all_alerts) == 2
    bus = stm_api.parse_service_alerts(_ALERTS, alert_type="bus")
    assert len(bus) == 1
    assert bus[0]["short_name"] == "80"
    metro = stm_api.parse_service_alerts(_ALERTS, alert_type="metro")
    assert len(metro) == 1


def test_require_api_key_missing(monkeypatch):
    monkeypatch.setattr(stm_api, "STM_API_KEY", "")
    with pytest.raises(ValueError, match="STM_API_KEY"):
        stm_api.require_api_key()


@pytest.mark.asyncio
async def test_find_stm_stops_nearby_tool():
    with patch(
        "helpers.mtl.nearby.resolve_user_point",
        new_callable=AsyncMock,
        return_value={
            "latitude": 45.5088,
            "longitude": -73.5541,
            "resolved_address": "Hôtel de Ville de Montréal",
            "location_source": "agent",
        },
    ):
        from tools.mtl.stm.find_stops_nearby import find_stm_stops_nearby

        result = json.loads(await find_stm_stops_nearby(latitude=45.5088, longitude=-73.5541, radius_m=400))
        assert "error" not in result
        assert result["total"] >= 1
        assert result["_meta"]["source"] == "stm"
        assert result["stops"][0]["google_maps_url"]


@pytest.mark.asyncio
async def test_next_arrivals_missing_key(monkeypatch):
    monkeypatch.setattr(stm_api, "STM_API_KEY", "")
    from tools.mtl.stm.get_next_arrivals import get_stm_next_arrivals

    result = json.loads(await get_stm_next_arrivals(stop_id="51543"))
    assert "error" in result
    assert "STM_API_KEY" in result["error"]


@pytest.mark.asyncio
async def test_next_arrivals_tool(monkeypatch):
    monkeypatch.setattr(stm_api, "STM_API_KEY", "test-key")
    fixture_time = stm_api.parse_feed_message(_TRIP_BIN).header.timestamp
    monkeypatch.setattr(stm_api.time, "time", lambda: fixture_time)
    with patch(
        "helpers.mtl.stm_api.fetch_bytes",
        new_callable=AsyncMock,
        return_value=_TRIP_BIN,
    ):
        from tools.mtl.stm.get_next_arrivals import get_stm_next_arrivals

        result = json.loads(await get_stm_next_arrivals(stop_id="51543", limit=5))
        assert "error" not in result
        assert result["total"] == 1
        assert result["arrivals"][0]["route_id"] == "80"
        assert result["_meta"]["source"] == "stm"


@pytest.mark.asyncio
async def test_bus_positions_tool(monkeypatch):
    monkeypatch.setattr(stm_api, "STM_API_KEY", "test-key")
    with patch(
        "helpers.mtl.stm_api.fetch_bytes",
        new_callable=AsyncMock,
        return_value=_VEH_BIN,
    ):
        from tools.mtl.stm.get_bus_positions import get_stm_bus_positions

        result = json.loads(await get_stm_bus_positions(route="80"))
        assert "error" not in result
        assert result["total"] == 1
        assert result["vehicles"][0]["google_maps_url"]


@pytest.mark.asyncio
async def test_service_alerts_tool(monkeypatch):
    monkeypatch.setattr(stm_api, "STM_API_KEY", "test-key")
    with patch(
        "helpers.mtl.stm_api.fetch_json",
        new_callable=AsyncMock,
        return_value=_ALERTS,
    ):
        from tools.mtl.stm.get_service_alerts import get_stm_service_alerts

        result = json.loads(await get_stm_service_alerts(type="bus"))
        assert "error" not in result
        assert result["total"] == 1
        assert result["_meta"]["source"] == "stm"
