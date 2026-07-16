"""Tests du cache HTTP GET TTL/LRU."""

import time

import httpx
import pytest
import respx

from helpers.common import http_client


@pytest.fixture(autouse=True)
def _reset_http_state():
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()
    yield
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_json_caches_response(monkeypatch):
    monkeypatch.setattr(http_client, "HTTP_CACHE_TTL_SECONDS", 60.0)
    monkeypatch.setattr(http_client, "HTTP_CACHE_MAX_ENTRIES", 256)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_RPS", 1000.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_BURST", 1000.0)

    route = respx.get("https://example.test/api").mock(return_value=httpx.Response(200, json={"ok": True}))

    first = await http_client.fetch_json("https://example.test/api")
    second = await http_client.fetch_json("https://example.test/api")

    assert first == {"ok": True}
    assert second == {"ok": True}
    assert route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_fetch_json_use_cache_false_bypasses(monkeypatch):
    monkeypatch.setattr(http_client, "HTTP_CACHE_TTL_SECONDS", 60.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_RPS", 1000.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_BURST", 1000.0)

    route = respx.get("https://example.test/sql").mock(return_value=httpx.Response(200, json={"n": 1}))

    await http_client.fetch_json("https://example.test/sql", use_cache=False)
    await http_client.fetch_json("https://example.test/sql", use_cache=False)

    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_cache_expires(monkeypatch):
    monkeypatch.setattr(http_client, "HTTP_CACHE_TTL_SECONDS", 0.05)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_RPS", 1000.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_BURST", 1000.0)

    route = respx.get("https://example.test/ttl").mock(return_value=httpx.Response(200, json={"v": 1}))

    await http_client.fetch_json("https://example.test/ttl")
    time.sleep(0.08)
    await http_client.fetch_json("https://example.test/ttl")

    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_fetch_text_caches(monkeypatch):
    monkeypatch.setattr(http_client, "HTTP_CACHE_TTL_SECONDS", 60.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_RPS", 1000.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_BURST", 1000.0)

    route = respx.get("https://example.test/xml").mock(return_value=httpx.Response(200, text="<ok/>"))

    assert await http_client.fetch_text("https://example.test/xml") == "<ok/>"
    assert await http_client.fetch_text("https://example.test/xml") == "<ok/>"
    assert route.call_count == 1
