"""Bar charts structures for La bicyclette API (not for chat dumps).

Chat UX uses markdown tables only - see skills/donneesqc-mcp/SKILL.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


def ascii_bars(
    categories: Sequence[str],
    values: Sequence[int | float],
    *,
    width: int = 24,
    max_items: int = 10,
    label_width: int = 22,
) -> str:
    """Rend un histogramme ASCII (usage API interne / La bicyclette).

    Chat agents must present rankings as markdown tables instead - see
    ``skills/donneesqc-mcp/SKILL.md``.
    """
    if not categories or not values:
        return ""
    pairs = list(zip(categories, values, strict=False))[:max_items]
    if not pairs:
        return ""
    max_val = max(float(v) for _, v in pairs)
    if max_val <= 0:
        max_val = 1.0

    lines: list[str] = []
    for label, raw in pairs:
        text = str(label)
        if len(text) > label_width:
            text = text[: label_width - 1] + "…"
        text = text.ljust(label_width)
        filled = round(width * float(raw) / max_val)
        filled = max(0, min(width, filled))
        bar = "█" * filled + " " * (width - filled)
        value_str = f"{raw:g}" if isinstance(raw, float) and not raw.is_integer() else f"{int(raw):,}".replace(",", " ")
        lines.append(f"{text} |{bar}| {value_str}")
    return "\n".join(lines)


def with_ascii(chart: dict[str, Any], *, width: int = 24, max_items: int = 10) -> dict[str, Any]:
    """Ajoute chart['ascii'] pour les bar charts categoriques."""
    if chart.get("type") != "bar":
        return chart
    categories = chart.get("categories") or []
    values = chart.get("values") or []
    if not isinstance(categories, list) or not isinstance(values, list):
        return chart
    out = dict(chart)
    out["ascii"] = ascii_bars(
        [str(c) for c in categories],
        [v if isinstance(v, int | float) else 0 for v in values],
        width=width,
        max_items=max_items,
    )
    return out


def bar_chart(
    categories: Sequence[str],
    values: Sequence[int | float],
    *,
    metric: str = "volume",
    width: int = 24,
    max_items: int = 10,
) -> dict[str, Any]:
    """Barres categoriques avec champ ascii pour le chat."""
    return with_ascii(
        {
            "type": "bar",
            "metric": metric,
            "categories": list(categories),
            "values": list(values),
        },
        width=width,
        max_items=max_items,
    )
