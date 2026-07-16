"""Helpers partagés pour les scrapers d'événements (Piknic / Jazz Fest)."""

from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING, Any

from helpers.common.response import ok
from helpers.common.tool_call import run_tool
from helpers.mtl.calendar_adapters import enrich_list_payload, festival_event_to_item

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


def clamp_limit(limit: int, *, max_limit: int = 50) -> int:
    """Clamp event list size to ``[1, max_limit]``."""
    return max(1, min(int(limit), max_limit))


def validate_optional_iso_date(date: str) -> str:
    """Return stripped YYYY-MM-DD or empty string; raise ValueError if invalid."""
    if not date or not date.strip():
        return ""
    cleaned = date.strip()
    try:
        date_type.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError("Date invalide (utilisez YYYY-MM-DD).") from exc
    return cleaned


def event_matches_query(event: dict[str, Any], query: str) -> bool:
    """True if query is a substring of venue/title/date_label/artists haystack."""
    q = query.strip().lower()
    if not q:
        return True
    hay = " ".join(
        [
            event.get("venue_or_stage") or "",
            event.get("title") or "",
            event.get("date_label") or "",
            *[a.get("name") or "" for a in event.get("artists") or []],
        ]
    ).lower()
    return q in hay


def filter_events(
    events: list[dict[str, Any]],
    *,
    query: str = "",
    date: str = "",
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Filter by optional category, ISO date, and free-text query."""
    filtered = events
    if category:
        filtered = [e for e in filtered if e.get("category") == category]
    if date:
        filtered = [e for e in filtered if e.get("date") == date]
    if query and query.strip():
        filtered = [e for e in filtered if event_matches_query(e, query)]
    return filtered


def events_payload(
    *,
    events: list[dict[str, Any]],
    filtered: list[dict[str, Any]],
    query: str,
    date: str,
    category: str,
    limit: int,
    empty_parse_warning: str,
    empty_filter_warning: str = "Aucun evenement ne correspond aux filtres.",
) -> dict[str, Any]:
    """Build the standard festival tool response dict."""
    capped = filtered[:limit]
    warning = None
    if not filtered and not events:
        warning = empty_parse_warning
    elif not filtered:
        warning = empty_filter_warning
    return {
        "query": query or "",
        "date": date or "",
        "category": category,
        "count": len(capped),
        "events": capped,
        "warning": warning,
    }


async def run_festival_tool(
    label: str,
    fetch: Callable[[], Awaitable[dict[str, Any]]],
    *,
    source: str,
    portal_url: str,
    generic_error: str,
) -> str:
    """Execute a festival search helper and wrap with ok/run_tool + calendar fields."""

    async def _run() -> str:
        data = await fetch()
        data = enrich_list_payload(data, list_key="events", mapper=festival_event_to_item)
        return ok(data, source=source, portal_url=portal_url)

    return await run_tool(label, _run, generic_error=generic_error)
