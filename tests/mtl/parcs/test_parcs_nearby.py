"""Tests parcs nearby (fixtures locales)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.mtl import parcs_api

_FIXTURE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "Type": "Parc",
                "Lien": None,
                "Nom": "François-Dollier-de Casson",
                "TYPO1": "Parc d'arrondissement",
                "TYPO2": "Parc de voisinage",
                "GESTION": "Ville-Marie",
                "SUPERFICIE": "0.14",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-73.5544, 45.5091],
                        [-73.5538, 45.5091],
                        [-73.5538, 45.5086],
                        [-73.5544, 45.5086],
                        [-73.5544, 45.5091],
                    ]
                ],
            },
        },
        {
            "type": "Feature",
            "properties": {
                "Nom": "Boisé voirie",
                "TYPO1": "Espace voirie",
                "TYPO2": "Îlot de voirie",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-73.5541, 45.5088],
            },
        },
    ],
}


def test_parse_parcs_geojson_parks_only():
    rows = parcs_api.parse_parcs_geojson(
        _FIXTURE,
        latitude=45.5088,
        longitude=-73.5541,
        radius_m=500,
        limit=10,
        parks_only=True,
    )
    assert len(rows) == 1
    assert "Dollier" in rows[0]["name"]
    assert rows[0]["distance_m"] < 200


@pytest.mark.asyncio
async def test_find_parcs_nearby_tool():
    with (
        patch(
            "helpers.mtl.nearby.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": 45.5088,
                "longitude": -73.5541,
                "resolved_address": "Hôtel de Ville / 275 Rue Notre-Dame Est",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.mtl.parcs_api.fetch_text",
            new_callable=AsyncMock,
            return_value=json.dumps(_FIXTURE),
        ),
    ):
        from tools.mtl.parcs.find_parcs_nearby import find_parcs_nearby

        result = json.loads(await find_parcs_nearby(address="275 Rue Notre-Dame Est, Montreal", limit=5))
        assert "error" not in result
        assert result["total"] >= 1
        assert result["_meta"]["source"] == "parcs"
