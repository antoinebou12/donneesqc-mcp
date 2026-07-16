"""Integration: package_search via respx for Données Québec catalog tools."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from helpers.common.config import DQ_API_URL
from tests.fixtures import load_ckan_fixture


@respx.mock
@pytest.mark.asyncio
async def test_qc_search_filters_json_invalid():
    from tools.qc.query_resource_data import query_resource_data

    result = json.loads(await query_resource_data(resource_id="x", filters="{not-json"))
    assert "error" in result
    assert "JSON" in result["error"]


@respx.mock
@pytest.mark.asyncio
async def test_qc_package_search_fixture_shape():
    """Sanity: fixture is a valid CKAN envelope for package_search."""
    fixture = load_ckan_fixture("package_search_ok.json")
    route = respx.get(f"{DQ_API_URL}/package_search").mock(return_value=httpx.Response(200, json=fixture))
    from helpers.common import ckan_api

    result = await ckan_api.package_search(DQ_API_URL, query="x", rows=5)
    assert route.called
    assert result["count"] == 1
    assert result["results"][0]["name"] == "actes-criminels"
