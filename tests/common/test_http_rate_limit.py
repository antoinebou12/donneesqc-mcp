"""Tests du rate limiting HTTP sortant."""

import time

import httpx
import pytest
import respx

from helpers.common import http_client
from helpers.common.http_client import _TokenBucket


@pytest.fixture(autouse=True)
def _reset_http_state():
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()
    yield
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()


@pytest.mark.asyncio
async def test_token_bucket_limits_burst():
    bucket = _TokenBucket(rate=100.0, burst=2.0)
    await bucket.acquire()
    await bucket.acquire()
    start = time.monotonic()
    # Troisième jeton : doit attendre un peu (rate 100/s → ~10ms)
    await bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.005


@respx.mock
@pytest.mark.asyncio
async def test_fetch_json_applies_rate_limit(monkeypatch):
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_RPS", 50.0)
    monkeypatch.setattr(http_client, "HTTP_RATE_LIMIT_BURST", 1.0)
    monkeypatch.setattr(http_client, "HTTP_CACHE_TTL_SECONDS", 0.0)

    respx.get("https://example.test/rl").mock(return_value=httpx.Response(200, json={"ok": True}))

    start = time.monotonic()
    await http_client.fetch_json("https://example.test/rl", use_cache=False)
    await http_client.fetch_json("https://example.test/rl", use_cache=False)
    elapsed = time.monotonic() - start
    # burst=1 → 2e requête attend ~1/50s
    assert elapsed >= 0.015
