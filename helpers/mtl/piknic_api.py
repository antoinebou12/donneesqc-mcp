"""Client Piknic Électronik - programmation HTML (OfF / Piknic / Petit)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from helpers.common.config import PIKNIC_BASE_URL
from helpers.common.http_client import fetch_text
from helpers.common.urls import PIKNIC_PROGRAM_PATH, join_portal
from helpers.mtl.events_common import (
    clamp_limit,
    events_payload,
    filter_events,
    validate_optional_iso_date,
)

PORTAL_URL = join_portal(PIKNIC_BASE_URL, PIKNIC_PROGRAM_PATH)

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_DATE_RE = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"^(\d{1,2})H(\d{2})$", re.IGNORECASE)
_TRAILING_TIME_RE = re.compile(r"^(.+?)\s*(\d{1,2}H\d{2})$", re.IGNORECASE)
_STAGE_RE = re.compile(r"^(?:SC[ÈE]NE|SCENE|Scène)\b", re.IGNORECASE)

_EXPERIENCE_MAP = {
    "off piknic": "off",
    "of f piknic": "off",
    "piknic": "piknic",
    "petit piknic": "petit",
}

_SKIP_LINES = {
    "billets",
    "achète tes billets",
    "achete tes billets",
    "achète ta passe",
    "achete ta passe",
    "tout piknic",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
}


def _normalize_space(text: str) -> str:
    return " ".join(text.split()).strip()


def _season_year(now: datetime | None = None) -> int:
    """Année de saison : année UTC courante (heuristique documentée)."""
    return (now or datetime.now(UTC)).year


def parse_date_label(label: str, *, year: int | None = None) -> tuple[str | None, str]:
    """Convertit 'Sun, Jul 19' en (ISO date, label normalisé)."""
    cleaned = _normalize_space(label)
    match = _DATE_RE.match(cleaned)
    if not match:
        return None, cleaned
    month = _MONTHS[match.group(1).lower()[:3]]
    day = int(match.group(2))
    y = year if year is not None else _season_year()
    try:
        iso = datetime(y, month, day, tzinfo=UTC).strftime("%Y-%m-%d")
    except ValueError:
        return None, cleaned
    return iso, cleaned


def _experience_category(line: str) -> str | None:
    key = _normalize_space(line).lower().replace("é", "e")
    key = re.sub(r"\s+", " ", key)
    if key in _EXPERIENCE_MAP:
        return _EXPERIENCE_MAP[key]
    # OfF PIKNIC variants
    if "off" in key and "piknic" in key and "petit" not in key:
        return "off"
    if key.startswith("petit") and "piknic" in key:
        return "petit"
    if key == "piknic":
        return "piknic"
    return None


def _is_skip(line: str) -> bool:
    low = _normalize_space(line).lower()
    if low in _SKIP_LINES:
        return True
    return low in {"mayjunjulaugsepoct", "may", "jun", "jul"}


def _is_stage(line: str) -> bool:
    return bool(_STAGE_RE.match(_normalize_space(line)))


def _is_time(line: str) -> bool:
    return bool(_TIME_RE.match(_normalize_space(line)))


def parse_programmation(
    html: str,
    *,
    category: str | None = None,
    query: str = "",
    date: str = "",
    limit: int = 25,
    year: int | None = None,
) -> dict[str, Any]:
    """Parse la page programmation Piknic en événements aplatis par (date, expérience, scène)."""
    limit = clamp_limit(limit)
    soup = BeautifulSoup(html, "html.parser")
    raw_text = soup.get_text("\n", strip=True)
    lines = [_normalize_space(line) for line in raw_text.splitlines() if _normalize_space(line)]

    events: list[dict[str, Any]] = []
    current_date_iso: str | None = None
    current_date_label: str | None = None
    current_category: str | None = None
    current_stage: str | None = None
    current_artists: list[dict[str, str | None]] = []
    pending_artist: str | None = None
    y = year if year is not None else _season_year()

    def flush_stage() -> None:
        nonlocal current_artists, pending_artist
        if pending_artist:
            current_artists.append({"name": pending_artist, "time": None})
            pending_artist = None
        if current_date_label and current_category and current_stage and current_artists:
            events.append(
                {
                    "date": current_date_iso,
                    "date_label": current_date_label,
                    "category": current_category,
                    "venue_or_stage": current_stage,
                    "artists": list(current_artists),
                    "title": None,
                    "ticket_url": None,
                    "url": PORTAL_URL,
                }
            )
        current_artists = []

    for line in lines:
        if _is_skip(line):
            continue

        iso, label = parse_date_label(line, year=y)
        if iso is not None:
            flush_stage()
            current_date_iso = iso
            current_date_label = label
            current_category = None
            current_stage = None
            continue

        exp = _experience_category(line)
        if exp is not None:
            flush_stage()
            current_category = exp
            current_stage = None
            continue

        if _is_stage(line):
            flush_stage()
            current_stage = _normalize_space(line)
            continue

        if _is_time(line) and pending_artist:
            current_artists.append({"name": pending_artist, "time": _normalize_space(line).upper()})
            pending_artist = None
            continue

        # Artist name (or leftover chrome); support "Name19H30" / "Name 19H30"
        if current_category and current_stage and current_date_label:
            trailing = _TRAILING_TIME_RE.match(_normalize_space(line))
            if trailing and not _is_stage(trailing.group(1)):
                name = _normalize_space(trailing.group(1))
                time_s = trailing.group(2).upper()
                if pending_artist:
                    current_artists.append({"name": pending_artist, "time": None})
                    pending_artist = None
                if name:
                    current_artists.append({"name": name, "time": time_s})
                continue
            if pending_artist:
                current_artists.append({"name": pending_artist, "time": None})
            pending_artist = _normalize_space(line)

    flush_stage()

    # Ticket URLs best-effort from anchors
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href")
        if not isinstance(href, str):
            continue
        text = _normalize_space(anchor.get_text(" ", strip=True)).lower()
        if "billet" in text or "ticket" in text:
            abs_url = urljoin(PIKNIC_BASE_URL.rstrip("/") + "/", href)
            for event in events:
                if event.get("ticket_url") is None:
                    event["ticket_url"] = abs_url

    filtered = filter_events(events, query=query, date=date, category=category)
    return events_payload(
        events=events,
        filtered=filtered,
        query=query,
        date=date,
        category=category or "",
        limit=limit,
        empty_parse_warning="Aucun evenement parse sur la page Piknic (hors saison ou changement de mise en page).",
    )


async def search_events(
    *,
    category: str,
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Telecharge et filtre la programmation Piknic pour une experience."""
    date = validate_optional_iso_date(date)

    url = f"{PIKNIC_BASE_URL.rstrip('/')}{PIKNIC_PROGRAM_PATH}"
    html = await fetch_text(url)
    return parse_programmation(
        html,
        category=category,
        query=query,
        date=date,
        limit=limit,
    )
