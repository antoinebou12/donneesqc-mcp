"""Unit tests for festival event filter helpers."""

from __future__ import annotations

import pytest

from helpers.mtl.events_common import (
    clamp_limit,
    event_matches_query,
    events_payload,
    filter_events,
    validate_optional_iso_date,
)
from helpers.mtl.geo import validate_wgs84


def test_clamp_and_date():
    assert clamp_limit(0) == 1
    assert clamp_limit(99) == 50
    assert validate_optional_iso_date("") == ""
    assert validate_optional_iso_date("2026-07-19") == "2026-07-19"
    with pytest.raises(ValueError, match="Date invalide"):
        validate_optional_iso_date("19-07-2026")


def test_filter_events_and_payload():
    events = [
        {
            "category": "off",
            "date": "2026-07-19",
            "title": "Mandragora",
            "venue_or_stage": "Main",
            "artists": [{"name": "Mandragora"}],
            "date_label": "Sun",
        },
        {
            "category": "piknic",
            "date": "2026-07-20",
            "title": "Other",
            "venue_or_stage": "Side",
            "artists": [],
            "date_label": "Mon",
        },
    ]
    filtered = filter_events(events, query="mandra", date="2026-07-19", category="off")
    assert len(filtered) == 1
    assert event_matches_query(filtered[0], "main")
    payload = events_payload(
        events=events,
        filtered=filtered,
        query="mandra",
        date="2026-07-19",
        category="off",
        limit=10,
        empty_parse_warning="empty",
    )
    assert payload["count"] == 1
    assert payload["warning"] is None


def test_validate_wgs84():
    validate_wgs84(45.5, -73.5)
    with pytest.raises(ValueError, match="latitude"):
        validate_wgs84(91.0, -73.5)
