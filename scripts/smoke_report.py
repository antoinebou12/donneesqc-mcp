"""Markdown + ASCII formatting for smoke_examples reports (not chat UX)."""

from __future__ import annotations

from typing import Any

from helpers.common.chart_format import ascii_bars


def md_table(headers: list[str], rows: list[list[Any]], *, max_rows: int = 15) -> str:
    """Build a GitHub-flavored markdown table."""
    if not headers:
        return ""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows[:max_rows]:
        cells = [str(c if c is not None else "") for c in row]
        while len(cells) < len(headers):
            cells.append("")
        lines.append("| " + " | ".join(cells[: len(headers)]) + " |")
    if len(rows) > max_rows:
        lines.append(f"| … | ({len(rows) - max_rows} more) |")
    return "\n".join(lines)


def _rows_from_dicts(items: list[dict[str, Any]], keys: list[str]) -> list[list[Any]]:
    return [[item.get(k) for k in keys] for item in items if isinstance(item, dict)]


def format_body_section(body: dict[str, Any]) -> str:
    """Render tables and optional ASCII bars from a tool JSON body."""
    chunks: list[str] = []

    if "total_organizations" in body or "total_datasets" in body:
        chunks.append(
            f"- organisations: **{body.get('total_organizations', '?')}** - jeux: **{body.get('total_datasets', '?')}**"
        )

    orgs = body.get("top_organizations")
    if isinstance(orgs, list) and orgs:
        rows = _rows_from_dicts(orgs, ["name", "datasets"])
        chunks.append(md_table(["Organisation", "Jeux"], rows))
        labels = [str(r[0] or "") for r in rows]
        values = [float(r[1] or 0) for r in rows]
        bars = ascii_bars(labels, values, max_items=10)
        if bars:
            chunks.append("```text\n" + bars + "\n```")

    boroughs = body.get("boroughs")
    if isinstance(boroughs, list) and boroughs:
        rows = _rows_from_dicts(boroughs, ["rank", "borough", "volume", "volumeSharePct"])
        chunks.append(md_table(["Rang", "Arrondissement", "Volume", "%"], rows))
        labels = [str(b.get("borough") or "") for b in boroughs if isinstance(b, dict)]
        values = [float(b.get("volume") or 0) for b in boroughs if isinstance(b, dict)]
        bars = ascii_bars(labels, values, max_items=10)
        if bars:
            chunks.append("```text\n" + bars + "\n```")

    events = body.get("events")
    if isinstance(events, list) and events:
        rows = []
        for ev in events[:15]:
            if not isinstance(ev, dict):
                continue
            artists = ev.get("artists") or []
            names = ", ".join(str(a.get("name") or "") for a in artists if isinstance(a, dict))[:80]
            rows.append(
                [
                    ev.get("date") or ev.get("date_label") or "",
                    ev.get("category") or "",
                    ev.get("venue_or_stage") or "",
                    names or ev.get("title") or "",
                ]
            )
        chunks.append(md_table(["Date", "Cat.", "Scène", "Artistes"], rows))

    # Collecte calendar-ish payloads
    for key in ("collections", "schedule", "days", "calendrier"):
        cal = body.get(key)
        if isinstance(cal, list) and cal and isinstance(cal[0], dict):
            keys = list(cal[0].keys())[:5]
            rows = _rows_from_dicts(cal, keys)
            chunks.append(md_table(keys, rows))
            break

    # Generic list of records
    for key in ("results", "datasets", "records", "murales", "items", "sites"):
        items = body.get(key)
        if isinstance(items, list) and items and isinstance(items[0], dict):
            keys = list(items[0].keys())[:5]
            rows = _rows_from_dicts(items, keys)
            chunks.append(md_table(keys, rows))
            break

    if body.get("warning"):
        chunks.append(f"*warning:* {body['warning']}")

    # Nested dict calendars / KPIs (Collecte MTL, overview)
    if not any("|" in c for c in chunks):
        for key, val in body.items():
            if key in {"_meta", "error", "warning", "query", "date", "category"}:
                continue
            if isinstance(val, dict) and val:
                rows = [[k, v] for k, v in list(val.items())[:20]]
                chunks.append(md_table([key, "value"], rows))
                break
            if isinstance(val, list) and val and not isinstance(val[0], dict):
                chunks.append(md_table([key], [[x] for x in val[:20]]))
                break

    if not chunks and body.get("version"):
        chunks.append(f"- version: `{body.get('version')}`")

    return "\n\n".join(chunks) if chunks else "_no tabular summary_"


def format_step_markdown(
    *,
    number: int,
    title: str,
    status: str,
    body: dict[str, Any] | None = None,
    error: str | None = None,
) -> str:
    """One EXAMPLES step block for the report file."""
    label = f"{number}. {title}" if number else title
    lines = [f"## {label}", "", f"**Status:** {status}"]
    if error:
        lines.extend(["", f"**Error:** `{error}`"])
    if body is not None:
        lines.extend(["", format_body_section(body)])
    lines.append("")
    return "\n".join(lines)
