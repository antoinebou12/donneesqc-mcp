"""Tests festivals Montréal (Piknic / Jazz Fest) - fixtures HTML, pas de réseau."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import jazzfest_api, piknic_api

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
PIKNIC_HTML = (FIXTURES / "piknic_programmation.html").read_text(encoding="utf-8")
JAZZ_HTML = (FIXTURES / "jazzfest_program.html").read_text(encoding="utf-8")


def test_piknic_category_isolation():
    off = piknic_api.parse_programmation(PIKNIC_HTML, category="off", year=2026)
    main = piknic_api.parse_programmation(PIKNIC_HTML, category="piknic", year=2026)
    petit = piknic_api.parse_programmation(PIKNIC_HTML, category="petit", year=2026)

    assert off["count"] >= 1
    assert all(e["category"] == "off" for e in off["events"])
    assert main["count"] >= 1
    assert all(e["category"] == "piknic" for e in main["events"])
    assert petit["count"] >= 1
    assert all(e["category"] == "petit" for e in petit["events"])


def test_piknic_query_mandragora():
    data = piknic_api.parse_programmation(
        PIKNIC_HTML,
        category="piknic",
        query="Mandragora",
        year=2026,
    )
    assert data["count"] >= 1
    names = [a["name"] for e in data["events"] for a in e["artists"]]
    assert any("Mandragora" in n for n in names)
    # Must not leak OfF-only cards
    assert all(e["category"] == "piknic" for e in data["events"])


def test_piknic_date_filter_sunday():
    data = piknic_api.parse_programmation(
        PIKNIC_HTML,
        category="piknic",
        date="2026-07-19",
        year=2026,
    )
    assert data["count"] >= 1
    assert all(e["date"] == "2026-07-19" for e in data["events"])


def test_piknic_empty_html_warning():
    data = piknic_api.parse_programmation("<html><body></body></html>", category="piknic")
    assert data["count"] == 0
    assert data["events"] == []
    assert data["warning"]


def test_jazzfest_free_vs_paid_isolation():
    free = jazzfest_api.parse_program(JAZZ_HTML, ticket_kind="free")
    paid = jazzfest_api.parse_program(JAZZ_HTML, ticket_kind="paid")

    assert free["count"] == 2
    assert paid["count"] == 2
    assert all(e["category"] == "free" for e in free["events"])
    assert all(e["category"] == "paid" for e in paid["events"])
    free_titles = {e["title"] for e in free["events"]}
    paid_titles = {e["title"] for e in paid["events"]}
    assert "Patrick Watson" in free_titles
    assert "Isaiah Collier — A Love Supreme" in paid_titles
    assert free_titles.isdisjoint(paid_titles)


def test_jazzfest_js_shell_warning():
    shell = (
        "<!DOCTYPE html><html><head></head><body>"
        '<script src="/_next/static/chunks/x.js"></script>'
        '<template data-dgst="NEXT_REDIRECT;replace;/fr/program;307;"></template>'
        "</body></html>"
    )
    data = jazzfest_api.parse_program(shell, ticket_kind="free")
    assert data["count"] == 0
    assert data["events"] == []
    assert data["warning"]
    assert "JS" in data["warning"] or "client" in data["warning"].lower()


@pytest.mark.asyncio
async def test_piknic_tool_meta_and_http_error():
    from tools.mtl.festivals import search_piknic

    payload = {
        "query": "",
        "date": "",
        "category": "piknic",
        "count": 1,
        "events": [
            {
                "date": "2026-07-19",
                "date_label": "Sun, Jul 19",
                "category": "piknic",
                "venue_or_stage": "SCÈNE FIZZ",
                "artists": [{"name": "Mandragora", "time": "19H30"}],
                "title": None,
                "ticket_url": None,
                "url": piknic_api.PORTAL_URL,
            }
        ],
        "warning": None,
    }
    with patch.object(piknic_api, "search_events", new=AsyncMock(return_value=payload)):
        raw = await search_piknic.search_piknic(query="Mandragora")
    body = json.loads(raw)
    assert body["_meta"]["source"] == "piknic"
    assert "piknicelectronik" in body["_meta"]["portal_url"]
    assert body["count"] == 1
    assert body["events"][0]["google_calendar_url"]
    assert "Mandragora" in body["calendar_ascii"]

    with patch.object(
        piknic_api,
        "search_events",
        new=AsyncMock(side_effect=RuntimeError("timeout")),
    ):
        err = await search_piknic.search_piknic()
    assert "error" in json.loads(err)


@pytest.mark.asyncio
async def test_jazzfest_tool_meta_and_http_error():
    from tools.mtl.festivals import search_jazzfest_free

    payload = {
        "query": "",
        "date": "",
        "category": "free",
        "count": 0,
        "events": [],
        "warning": "JS shell",
    }
    with patch.object(jazzfest_api, "search_events", new=AsyncMock(return_value=payload)):
        raw = await search_jazzfest_free.search_jazzfest_free()
    body = json.loads(raw)
    assert body["_meta"]["source"] == "jazzfest"
    assert "montrealjazzfest" in body["_meta"]["portal_url"]

    with patch.object(
        jazzfest_api,
        "search_events",
        new=AsyncMock(side_effect=RuntimeError("down")),
    ):
        err = await search_jazzfest_free.search_jazzfest_free()
    assert "error" in json.loads(err)


@pytest.mark.asyncio
async def test_invalid_date_value_error():
    with pytest.raises(ValueError, match="Date invalide"):
        await piknic_api.search_events(category="piknic", date="19/07/2026")
