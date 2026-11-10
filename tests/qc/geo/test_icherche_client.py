"""Tests iCherche client + parse civic."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from helpers.qc.geo.icherche_client import (
    geocode_features,
    parse_civic_from_label,
    reverse_features,
)

# Adresse civique publique : Hôtel de Ville de Montréal
_HOTEL_VILLE_LABEL = "275 rue Notre-Dame Est, Montréal H2Y1C6"
_HOTEL_VILLE_QUERY = "275 Rue Notre-Dame Est, Montreal"


def test_parse_civic_from_label_hotel_de_ville():
    parsed = parse_civic_from_label(_HOTEL_VILLE_LABEL)
    assert parsed["street_number"] == "275"
    assert parsed["street"] == "rue Notre-Dame Est"
    assert parsed["postal_code"] == "H2Y 1C6"


def test_parse_civic_from_label_spaced_postal():
    parsed = parse_civic_from_label("1 Place Ville-Marie, Montréal H3B 3Y1")
    assert parsed["street_number"] == "1"
    assert "Place Ville-Marie" in parsed["street"]
    assert parsed["postal_code"] == "H3B 3Y1"


def test_parse_civic_from_label_empty():
    assert parse_civic_from_label("")["street_number"] == ""


@pytest.mark.asyncio
async def test_geocode_features_passes_geometry_true():
    feat = {
        "type": "Feature",
        "properties": {"nom": _HOTEL_VILLE_LABEL},
        "geometry": {"type": "Point", "coordinates": [-73.55410909, 45.50882581]},
    }
    with patch(
        "helpers.qc.geo.icherche_client.fetch_json",
        new_callable=AsyncMock,
        return_value={"features": [feat]},
    ) as mock_fetch:
        features = await geocode_features(_HOTEL_VILLE_QUERY, limit=1)
        assert len(features) == 1
        assert mock_fetch.await_args is not None
        params = mock_fetch.await_args.kwargs["params"]
        assert params["geometry"] == "true"
        assert params["type"] == "adresses"


@pytest.mark.asyncio
async def test_reverse_features_raises_clear_error_on_400():
    request = httpx.Request("GET", "https://example.test/reverse")
    response = httpx.Response(400, request=request)

    async def boom(*_a, **_k):
        raise httpx.HTTPStatusError("bad", request=request, response=response)

    with (
        patch("helpers.qc.geo.icherche_client.fetch_json", side_effect=boom),
        pytest.raises(ValueError, match="adresse civique"),
    ):
        await reverse_features(45.5088, -73.5541)
