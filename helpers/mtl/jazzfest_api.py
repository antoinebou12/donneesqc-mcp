"""Client Festival International de Jazz de Montréal - horaire Free / Paid."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from helpers.common.config import JAZZFEST_BASE_URL
from helpers.common.http_client import fetch_text
from helpers.common.urls import JAZZFEST_PROGRAM_PATH, join_portal
from helpers.mtl.events_common import (
    clamp_limit,
    events_payload,
    filter_events,
    validate_optional_iso_date,
)

# FR schedule page (Next.js; may be a JS shell - v1 returns warning if empty).
PORTAL_URL = join_portal(JAZZFEST_BASE_URL, JAZZFEST_PROGRAM_PATH)

_DATE_ISO_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")
_DATE_LABEL_RE = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|lun|mar|mer|jeu|ven|sam|dim)"
    r"[a-zéû.]*\s+\d{1,2}\s+\w+",
    re.IGNORECASE,
)
_TIME_RE = re.compile(r"\b(\d{1,2}[hH:]\d{2})\b")

_FREE_MARKERS = ("gratuit", "free", "outdoor", "plein air")
_PAID_MARKERS = ("payant", "paid", "indoor", "billets", "ticket")


def _normalize_space(text: str) -> str:
    return " ".join(text.split()).strip()


def _looks_like_js_shell(html: str, soup: BeautifulSoup) -> bool:
    text = _normalize_space(soup.get_text(" ", strip=True))
    if len(text) < 80 and ("__NEXT_DATA__" in html or "/_next/" in html):
        return True
    return bool("NEXT_REDIRECT" in html and len(text) < 200)


def parse_program(
    html: str,
    *,
    ticket_kind: str,
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Parse Free ou Paid depuis HTML structure (sections + articles).

    `ticket_kind` is ``free`` or ``paid``.
    """
    if ticket_kind not in {"free", "paid"}:
        raise ValueError("ticket_kind must be 'free' or 'paid'")

    limit = clamp_limit(limit)
    soup = BeautifulSoup(html, "html.parser")
    category = ticket_kind
    events: list[dict[str, Any]] = []

    if _looks_like_js_shell(html, soup):
        return {
            "query": query or "",
            "date": date or "",
            "category": category,
            "count": 0,
            "events": [],
            "warning": (
                "La page Jazz Fest semble rendue cote client (JS). Aucun evenement extractible en HTML statique (v1)."
            ),
        }

    # Prefer explicit section markers in fixtures / static HTML
    section_selector = (
        '[data-ticket="free"], section.free, .program-free, #gratuit, #free'
        if ticket_kind == "free"
        else '[data-ticket="paid"], section.paid, .program-paid, #payant, #paid'
    )
    sections = soup.select(section_selector)
    roots = sections if sections else [soup]

    for root in roots:
        # If we got the whole soup and both kinds exist, skip opposite markers
        for article in root.select("article, .event, .concert, li.event"):
            ticket_raw = article.get("data-ticket")
            ticket_attr = (ticket_raw if isinstance(ticket_raw, str) else "").lower()
            blob = _normalize_space(article.get_text(" ", strip=True)).lower()
            if ticket_kind == "free":
                if ticket_attr == "paid" or (
                    any(m in blob for m in _PAID_MARKERS)
                    and not any(m in blob for m in _FREE_MARKERS)
                    and ticket_attr != "free"
                ):
                    if sections:
                        pass
                    elif ticket_attr == "paid":
                        continue
            else:
                if ticket_attr == "free":
                    continue

            title_el = article.find(["h2", "h3", "h4", "a"])
            title = _normalize_space(title_el.get_text(" ", strip=True)) if title_el else ""
            if not title:
                continue

            date_iso = article.get("data-date") if isinstance(article.get("data-date"), str) else None
            date_label = None
            time_s = None
            venue = None

            for el in article.select("[data-date], .date, time"):
                raw = el.get("datetime") or el.get("data-date") or el.get_text(" ", strip=True)
                raw = _normalize_space(str(raw))
                if _DATE_ISO_RE.match(raw):
                    date_iso = raw
                elif _DATE_LABEL_RE.match(raw) or raw:
                    date_label = raw

            for el in article.select(".time, [data-time]"):
                data_time = el.get("data-time")
                raw = _normalize_space(data_time if isinstance(data_time, str) else el.get_text(" ", strip=True))
                m = _TIME_RE.search(raw)
                if m:
                    time_s = m.group(1).upper().replace(":", "H")

            for el in article.select(".venue, .stage, [data-venue]"):
                data_venue = el.get("data-venue")
                venue = _normalize_space(data_venue if isinstance(data_venue, str) else el.get_text(" ", strip=True))
                if venue:
                    break

            ticket_url = None
            for link in article.find_all("a", href=True):
                href = link.get("href")
                if isinstance(href, str) and href and not href.startswith("#"):
                    ticket_url = urljoin(JAZZFEST_BASE_URL.rstrip("/") + "/", href)
                    break

            if date_iso is None and date_label and _DATE_ISO_RE.match(date_label):
                date_iso = date_label

            events.append(
                {
                    "date": date_iso,
                    "date_label": date_label,
                    "category": category,
                    "venue_or_stage": venue,
                    "artists": [{"name": title, "time": time_s}],
                    "title": title,
                    "ticket_url": ticket_url,
                    "url": PORTAL_URL,
                }
            )

    # Fallback: line-oriented sections headed by Gratuit / Payant
    if not events:
        events = _parse_text_sections(soup, ticket_kind=ticket_kind)

    filtered = filter_events(events, query=query, date=date)
    return events_payload(
        events=events,
        filtered=filtered,
        query=query,
        date=date,
        category=category,
        limit=limit,
        empty_parse_warning=(
            "Aucun evenement parse sur la page Jazz Fest (layout JS, hors saison, ou changement de mise en page)."
        ),
    )


def _parse_text_sections(soup: BeautifulSoup, *, ticket_kind: str) -> list[dict[str, Any]]:
    """Fallback parse from plain text blocks under Gratuit/Free or Payant/Paid headings."""
    text = soup.get_text("\n", strip=True)
    lines = [_normalize_space(line) for line in text.splitlines() if _normalize_space(line)]
    target_headers = _FREE_MARKERS if ticket_kind == "free" else _PAID_MARKERS
    other_headers = _PAID_MARKERS if ticket_kind == "free" else _FREE_MARKERS

    events: list[dict[str, Any]] = []
    in_section = False
    current_date: str | None = None
    current_label: str | None = None

    for line in lines:
        low = line.lower()
        if any(h in low for h in target_headers) and len(line) < 40:
            in_section = True
            continue
        if any(h in low for h in other_headers) and len(line) < 40:
            in_section = False
            continue
        if not in_section:
            continue

        if _DATE_ISO_RE.match(line):
            current_date = line
            current_label = line
            continue
        if _DATE_LABEL_RE.match(line):
            current_label = line
            continue

        time_m = _TIME_RE.search(line)
        time_s = time_m.group(1).upper().replace(":", "H") if time_m else None
        name = _TIME_RE.sub("", line).strip(" -|")
        name = _normalize_space(name)
        if not name or len(name) < 2:
            continue

        events.append(
            {
                "date": current_date,
                "date_label": current_label,
                "category": ticket_kind,
                "venue_or_stage": None,
                "artists": [{"name": name, "time": time_s}],
                "title": name,
                "ticket_url": None,
                "url": PORTAL_URL,
            }
        )
    return events


async def search_events(
    *,
    ticket_kind: str,
    query: str = "",
    date: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Telecharge et filtre l'horaire Jazz Fest (free ou paid)."""
    date = validate_optional_iso_date(date)

    url = f"{JAZZFEST_BASE_URL.rstrip('/')}{JAZZFEST_PROGRAM_PATH}"
    html = await fetch_text(url)
    return parse_program(
        html,
        ticket_kind=ticket_kind,
        query=query,
        date=date,
        limit=limit,
    )
