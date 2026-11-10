"""Snow / parking déneigement season status (Montréal heuristic)."""

from __future__ import annotations

from datetime import date
from typing import Any

from helpers.common.context import resolve_now
from helpers.common.season import date_type_from_iso
from helpers.common.urls import (
    PARKING_DENEIGEMENT_DATASET_ID,
    PARKING_DENEIGEMENT_DQ_DATASET_ID,
    dq_dataset_url,
    mtl_dataset_url,
)

# Aligns with Ville de Montréal open-data publish window (November start).
_SEASON_START_MD = (11, 1)
_SEASON_END_MD = (4, 15)

_HEURISTIC = "Nov 1 - Apr 15 (America/Toronto); jeu stationnements-deneigement publié chaque novembre"


def _season_bounds_for_start_year(start_year: int) -> tuple[date, date, str]:
    """Return (start, end, label) for season starting 1 Nov ``start_year``."""
    start = date(start_year, *_SEASON_START_MD)
    end = date(start_year + 1, *_SEASON_END_MD)
    label = f"{start_year}-{start_year + 1}"
    return start, end, label


def parking_season_for_day(day: date) -> dict[str, Any]:
    """Compute in_season + label for a calendar day."""
    y, m, d = day.year, day.month, day.day

    # Active season: Nov 1 Y → Apr 15 Y+1
    if m > _SEASON_START_MD[0] or (m == _SEASON_START_MD[0] and d >= _SEASON_START_MD[1]):
        # Nov 1 - Dec 31
        start, end, label = _season_bounds_for_start_year(y)
        in_season = True
    elif m < _SEASON_END_MD[0] or (m == _SEASON_END_MD[0] and d <= _SEASON_END_MD[1]):
        # Jan 1 - Apr 15
        start, end, label = _season_bounds_for_start_year(y - 1)
        in_season = True
    else:
        # Apr 16 - Oct 31 -> next season
        start, end, label = _season_bounds_for_start_year(y)
        in_season = False

    return {
        "in_season": in_season,
        "season_label": label,
        "season_start": start.isoformat(),
        "season_end": end.isoformat(),
        "heuristic": _HEURISTIC,
    }


def build_parking_season_status(
    *,
    date: str | None = None,
    timezone_name: str | None = None,
) -> dict[str, Any]:
    """Build snow/parking season status payload."""
    now = resolve_now(date=date, timezone_name=timezone_name)
    day = date_type_from_iso(now["date"])
    body = parking_season_for_day(day)
    body.update(
        {
            "date": now["date"],
            "timezone": now["timezone"],
            "time_source": now["time_source"],
            "portal_url": mtl_dataset_url(PARKING_DENEIGEMENT_DATASET_ID),
            "dq_url": dq_dataset_url(PARKING_DENEIGEMENT_DQ_DATASET_ID),
        }
    )
    return body
