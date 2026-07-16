"""Tests Info-pannes Hydro-Québec (mocked HTTP)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from helpers.qc.hydro import address_resolve, infopannes_api

# Adresse civique publique (pas de résidence personnelle)
_PUBLIC_ADDRESS = "1 Place Ville-Marie, Montréal"
_LIEU_ID = "0500999999"

_CIVIC = {
    "street_number": "1",
    "street": "Place Ville-Marie",
    "postal_code": "H3B 3Y1",
    "municipality": "Montréal",
    "address": "1 Place Ville-Marie, Montréal",
    "latitude": 45.5017,
    "longitude": -73.5673,
}

_LIEUX_FIXTURE = [
    {
        "lieuConsommation": _LIEU_ID,
        "noRue": "1",
        "nomRue": "Place Ville-Marie",
        "ville": "Montréal",
        "codePostal": "H3B 3Y1",
        "adresseCompleteFr": "1 Place Ville-Marie, Montréal, Qc H3B 3Y1",
        "eligible": True,
    }
]

_ETATS_FIXTURE = [
    {
        "idLieuConso": _LIEU_ID,
        "etat": "A",
        "date": "2026-07-16T12:00:00.000+00:00",
        "repriseGraduellePossible": False,
        "declencheurReprise": False,
        "interruptions": [],
    }
]


def test_normalize_postal_code():
    assert address_resolve.normalize_postal_code("h3b3y1") == "H3B 3Y1"
    assert address_resolve.normalize_postal_code("H3B 3Y1") == "H3B 3Y1"
    assert address_resolve.normalize_postal_code("H3B\u00a03Y1") == "H3B 3Y1"


def test_feature_to_civic():
    feat = {
        "properties": {
            "numero": "1",
            "rue": "Place Ville-Marie",
            "codePostal": "H3B3Y1",
            "municipalite": "Montréal",
            "recherche": "1 Place Ville-Marie",
        },
        "geometry": {"coordinates": [-73.5673, 45.5017]},
    }
    civic = address_resolve.feature_to_civic(feat)
    assert civic["street_number"] == "1"
    assert civic["postal_code"] == "H3B 3Y1"
    assert civic["latitude"] == 45.5017


def test_feature_to_civic_sparse_nom_only():
    feat = {
        "properties": {
            "code": "abcH2Y1C6",
            "nom": "275 rue Notre-Dame Est, Montréal H2Y1C6",
            "nbUnite": "1",
        },
        "geometry": {"type": "Point", "coordinates": [-73.55410909, 45.50882581]},
    }
    civic = address_resolve.feature_to_civic(feat)
    assert civic["street_number"] == "275"
    assert civic["street"] == "rue Notre-Dame Est"
    assert civic["postal_code"] == "H2Y 1C6"
    assert civic["latitude"] == 45.50882581


@pytest.mark.asyncio
async def test_resolve_from_address_sparse_nom(monkeypatch):
    feat = {
        "properties": {
            "nom": "275 rue Notre-Dame Est, Montréal H2Y1C6",
        },
        "geometry": {"type": "Point", "coordinates": [-73.55410909, 45.50882581]},
    }

    async def fake_geocode(_q: str, *, limit: int = 1):  # noqa: ARG001
        return [feat]

    monkeypatch.setattr(address_resolve, "geocode_features", fake_geocode)
    civic = await address_resolve.resolve_from_address("275 Rue Notre-Dame Est, Montreal")
    assert civic["street_number"] == "275"
    assert civic["postal_code"] == "H2Y 1C6"


@pytest.mark.asyncio
async def test_resolve_civic_rejects_both():
    with pytest.raises(ValueError, match="soit"):
        await address_resolve.resolve_civic(
            address=_PUBLIC_ADDRESS,
            latitude=45.5,
            longitude=-73.5,
        )


@pytest.mark.asyncio
async def test_resolve_civic_rejects_partial_coords():
    with pytest.raises(ValueError, match="ensemble"):
        await address_resolve.resolve_civic(latitude=45.5)


@pytest.mark.asyncio
async def test_lookup_and_etats():
    with (
        patch(
            "helpers.qc.hydro.infopannes_api.fetch_json",
            new_callable=AsyncMock,
            side_effect=[_LIEUX_FIXTURE, _ETATS_FIXTURE],
        ) as mock_fetch,
    ):
        lieux = await infopannes_api.lookup_lieux_conso(
            street_number="1",
            street="Place Ville-Marie",
            postal_code="H3B3Y1",
        )
        assert lieux[0]["lieuConsommation"] == _LIEU_ID
        etats = await infopannes_api.get_etats([_LIEU_ID])
        assert etats[0]["etat"] == "A"
        assert mock_fetch.await_count == 2
        lieux_call = mock_fetch.await_args_list[0]
        assert "lieux-conso" in lieux_call.args[0]
        assert lieux_call.kwargs["params"]["codePostal"] == "H3B 3Y1"
        assert "hqToken" in lieux_call.kwargs["params"]
        assert len(lieux_call.kwargs["params"]["hqToken"]) >= 8


@pytest.mark.asyncio
async def test_outage_status_for_civic_no_lieux():
    with (
        patch(
            "helpers.qc.hydro.infopannes_api.fetch_json",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(ValueError, match="Aucun lieu"),
    ):
        await infopannes_api.outage_status_for_civic(
            street_number="1",
            street="Place Ville-Marie",
            postal_code="H3B 3Y1",
        )


@pytest.mark.asyncio
async def test_qc_hydro_outage_status_by_address():
    with (
        patch(
            "tools.qc.hydro.outage_status.address_resolve.resolve_civic",
            new_callable=AsyncMock,
            return_value=_CIVIC,
        ),
        patch(
            "tools.qc.hydro.outage_status.infopannes_api.outage_status_for_civic",
            new_callable=AsyncMock,
            return_value={
                "total": 1,
                "lieux": [
                    infopannes_api.format_lieu_status(_LIEUX_FIXTURE[0], _ETATS_FIXTURE[0]),
                ],
                "note": infopannes_api.INFO_NOTE,
            },
        ),
    ):
        from tools.qc.hydro.outage_status import outage_status

        result = json.loads(await outage_status(address=_PUBLIC_ADDRESS))
        assert result["_meta"]["source"] == "hydro_quebec_infopannes"
        assert "infopannes" in result["_meta"]["portal_url"]
        assert result["total"] == 1
        assert result["lieux"][0]["etat"] == "A"
        assert result["lieux"][0]["etat_label"] == "alimenté"
        assert result["lieux"][0]["has_outage"] is False
        assert result["resolved_address"]["street_number"] == "1"


@pytest.mark.asyncio
async def test_qc_hydro_outage_status_by_coords():
    with (
        patch(
            "tools.qc.hydro.outage_status.address_resolve.resolve_civic",
            new_callable=AsyncMock,
            return_value=_CIVIC,
        ) as mock_resolve,
        patch(
            "tools.qc.hydro.outage_status.infopannes_api.outage_status_for_civic",
            new_callable=AsyncMock,
            return_value={
                "total": 1,
                "lieux": [
                    infopannes_api.format_lieu_status(_LIEUX_FIXTURE[0], _ETATS_FIXTURE[0]),
                ],
                "note": infopannes_api.INFO_NOTE,
            },
        ),
    ):
        from tools.qc.hydro.outage_status import outage_status

        result = json.loads(await outage_status(latitude=45.5017, longitude=-73.5673))
        assert "error" not in result
        mock_resolve.assert_awaited_once()
        assert result["query"]["latitude"] == 45.5017


@pytest.mark.asyncio
async def test_qc_hydro_outage_status_validation_error():
    from tools.qc.hydro.outage_status import outage_status

    result = json.loads(await outage_status())
    assert "error" in result
