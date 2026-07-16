"""Tests unitaires pour les outils Collecte MTL (mockés)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

_ADDRESS = "1 Place Ville-Marie, Montréal"

_COLLECTIONS_FIXTURE = {
    "query": {
        "address": _ADDRESS,
        "matched": "1 Place Ville-Marie, Montréal, Quebec",
        "lat": 45.50882581,
        "lng": -73.55410909,
    },
    "collections": [
        {
            "stream": "garbage",
            "labelFr": "Ordures ménagères",
            "labelEn": "Household garbage",
            "available": True,
            "sector": {"id": "VM-2", "secteur": "VM-2", "municipalite": "Montreal"},
            "schedule": {
                "days": [{"fr": "lundi", "en": "Monday", "iso": 1}],
                "startsNightBefore": True,
            },
        },
        {
            "stream": "recycling",
            "labelFr": "Matières recyclables",
            "labelEn": "Recyclables",
            "available": True,
            "sector": {"id": "VM-2"},
            "schedule": {"days": [{"fr": "mardi", "en": "Tuesday", "iso": 2}]},
        },
        {
            "stream": "food",
            "labelFr": "Résidus alimentaires",
            "labelEn": "Food residues",
            "available": True,
            "sector": {"id": "VM-2a_RA"},
            "schedule": {"days": [{"fr": "jeudi", "en": "Thursday", "iso": 4}]},
        },
    ],
    "disclaimer": "Best-effort, refreshed ~monthly.",
    "attribution": "Secteurs Info-collectes, CC-BY 4.0.",
}

_ECOCENTRES_FIXTURE = {
    "query": {"lat": 45.5088, "lng": -73.5541},
    "ecocentres": [
        {
            "id": "la-petite-patrie",
            "name": "Écocentre La Petite-Patrie",
            "borough": "Rosemont-La Petite-Patrie",
            "lat": 45.533996,
            "lng": -73.59187,
        }
    ],
}

_BOROUGH_FIXTURE = {
    "query": {
        "address": _ADDRESS,
        "matched": "1 Place Ville-Marie, Montréal, Quebec",
        "lat": 45.50882581,
        "lng": -73.55410909,
    },
    "borough": {"slug": "ville-marie", "nameFr": "Ville-Marie", "nameEn": "Ville-Marie"},
    "glance": {"slug": "ville-marie", "year": 2025},
}


# ── find_montreal_waste_collection ───────────────────────────────────


@pytest.mark.asyncio
async def test_find_montreal_waste_collection():
    with patch(
        "tools.mtl.collecte.find_montreal_waste_collection.collectemtl_api.get_collections",
        new_callable=AsyncMock,
        return_value=_COLLECTIONS_FIXTURE,
    ):
        from tools.mtl.collecte.find_montreal_waste_collection import find_montreal_waste_collection

        result = json.loads(await find_montreal_waste_collection(_ADDRESS))
        streams = [c["stream"] for c in result["collections"]]
        assert "garbage" in streams
        assert "recycling" in streams
        assert "food" in streams
        assert result["_meta"]["source"] == "collectemtl"
        assert "collectemtl.ca" in result["_meta"]["portal_url"]
        assert result["_meta"]["dataset_id"] == "info-collectes"


@pytest.mark.asyncio
async def test_find_montreal_waste_collection_empty_address():
    from tools.mtl.collecte.find_montreal_waste_collection import find_montreal_waste_collection

    result = json.loads(await find_montreal_waste_collection(""))
    assert "error" in result

    result_ws = json.loads(await find_montreal_waste_collection("   "))
    assert "error" in result_ws


@pytest.mark.asyncio
async def test_find_montreal_waste_collection_error():
    with patch(
        "tools.mtl.collecte.find_montreal_waste_collection.collectemtl_api.get_collections",
        new_callable=AsyncMock,
        side_effect=RuntimeError("timeout"),
    ):
        from tools.mtl.collecte.find_montreal_waste_collection import find_montreal_waste_collection

        result = json.loads(await find_montreal_waste_collection(_ADDRESS))
        assert "error" in result


# ── find_montreal_ecocentres ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_montreal_ecocentres():
    with patch(
        "tools.mtl.collecte.find_montreal_ecocentres.collectemtl_api.get_ecocentres",
        new_callable=AsyncMock,
        return_value=_ECOCENTRES_FIXTURE,
    ) as mock_get:
        from tools.mtl.collecte.find_montreal_ecocentres import find_montreal_ecocentres

        result = json.loads(await find_montreal_ecocentres(45.5088, -73.5541, limit=3))
        assert result["ecocentres"][0]["id"] == "la-petite-patrie"
        assert result["_meta"]["source"] == "collectemtl"
        mock_get.assert_awaited_once_with(45.5088, -73.5541, 3)


@pytest.mark.asyncio
async def test_find_montreal_ecocentres_limit_clamped():
    with patch(
        "tools.mtl.collecte.find_montreal_ecocentres.collectemtl_api.get_ecocentres",
        new_callable=AsyncMock,
        return_value=_ECOCENTRES_FIXTURE,
    ) as mock_get:
        from tools.mtl.collecte.find_montreal_ecocentres import find_montreal_ecocentres

        await find_montreal_ecocentres(45.5, -73.5, limit=0)
        mock_get.assert_awaited_with(45.5, -73.5, 1)

        await find_montreal_ecocentres(45.5, -73.5, limit=99)
        mock_get.assert_awaited_with(45.5, -73.5, 8)


@pytest.mark.asyncio
async def test_find_montreal_ecocentres_error():
    with patch(
        "tools.mtl.collecte.find_montreal_ecocentres.collectemtl_api.get_ecocentres",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connexion refusee"),
    ):
        from tools.mtl.collecte.find_montreal_ecocentres import find_montreal_ecocentres

        result = json.loads(await find_montreal_ecocentres(45.5, -73.5))
        assert "error" in result


# ── get_montreal_borough_waste_stats ─────────────────────────────────


@pytest.mark.asyncio
async def test_get_montreal_borough_waste_stats():
    with patch(
        "tools.mtl.collecte.get_montreal_borough_waste_stats.collectemtl_api.get_borough_stats",
        new_callable=AsyncMock,
        return_value=_BOROUGH_FIXTURE,
    ):
        from tools.mtl.collecte.get_montreal_borough_waste_stats import get_montreal_borough_waste_stats

        result = json.loads(await get_montreal_borough_waste_stats(_ADDRESS))
        assert result["borough"]["slug"] == "ville-marie"
        assert result["_meta"]["source"] == "collectemtl"


@pytest.mark.asyncio
async def test_get_montreal_borough_waste_stats_empty_address():
    from tools.mtl.collecte.get_montreal_borough_waste_stats import get_montreal_borough_waste_stats

    result = json.loads(await get_montreal_borough_waste_stats(""))
    assert "error" in result


@pytest.mark.asyncio
async def test_get_montreal_borough_waste_stats_error():
    with patch(
        "tools.mtl.collecte.get_montreal_borough_waste_stats.collectemtl_api.get_borough_stats",
        new_callable=AsyncMock,
        side_effect=RuntimeError("timeout"),
    ):
        from tools.mtl.collecte.get_montreal_borough_waste_stats import get_montreal_borough_waste_stats

        result = json.loads(await get_montreal_borough_waste_stats(_ADDRESS))
        assert "error" in result


# ── helper URL / params ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collectemtl_api_get_collections_url():
    with patch(
        "helpers.mtl.collectemtl_api.fetch_json",
        new_callable=AsyncMock,
        return_value={"collections": []},
    ) as mock_fetch:
        from helpers.mtl import collectemtl_api

        await collectemtl_api.get_collections(_ADDRESS)
        mock_fetch.assert_awaited_once()
        await_args = mock_fetch.await_args
        assert await_args is not None
        args, kwargs = await_args
        assert args[0].endswith("/api/collections")
        assert kwargs["params"]["address"] == _ADDRESS


@pytest.mark.asyncio
async def test_collectemtl_api_get_ecocentres_url():
    with patch(
        "helpers.mtl.collectemtl_api.fetch_json",
        new_callable=AsyncMock,
        return_value={
            "ecocentres": [
                {
                    "id": "la-petite-patrie",
                    "name": "Écocentre La Petite-Patrie",
                    "lat": 45.533996,
                    "lng": -73.59187,
                }
            ]
        },
    ) as mock_fetch:
        from helpers.mtl import collectemtl_api

        data = await collectemtl_api.get_ecocentres(45.51, -73.55, limit=2)
        mock_fetch.assert_awaited_once()
        await_args = mock_fetch.await_args
        assert await_args is not None
        args, kwargs = await_args
        assert args[0].endswith("/api/ecocentres")
        assert kwargs["params"] == {"lat": 45.51, "lng": -73.55, "limit": 2}
        assert data["ecocentres"][0]["google_maps_url"]
        assert data["nearest_google_maps_directions_url"]


@pytest.mark.asyncio
async def test_collectemtl_api_get_borough_stats_url():
    with patch(
        "helpers.mtl.collectemtl_api.fetch_json",
        new_callable=AsyncMock,
        return_value={"borough": {}},
    ) as mock_fetch:
        from helpers.mtl import collectemtl_api

        await collectemtl_api.get_borough_stats(_ADDRESS)
        mock_fetch.assert_awaited_once()
        await_args = mock_fetch.await_args
        assert await_args is not None
        args, kwargs = await_args
        assert args[0].endswith("/api/borough")
        assert kwargs["params"]["address"] == _ADDRESS


@pytest.mark.asyncio
async def test_collectemtl_api_rejects_non_dict():
    with patch(
        "helpers.mtl.collectemtl_api.fetch_json",
        new_callable=AsyncMock,
        return_value=["not", "a", "dict"],
    ):
        from helpers.mtl import collectemtl_api

        with pytest.raises(TypeError, match="/api/collections"):
            await collectemtl_api.get_collections(_ADDRESS)
