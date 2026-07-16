"""Integration: package_search / datastore_search via respx (tool -> ckan_api -> HTTP)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from helpers.common.config import DQ_API_URL, MTL_API_URL
from tests.fixtures import load_ckan_fixture


@respx.mock
@pytest.mark.asyncio
async def test_qc_search_datasets_through_http():
    fixture = load_ckan_fixture("package_search_ok.json")
    respx.get(f"{DQ_API_URL}/package_search").mock(return_value=httpx.Response(200, json=fixture))
    from tools.qc.search_datasets import search_datasets

    result = json.loads(await search_datasets(query="criminalite"))
    assert result["count"] == 1
    assert result["datasets"][0]["name"] == "actes-criminels"
    assert "donneesquebec.ca" in result["datasets"][0]["url"]
    assert result["_meta"]["source"] == "donnees_quebec"


@respx.mock
@pytest.mark.asyncio
async def test_mtl_search_datasets_through_http():
    fixture = load_ckan_fixture("package_search_ok.json")
    respx.get(f"{MTL_API_URL}/package_search").mock(return_value=httpx.Response(200, json=fixture))
    from tools.mtl.search_datasets import search_montreal_datasets

    result = json.loads(await search_montreal_datasets(query="arbres"))
    assert result["count"] == 1
    assert result["_meta"]["source"] == "montreal"


@respx.mock
@pytest.mark.asyncio
async def test_qc_query_resource_data_through_http():
    fixture = load_ckan_fixture("datastore_search_ok.json")
    respx.get(f"{DQ_API_URL}/datastore_search").mock(return_value=httpx.Response(200, json=fixture))
    from tools.qc.query_resource_data import query_resource_data

    result = json.loads(await query_resource_data(resource_id="res-1", page_size=10))
    assert result["total"] == 2
    assert "ARROND" in result["fields"]
    assert result["_meta"]["resource_id"] == "res-1"


@respx.mock
@pytest.mark.asyncio
async def test_mtl_query_data_through_http():
    fixture = load_ckan_fixture("datastore_search_ok.json")
    respx.get(f"{MTL_API_URL}/datastore_search").mock(return_value=httpx.Response(200, json=fixture))
    from tools.mtl.query_data import query_montreal_data

    result = json.loads(await query_montreal_data(resource_id="res-mtl", filters='{"ARROND": "Plateau"}'))
    assert result["total"] == 2
    assert result["_meta"]["source"] == "montreal"
