"""Agrégation calendrier semaine (festivals + evenements + avis)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from helpers.common.calendar_format import CalendarItem, calendar_ascii, google_calendar_url
from helpers.mtl.avis_api import active_on
from helpers.mtl.calendar_adapters import (
    avis_alert_to_item,
    evenement_row_to_item,
    festival_event_to_item,
)
from helpers.mtl.events_common import clamp_limit, validate_optional_iso_date

try:
    _TZ: ZoneInfo | Any = ZoneInfo("America/Toronto")
except ZoneInfoNotFoundError:
    from datetime import timezone

    _TZ = timezone(timedelta(hours=-4))


def monday_of_week(d: date) -> date:
    """Return Monday of the ISO week containing ``d``."""
    return d - timedelta(days=d.weekday())


def resolve_week_start(week_start: str = "") -> date:
    """Parse YYYY-MM-DD Monday or default to current Monday (America/Toronto)."""
    cleaned = validate_optional_iso_date(week_start)
    if cleaned:
        d = date.fromisoformat(cleaned)
        return monday_of_week(d)
    now = datetime.now(_TZ).date()
    return monday_of_week(now)


def week_dates(week_start: date) -> list[date]:
    return [week_start + timedelta(days=i) for i in range(7)]


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


def _festival_active_on(event: dict[str, Any], day: date) -> bool:
    ev_date = event.get("date")
    if not ev_date:
        return False
    try:
        return date.fromisoformat(str(ev_date)[:10]) == day
    except ValueError:
        return False


async def build_calendar_week(
    *,
    week_start: str = "",
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_m: float = 1000.0,
    include_festivals: bool = True,
    include_evenements: bool = True,
    include_avis: bool = True,
    limit_per_source: int = 25,
) -> dict[str, Any]:
    """Fetch and merge calendar items for one week."""
    from helpers.mtl import avis_api, evenements_api, jazzfest_api, piknic_api

    start = resolve_week_start(week_start)
    days = week_dates(start)
    limit = clamp_limit(limit_per_source)
    items: list[CalendarItem] = []
    sources: list[dict[str, Any]] = []
    warnings: list[str] = []

    if include_festivals:
        festival_payloads: list[tuple[str, dict[str, Any]]] = []
        for category, ticket_or_cat in (
            ("off", "off"),
            ("piknic", "piknic"),
            ("petit", "petit"),
            ("free", "free"),
            ("paid", "paid"),
        ):
            try:
                if category in {"off", "piknic", "petit"}:
                    data = await piknic_api.search_events(category=ticket_or_cat, limit=limit)
                else:
                    data = await jazzfest_api.search_events(ticket_kind=ticket_or_cat, limit=limit)
                festival_payloads.append((category, data))
                sources.append(
                    {
                        "kind": "festival",
                        "category": category,
                        "count": data.get("count", 0),
                        "warning": data.get("warning"),
                    }
                )
            except Exception as exc:
                warnings.append(f"Festival {category}: {exc}")
                sources.append({"kind": "festival", "category": category, "error": str(exc)})

        for _category, data in festival_payloads:
            for event in data.get("events") or []:
                if not isinstance(event, dict):
                    continue
                if any(_festival_active_on(event, d) for d in days):
                    items.append(festival_event_to_item(event))

    if include_evenements:
        try:
            # Pull a broader window then filter to week
            eve = await evenements_api.search_evenements(query="", date="", limit=limit)
            # search_evenements already enriches - use raw fields before calendar noise
            # Re-map from events list (titre/dates still present)
            for row in eve.get("events") or []:
                if not isinstance(row, dict):
                    continue
                # Active any day in week
                if any(active_on(d, row.get("date_debut"), row.get("date_fin")) for d in days):
                    items.append(evenement_row_to_item(row))
            sources.append(
                {
                    "kind": "evenement",
                    "portal_used": eve.get("portal_used"),
                    "count": eve.get("count", 0),
                    "warning": eve.get("warning"),
                }
            )
        except Exception as exc:
            warnings.append(f"Evenements publics: {exc}")
            sources.append({"kind": "evenement", "error": str(exc)})

    has_geo = (latitude is not None and longitude is not None) or (address is not None and str(address).strip())
    if include_avis:
        if not has_geo:
            warnings.append("Avis omis: fournir address ou latitude/longitude pour inclure les avis/alertes.")
            sources.append({"kind": "avis", "skipped": True, "reason": "no_geo"})
        else:
            try:
                # Query each day (avis are date-windowed); de-dupe by titre+lien
                seen: set[str] = set()
                avis_count = 0
                for d in days:
                    nearby = await avis_api.list_nearby(
                        date=d.isoformat(),
                        address=address,
                        latitude=latitude,
                        longitude=longitude,
                        radius_m=radius_m,
                        limit=limit,
                    )
                    for alert in nearby.get("alerts") or []:
                        if not isinstance(alert, dict):
                            continue
                        key = f"{alert.get('titre')}|{alert.get('lien')}"
                        if key in seen:
                            continue
                        seen.add(key)
                        items.append(avis_alert_to_item(alert))
                        avis_count += 1
                sources.append({"kind": "avis", "count": avis_count})
            except Exception as exc:
                warnings.append(f"Avis: {exc}")
                sources.append({"kind": "avis", "error": str(exc)})

    # Deduplicate calendar items by (kind, title, start)
    deduped: list[CalendarItem] = []
    seen_items: set[tuple[str, str, str | None]] = set()
    for item in items:
        key = (item.kind, item.title, item.start)
        if key in seen_items:
            continue
        seen_items.add(key)
        deduped.append(item)

    warning = " ".join(warnings) if warnings else None
    return {
        "week_start": start.isoformat(),
        "week_end": (start + timedelta(days=6)).isoformat(),
        "count": len(deduped),
        "items": [_item_dict(i) for i in deduped],
        "calendar_ascii": calendar_ascii(deduped),
        "warning": warning,
        "sources": sources,
    }
