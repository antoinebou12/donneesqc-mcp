"""Tests NosOrigines (fixtures / mocks, noms publics uniquement)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from helpers.qc.nosorigines import nosorigines_api

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
FRANCOIS_HTML = (FIXTURES / "nosorigines_francois_boucher.html").read_text(encoding="utf-8")
PRIVE_HTML = (FIXTURES / "nosorigines_prive.html").read_text(encoding="utf-8")


def test_parse_francois_boucher_person_page():
    data = nosorigines_api.parse_person_page(FRANCOIS_HTML, pid="781")
    assert data["pid"] == "781"
    assert data["first_name"] == "Francois"
    assert data["last_name"] == "Boucher"
    assert data["name"] == "Francois Boucher"
    assert data["is_private"] is False
    assert data["occupation"] == "Habitant"
    assert data["birth"] == "22 novembre 1617"
    assert "Mortagne" in data["birth_place"]
    assert data["birth_country"] == "France"
    assert data["father"]["pid"] == "774"
    assert data["father"]["name"] == "Marin Boucher"
    assert data["mother"]["pid"] == "780"
    assert data["mother"]["name"] == "Julienne Baril"
    assert data["spouse_father"]["pid"] == "24674"
    assert data["spouse_mother"]["name"] == "Madeleine Charlot"
    assert data["spouse"]["pid"] == "782"
    assert data["spouse"]["name"] == "Florence Gareman"
    assert data["marriage"]["date"] == "03 septembre 1641"
    assert "Québec" in data["marriage"]["place"]
    assert len(data["children_married"]) >= 2
    assert data["children_married"][0]["pid"] == "3966"
    assert data["children_unmarried"][0]["pid"] == "317322"
    assert "Pierre de Nesle" in data["notes"]


def test_parse_prive_person_page_no_meta_leak():
    data = nosorigines_api.parse_person_page(PRIVE_HTML, pid="999")
    assert data["is_private"] is True
    assert data["name"] == "Privé"
    assert data["birth"] == "****"
    assert data["father"]["is_private"] is True
    assert data["father"]["name"] == "Privé"


def test_validate_pid_rejects_non_digits():
    with pytest.raises(ValueError, match="pid"):
        nosorigines_api.validate_pid("abc")


@pytest.mark.asyncio
async def test_search_nosorigines_tool():
    mock_data = {
        "query": {"last_name": "Champlain", "first_name": "Samuel"},
        "total_returned": 1,
        "results": [
            {
                "name": "Champlain, Samuel",
                "url": "https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=1",
            }
        ],
        "source": "https://www.nosorigines.qc.ca",
    }
    with patch(
        "helpers.qc.nosorigines.nosorigines_api.search_nosorigines",
        new_callable=AsyncMock,
        return_value=mock_data,
    ):
        from tools.qc.nosorigines.search_nosorigines import search_nosorigines

        result = json.loads(await search_nosorigines(last_name="Champlain", first_name="Samuel"))
        assert result["total_returned"] == 1
        assert "Champlain" in result["results"][0]["name"]


@pytest.mark.asyncio
async def test_get_person_tool():
    parsed = nosorigines_api.parse_person_page(FRANCOIS_HTML, pid="781")
    with patch(
        "helpers.qc.nosorigines.nosorigines_api.get_person",
        new_callable=AsyncMock,
        return_value=parsed,
    ):
        from tools.qc.nosorigines.get_person import get_person

        result = json.loads(await get_person(pid="781"))
        assert result["name"] == "Francois Boucher"
        assert result["father"]["name"] == "Marin Boucher"
        assert "error" not in result


@pytest.mark.asyncio
async def test_get_person_tool_invalid_pid():
    from tools.qc.nosorigines.get_person import get_person

    result = json.loads(await get_person(pid="not-a-pid"))
    assert "error" in result


@pytest.mark.asyncio
async def test_get_ancestors_tool():
    root = nosorigines_api.parse_person_page(FRANCOIS_HTML, pid="781")
    marin = {
        "pid": "774",
        "name": "Marin Boucher",
        "is_private": False,
        "birth": "1587",
        "death": "25 mars 1671",
        "url": "https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=774",
        "father": None,
        "mother": None,
    }
    tree = {
        "pid": "781",
        "generations": 1,
        "person": root,
        "father": {"person": marin, "father": None, "mother": None},
        "mother": {
            "person": {
                "pid": "780",
                "name": "Julienne Baril",
                "is_private": False,
                "birth": "1591",
                "death": "15 déc 1627",
                "url": "https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid=780",
                "father": None,
                "mother": None,
            },
            "father": None,
            "mother": None,
        },
        "source": "https://www.nosorigines.qc.ca",
    }
    with patch(
        "helpers.qc.nosorigines.nosorigines_api.get_ancestors",
        new_callable=AsyncMock,
        return_value=tree,
    ):
        from tools.qc.nosorigines.get_ancestors import get_ancestors

        result = json.loads(await get_ancestors(pid="781", generations=1))
        assert result["father"]["person"]["name"] == "Marin Boucher"
        assert result["generations"] == 1


@pytest.mark.asyncio
async def test_get_ancestors_dedupes_fetches():
    """Une seule fiche par pid meme si remontee bilaterale."""
    calls: list[str] = []

    async def fake_get_person(pid: str, **_kwargs):
        calls.append(pid)
        if pid == "781":
            return nosorigines_api.parse_person_page(FRANCOIS_HTML, pid="781")
        return {
            "pid": pid,
            "name": f"Person {pid}",
            "is_private": False,
            "birth": "",
            "death": "",
            "url": f"https://www.nosorigines.qc.ca/GenealogieQuebec.aspx?pid={pid}",
            "father": None,
            "mother": None,
        }

    with patch(
        "helpers.qc.nosorigines.nosorigines_api.get_person",
        side_effect=fake_get_person,
    ):
        tree = await nosorigines_api.get_ancestors("781", generations=1)
        assert tree["father"]["person"]["pid"] == "774"
        assert tree["mother"]["person"]["pid"] == "780"
        assert calls.count("781") == 1
        assert calls.count("774") == 1
        assert calls.count("780") == 1
