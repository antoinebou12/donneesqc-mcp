"""Tests QUALO nearby."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import qualo_api

_RECORDS = [
    {
        "point_echantillonnage": "FSL-205",
        "nom": "Plage de l'Horloge",
        "plan_eau": "Fleuve Saint-Laurent",
        "date_heure": "2026-07-07T12:05:07",
        "temperature": "24.0",
        "pH": "8.1",
        "coliformes_fecaux": "8",
        "latitude": "45.51279",
        "longitude": "-73.54613",
    },
    {
        "point_echantillonnage": "FSL-205",
        "nom": "Plage de l'Horloge",
        "plan_eau": "Fleuve Saint-Laurent",
        "date_heure": "2026-06-01T12:00:00",
        "temperature": "18.0",
        "pH": "7.9",
        "coliformes_fecaux": "20",
        "latitude": "45.51279",
        "longitude": "-73.54613",
    },
    {
        "point_echantillonnage": "FAR",
        "nom": "Loin",
        "plan_eau": "Autre",
        "date_heure": "2026-07-07T12:00:00",
        "temperature": "20.0",
        "pH": "7.5",
        "coliformes_fecaux": "100",
        "latitude": "45.7",
        "longitude": "-73.9",
    },
]


def test_pick_nearby_latest_one_per_station():
    rows = qualo_api.pick_nearby_latest(
        _RECORDS,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=2000,
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0]["point_echantillonnage"] == "FSL-205"
    assert rows[0]["coliformes_fecaux"] == "8"
    assert rows[0]["date_heure"].startswith("2026-07-07")


@pytest.mark.asyncio
async def test_find_qualo_nearby_tool():
    with (
        patch(
            "helpers.mtl.nearby.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": "275",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.mtl.qualo_api.ckan_api.datastore_search",
            new_callable=AsyncMock,
            return_value={"records": _RECORDS},
        ),
    ):
        from tools.mtl.qualo.find_qualo_nearby import find_qualo_nearby

        result = json.loads(await find_qualo_nearby(address="275 Rue Notre-Dame Est, Montreal", radius_m=2000))
        assert "error" not in result
        assert result["total"] == 1
        assert result["_meta"]["source"] == "qualo"
        assert result["stations"][0]["station_nom"] == "Plage de l'Horloge"
