"""Tests REM GTFS-RT / HTML status / news / arrets."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from google.transit import gtfs_realtime_pb2

from helpers.mtl import rem_api, rem_gtfs, rem_html

_FIX = Path(__file__).resolve().parents[2] / "fixtures" / "rem"
_ALERTS_PB = (_FIX / "alerts.pb").read_bytes()
_STATUS_HTML = (_FIX / "network_status_fr.html").read_text(encoding="utf-8")
_NEWS_HTML = (_FIX / "news_fr.html").read_text(encoding="utf-8")
_EMPTY_RSS = (_FIX / "empty_rss.xml").read_text(encoding="utf-8")
_STOPS_SAMPLE = _FIX / "rem_stops_sample.json"


@pytest.fixture(autouse=True)
def _reload_stops(tmp_path, monkeypatch):
    dest = tmp_path / "rem_stops.json"
    dest.write_text(_STOPS_SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(rem_gtfs, "_DATA_PATH", dest)
    rem_gtfs.clear_stops_cache()
    yield
    rem_gtfs.clear_stops_cache()


def test_parse_gtfs_rt_alerts_french():
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(_ALERTS_PB)
    alerts = rem_api.parse_gtfs_rt_alerts(feed, lang="fr")
    assert len(alerts) >= 1
    assert alerts[0]["header"]
    assert alerts[0]["language"] in {"fr", "en", "und"}
    # Prefer French when available
    fr = rem_api.parse_gtfs_rt_alerts(feed, lang="fr")
    en = rem_api.parse_gtfs_rt_alerts(feed, lang="en")
    assert fr[0]["header"] != en[0]["header"] or "REM" in (fr[0]["header"] or "")


def test_parse_network_status_html_interruptions():
    parsed = rem_html.parse_network_status_html(_STATUS_HTML)
    assert parsed["interruption_count"] >= 1
    assert len(parsed["interruptions"]) >= 1
    first = parsed["interruptions"][0]
    assert first.get("stations") or first.get("date") or first.get("details")
    assert "warnings" in parsed


def test_parse_network_status_html_empty():
    parsed = rem_html.parse_network_status_html("")
    assert parsed["interruptions"] == []
    assert parsed["warnings"]


def test_parse_news_html():
    items = rem_html.parse_news_html(_NEWS_HTML, limit=5)
    assert len(items) >= 1
    assert items[0]["title"]
    assert items[0]["url"].startswith("https://")
    assert "actualites" in items[0]["url"] or "news" in items[0]["url"]


def test_filter_stops_nearby_gare_centrale():
    stops = rem_gtfs.load_stops()
    # Approximate Gare Centrale
    rows = rem_gtfs.filter_stops_nearby(
        stops,
        latitude=45.4992,
        longitude=-73.5664,
        radius_m=1500,
        limit=10,
    )
    assert len(rows) >= 1
    assert all(r["distance_m"] <= 1500 for r in rows)
    assert rows[0]["distance_m"] <= rows[-1]["distance_m"]


@pytest.mark.asyncio
async def test_list_service_alerts_mocked():
    with patch(
        "helpers.mtl.rem_api.fetch_bytes",
        new_callable=AsyncMock,
        return_value=_ALERTS_PB,
    ):
        data = await rem_api.list_service_alerts(lang="fr")
        assert data["total"] >= 1
        assert data["alerts_url"]
        assert data["alerts"][0]["header"]


@pytest.mark.asyncio
async def test_list_news_falls_back_to_html():
    with (
        patch(
            "helpers.mtl.rem_api.fetch_text",
            new_callable=AsyncMock,
            return_value=_EMPTY_RSS,
        ),
        patch(
            "helpers.mtl.rem_html.fetch_text",
            new_callable=AsyncMock,
            return_value=_NEWS_HTML,
        ),
    ):
        data = await rem_html.list_news(lang="fr", limit=5)
        assert data["fetch_method"] == "html"
        assert data["total"] >= 1
        assert data["items"][0]["url"]


@pytest.mark.asyncio
async def test_get_network_status_mocked():
    with patch(
        "helpers.mtl.rem_html.fetch_text",
        new_callable=AsyncMock,
        return_value=_STATUS_HTML,
    ):
        data = await rem_html.get_network_status(lang="fr")
        assert data["source_url"].endswith("etat-du-service")
        assert data["interruption_count"] >= 1


@pytest.mark.asyncio
async def test_find_rem_stops_nearby_tool():
    with patch(
        "helpers.mtl.nearby.resolve_user_point",
        new_callable=AsyncMock,
        return_value={
            "latitude": 45.4992,
            "longitude": -73.5664,
            "resolved_address": "Gare Centrale",
            "location_source": "agent",
        },
    ):
        from tools.mtl.rem.find_stops_nearby import find_rem_stops_nearby

        result = json.loads(
            await find_rem_stops_nearby(
                latitude=45.4992,
                longitude=-73.5664,
                radius_m=1500,
            )
        )
        assert "error" not in result
        assert result["total"] >= 1
        assert result["_meta"]["source"] == "rem"
        assert result["stops"][0]["google_maps_url"]


@pytest.mark.asyncio
async def test_rem_service_alerts_tool():
    with patch(
        "helpers.mtl.rem_api.fetch_bytes",
        new_callable=AsyncMock,
        return_value=_ALERTS_PB,
    ):
        from tools.mtl.rem.get_service_alerts import get_rem_service_alerts

        result = json.loads(await get_rem_service_alerts(lang="fr"))
        assert "error" not in result
        assert result["_meta"]["source"] == "rem"
        assert result["total"] >= 1


@pytest.mark.asyncio
async def test_rem_news_tool_html_fallback():
    with (
        patch(
            "helpers.mtl.rem_api.fetch_text",
            new_callable=AsyncMock,
            return_value=_EMPTY_RSS,
        ),
        patch(
            "helpers.mtl.rem_html.fetch_text",
            new_callable=AsyncMock,
            return_value=_NEWS_HTML,
        ),
    ):
        from tools.mtl.rem.list_news import list_rem_news

        result = json.loads(await list_rem_news(lang="fr", limit=3))
        assert "error" not in result
        assert result["fetch_method"] == "html"
        assert result["total"] >= 1


@pytest.mark.asyncio
async def test_rem_network_status_tool():
    with patch(
        "helpers.mtl.rem_html.fetch_text",
        new_callable=AsyncMock,
        return_value=_STATUS_HTML,
    ):
        from tools.mtl.rem.get_network_status import get_rem_network_status

        result = json.loads(await get_rem_network_status(lang="fr"))
        assert "error" not in result
        assert result["_meta"]["source"] == "rem"
        assert result["interruption_count"] >= 1
