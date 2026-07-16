"""Tests contexte utilisateur (date/IP/GPS) - sans reseau."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.common import context


def test_is_public_ip_rejects_private_and_loopback():
    assert context.is_public_ip("8.8.8.8")
    assert not context.is_public_ip("127.0.0.1")
    assert not context.is_public_ip("10.0.0.1")
    assert not context.is_public_ip("192.168.1.1")
    assert not context.is_public_ip("not-an-ip")


def test_client_ip_from_headers_prefers_public_forwarded():
    headers = {"x-forwarded-for": "192.168.0.1, 8.8.8.8"}
    assert context.client_ip_from_headers(headers) == "8.8.8.8"


def test_resolve_now_default_toronto():
    now = context.resolve_now()
    assert now["time_source"] == "default"
    assert now["timezone"] == "America/Toronto"
    assert len(now["date"]) == 10


def test_resolve_now_agent_date():
    now = context.resolve_now(date="2026-07-16", timezone_name="America/Toronto")
    assert now["date"] == "2026-07-16"
    assert now["time_source"] == "agent"


def test_read_client_ip_outside_http_is_none():
    assert context.read_client_ip() is None


@pytest.mark.asyncio
async def test_geolocate_client_ip_rejects_empty_and_private():
    with pytest.raises(ValueError, match="manquante"):
        await context.geolocate_client_ip("")
    with pytest.raises(ValueError, match="non publique"):
        await context.geolocate_client_ip("127.0.0.1")


@pytest.mark.asyncio
async def test_geolocate_client_ip_parses_response():
    fake = {
        "latitude": 45.5,
        "longitude": -73.6,
        "city": "Montreal",
        "region": "Quebec",
        "country_name": "Canada",
    }
    with patch("helpers.common.context.fetch_json", new=AsyncMock(return_value=fake)):
        geo = await context.geolocate_client_ip("8.8.8.8")
    assert geo["latitude"] == 45.5
    assert geo["location_source"] == "client_ip"
    assert "Montreal" in (geo["label"] or "")


@pytest.mark.asyncio
async def test_resolve_user_location_agent_gps():
    loc = await context.resolve_user_location(latitude=45.5, longitude=-73.6)
    assert loc["location_source"] == "agent"
    assert loc["latitude"] == 45.5


@pytest.mark.asyncio
async def test_resolve_user_location_no_input_errors():
    with (
        patch("helpers.common.context.read_client_ip", return_value=None),
        pytest.raises(ValueError, match="GPS"),
    ):
        await context.resolve_user_location(allow_client_ip=True)


@pytest.mark.asyncio
async def test_common_get_context_tool_with_gps():
    from tools.common.get_context import get_context

    raw = await get_context(latitude=45.5088, longitude=-73.5617, date="2026-07-16")
    data = json.loads(raw)
    assert data["now"]["date"] == "2026-07-16"
    assert data["location"]["location_source"] == "agent"
    assert data["_meta"]["source"] == "donneesqc_mcp"
