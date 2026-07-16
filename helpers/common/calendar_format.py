"""Day-agenda ASCII calendars and Google Calendar TEMPLATE links.

Chat may paste ``calendar_ascii`` for schedules. Rankings still use markdown
tables - do not use ASCII bar charts (see skills/donneesqc-mcp/SKILL.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    _TZ: ZoneInfo | timezone = ZoneInfo("America/Toronto")
except ZoneInfoNotFoundError:
    # Windows / minimal images without tzdata: EDT fallback (UTC-4)
    _TZ = timezone(timedelta(hours=-4))

_MAX_ASCII_LINES = 40

_WEEKDAYS_FR = ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")
_MONTHS_FR = (
    "janv.",
    "févr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "août",
    "sept.",
    "oct.",
    "nov.",
    "déc.",
)


@dataclass(frozen=True, slots=True)
class CalendarItem:
    """Normalized event for calendar presentation."""

    kind: str
    start: str | None
    end: str | None
    all_day: bool
    title: str
    place: str | None
    url: str | None
    source: str


def _parse_start(raw: str | None) -> datetime | date | None:
    if not raw:
        return None
    text = str(raw).strip().replace("Z", "")
    if "T" in text:
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=_TZ)
        return dt.astimezone(_TZ)
    if len(text) >= 10:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def _as_local_date(value: datetime | date) -> date:
    if isinstance(value, datetime):
        return value.astimezone(_TZ).date() if value.tzinfo else value.replace(tzinfo=_TZ).date()
    return value


def _default_end_timed(start: datetime) -> datetime:
    return start + timedelta(hours=1)


def _format_gcal_dates(item: CalendarItem) -> str | None:
    parsed = _parse_start(item.start)
    if parsed is None:
        return None

    if item.all_day or (isinstance(parsed, date) and not isinstance(parsed, datetime)):
        start_d = _as_local_date(parsed)
        end_parsed = _parse_start(item.end) if item.end else None
        if end_parsed is not None:
            end_d = _as_local_date(end_parsed) + timedelta(days=1)  # exclusive
        else:
            end_d = start_d + timedelta(days=1)
        return f"{start_d.strftime('%Y%m%d')}/{end_d.strftime('%Y%m%d')}"

    assert isinstance(parsed, datetime)
    start_dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=_TZ)
    end_parsed = _parse_start(item.end) if item.end else None
    if isinstance(end_parsed, datetime):
        end_dt = end_parsed if end_parsed.tzinfo else end_parsed.replace(tzinfo=_TZ)
    elif isinstance(end_parsed, date):
        end_dt = datetime(end_parsed.year, end_parsed.month, end_parsed.day, 23, 59, 59, tzinfo=_TZ)
    else:
        end_dt = _default_end_timed(start_dt)
    # Wall-time form without Z (America/Toronto heuristic)
    start_naive = start_dt.astimezone(_TZ).replace(tzinfo=None)
    end_naive = end_dt.astimezone(_TZ).replace(tzinfo=None)
    return f"{start_naive.strftime('%Y%m%dT%H%M%S')}/{end_naive.strftime('%Y%m%dT%H%M%S')}"


def google_calendar_url(item: CalendarItem) -> str | None:
    """Build a Google Calendar TEMPLATE URL, or None if no parseable start."""
    dates = _format_gcal_dates(item)
    if dates is None:
        return None
    params: dict[str, str] = {
        "action": "TEMPLATE",
        "text": item.title or "Événement",
        "dates": dates,
    }
    details_parts: list[str] = []
    if item.source:
        details_parts.append(f"Source: {item.source}")
    if item.url:
        details_parts.append(item.url)
    if details_parts:
        params["details"] = "\n".join(details_parts)
    if item.place:
        params["location"] = item.place
    return "https://calendar.google.com/calendar/render?" + urlencode(params, quote_via=quote)


def _day_header(d: date) -> str:
    wd = _WEEKDAYS_FR[d.weekday()]
    month = _MONTHS_FR[d.month - 1]
    return f"=== {wd} {d.day} {month} {d.year} ==="


def _time_label(item: CalendarItem, parsed: datetime | date) -> str:
    if item.all_day or (isinstance(parsed, date) and not isinstance(parsed, datetime)):
        return "all-day"
    assert isinstance(parsed, datetime)
    local = parsed.astimezone(_TZ) if parsed.tzinfo else parsed.replace(tzinfo=_TZ)
    return f"{local.hour:02d}h{local.minute:02d}"


def _line_for_item(item: CalendarItem, parsed: datetime | date) -> str:
    time_lbl = _time_label(item, parsed)
    kind_label = {
        "festival": item.source.capitalize() if item.source else "Festival",
        "avis": "Avis",
        "evenement": "Événement",
    }.get(item.kind, item.kind.capitalize() if item.kind else "Événement")
    if item.kind == "festival" and item.source:
        kind_label = {
            "piknic": "Piknic",
            "jazzfest": "Jazz Fest",
            "off": "OfF Piknic",
            "petit": "Petit Piknic",
        }.get(item.source, item.source.capitalize())
    body = f"{kind_label} · {item.title}"
    if item.place:
        body = f"{body} @ {item.place}"
    return f"{time_lbl}  {body}"


def calendar_ascii(items: list[CalendarItem], *, max_lines: int = _MAX_ASCII_LINES) -> str:
    """Render a day-agenda ASCII calendar (layout C)."""
    dated: list[tuple[date, datetime | date, CalendarItem]] = []
    for item in items:
        parsed = _parse_start(item.start)
        if parsed is None:
            continue
        dated.append((_as_local_date(parsed), parsed, item))
    if not dated:
        return ""

    def _sort_key(t: tuple[date, datetime | date, CalendarItem]) -> tuple[date, int, datetime | date]:
        day, parsed, item = t
        all_day = item.all_day or (isinstance(parsed, date) and not isinstance(parsed, datetime))
        return (day, 0 if all_day else 1, parsed)

    dated.sort(key=_sort_key)

    lines: list[str] = []
    current_day: date | None = None
    omitted = 0
    for day, parsed, item in dated:
        header = _day_header(day)
        line = _line_for_item(item, parsed)
        needed = (1 if day != current_day else 0) + 1
        if len(lines) + needed > max_lines:
            omitted += 1
            continue
        if day != current_day:
            if lines:
                lines.append("")
            lines.append(header)
            current_day = day
        lines.append(line)

    if omitted:
        lines.append(f"… (+{omitted})")
    return "\n".join(lines)


def attach_calendar(
    payload: dict[str, Any],
    items: list[CalendarItem],
    *,
    list_key: str,
) -> dict[str, Any]:
    """Add ``google_calendar_url`` on each list row and ``calendar_ascii`` on payload."""
    out = dict(payload)
    rows = list(out.get(list_key) or [])
    enriched: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        row_out = dict(row) if isinstance(row, dict) else {"value": row}
        item = items[idx] if idx < len(items) else None
        if item is not None:
            row_out["google_calendar_url"] = google_calendar_url(item)
        else:
            row_out.setdefault("google_calendar_url", None)
        enriched.append(row_out)
    out[list_key] = enriched
    out["calendar_ascii"] = calendar_ascii(items)
    return out
