"""Fixtures partagees pour les tests."""

import pytest

from helpers.common import http_client


@pytest.fixture(autouse=True)
async def _cleanup_http_client():
    """Reset cache/rate-limit et ferme le client HTTP apres chaque test."""
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()
    yield
    http_client.clear_http_cache()
    http_client.clear_rate_limiters()
    await http_client.close()
