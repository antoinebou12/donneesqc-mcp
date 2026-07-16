"""Événements « bientôt » - festivals + civiques dans une fenêtre horaire."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from helpers.common.calendar_format import CalendarItem, calendar_ascii, google_calendar_url
from helpers.common.context import resolve_now, resolve_timezone, resolve_user_location
from helpers.mtl.calendar_adapters import evenement_row_to_item, festival_event_to_item
from helpers.mtl.events_common import clamp_limit


def _parse_item_start(item: CalendarItem, tz: Any) -> datetime | None:
    if not item.start:
        return None
    raw = str(item.start)
    try:
        if "T" in raw:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=tz)
            return dt.astimezone(tz)
        day = date.fromisoformat(raw[:10])
        return datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=tz)
    except ValueError:
        return None


def _item_in_window(item: CalendarItem, *, start: datetime, end: datetime, tz: Any) -> bool:
    parsed = _parse_item_start(item, tz)
    if parsed is None:
        return False
    # All-day / date-only: keep if calendar day overlaps [start.date, end.date]
    if item.all_day or "T" not in str(item.start or ""):
        day = parsed.date()
        return start.date() <= day <= end.date()
    return start <= parsed <= end


def _evenement_matches_location(row: dict[str, Any], *, haystack: str) -> bool:
    if not haystack:
        return True
    blob = " ".join(
        [
            str(row.get("arrondissement") or ""),
            str(row.get("emplacement") or ""),
            str(row.get("adresse_principale") or ""),
        ]
    ).lower()
    return any(token in blob for token in haystack.split() if len(token) >= 3)


def _item_dict(item: CalendarItem) -> dict[str, Any]:
    return {
        "kind": item.kind,
        "start": item.start,
        "end": item.end,
        "all_day": item.all_day,
        "title": item.title,
        "place": item.place,
        "url": item.url,
        "source": item.source,
        "google_calendar_url": google_calendar_url(item),
    }


async def build_events_soon(
    *,
    query: str = "",
    hours: float = 24.0,
    date: str = "",
    timezone_name: str = "",
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Merge festival + civic events in [now, now+hours]."""
    from helpers.mtl import evenements_api, jazzfest_api, piknic_api

    if hours <= 0 or hours > 168:
        msg = "hours doit etre entre 0 (exclus) et 168."
        raise ValueError(msg)

    now_info = resolve_now(date=date or None, timezone_name=timezone_name or None)
    tz = resolve_timezone(now_info["timezone"])
    window_start = datetime.fromisoformat(now_info["datetime_iso"])
    if window_start.tzinfo is None:
        window_start = window_start.replace(tzinfo=tz)
    window_end = window_start + timedelta(hours=float(hours))
    lim = clamp_limit(limit)

    location: dict[str, Any] | None = None
    location_filter = "none"
    location_haystack = ""
    has_loc_input = (latitude is not None and longitude is not None) or bool(address and address.strip())
    if has_loc_input:
        try:
            location = await resolve_user_location(
                latitude=latitude,
                longitude=longitude,
                address=address,
                allow_client_ip=False,
            )
            location_filter = "approx"
            parts = [
                str(location.get("city") or ""),
                str(location.get("resolved_address") or address or ""),
            ]
            location_haystack = " ".join(parts).lower()
        except ValueError:
            location = None
            location_filter = "none"

    items: list[CalendarItem] = []
    sources: list[dict[str, Any]] = []
    warnings: list[str] = []

    # Festivals - fetch without date filter, filter by window locally
    for label, fetch in (
        ("piknic_off", lambda: piknic_api.search_events(category="off", query=query, date="", limit=50)),
        ("piknic", lambda: piknic_api.search_events(category="piknic", query=query, date="", limit=50)),
        ("piknic_petit", lambda: piknic_api.search_events(category="petit", query=query, date="", limit=50)),
        ("jazzfest_free", lambda: jazzfest_api.search_events(ticket_kind="free", query=query, date="", limit=50)),
        ("jazzfest_paid", lambda: jazzfest_api.search_events(ticket_kind="paid", query=query, date="", limit=50)),
    ):
        try:
            payload = await fetch()
            events = payload.get("events") or []
            count_before = 0
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                item = festival_event_to_item(ev)
                if _item_in_window(item, start=window_start, end=window_end, tz=tz):
                    items.append(item)
                    count_before += 1
            sources.append({"kind": "festival", "label": label, "matched": count_before})
            if payload.get("warning"):
                warnings.append(f"{label}: {payload['warning']}")
        except Exception as exc:
            warnings.append(f"{label}: {exc}")
            sources.append({"kind": "festival", "label": label, "error": str(exc)})

    # Civic events - search without date, filter window + optional place text
    try:
        eve = await evenements_api.search_evenements(query=query, date="", limit=200)
        matched = 0
        for row in eve.get("events") or []:
            if not isinstance(row, dict):
                continue
            if (
                location_filter == "approx"
                and location_haystack
                and not _evenement_matches_location(row, haystack=location_haystack)
            ):
                continue
            item = evenement_row_to_item(row)
            if _item_in_window(item, start=window_start, end=window_end, tz=tz):
                items.append(item)
                matched += 1
        sources.append({"kind": "evenement", "matched": matched})
        if eve.get("warning"):
            warnings.append(str(eve["warning"]))
    except Exception as exc:
        warnings.append(f"Evenements publics: {exc}")
        sources.append({"kind": "evenement", "error": str(exc)})

    # Deduplicate
    seen: set[tuple[str, str, str | None]] = set()
    deduped: list[CalendarItem] = []
    for item in items:
        key = (item.kind, item.title, item.start)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    def _sort_key(it: CalendarItem) -> tuple[str, str]:
        return (str(it.start or ""), it.title)

    deduped.sort(key=_sort_key)
    capped = deduped[:lim]

    return {
        "query": query or "",
        "hours": float(hours),
        "window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
            "timezone": now_info["timezone"],
            "time_source": now_info["time_source"],
        },
        "location": location,
        "location_filter": location_filter,
        "count": len(capped),
        "items": [_item_dict(i) for i in capped],
        "calendar_ascii": calendar_ascii(capped),
        "sources": sources,
        "warning": " | ".join(warnings) if warnings else None,
    }
