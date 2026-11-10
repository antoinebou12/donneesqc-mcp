"""Calendar seasons (meteorological + astronomical, Northern Hemisphere)."""

from __future__ import annotations

from datetime import date
from typing import Any

from helpers.common.context import resolve_now

_SEASON_LABELS: dict[str, dict[str, str]] = {
    "printemps": {"id": "printemps", "label_fr": "printemps", "label_en": "spring"},
    "ete": {"id": "ete", "label_fr": "été", "label_en": "summer"},
    "automne": {"id": "automne", "label_fr": "automne", "label_en": "autumn"},
    "hiver": {"id": "hiver", "label_fr": "hiver", "label_en": "winter"},
}

# Northern Hemisphere astronomical season starts (approx civil dates, ±1 day).
_ASTRO_START_MD: tuple[tuple[int, int, str], ...] = (
    (3, 20, "printemps"),
    (6, 21, "ete"),
    (9, 22, "automne"),
    (12, 21, "hiver"),
)


def _labels(season_id: str) -> dict[str, str]:
    return dict(_SEASON_LABELS[season_id])


def meteorological_season(day: date) -> dict[str, Any]:
    """Meteorological season for ``day`` (fixed calendar quarters)."""
    month = day.month
    if month in (3, 4, 5):
        sid = "printemps"
        start = date(day.year, 3, 1)
        end = date(day.year, 5, 31)
    elif month in (6, 7, 8):
        sid = "ete"
        start = date(day.year, 6, 1)
        end = date(day.year, 8, 31)
    elif month in (9, 10, 11):
        sid = "automne"
        start = date(day.year, 9, 1)
        end = date(day.year, 11, 30)
    else:
        sid = "hiver"
        if month == 12:
            start = date(day.year, 12, 1)
            end = date(day.year + 1, 2, 28)
            # Feb 29 in leap years for range_end of Dec-Feb winter
            try:
                end = date(day.year + 1, 2, 29)
            except ValueError:
                end = date(day.year + 1, 2, 28)
        else:
            # Jan / Feb
            start = date(day.year - 1, 12, 1)
            try:
                end = date(day.year, 2, 29)
            except ValueError:
                end = date(day.year, 2, 28)
    out = _labels(sid)
    out["range_start"] = start.isoformat()
    out["range_end"] = end.isoformat()
    return out


def _astro_start(year: int, month: int, day_n: int) -> date:
    return date(year, month, day_n)


def astronomical_season(day: date) -> dict[str, Any]:
    """Astronomical season for ``day`` (approx equinox/solstice dates)."""
    y = day.year
    starts = [(_astro_start(y, m, d), sid) for m, d, sid in _ASTRO_START_MD]
    # Previous winter start (Dec 21 of previous year)
    winter_prev = (_astro_start(y - 1, 12, 21), "hiver")
    spring = starts[0]
    summer = starts[1]
    autumn = starts[2]
    winter = starts[3]
    next_spring = (_astro_start(y + 1, 3, 20), "printemps")

    if day < spring[0]:
        sid = winter_prev[1]
        starts_on = winter_prev[0]
        ends_before = spring[0]
    elif day < summer[0]:
        sid = spring[1]
        starts_on = spring[0]
        ends_before = summer[0]
    elif day < autumn[0]:
        sid = summer[1]
        starts_on = summer[0]
        ends_before = autumn[0]
    elif day < winter[0]:
        sid = autumn[1]
        starts_on = autumn[0]
        ends_before = winter[0]
    else:
        sid = winter[1]
        starts_on = winter[0]
        ends_before = next_spring[0]

    out = _labels(sid)
    out["starts_on"] = starts_on.isoformat()
    out["ends_before"] = ends_before.isoformat()
    out["note"] = "Dates approximatives (±1 jour vs équinoxe/solstice réel; hémisphère nord)"
    return out


def build_calendar_season(
    *,
    date: str | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    """Build meteorological + astronomical season payload for a date."""
    now = resolve_now(date=date, timezone_name=timezone_name)
    day = date_type_from_iso(now["date"])
    return {
        "date": now["date"],
        "timezone": now["timezone"],
        "time_source": now["time_source"],
        "meteorological": meteorological_season(day),
        "astronomical": astronomical_season(day),
    }


def date_type_from_iso(iso: str) -> date:
    """Parse YYYY-MM-DD into ``date``."""
    return date.fromisoformat(iso[:10])
