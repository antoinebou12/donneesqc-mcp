"""Integration: fake SQL through QC/MTL SQL tools (no live network)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from helpers.common.config import DQ_API_URL, MTL_API_URL
from tests.fixtures import load_ckan_fixture


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sql", "needle"),
    [
        ('DELETE FROM "abc"', "SELECT"),
        ("", "SELECT"),
        ("SELECT 1; SELECT 2", "une seule"),
    ],
)
async def test_qc_query_resource_sql_rejects_bad_sql(sql: str, needle: str):
    from tools.qc.query_resource_sql import query_resource_sql

    result = json.loads(await query_resource_sql(sql))
    assert "error" in result
    assert needle.lower() in result["error"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sql", "needle"),
    [
        ("UPDATE x SET y=1", "SELECT"),
        ("INSERT INTO t VALUES (1)", "SELECT"),
    ],
)
async def test_mtl_query_sql_rejects_bad_sql(sql: str, needle: str):
    from tools.mtl.query_sql import query_montreal_sql

    result = json.loads(await query_montreal_sql(sql))
    assert "error" in result
    assert needle.lower() in result["error"].lower()


@respx.mock
@pytest.mark.asyncio
async def test_qc_query_resource_sql_happy_path():
    fixture = load_ckan_fixture("datastore_sql_ok.json")
    respx.get(f"{DQ_API_URL}/datastore_search_sql").mock(return_value=httpx.Response(200, json=fixture))
    from tools.qc.query_resource_sql import query_resource_sql

    sql = 'SELECT ville, COUNT(*) AS total FROM "res-1" GROUP BY ville LIMIT 10'
    result = json.loads(await query_resource_sql(sql))
    assert "error" not in result
    assert result["fields"] == ["ville", "total"]
    assert len(result["records"]) == 2
    assert result["_meta"]["source"] == "donnees_quebec"


@respx.mock
@pytest.mark.asyncio
async def test_mtl_query_sql_happy_path():
    fixture = load_ckan_fixture("datastore_sql_ok.json")
    respx.get(f"{MTL_API_URL}/datastore_search_sql").mock(return_value=httpx.Response(200, json=fixture))
    from tools.mtl.query_sql import query_montreal_sql

    result = json.loads(await query_montreal_sql('SELECT * FROM "res-1" LIMIT 5'))
    assert "error" not in result
    assert result["_meta"]["source"] == "montreal"
