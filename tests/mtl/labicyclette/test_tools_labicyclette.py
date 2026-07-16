"""Tests unitaires pour les outils La bicyclette MCP-first (mockés)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

# ── get_labicyclette_overview ────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_labicyclette_overview():
    mock_data = {
        "totalVolume": 180309427,
        "activeCounters": 81,
        "totalRecords": 157317,
        "uniqueDays": 6401,
        "minDate": "2009-01-01",
        "maxDate": "2026-07-11",
    }
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_overview.labicyclette_api.get_overview",
        new_callable=AsyncMock,
        return_value=mock_data,
    ):
        from tools.mtl.labicyclette.get_labicyclette_overview import get_labicyclette_overview

        result = json.loads(await get_labicyclette_overview())
        assert result["view"] == "overview"
        assert result["totals"]["totalVolume"] == 180309427
        assert len(result["kpis"]) == 3
        assert result["kpis"][0]["id"] == "total_rides"
        assert result["kpis"][0]["display"] == "180.3M"
        assert result["dashboard_url"].endswith("/en")
        assert result["_meta"]["source"] == "labicyclette"


@pytest.mark.asyncio
async def test_get_labicyclette_overview_error():
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_overview.labicyclette_api.get_overview",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connexion refusee"),
    ):
        from tools.mtl.labicyclette.get_labicyclette_overview import get_labicyclette_overview

        result = json.loads(await get_labicyclette_overview())
        assert "error" in result


# ── list_labicyclette_counters ───────────────────────────────────────


@pytest.mark.asyncio
async def test_list_labicyclette_counters():
    mock_counters = [
        {
            "instance": "100003032",
            "longitude": -73.56297,
            "latitude": 45.516216,
            "arrondissement": "Ville-Marie",
            "rue1": "Berri1",
            "rue2": None,
        },
        {
            "instance": "300014995",
            "longitude": -73.57603,
            "latitude": 45.52086,
            "arrondissement": "Le Plateau-Mont-Royal",
            "rue1": "REV St-Denis/Duluth dir nord",
            "rue2": None,
        },
    ]
    with patch(
        "tools.mtl.labicyclette.list_labicyclette_counters.labicyclette_api.list_counters",
        new_callable=AsyncMock,
        return_value=mock_counters,
    ):
        from tools.mtl.labicyclette.list_labicyclette_counters import list_labicyclette_counters

        result = json.loads(await list_labicyclette_counters())
        assert result["view"] == "counters"
        assert result["count"] == 2
        assert result["counters"][0]["name"] == "Berri1"
        assert result["chart"]["type"] == "map_points"
        assert len(result["chart"]["points"]) == 2


@pytest.mark.asyncio
async def test_list_labicyclette_counters_filter_and_limit():
    mock_counters = [
        {
            "instance": "100003032",
            "arrondissement": "Ville-Marie",
            "rue1": "Berri1",
            "latitude": 45.5,
            "longitude": -73.5,
        },
        {
            "instance": "300014995",
            "arrondissement": "Le Plateau-Mont-Royal",
            "rue1": "REV St-Denis/Duluth dir nord",
            "latitude": 45.52,
            "longitude": -73.57,
        },
    ]
    with patch(
        "tools.mtl.labicyclette.list_labicyclette_counters.labicyclette_api.list_counters",
        new_callable=AsyncMock,
        return_value=mock_counters,
    ):
        from tools.mtl.labicyclette.list_labicyclette_counters import list_labicyclette_counters

        result = json.loads(
            await list_labicyclette_counters(arrondissement="plateau", limit=1),
        )
        assert result["count"] == 1
        assert result["counters"][0]["instance"] == "300014995"


@pytest.mark.asyncio
async def test_list_labicyclette_counters_error():
    with patch(
        "tools.mtl.labicyclette.list_labicyclette_counters.labicyclette_api.list_counters",
        new_callable=AsyncMock,
        side_effect=RuntimeError("timeout"),
    ):
        from tools.mtl.labicyclette.list_labicyclette_counters import list_labicyclette_counters

        result = json.loads(await list_labicyclette_counters())
        assert "error" in result


# ── get_labicyclette_counter ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_labicyclette_counter_compact_default():
    mock_detail = {
        "instance": "100003032",
        "rue1": "Berri1",
        "arrondissement": "Ville-Marie",
        "latitude": 45.516216,
        "longitude": -73.56297,
        "dailyData": [
            {
                "date": "2025-07-16",
                "volume": 6787,
                "temperatureMeanC": 27.9,
                "precipitationMm": 0,
            },
            {
                "date": "2025-07-17",
                "volume": 4000,
                "temperatureMeanC": 25.0,
                "precipitationMm": 5.0,
            },
        ],
        "weatherMeta": {"city": "montreal"},
        "activeConstruction": [
            {
                "permitId": "p1",
                "status": "blocked",
                "distanceMeters": 120,
                "impact": {"signal": "decrease", "duringDeltaPct": -10.0},
            }
        ],
    }
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_counter.labicyclette_api.get_counter",
        new_callable=AsyncMock,
        return_value=mock_detail,
    ) as mock:
        from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

        result = json.loads(
            await get_labicyclette_counter(
                instance="100003032",
                from_date="2025-07-01",
                to_date="2025-07-16",
            ),
        )
        assert result["view"] == "counter"
        assert result["counter"]["name"] == "Berri1"
        assert result["summary"]["totalVolume"] == 10787
        assert result["summary"]["peak"]["date"] == "2025-07-16"
        assert result["chart"]["type"] == "line"
        assert "tempC" not in result["chart"]["points"][0]
        assert result["weather"] is None
        assert result["construction"][0]["permitId"] == "p1"
        assert "dailyData" not in result
        mock.assert_awaited_once_with(
            "100003032",
            from_date="2025-07-01",
            to_date="2025-07-16",
        )


@pytest.mark.asyncio
async def test_get_labicyclette_counter_include_weather():
    mock_detail = {
        "instance": "100003032",
        "rue1": "Berri1",
        "arrondissement": "Ville-Marie",
        "dailyData": [
            {
                "date": "2025-07-16",
                "volume": 100,
                "temperatureMeanC": 20.5,
                "precipitationMm": 1.2,
            }
        ],
        "weatherMeta": {"city": "montreal"},
        "activeConstruction": [],
    }
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_counter.labicyclette_api.get_counter",
        new_callable=AsyncMock,
        return_value=mock_detail,
    ):
        from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

        result = json.loads(
            await get_labicyclette_counter(
                instance="100003032",
                from_date="2025-07-01",
                to_date="2025-07-16",
                include_weather=True,
            ),
        )
        point = result["chart"]["points"][0]
        assert point["tempC"] == 20.5
        assert point["precipMm"] == 1.2
        assert result["weather"]["included"] is True


@pytest.mark.asyncio
async def test_get_labicyclette_counter_missing_instance():
    from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

    result = json.loads(await get_labicyclette_counter(instance=""))
    assert "error" in result


@pytest.mark.asyncio
async def test_get_labicyclette_counter_invalid_date():
    from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

    result = json.loads(
        await get_labicyclette_counter(
            instance="100003032",
            from_date="01-07-2025",
            to_date="2025-07-16",
        ),
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_get_labicyclette_counter_span_too_long():
    from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

    result = json.loads(
        await get_labicyclette_counter(
            instance="100003032",
            from_date="2024-01-01",
            to_date="2026-01-02",
        ),
    )
    assert "error" in result
    assert "366" in result["error"]


@pytest.mark.asyncio
async def test_get_labicyclette_counter_partial_dates():
    from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

    result = json.loads(
        await get_labicyclette_counter(instance="100003032", from_date="2025-07-01"),
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_get_labicyclette_counter_http_error():
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_counter.labicyclette_api.get_counter",
        new_callable=AsyncMock,
        side_effect=RuntimeError("404"),
    ):
        from tools.mtl.labicyclette.get_labicyclette_counter import get_labicyclette_counter

        result = json.loads(
            await get_labicyclette_counter(
                instance="100003032",
                from_date="2025-07-01",
                to_date="2025-07-16",
            ),
        )
        assert "error" in result


# ── get_labicyclette_boroughs ────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_labicyclette_boroughs():
    mock_rows = [
        {"borough": "Ville-Marie", "volume": 50, "counterCount": 2},
        {"borough": "Le Plateau-Mont-Royal", "volume": 150, "counterCount": 5},
    ]
    with patch(
        "tools.mtl.labicyclette.get_labicyclette_boroughs.labicyclette_api.get_boroughs",
        new_callable=AsyncMock,
        return_value=mock_rows,
    ):
        from tools.mtl.labicyclette.get_labicyclette_boroughs import get_labicyclette_boroughs

        result = json.loads(await get_labicyclette_boroughs())
        assert result["view"] == "boroughs"
        assert result["boroughs"][0]["borough"] == "Le Plateau-Mont-Royal"
        assert result["boroughs"][0]["rank"] == 1
        assert result["boroughs"][0]["volumeSharePct"] == 75.0
        assert result["chart"]["type"] == "bar"
        assert result["chart"]["values"] == [150, 50]
        assert "ascii" in result["chart"]
        assert "Le Plateau-Mont-Royal" in result["chart"]["ascii"]
        assert "150" in result["chart"]["ascii"]


# ── list_labicyclette_construction ───────────────────────────────────


@pytest.mark.asyncio
async def test_list_labicyclette_construction_filters():
    mock_rows = [
        {
            "permitId": "a",
            "streetName": "Rue A",
            "borough": "Verdun",
            "status": "blocked",
            "severityScore": 90,
            "latitude": 45.46,
            "longitude": -73.57,
            "snapshotDate": "2026-07-16",
            "impact": {"signal": "decrease", "duringDeltaPct": -12.0},
        },
        {
            "permitId": "b",
            "streetName": "Rue B",
            "borough": "Ville-Marie",
            "status": "obstructed",
            "severityScore": 40,
            "latitude": 45.5,
            "longitude": -73.55,
            "snapshotDate": "2026-07-16",
            "impact": {"signal": "stable", "duringDeltaPct": 1.0},
        },
        {
            "permitId": "c",
            "streetName": "Rue C",
            "borough": "Verdun",
            "status": "blocked",
            "severityScore": 20,
            "latitude": 45.47,
            "longitude": -73.56,
            "snapshotDate": "2026-07-16",
            "impact": {"signal": "insufficient", "duringDeltaPct": None},
        },
    ]
    with patch(
        "tools.mtl.labicyclette.list_labicyclette_construction.labicyclette_api.list_construction",
        new_callable=AsyncMock,
        return_value=mock_rows,
    ):
        from tools.mtl.labicyclette.list_labicyclette_construction import list_labicyclette_construction

        result = json.loads(
            await list_labicyclette_construction(
                status="blocked",
                borough="Verdun",
                min_severity=50,
                limit=10,
            ),
        )
        assert result["view"] == "construction"
        assert result["total_matching"] == 1
        assert result["count"] == 1
        assert result["sites"][0]["permitId"] == "a"
        assert "schedule" not in result["sites"][0]
        assert result["chart"]["type"] == "map_points"


@pytest.mark.asyncio
async def test_list_labicyclette_construction_bad_status():
    from tools.mtl.labicyclette.list_labicyclette_construction import list_labicyclette_construction

    result = json.loads(await list_labicyclette_construction(status="closed"))
    assert "error" in result
