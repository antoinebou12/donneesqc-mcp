"""Adapters: domain rows → CalendarItem for GCal / day-agenda ASCII."""

from __future__ import annotations

import re
from typing import Any

from helpers.common.calendar_format import CalendarItem, attach_calendar

_TIME_RE = re.compile(r"^(\d{1,2})[hH:](\d{2})$")
_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _parse_fr_time(raw: str | None) -> tuple[int, int] | None:
    if not raw:
        return None
    match = _TIME_RE.match(str(raw).strip())
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _iso_date(raw: Any) -> str | None:
    if raw is None or raw == "":
        return None
    text = str(raw).strip()
    match = _DATE_RE.match(text)
    return match.group(1) if match else None


def festival_event_to_item(event: dict[str, Any]) -> CalendarItem:
    """Map Piknic / Jazz Fest event object to CalendarItem."""
    category = str(event.get("category") or "")
    source = {
        "piknic": "piknic",
        "off": "off",
        "petit": "petit",
        "free": "jazzfest",
        "paid": "jazzfest",
    }.get(category, category or "festival")

    artists = event.get("artists") or []
    first_time: str | None = None
    names: list[str] = []
    if isinstance(artists, list):
        for artist in artists:
            if not isinstance(artist, dict):
                continue
            name = artist.get("name")
            if name:
                names.append(str(name))
            if first_time is None and artist.get("time"):
                first_time = str(artist["time"])

    title = event.get("title")
    if not title and names:
        title = names[0] if len(names) == 1 else ", ".join(names[:3])
    if not title:
        title = "Spectacle"

    date_iso = _iso_date(event.get("date"))
    start: str | None = None
    all_day = True
    if date_iso:
        parsed_time = _parse_fr_time(first_time)
        if parsed_time:
            h, m = parsed_time
            start = f"{date_iso}T{h:02d}:{m:02d}:00"
            all_day = False
        else:
            start = date_iso

    url = event.get("ticket_url") or event.get("url")
    return CalendarItem(
        kind="festival",
        start=start,
        end=None,
        all_day=all_day,
        title=str(title),
        place=str(event["venue_or_stage"]) if event.get("venue_or_stage") else None,
        url=str(url) if url else None,
        source=source,
    )


def avis_alert_to_item(alert: dict[str, Any]) -> CalendarItem:
    """Map avis/alertes row to CalendarItem (date window, typically all-day)."""
    start = alert.get("date_debut")
    end = alert.get("date_fin")
    start_s = str(start) if start else None
    end_s = str(end) if end else None
    # Prefer all-day agenda for civic windows unless we keep full ISO datetimes
    all_day = True
    if start_s and "T" in start_s:
        # Keep timed start for GCal accuracy but mark all_day False only if time not midnight
        all_day = start_s.endswith("T00:00:00") or "T00:00:00" in start_s[:19]
    titre = alert.get("titre") or "Avis"
    type_lbl = alert.get("type")
    title = f"{titre} · {type_lbl}" if type_lbl else str(titre)
    return CalendarItem(
        kind="avis",
        start=start_s,
        end=end_s,
        all_day=all_day,
        title=str(title),
        place=None,
        url=str(alert["lien"]) if alert.get("lien") else None,
        source="avis_alertes",
    )


def evenement_row_to_item(row: dict[str, Any]) -> CalendarItem:
    """Map vmtl-evenements-publics datastore row to CalendarItem."""
    start = row.get("date_debut") or row.get("date")
    end = row.get("date_fin")
    start_s = str(start) if start else None
    end_s = str(end) if end else None
    all_day = True
    if start_s and "T" in start_s and not start_s.startswith(start_s[:10] + "T00:00"):
        # has a non-midnight time
        time_part = start_s.split("T", 1)[-1][:8]
        all_day = time_part in {"00:00:00", "00:00:00Z", ""}
    titre = row.get("titre") or row.get("title") or "Événement"
    place = row.get("emplacement") or row.get("adresse_principale") or row.get("arrondissement")
    url = row.get("url_fiche") or row.get("url")
    return CalendarItem(
        kind="evenement",
        start=start_s,
        end=end_s,
        all_day=all_day,
        title=str(titre),
        place=str(place) if place else None,
        url=str(url) if url else None,
        source="evenements_publics",
    )


def enrich_list_payload(
    payload: dict[str, Any],
    *,
    list_key: str,
    mapper: Any,
) -> dict[str, Any]:
    """Map each row in payload[list_key] and attach calendar fields."""
    rows = payload.get(list_key) or []
    if not isinstance(rows, list):
        rows = []
    items = [mapper(row) if isinstance(row, dict) else festival_event_to_item({}) for row in rows]
    return attach_calendar(payload, items, list_key=list_key)
