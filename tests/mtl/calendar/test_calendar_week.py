"""Tests mtl_calendar_week."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl.calendar_week import monday_of_week, resolve_week_start


def test_monday_of_week():
    assert monday_of_week(date(2026, 7, 19)) == date(2026, 7, 13)
    assert monday_of_week(date(2026, 7, 13)) == date(2026, 7, 13)


def test_resolve_week_start_explicit():
    assert resolve_week_start("2026-07-16") == date(2026, 7, 13)


@pytest.mark.asyncio
async def test_build_calendar_week_merges_and_skips_avis_without_geo():
    from helpers.mtl import calendar_week

    festival_payload = {
        "query": "",
        "date": "",
        "category": "piknic",
        "count": 1,
        "events": [
            {
                "date": "2026-07-19",
                "category": "piknic",
                "venue_or_stage": "SCÈNE FIZZ",
                "artists": [{"name": "Mandragora", "time": "19H30"}],
                "title": None,
                "url": "https://piknicelectronik.com/fr/programmation",
                "ticket_url": None,
            }
        ],
        "warning": None,
    }
    empty_fest = {**festival_payload, "events": [], "count": 0, "category": "off"}
    eve_payload = {
        "query": "",
        "date": "",
        "count": 1,
        "events": [
            {
                "titre": "Festival culturel",
                "type_evenement": "Festival",
                "date_debut": "2026-07-19T10:00:00",
                "date_fin": "2026-07-19T18:00:00",
                "emplacement": "Parc",
                "url_fiche": "https://montreal.ca/x",
            }
        ],
        "calendar_ascii": "",
        "warning": None,
        "portal_used": "donnees_quebec",
        "_portal": {
            "source": "donnees_quebec",
            "portal_url": "https://www.donneesquebec.ca/dataset/vmtl-evenements-publics",
        },
    }

    with (
        patch("helpers.mtl.piknic_api.search_events", new_callable=AsyncMock) as pik,
        patch("helpers.mtl.jazzfest_api.search_events", new_callable=AsyncMock) as jazz,
        patch("helpers.mtl.evenements_api.search_evenements", new_callable=AsyncMock) as eve,
    ):

        async def _pik(*, category, **_kw):
            return festival_payload if category == "piknic" else {**empty_fest, "category": category}

        pik.side_effect = _pik
        jazz.return_value = {**empty_fest, "category": "free"}
        eve.return_value = eve_payload

        data = await calendar_week.build_calendar_week(
            week_start="2026-07-13",
            include_avis=True,
            include_festivals=True,
            include_evenements=True,
        )

    assert data["week_start"] == "2026-07-13"
    assert data["count"] >= 2
    assert any(i["title"] == "Mandragora" for i in data["items"])
    assert any(i["title"] == "Festival culturel" for i in data["items"])
    assert all(i.get("google_calendar_url") for i in data["items"] if i.get("start"))
    assert "Mandragora" in data["calendar_ascii"]
    assert data["warning"]
    assert "Avis omis" in data["warning"]


@pytest.mark.asyncio
async def test_calendar_week_tool():
    from tools.mtl.calendar import week as week_tool

    fake = {
        "week_start": "2026-07-13",
        "week_end": "2026-07-19",
        "count": 1,
        "items": [
            {
                "kind": "festival",
                "start": "2026-07-19T19:30:00",
                "end": None,
                "all_day": False,
                "title": "Mandragora",
                "place": "SCÈNE FIZZ",
                "url": "https://example.com",
                "source": "piknic",
                "google_calendar_url": "https://calendar.google.com/calendar/render?action=TEMPLATE",
            }
        ],
        "calendar_ascii": "=== Dim 19 juil. 2026 ===\n19h30  Piknic · Mandragora @ SCÈNE FIZZ",
        "warning": None,
        "sources": [],
    }
    with patch(
        "helpers.mtl.calendar_week.build_calendar_week",
        new_callable=AsyncMock,
        return_value=fake,
    ):
        raw = await week_tool.calendar_week_tool(week_start="2026-07-13", include_avis=False)
    body = json.loads(raw)
    assert body["_meta"]["source"] == "mtl_calendar"
    assert body["items"][0]["google_calendar_url"]
    assert body["calendar_ascii"]
