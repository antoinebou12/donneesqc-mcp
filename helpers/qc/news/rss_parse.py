"""Parse RSS 2.0 / Atom vers des items de manchettes."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Any

import defusedxml.ElementTree as DefusedET

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec B405 - type only; runtime parsing uses defusedxml

_TAG_RE = re.compile(r"<[^>]+>")


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(el: Element | None) -> str:
    if el is None:
        return ""
    raw = "".join(el.itertext()) if list(el) else (el.text or "")
    return _TAG_RE.sub("", raw).strip()


def _child(parent: Element, *names: str) -> Element | None:
    wanted = {n.lower() for n in names}
    for child in parent:
        if _local(child.tag).lower() in wanted:
            return child
    return None


def _attr_link(item: Element) -> str:
    """RSS ``<link>`` text or Atom ``<link href>``."""
    for child in item:
        if _local(child.tag).lower() != "link":
            continue
        href = child.get("href") or child.get("HREF")
        if href:
            rel = (child.get("rel") or "alternate").lower()
            if rel in {"alternate", ""}:
                return href.strip()
            continue
        text = (child.text or "").strip()
        if text:
            return text
    return ""


def parse_published(raw: str) -> str | None:
    """Normalise une date RSS/Atom en ISO-8601 UTC (ou None)."""
    value = (raw or "").strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError, IndexError, OverflowError):
        pass
    try:
        # Atom often uses ISO-8601
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def parse_rss_items(xml_text: str) -> list[dict[str, Any]]:
    """Extrait title / url / published_at / summary depuis un document RSS ou Atom."""
    if not xml_text or not xml_text.strip():
        return []
    try:
        root = DefusedET.fromstring(xml_text)
    except DefusedET.ParseError:
        return []

    root_name = _local(root.tag).lower()
    items: list[Element] = []

    if root_name == "rss":
        channel = _child(root, "channel")
        parent = channel if channel is not None else root
        items = [c for c in parent if _local(c.tag).lower() == "item"]
    elif root_name == "feed":
        items = [c for c in root if _local(c.tag).lower() == "entry"]
    elif root_name == "channel":
        items = [c for c in root if _local(c.tag).lower() == "item"]
    else:
        # Fallback: any item/entry descendants
        items = [el for el in root.iter() if _local(el.tag).lower() in {"item", "entry"}]

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        title = _text(_child(item, "title"))
        url = _attr_link(item)
        if not url:
            guid = _child(item, "guid", "id")
            url = _text(guid)
        pub_el = _child(item, "pubDate", "published", "updated", "date")
        published_at = parse_published(_text(pub_el))
        summary_el = _child(item, "description", "summary", "content")
        summary = _text(summary_el)
        if summary and len(summary) > 400:
            summary = summary[:397] + "..."
        if not title or not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        results.append(
            {
                "title": title,
                "url": url,
                "published_at": published_at,
                "summary": summary or None,
            }
        )
    return results
