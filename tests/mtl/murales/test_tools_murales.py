"""Tests des outils murales (DataStore Montréal)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl.murales_api import normalize_record


def test_normalize_record_https_image_and_coords():
    row = {
        "id": "1",
        "artiste": "Yannick Picard",
        "organisme": "MU",
        "adresse": "4105, 47e rue",
        "annee": "2007",
        "arrondissement": "Villeray-Saint-Michel-Parc-Extension",
        "programme_entente": "Programme graffitis et murales",
        "latitude": "45.58041",
        "longitude": "-73.622218",
        "image": "//murales.s3.montreal.ca/s3fs-public/MU.jpg",
    }
    out = normalize_record(row)
    assert out["id"] == 1
    assert out["latitude"] == pytest.approx(45.58041)
    assert out["image"].startswith("https://")
    assert out["google_maps_url"].startswith("https://www.google.com/maps/search/")


@pytest.mark.asyncio
async def test_list_nearby_helper_maps_urls():
    records = [
        {
            "id": "10",
            "artiste": "A",
            "organisme": "MU",
            "adresse": "near",
            "annee": "2020",
            "arrondissement": "Ville-Marie",
            "programme_entente": "x",
            "latitude": "45.5090",
            "longitude": "-73.5620",
            "image": "",
        },
        {
            "id": "11",
            "artiste": "B",
            "organisme": "MU",
            "adresse": "far",
            "annee": "2021",
            "arrondissement": "Ville-Marie",
            "programme_entente": "x",
            "latitude": "45.5200",
            "longitude": "-73.5700",
            "image": "",
        },
    ]
    with patch(
        "helpers.mtl.murales_api.ckan_api.datastore_search",
        new_callable=AsyncMock,
        return_value={"records": records},
    ):
        from helpers.mtl import murales_api

        result = await murales_api.list_nearby(
            latitude=45.5088,
            longitude=-73.5617,
            radius_m=2000.0,
            limit=10,
        )
    assert result["murals"][0]["google_maps_url"]
    assert result["murals"][0]["google_maps_directions_url"]
    assert "google_maps_directions_url" not in result["murals"][1]
    assert result["nearest_google_maps_directions_url"] == result["murals"][0]["google_maps_directions_url"]


@pytest.mark.asyncio
async def test_search_murales():
    payload = {
        "total": 1,
        "page": 1,
        "page_size": 20,
        "murals": [{"id": 1, "artiste": "Yannick Picard", "annee": "2007"}],
    }
    with patch(
        "tools.mtl.murales.search_murales.murales_api.search_murales",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.murales.search_murales import search_murales

        result = json.loads(await search_murales(arrondissement="Villeray"))
        assert result["total"] == 1
        assert result["_meta"]["source"] == "murales"
        assert "mtlmurales.ca" in result["viewer_url"]
        assert "donnees.montreal.ca" in result["dataset_url"]


@pytest.mark.asyncio
async def test_search_murales_validation_error():
    with patch(
        "tools.mtl.murales.search_murales.murales_api.search_murales",
        new_callable=AsyncMock,
        side_effect=ValueError("annee invalide"),
    ):
        from tools.mtl.murales.search_murales import search_murales

        result = json.loads(await search_murales(annee="abc"))
        assert "error" in result


@pytest.mark.asyncio
async def test_search_murales_http_error():
    with patch(
        "tools.mtl.murales.search_murales.murales_api.search_murales",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        from tools.mtl.murales.search_murales import search_murales

        result = json.loads(await search_murales())
        assert "error" in result


# ── get_murale ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_murale():
    murale = {"id": 307, "artiste": "Ankhone et Nicole Boyce"}
    with patch(
        "tools.mtl.murales.get_murale.murales_api.get_murale",
        new_callable=AsyncMock,
        return_value=murale,
    ):
        from tools.mtl.murales.get_murale import get_murale

        result = json.loads(await get_murale(murale_id="307"))
        assert result["murale"]["id"] == 307
        assert result["_meta"]["dataset_id"] == "murales"


@pytest.mark.asyncio
async def test_get_murale_missing_id():
    from tools.mtl.murales.get_murale import get_murale

    result = json.loads(await get_murale(murale_id=""))
    assert "error" in result


@pytest.mark.asyncio
async def test_get_murale_not_found():
    with patch(
        "tools.mtl.murales.get_murale.murales_api.get_murale",
        new_callable=AsyncMock,
        return_value=None,
    ):
        from tools.mtl.murales.get_murale import get_murale

        result = json.loads(await get_murale(murale_id="99999"))
        assert "error" in result


# ── list_murales_nearby ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_murales_nearby():
    payload = {
        "latitude": 45.5088,
        "longitude": -73.5617,
        "radius_m": 800.0,
        "total": 1,
        "murals": [{"id": 2, "distance_m": 120.5}],
    }
    with patch(
        "tools.mtl.murales.list_murales_nearby.murales_api.list_nearby",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.murales.list_murales_nearby import list_murales_nearby

        result = json.loads(await list_murales_nearby(latitude=45.5088, longitude=-73.5617, radius_m=800))
        assert result["murals"][0]["distance_m"] == 120.5
        assert result["_meta"]["source"] == "murales"


@pytest.mark.asyncio
async def test_list_murales_nearby_validation():
    from tools.mtl.murales.list_murales_nearby import list_murales_nearby

    result = json.loads(await list_murales_nearby(latitude=999, longitude=0))
    assert "error" in result


# ── get_random_murale ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_random_murale():
    payload = {"count": 1, "murals": [{"id": 42, "artiste": "A'Shop"}]}
    with patch(
        "tools.mtl.murales.get_random_murale.murales_api.get_random",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.murales.get_random_murale import get_random_murale

        result = json.loads(await get_random_murale(arrondissement="Ville-Marie"))
        assert result["count"] == 1
        assert result["_meta"]["source"] == "murales"


# ── list_murales_facet ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_murales_facet():
    payload = {
        "facet": "arrondissement",
        "total": 2,
        "values": [
            {"value": "Ville-Marie", "count": 60},
            {"value": "Le Plateau-Mont-Royal", "count": 28},
        ],
    }
    with patch(
        "tools.mtl.murales.list_murales_facet.murales_api.list_facets",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.murales.list_murales_facet import list_murales_facet

        result = json.loads(await list_murales_facet(facet="arrondissement"))
        assert result["values"][0]["count"] == 60
        assert "mtlmurales.ca" in result["viewer_url"]


# ── helper unit tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_murales_api_list_nearby_haversine():
    records = {
        "records": [
            {
                "id": "1",
                "artiste": "Near",
                "organisme": "",
                "adresse": "x",
                "annee": "2020",
                "arrondissement": "Ville-Marie",
                "programme_entente": "",
                "latitude": "45.5088",
                "longitude": "-73.5617",
                "image": "",
            },
            {
                "id": "2",
                "artiste": "Far",
                "organisme": "",
                "adresse": "y",
                "annee": "2020",
                "arrondissement": "Lachine",
                "programme_entente": "",
                "latitude": "45.44",
                "longitude": "-73.68",
                "image": "",
            },
        ]
    }
    with patch(
        "helpers.mtl.murales_api.ckan_api.datastore_search",
        new_callable=AsyncMock,
        return_value=records,
    ):
        from helpers.mtl import murales_api

        out = await murales_api.list_nearby(latitude=45.5088, longitude=-73.5617, radius_m=500, limit=10)
        assert out["total"] == 1
        assert out["murals"][0]["id"] == 1
        assert out["murals"][0]["distance_m"] == 0.0
