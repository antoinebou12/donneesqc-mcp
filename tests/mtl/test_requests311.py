"""311 location filtering, bounded results and public field selection."""

from unittest.mock import AsyncMock

import pytest

from helpers.common.ckan_api import validate_sql
from helpers.mtl import requests311_api


async def test_requests_filter_distance_and_retain_status(monkeypatch):
    monkeypatch.setattr(requests311_api, "resolve_point", AsyncMock(return_value=(45.5088, -73.5541, None)))
    records = [
        {
            "LOC_LAT": "45.5088",
            "LOC_LONG": "-73.5541",
            "ACTI_NOM": "Nettoyage",
            "DDS_DATE_CREATION": "2026-11-01",
            "DERNIER_STATUT": "Fermée",
            "LIN_CODE_POSTAL": "excluded",
        },
        {"LOC_LAT": "45.7", "LOC_LONG": "-73.8"},
        {"LOC_LAT": "invalid", "LOC_LONG": None},
        {"LOC_LAT": "NaN", "LOC_LONG": "-73.5541"},
    ]
    query = AsyncMock(return_value={"records": records})
    monkeypatch.setattr(requests311_api.ckan_api, "datastore_search_sql", query)
    monkeypatch.setattr(requests311_api, "MAX_CANDIDATES", 4)
    result = await requests311_api.list_nearby(latitude=45.5088, longitude=-73.5541)
    assert len(result["items"]) == 1
    assert result["items"][0]["status"] == "Fermée"
    assert "LIN_CODE_POSTAL" not in result["items"][0]
    assert result["items"][0]["google_maps_url"].startswith("https://")
    assert result["truncated"] is True
    sql = query.call_args.args[1]
    validate_sql(sql)
    assert "LIMIT 4" in sql
    assert '"DDS_DATE_CREATION" <' in sql


@pytest.mark.parametrize("kwargs", [{"radius_m": float("nan")}, {"days": 91}, {"limit": 0}])
async def test_requests_validation(kwargs):
    with pytest.raises(ValueError, match=r"rayon|days"):
        await requests311_api.list_nearby(**kwargs)


async def test_latest_available_period_is_explicitly_historical(monkeypatch):
    monkeypatch.setattr(requests311_api, "resolve_point", AsyncMock(return_value=(45.5088, -73.5541, None)))
    query = AsyncMock(
        side_effect=[
            {"records": [{"DDS_DATE_CREATION": "2025-07-20T21:50:09"}]},
            {
                "records": [
                    {
                        "ACTI_NOM": "Nettoyage",
                        "DDS_DATE_CREATION": "2025-07-10",
                        "LOC_LAT": "45.5088",
                        "LOC_LONG": "-73.5541",
                    }
                ]
            },
        ]
    )
    monkeypatch.setattr(requests311_api.ckan_api, "datastore_search_sql", query)
    result = await requests311_api.list_nearby(use_latest_available=True)
    assert result["historical"] is True
    assert result["through"] == "2025-07-20"
    assert result["since"] == "2025-06-21"
    assert len(result["items"]) == 1
    assert "2025-07-21" in query.call_args.args[1]
