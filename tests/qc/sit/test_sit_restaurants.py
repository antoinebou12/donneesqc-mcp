"""Tests SIT Québec restauration (DataStore mocké)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from helpers.qc.sit import sit_api

_HOTEL_LAT = 45.5098
_HOTEL_LON = -73.5576

_FIXTURE_ROWS = [
    {
        "IdentifiantUnique": "RESTNEAR1",
        "NomEtablissement": "Qing Hua Ravioli",
        "TypeEtablissement": "Restaurant",
        "NumeroVoie": "1019 boulevard Saint-Laurent",
        "Municipalite": "Montréal",
        "CodePostal": "H2Z 1J4",
        "Latitude": "45.508143",
        "Longitude": "-73.559573",
        "TelephonePrincipal": "514 903-9887",
        "SiteInternet": "https://www.qinghuadumpling.com/",
        "CuisineOrigine": "Chine",
        "CuisineTypeSpecialite": "Dumplings",
    },
    {
        "IdentifiantUnique": "RESTFAR1",
        "NomEtablissement": "Loin",
        "TypeEtablissement": "Restaurant",
        "NumeroVoie": "100 rue Lointaine",
        "Municipalite": "Laval",
        "CodePostal": "H7N 0A1",
        "Latitude": "45.55",
        "Longitude": "-73.70",
        "TelephonePrincipal": None,
        "SiteInternet": None,
        "CuisineOrigine": "Québec régional / du terroir",
        "CuisineTypeSpecialite": None,
    },
]


def test_normalize_restaurant_maps():
    row = sit_api.normalize_restaurant(_FIXTURE_ROWS[0])
    assert row["name"] == "Qing Hua Ravioli"
    assert row["type"] == "Restaurant"
    assert row["cuisine"] == "Chine — Dumplings"
    assert "Saint-Laurent" in (row["address"] or "")
    assert row["latitude"] == pytest.approx(45.508143)
    assert row["longitude"] == pytest.approx(-73.559573)


@pytest.mark.asyncio
async def test_list_nearby_filters_by_radius():
    with (
        patch(
            "helpers.qc.sit.sit_api.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": _HOTEL_LAT,
                "longitude": _HOTEL_LON,
                "resolved_address": "Hôtel de Ville",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.qc.sit.sit_api.ckan_api.datastore_search_sql",
            new_callable=AsyncMock,
            return_value={"records": _FIXTURE_ROWS},
        ),
    ):
        data = await sit_api.list_nearby(
            latitude=_HOTEL_LAT,
            longitude=_HOTEL_LON,
            radius_m=500.0,
            limit=10,
        )

    assert data["total"] == 1
    assert data["restaurants"][0]["name"] == "Qing Hua Ravioli"
    assert data["restaurants"][0]["distance_m"] < 500
    assert "google_maps_url" in data["restaurants"][0]
    assert data["nearest_google_maps_directions_url"]
    assert "sit-quebec-restauration" in data["source"]


@pytest.mark.asyncio
async def test_list_nearby_rejects_bad_radius():
    with pytest.raises(ValueError, match="radius_m"):
        await sit_api.list_nearby(latitude=_HOTEL_LAT, longitude=_HOTEL_LON, radius_m=10.0)


@pytest.mark.asyncio
async def test_list_tourist_nearby_merges_categories():
    culture_row = {
        "IdentifiantUnique": "CULT1",
        "NomEtablissement": "Champ-de-Mars",
        "TypeEtablissement": "Monument",
        "NumeroVoie": "Rue Saint-Antoine Est",
        "Municipalite": "Montréal",
        "CodePostal": "H2Y 1C6",
        "Latitude": "45.50866",
        "Longitude": "-73.55535",
        "TelephonePrincipal": None,
        "SiteInternet": "https://montreal.ca",
    }

    async def _fake_cat(**kwargs):
        cat = kwargs["category"]
        if cat == "restauration":
            places = [
                {
                    **sit_api.normalize_place(_FIXTURE_ROWS[0], category="restauration"),
                    "distance_m": 240.0,
                }
            ]
        elif cat == "culture":
            places = [
                {
                    **sit_api.normalize_place(culture_row, category="culture"),
                    "distance_m": 220.0,
                }
            ]
        else:
            places = []
        return {
            "category": cat,
            "label": cat,
            "total": len(places),
            "places": places,
            "nearest_google_maps_directions_url": None,
            "source": f"https://example/{cat}",
            "dataset_id": cat,
            "resource_id": "x",
            "note": sit_api.SIT_CSV_NOTE,
        }

    with (
        patch(
            "helpers.qc.sit.sit_api.resolve_user_point",
            new_callable=AsyncMock,
            return_value={
                "latitude": _HOTEL_LAT,
                "longitude": _HOTEL_LON,
                "resolved_address": "Hôtel de Ville",
                "location_source": "address",
            },
        ),
        patch(
            "helpers.qc.sit.sit_api._list_category_nearby",
            new_callable=AsyncMock,
            side_effect=_fake_cat,
        ),
    ):
        data = await sit_api.list_tourist_nearby(
            latitude=_HOTEL_LAT,
            longitude=_HOTEL_LON,
            radius_m=500.0,
            limit_per_category=5,
            categories=["restauration", "culture", "hotels"],
        )

    assert data["total"] == 2
    assert data["places"][0]["name"] == "Champ-de-Mars"
    assert "aperçu" in data["note"].lower() or "Aperçu" in data["note"]
    assert data["by_category"]["restauration"]["total"] == 1
