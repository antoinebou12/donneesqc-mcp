"""Tests mtl_evenements_search - fixtures CKAN, pas de réseau."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import evenements_api

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "ckan"
PKG = json.loads((FIXTURES / "evenements_package_show.json").read_text(encoding="utf-8"))
DS = json.loads((FIXTURES / "evenements_datastore.json").read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_search_evenements_dq_with_calendar():
    with (
        patch("helpers.mtl.evenements_api.ckan_api.package_show", new_callable=AsyncMock) as pkg_show,
        patch("helpers.mtl.evenements_api.ckan_api.datastore_search", new_callable=AsyncMock) as ds_search,
    ):
        pkg_show.return_value = PKG["result"]
        ds_search.return_value = DS["result"]
        data = await evenements_api.search_evenements(query="Festival", date="2026-07-19", limit=10)

    assert data["count"] == 1
    assert data["events"][0]["titre"] == "Festival culturel test"
    assert data["events"][0]["google_calendar_url"]
    assert data["events"][0].get("google_maps_url")
    assert "Festival culturel test" in data["calendar_ascii"]
    assert data["portal_used"] == "donnees_quebec"
    assert "donneesquebec" in data["_portal"]["portal_url"]


@pytest.mark.asyncio
async def test_search_evenements_mtl_fallback():
    with (
        patch("helpers.mtl.evenements_api.ckan_api.package_show", new_callable=AsyncMock) as pkg_show,
        patch("helpers.mtl.evenements_api.ckan_api.datastore_search", new_callable=AsyncMock) as ds_search,
    ):
        pkg_show.side_effect = [RuntimeError("DQ down"), PKG["result"]]
        ds_search.return_value = DS["result"]
        data = await evenements_api.search_evenements(limit=10)

    assert data["portal_used"] == "montreal"
    assert data["warning"]
    assert data["count"] == 2


@pytest.mark.asyncio
async def test_evenements_tool_meta():
    from tools.mtl.evenements import search_evenements as tool_mod

    fake = {
        "query": "",
        "date": "",
        "count": 1,
        "events": [
            {
                "titre": "X",
                "date_debut": "2026-07-19T10:00:00",
                "date_fin": "2026-07-19T18:00:00",
                "google_calendar_url": "https://calendar.google.com/calendar/render?action=TEMPLATE",
            }
        ],
        "calendar_ascii": "=== Dim 19 juil. 2026 ===\n10h00  Événement · X",
        "warning": None,
        "dataset": "vmtl-evenements-publics",
        "resource_id": "6decf611-6f11-4f34-bb36-324d804c9bad",
        "portal_used": "donnees_quebec",
        "alternate_portal_note": "note",
        "_portal": {
            "source": "donnees_quebec",
            "portal_url": "https://www.donneesquebec.ca/dataset/vmtl-evenements-publics",
            "license": "CC BY 4.0",
        },
    }
    with patch("helpers.mtl.evenements_api.search_evenements", new_callable=AsyncMock, return_value=fake):
        raw = await tool_mod.search_evenements(query="", limit=5)
    body = json.loads(raw)
    assert body["_meta"]["source"] == "donnees_quebec"
    assert "donneesquebec" in body["_meta"]["portal_url"]
    assert body["events"][0]["google_calendar_url"]
