"""Tests unitaires pour les outils Ville de Montréal (mockés)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

# ── search_montreal_datasets ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_montreal_datasets():
    mock_result = {
        "count": 15,
        "results": [
            {
                "id": "mtl-001",
                "name": "pistes-cyclables",
                "title": "Réseau cyclable",
                "notes": "Pistes cyclables de la Ville de Montréal",
                "organization": {"title": "Ville de Montréal"},
                "num_resources": 2,
                "metadata_modified": "2024-05-01",
            },
        ],
    }
    with patch(
        "helpers.common.ckan_format.ckan_api.package_search",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        from tools.mtl.search_datasets import search_montreal_datasets

        result = json.loads(
            await search_montreal_datasets(query="pistes cyclables"),
        )
        assert result["count"] == 15
        assert result["datasets"][0]["name"] == "pistes-cyclables"
        assert "donnees.montreal.ca" in result["datasets"][0]["url"]


@pytest.mark.asyncio
async def test_search_montreal_datasets_pagination():
    mock_result = {"count": 50, "results": []}
    with patch(
        "helpers.common.ckan_format.ckan_api.package_search",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock:
        from tools.mtl.search_datasets import search_montreal_datasets

        await search_montreal_datasets(query="arbres", page=3, page_size=10)
        assert mock.call_args[1]["start"] == 20  # (3-1) * 10
        assert mock.call_args[1]["rows"] == 10


@pytest.mark.asyncio
async def test_search_montreal_datasets_error():
    with patch(
        "helpers.common.ckan_format.ckan_api.package_search",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connexion refusée"),
    ):
        from tools.mtl.search_datasets import search_montreal_datasets

        result = json.loads(
            await search_montreal_datasets(query="test"),
        )
        assert "error" in result


# ── query_montreal_data ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_montreal_data():
    mock_result = {
        "total": 500,
        "fields": [{"id": "_id"}, {"id": "ARROND"}, {"id": "NB_CRIMES"}],
        "records": [{"ARROND": "Le Plateau-Mont-Royal", "NB_CRIMES": 120}],
    }
    with (
        patch(
            "tools.mtl.query_data.ckan_api.datastore_search",
            new_callable=AsyncMock,
            return_value=mock_result,
        ),
        patch(
            "tools.mtl.query_data.ckan_format.resolve_resource_citation",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        from tools.mtl.query_data import query_montreal_data

        result = json.loads(
            await query_montreal_data(resource_id="mtl-r1"),
        )
        assert result["total"] == 500
        assert "_id" not in result["fields"]
        assert result["records"][0]["ARROND"] == "Le Plateau-Mont-Royal"


@pytest.mark.asyncio
async def test_query_montreal_data_with_filters():
    mock_result = {"total": 10, "fields": [{"id": "ARROND"}], "records": []}
    with (
        patch(
            "tools.mtl.query_data.ckan_api.datastore_search",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock,
        patch(
            "tools.mtl.query_data.ckan_format.resolve_resource_citation",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        from tools.mtl.query_data import query_montreal_data

        await query_montreal_data(
            resource_id="r1",
            filters='{"ARROND": "Rosemont"}',
        )
        assert mock.call_args[1]["filters"] == {"ARROND": "Rosemont"}


@pytest.mark.asyncio
async def test_query_montreal_data_invalid_filters():
    from tools.mtl.query_data import query_montreal_data

    result = json.loads(
        await query_montreal_data(resource_id="r1", filters="{invalide"),
    )
    assert "error" in result
    assert "JSON" in result["error"]


# ── query_montreal_sql ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_montreal_sql():
    mock_result = {
        "fields": [{"id": "ARROND"}, {"id": "total"}],
        "records": [
            {"ARROND": "Ville-Marie", "total": 3500},
            {"ARROND": "Le Plateau-Mont-Royal", "total": 2100},
        ],
    }
    with (
        patch(
            "tools.mtl.query_sql.ckan_api.datastore_search_sql",
            new_callable=AsyncMock,
            return_value=mock_result,
        ),
        patch(
            "tools.mtl.query_sql.ckan_format.resolve_resource_citation",
            new_callable=AsyncMock,
            return_value={},
        ),
    ):
        from tools.mtl.query_sql import query_montreal_sql

        result = json.loads(
            await query_montreal_sql(
                sql='SELECT "ARROND", COUNT(*) as total FROM "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" GROUP BY "ARROND"',
            )
        )
        assert len(result["records"]) == 2
        assert result["fields"] == ["ARROND", "total"]
        assert "sql_url" in result
        assert "datastore_search_sql" in result["sql_url"]


@pytest.mark.asyncio
async def test_query_montreal_sql_enriches_pdq_and_citations():
    rid = "c6f482bf-bf0f-4960-8b2f-9982c211addd"
    mock_result = {
        "fields": [{"id": "PDQ"}, {"id": "total"}],
        "records": [{"PDQ": "38", "total": 25787}],
    }
    citation = {
        "dataset_url": "https://donnees.montreal.ca/dataset/actes-criminels",
        "resource_url": f"https://donnees.montreal.ca/dataset/actes-criminels/resource/{rid}",
        "dataset_title": "Actes criminels",
        "dataset_name": "actes-criminels",
    }
    with (
        patch(
            "tools.mtl.query_sql.ckan_api.datastore_search_sql",
            new_callable=AsyncMock,
            return_value=mock_result,
        ),
        patch(
            "tools.mtl.query_sql.ckan_format.resolve_resource_citation",
            new_callable=AsyncMock,
            return_value=citation,
        ),
    ):
        from tools.mtl.query_sql import query_montreal_sql

        sql = 'SELECT "PDQ", COUNT(*) AS total FROM "c6f482bf-bf0f-4960-8b2f-9982c211addd" GROUP BY "PDQ"'
        result = json.loads(await query_montreal_sql(sql=sql))
        assert result["records"][0]["pdq_label"] == "38 (Plateau-Mont-Royal)"
        assert result["dataset_url"] == citation["dataset_url"]
        assert result["resource_url"] == citation["resource_url"]
        assert rid in result["sql_url"]
        assert result["_meta"]["portal_url"] == citation["dataset_url"]
        assert result["_meta"]["resource_id"] == rid


@pytest.mark.asyncio
async def test_query_montreal_sql_error():
    with patch(
        "tools.mtl.query_sql.ckan_api.datastore_search_sql",
        new_callable=AsyncMock,
        side_effect=RuntimeError("erreur SQL"),
    ):
        from tools.mtl.query_sql import query_montreal_sql

        result = json.loads(await query_montreal_sql(sql="INVALID SQL"))
        assert "error" in result
