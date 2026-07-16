"""Tests mtl_events_soon - mocks reseau."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.common.calendar_format import CalendarItem
from helpers.mtl import events_soon


def test_item_in_window_all_day():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("America/Toronto")
    start = datetime(2026, 7, 16, 10, 0, tzinfo=tz)
    end = datetime(2026, 7, 17, 10, 0, tzinfo=tz)
    item = CalendarItem(
        kind="festival",
        start="2026-07-16",
        end=None,
        all_day=True,
        title="Test",
        place=None,
        url=None,
        source="piknic",
    )
    assert events_soon._item_in_window(item, start=start, end=end, tz=tz)


@pytest.mark.asyncio
async def test_build_events_soon_merges_mocked_sources():
    festival_payload = {
        "events": [
            {
                "date": "2026-07-16",
                "title": "Show A",
                "category": "piknic",
                "venue_or_stage": "Parc Jean-Drapeau",
                "artists": [{"name": "DJ", "time": "20H00"}],
            }
        ],
        "warning": None,
    }
    eve_payload = {
        "events": [
            {
                "titre": "Fete locale",
                "date_debut": "2026-07-16",
                "date_fin": "2026-07-16",
                "arrondissement": "Ville-Marie",
                "emplacement": "Vieux-Montreal",
                "adresse_principale": "",
                "url_fiche": "https://example.test/e",
            }
        ],
        "warning": None,
    }

    with (
        patch(
            "helpers.common.context.resolve_now",
            return_value={
                "date": "2026-07-16",
                "datetime_iso": "2026-07-16T12:00:00-04:00",
                "timezone": "America/Toronto",
                "time_source": "agent",
            },
        ),
        patch(
            "helpers.mtl.piknic_api.search_events",
            new=AsyncMock(return_value=festival_payload),
        ),
        patch(
            "helpers.mtl.jazzfest_api.search_events",
            new=AsyncMock(return_value={"events": [], "warning": None}),
        ),
        patch(
            "helpers.mtl.evenements_api.search_evenements",
            new=AsyncMock(return_value=eve_payload),
        ),
    ):
        data = await events_soon.build_events_soon(
            hours=24,
            date="2026-07-16",
            limit=10,
        )

    assert data["count"] >= 1
    assert data["calendar_ascii"]
    titles = {i["title"] for i in data["items"]}
    assert "Show A" in titles or "Fete locale" in titles


@pytest.mark.asyncio
async def test_events_soon_tool():
    from tools.mtl.events.events_soon import events_soon_tool

    with patch(
        "helpers.mtl.events_soon.build_events_soon",
        new=AsyncMock(
            return_value={
                "query": "",
                "hours": 24,
                "window": {"start": "x", "end": "y", "timezone": "America/Toronto"},
                "count": 0,
                "items": [],
                "calendar_ascii": "",
                "sources": [],
                "warning": None,
                "location": None,
                "location_filter": "none",
            }
        ),
    ):
        raw = await events_soon_tool(hours=24)
    data = json.loads(raw)
    assert data["hours"] == 24
    assert data["_meta"]["source"] == "mtl_events_soon"
