"""Documented permit fallback preserves its source and published dates."""

from unittest.mock import AsyncMock

import httpx

from helpers.mtl import planned_works_api


async def test_planned_works_filters_distance_and_keeps_provenance(monkeypatch):
    query = AsyncMock(
        return_value={
            "records": [
                {
                    "id": "test",
                    "occupancy_name": "Place publique",
                    "latitude": "45.5088",
                    "longitude": "-73.5541",
                    "duration_end_date": "2026-11-13",
                },
                {"latitude": "45.7", "longitude": "-73.9"},
            ]
        }
    )
    monkeypatch.setattr(planned_works_api.ckan_api, "datastore_search_sql", query)
    result = await planned_works_api.list_nearby(45.5088, -73.5541, 800, 6, True)
    assert len(result["items"]) == 1
    assert result["fallback"] is True
    assert result["items"][0]["endtime"] == "2026-11-13"
    assert result["source_url"].endswith("vmtl-info-travaux")
    assert "duration_end_date" in query.call_args.args[1]


async def test_live_feed_failure_uses_planned_works(monkeypatch):
    from helpers.mtl import entraves_api

    monkeypatch.setattr(
        "helpers.mtl.nearby.resolve_user_point", AsyncMock(return_value={"latitude": 45.5088, "longitude": -73.5541})
    )
    monkeypatch.setattr(entraves_api, "fetch_json", AsyncMock(side_effect=httpx.ConnectError("unavailable")))
    fallback = AsyncMock(return_value={"fallback": True, "items": []})
    monkeypatch.setattr(planned_works_api, "list_nearby", fallback)
    result = await entraves_api.list_nearby(latitude=45.5088, longitude=-73.5541)
    assert result["fallback"] is True
    fallback.assert_awaited_once()
