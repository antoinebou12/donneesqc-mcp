"""Tests de l'enveloppe de réponse `_meta`."""

import json

from helpers.common.response import DISCLAIMER, error, ok


def test_ok_adds_meta():
    raw = ok(
        {"count": 1},
        source="donnees_quebec",
        portal_url="https://www.donneesquebec.ca/recherche/dataset/x",
        license="CC-BY-4.0",
        retrieved_at="2026-07-16T20:00:00Z",
        metadata_modified="2026-01-01T00:00:00",
    )
    data = json.loads(raw)
    assert data["count"] == 1
    assert data["_meta"]["source"] == "donnees_quebec"
    assert data["_meta"]["license"] == "CC-BY-4.0"
    assert data["_meta"]["disclaimer"] == DISCLAIMER
    assert data["_meta"]["retrieved_at"] == "2026-07-16T20:00:00Z"


def test_error_has_no_meta():
    data = json.loads(error("boom", code="sql_invalid"))
    assert data == {"error": "boom", "code": "sql_invalid"}
    assert "_meta" not in data
