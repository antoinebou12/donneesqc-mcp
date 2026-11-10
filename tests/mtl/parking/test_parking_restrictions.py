"""Tests signalisation stationnement (interdictions)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import parking_signalisation_api

_HOTEL_LAT = 45.5088
_HOTEL_LON = -73.5541

_FIXTURE_ROWS = [
    {
        "DESCRIPTION_RPA": r"\A EN TOUT TEMPS",
        "CODE_RPA": "AD-TT",
        "DESCRIPTION_CAT": "STATIONNEMENT",
        "TOPONYME_PAN": "Notre-Dame",
        "NOM_ARROND": "Ville-Marie",
        "Latitude": "45.5089",
        "Longitude": "-73.5542",
    },
    {
        "DESCRIPTION_RPA": "STATIONNEMENT TARIFÉ",
        "CODE_RPA": "PP-AQ",
        "DESCRIPTION_CAT": "STAT-$",
        "TOPONYME_PAN": "Notre-Dame",
        "NOM_ARROND": "Ville-Marie",
        "Latitude": "45.50885",
        "Longitude": "-73.55415",
    },
    {
        "DESCRIPTION_RPA": r"\P EN TOUT TEMPS",
        "CODE_RPA": "SD-TT",
        "DESCRIPTION_CAT": "STATIONNEMENT",
        "TOPONYME_PAN": "Far",
        "NOM_ARROND": "Verdun",
        "Latitude": "45.45",
        "Longitude": "-73.57",
    },
    {
        "DESCRIPTION_RPA": "REMORQUAGE À VOS FRAIS",
        "CODE_RPA": "SLR-ST-02",
        "DESCRIPTION_CAT": "STATIONNEMENT",
        "TOPONYME_PAN": "Place",
        "NOM_ARROND": "Ville-Marie",
        "Latitude": "45.5090",
        "Longitude": "-73.5540",
    },
]


def test_is_restriction_sign():
    assert parking_signalisation_api.is_restriction_sign(r"\A EN TOUT TEMPS", "AD-TT")
    assert parking_signalisation_api.is_restriction_sign(r"\P EN TOUT TEMPS", "SD-TT")
    assert parking_signalisation_api.is_restriction_sign("REMORQUAGE À VOS FRAIS", "X")
    assert not parking_signalisation_api.is_restriction_sign("STATIONNEMENT TARIFÉ", "PP-AQ")
    assert not parking_signalisation_api.is_restriction_sign("P 02h 09h-21h", "PD-JD")


@pytest.mark.asyncio
async def test_list_restrictions_nearby_filters():
    with (
        patch(
            "helpers.mtl.parking_signalisation_api.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": _HOTEL_LAT,
                "longitude": _HOTEL_LON,
                "resolved_address": "Hôtel de Ville",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.mtl.parking_signalisation_api.ckan_api.datastore_search_sql",
            new_callable=AsyncMock,
            return_value={"records": _FIXTURE_ROWS},
        ),
    ):
        data = await parking_signalisation_api.list_restrictions_nearby(
            address="Hôtel de Ville",
            radius_m=300,
            limit=10,
        )

    assert data["total"] >= 2
    descs = [r["description"] for r in data["restrictions"]]
    assert any("\\A" in (d or "") or "EN TOUT TEMPS" in (d or "") for d in descs)
    assert all("TARIF" not in (d or "").upper() for d in descs)
    assert data["restrictions"][0]["distance_m"] <= data["restrictions"][-1]["distance_m"]
    assert "google_maps_url" in data["restrictions"][0]


@pytest.mark.asyncio
async def test_tool_parking_restrictions():
    payload = {
        "query": {"latitude": _HOTEL_LAT, "longitude": _HOTEL_LON},
        "total": 1,
        "restrictions": [
            {
                "description": r"\A EN TOUT TEMPS",
                "code_rpa": "AD-TT",
                "distance_m": 12.0,
                "google_maps_url": "https://maps.google.com/?q=45.5,-73.5",
            }
        ],
    }
    with patch(
        "helpers.mtl.parking_signalisation_api.list_restrictions_nearby",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        from tools.mtl.parking.find_restrictions_nearby import find_parking_restrictions_nearby

        result = json.loads(await find_parking_restrictions_nearby(latitude=_HOTEL_LAT, longitude=_HOTEL_LON))
    assert "error" not in result
    assert result["_meta"]["source"] == "parking_signalisation"
    assert result["total"] == 1
