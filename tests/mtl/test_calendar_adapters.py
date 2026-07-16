"""Tests adapters calendrier MTL."""

from __future__ import annotations

from helpers.mtl.calendar_adapters import (
    avis_alert_to_item,
    enrich_list_payload,
    evenement_row_to_item,
    festival_event_to_item,
)


def test_festival_event_with_time() -> None:
    event = {
        "date": "2026-07-19",
        "category": "piknic",
        "venue_or_stage": "SCÈNE FIZZ",
        "artists": [{"name": "Mandragora", "time": "19H30"}],
        "title": None,
        "ticket_url": "https://example.com/tix",
        "url": "https://piknicelectronik.com/fr/programmation",
    }
    item = festival_event_to_item(event)
    assert item.kind == "festival"
    assert item.source == "piknic"
    assert item.start == "2026-07-19T19:30:00"
    assert item.all_day is False
    assert item.title == "Mandragora"
    assert item.place == "SCÈNE FIZZ"


def test_festival_event_date_only() -> None:
    event = {
        "date": "2026-07-19",
        "category": "free",
        "venue_or_stage": "Scène TD",
        "artists": [{"name": "Patrick Watson", "time": None}],
        "title": "Patrick Watson",
        "url": None,
        "ticket_url": None,
    }
    item = festival_event_to_item(event)
    assert item.start == "2026-07-19"
    assert item.all_day is True
    assert item.source == "jazzfest"


def test_avis_alert_to_item() -> None:
    alert = {
        "titre": "Entrave proche",
        "type": "Circulation et transport",
        "date_debut": "2026-06-01T12:00:00",
        "date_fin": "2026-08-01T12:00:00",
        "lien": "https://montreal.ca/alertes/exemple",
    }
    item = avis_alert_to_item(alert)
    assert item.kind == "avis"
    assert item.start == "2026-06-01T12:00:00"
    assert item.end == "2026-08-01T12:00:00"
    assert item.url == "https://montreal.ca/alertes/exemple"


def test_evenement_row_to_item() -> None:
    row = {
        "titre": "Festival culturel",
        "type_evenement": "Festival",
        "date_debut": "2026-07-19T10:00:00",
        "date_fin": "2026-07-19T18:00:00",
        "emplacement": "Parc La Fontaine",
        "url_fiche": "https://montreal.ca/lieux/x",
    }
    item = evenement_row_to_item(row)
    assert item.kind == "evenement"
    assert item.title == "Festival culturel"
    assert item.place == "Parc La Fontaine"
    assert item.start == "2026-07-19T10:00:00"
    assert item.all_day is False


def test_enrich_list_payload_festivals() -> None:
    payload = {
        "events": [
            {
                "date": "2026-07-19",
                "category": "piknic",
                "venue_or_stage": "SCÈNE FIZZ",
                "artists": [{"name": "Mandragora", "time": "19H30"}],
                "title": None,
                "url": "https://example.com",
                "ticket_url": None,
            }
        ],
        "count": 1,
    }
    out = enrich_list_payload(payload, list_key="events", mapper=festival_event_to_item)
    assert out["events"][0]["google_calendar_url"]
    assert "Mandragora" in out["calendar_ascii"]
