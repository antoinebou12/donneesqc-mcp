"""Tests pour helpers.common.calendar_format."""

from __future__ import annotations

from helpers.common.calendar_format import (
    CalendarItem,
    attach_calendar,
    calendar_ascii,
    google_calendar_url,
)


def test_google_calendar_url_timed() -> None:
    item = CalendarItem(
        kind="festival",
        start="2026-07-19T19:30:00",
        end=None,
        all_day=False,
        title="Mandragora",
        place="SCÈNE FIZZ",
        url="https://piknicelectronik.com/fr/programmation",
        source="piknic",
    )
    url = google_calendar_url(item)
    assert url is not None
    assert url.startswith("https://calendar.google.com/calendar/render?")
    assert "action=TEMPLATE" in url
    assert "text=Mandragora" in url
    assert "dates=20260719T193000%2F20260719T203000" in url or "dates=20260719T193000/20260719T203000" in url
    assert "location=" in url
    assert "details=" in url


def test_google_calendar_url_all_day() -> None:
    item = CalendarItem(
        kind="avis",
        start="2026-07-19",
        end="2026-07-21",
        all_day=True,
        title="Circulation Plateau",
        place=None,
        url="https://montreal.ca/avis/1",
        source="avis_alertes",
    )
    url = google_calendar_url(item)
    assert url is not None
    # Google all-day end is exclusive → 20260722
    assert "dates=20260719%2F20260722" in url or "dates=20260719/20260722" in url


def test_google_calendar_url_undated_returns_none() -> None:
    item = CalendarItem(
        kind="festival",
        start=None,
        end=None,
        all_day=False,
        title="Unknown",
        place=None,
        url=None,
        source="piknic",
    )
    assert google_calendar_url(item) is None


def test_calendar_ascii_groups_by_day() -> None:
    items = [
        CalendarItem(
            kind="festival",
            start="2026-07-19T19:30:00",
            end=None,
            all_day=False,
            title="Mandragora",
            place="SCÈNE FIZZ",
            url=None,
            source="piknic",
        ),
        CalendarItem(
            kind="avis",
            start="2026-07-19",
            end="2026-07-19",
            all_day=True,
            title="Circulation Plateau",
            place=None,
            url=None,
            source="avis_alertes",
        ),
        CalendarItem(
            kind="festival",
            start="2026-07-20T14:00:00",
            end=None,
            all_day=False,
            title="Jazz act",
            place="Scène",
            url=None,
            source="jazzfest",
        ),
    ]
    text = calendar_ascii(items)
    assert "=== Dim 19 juil. 2026 ===" in text
    assert "19h30" in text
    assert "Mandragora" in text
    assert "all-day" in text
    assert "Circulation Plateau" in text
    assert "=== Lun 20 juil. 2026 ===" in text
    assert "Jazz act" in text


def test_calendar_ascii_omits_undated() -> None:
    items = [
        CalendarItem(
            kind="festival",
            start=None,
            end=None,
            all_day=False,
            title="No date",
            place=None,
            url=None,
            source="piknic",
        ),
    ]
    assert calendar_ascii(items) == ""


def test_attach_calendar_adds_fields() -> None:
    payload = {
        "events": [
            {
                "date": "2026-07-19",
                "title": "Show",
                "google_calendar_url": None,  # overwritten
            }
        ]
    }
    items = [
        CalendarItem(
            kind="festival",
            start="2026-07-19T19:30:00",
            end=None,
            all_day=False,
            title="Show",
            place=None,
            url=None,
            source="piknic",
        ),
    ]
    out = attach_calendar(payload, items, list_key="events")
    assert out["events"][0]["google_calendar_url"]
    assert "calendar_ascii" in out
    assert "Show" in out["calendar_ascii"]
