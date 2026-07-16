#!/usr/bin/env python3
"""Smoke EXAMPLES.md tool chains (in-process) with a temp markdown report.

Usage:
  uv run python scripts/smoke_examples.py
  uv run python scripts/smoke_examples.py --live
  uv run python scripts/smoke_examples.py --live --only 3,25,32,35,37,40-44
  uv run python scripts/smoke_examples.py --live --keep-report
  uv run python scripts/smoke_examples.py --list

Report: written under the system temp dir. Deleted automatically when all
steps pass (unless --keep-report). Kept on failure for inspection.

ASCII bars appear only in the report file for ranked metrics; chat UX stays
table-only (skills/donneesqc-mcp/SKILL.md).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from smoke_report import format_step_markdown  # noqa: E402


@dataclass(frozen=True)
class Step:
    """One EXAMPLES.md section smoke step."""

    number: int
    title: str
    needs_live: bool
    run: Callable[[], Awaitable[str]]
    allow_empty_events: bool = False


def _parse_json(raw: str) -> dict:
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = f"expected object, got {type(data)}"
        raise TypeError(msg)
    return data


def _ok_or_raise(raw: str, *, allow_empty_events: bool = False) -> dict:
    body = _parse_json(raw)
    if "error" in body:
        raise RuntimeError(body["error"])
    if allow_empty_events and body.get("events") == [] and body.get("warning"):
        return body
    return body


async def _offline_festivals() -> str:
    from helpers.mtl import jazzfest_api, piknic_api

    fixtures = ROOT / "tests" / "fixtures"
    piknic_html = (fixtures / "piknic_programmation.html").read_text(encoding="utf-8")
    jazz_html = (fixtures / "jazzfest_program.html").read_text(encoding="utf-8")
    main = piknic_api.parse_programmation(piknic_html, category="piknic", year=2026)
    if main["count"] < 1:
        raise RuntimeError("piknic fixture returned no piknic events")
    free = jazzfest_api.parse_program(jazz_html, ticket_kind="free")
    paid = jazzfest_api.parse_program(jazz_html, ticket_kind="paid")
    if free["count"] < 1 or paid["count"] < 1:
        raise RuntimeError("jazzfest fixture free/paid isolation failed")
    return json.dumps(
        {
            "piknic_count": main["count"],
            "jazz_free": free["count"],
            "jazz_paid": paid["count"],
            "events": main["events"][:3],
        }
    )


def _build_steps() -> list[Step]:
    async def version() -> str:
        from tools.common.get_version import get_version

        return await get_version()

    async def catalog_stats() -> str:
        from tools.qc.get_catalog_stats import get_catalog_stats

        return await get_catalog_stats()

    async def list_orgs() -> str:
        from tools.qc.list_organizations import list_organizations

        return await list_organizations(query="ville")

    async def find_crime() -> str:
        from tools.qc.find_and_query import find_and_query

        return await find_and_query(query="actes criminels montreal", page_size=3)

    async def geo_mcc() -> str:
        from tools.qc.geo.list_geospatial_layers import list_geospatial_layers

        return await list_geospatial_layers(service="wfs", query="MCC")

    async def geocode() -> str:
        from tools.qc.geo.geocode import geocode

        return await geocode(address="380 rue Sherbrooke Ouest, Montréal")

    async def nosorigines() -> str:
        from tools.qc.nosorigines.search_nosorigines import search_nosorigines

        return await search_nosorigines(last_name="Champlain", first_name="Samuel")

    async def nosorigines_person() -> str:
        from tools.qc.nosorigines.get_person import get_person

        return await get_person(pid="781")

    async def nosorigines_ancestors() -> str:
        from tools.qc.nosorigines.get_ancestors import get_ancestors

        return await get_ancestors(pid="781", generations=1)

    async def labicyclette() -> str:
        from tools.mtl.labicyclette.get_labicyclette_overview import get_labicyclette_overview

        return await get_labicyclette_overview()

    async def labicyclette_boroughs() -> str:
        from tools.mtl.labicyclette.get_labicyclette_boroughs import get_labicyclette_boroughs

        return await get_labicyclette_boroughs()

    async def collecte_calendar() -> str:
        from tools.mtl.collecte.find_montreal_waste_collection import (
            find_montreal_waste_collection,
        )

        return await find_montreal_waste_collection(address="275 Rue Notre-Dame Est")

    async def murales() -> str:
        from tools.mtl.murales.search_murales import search_murales

        return await search_murales(arrondissement="Plateau", annee_min="2020", page_size=3)

    async def piknic_off() -> str:
        from tools.mtl.festivals.search_piknic_off import search_piknic_off

        return await search_piknic_off(limit=5)

    async def piknic_main() -> str:
        from tools.mtl.festivals.search_piknic import search_piknic

        return await search_piknic(query="Mandragora", limit=10)

    async def piknic_petit() -> str:
        from tools.mtl.festivals.search_piknic_petit import search_piknic_petit

        return await search_piknic_petit(date="2026-07-19", limit=10)

    async def jazz_free() -> str:
        from tools.mtl.festivals.search_jazzfest_free import search_jazzfest_free

        return await search_jazzfest_free(limit=10)

    async def jazz_paid() -> str:
        from tools.mtl.festivals.search_jazzfest_paid import search_jazzfest_paid

        return await search_jazzfest_paid(query="Isaiah Collier", limit=10)

    async def autour_hotel_de_ville() -> str:
        from tools.mtl.avis.find_avis_nearby import find_avis_nearby
        from tools.mtl.bixi.find_bixi_nearby import find_bixi_nearby
        from tools.mtl.parcs.find_parcs_nearby import find_parcs_nearby
        from tools.mtl.qualo.find_qualo_nearby import find_qualo_nearby
        from tools.qc.geo.geocode import geocode
        from tools.qc.hydro.outage_status import outage_status

        addr = "275 Rue Notre-Dame Est, Montreal"
        geo = _ok_or_raise(await geocode(address=addr, limit=1))
        results = geo.get("results") or []
        if not results or results[0].get("latitude") is None:
            raise RuntimeError("geocode returned no coordinates (geometry=true required)")
        avis = _ok_or_raise(await find_avis_nearby(date="2026-07-16", address=addr, radius_m=1000, limit=5))
        # Info-pannes can return HTTP 400 intermittently; do not fail the whole nearby bundle.
        hydro_raw = await outage_status(address=addr)
        hydro = json.loads(hydro_raw) if isinstance(hydro_raw, str) else hydro_raw
        if not isinstance(hydro, dict):
            hydro = {"error": "invalid hydro response"}
        qualo = _ok_or_raise(await find_qualo_nearby(address=addr, radius_m=1500, limit=5))
        parcs = _ok_or_raise(await find_parcs_nearby(address=addr, radius_m=300, limit=5, parks_only=False))
        bixi = _ok_or_raise(await find_bixi_nearby(address=addr, radius_m=400, limit=5))
        return json.dumps(
            {
                "geocode_total": geo.get("total"),
                "avis_total": avis.get("total"),
                "hydro_total": hydro.get("total"),
                "hydro_error": hydro.get("error"),
                "qualo_total": qualo.get("total"),
                "parcs_total": parcs.get("total"),
                "bixi_total": bixi.get("total"),
                "latitude": results[0].get("latitude"),
                "longitude": results[0].get("longitude"),
            },
            ensure_ascii=False,
        )

    async def bixi_hotel_ville() -> str:
        from tools.mtl.bixi.find_bixi_nearby import find_bixi_nearby

        raw = await find_bixi_nearby(
            address="275 Rue Notre-Dame Est, Montreal",
            radius_m=400,
            limit=8,
        )
        body = _ok_or_raise(raw)
        if int(body.get("total") or 0) < 1:
            raise RuntimeError("mtl_bixi_nearby returned no stations")
        stations = body.get("stations") or []
        if not stations or stations[0].get("distance_m") is None:
            raise RuntimeError("mtl_bixi_nearby stations missing distance_m")
        return raw

    async def parcs_hotel_ville() -> str:
        from tools.mtl.parcs.find_parcs_nearby import find_parcs_nearby

        raw = await find_parcs_nearby(
            address="275 Rue Notre-Dame Est, Montreal",
            radius_m=300,
            limit=8,
            parks_only=False,
        )
        body = _ok_or_raise(raw)
        if int(body.get("total") or 0) < 1:
            raise RuntimeError("mtl_parcs_nearby returned no parks")
        return raw

    async def qualo_hotel_ville() -> str:
        from tools.mtl.qualo.find_qualo_nearby import find_qualo_nearby

        raw = await find_qualo_nearby(
            address="275 Rue Notre-Dame Est, Montreal",
            radius_m=1500,
            limit=8,
        )
        body = _ok_or_raise(raw)
        if int(body.get("total") or 0) < 1:
            raise RuntimeError("mtl_qualo_nearby returned no stations")
        return raw

    async def neighborhood_briefing_live() -> str:
        from tools.mtl.neighborhood.briefing import neighborhood_briefing

        raw = await neighborhood_briefing(
            address="275 Rue Notre-Dame Est, Montreal",
            date="2026-07-16",
            avis_radius_m=1000,
            parks_radius_m=300,
            bixi_radius_m=400,
            qualo_radius_m=1500,
            limit=5,
        )
        body = _ok_or_raise(raw)
        if "summary" not in body:
            raise RuntimeError("neighborhood briefing missing summary")
        return raw

    async def offline_neighborhood() -> str:
        from unittest.mock import AsyncMock, patch

        payload = {
            "query": {"latitude": 45.5088, "longitude": -73.5541, "date": "2026-07-16"},
            "summary": {
                "hydro_ok": True,
                "avis_count": 1,
                "qualo_bathing_ok": True,
                "parks_count": 1,
                "bixi_stations": 1,
            },
            "hydro": {"total": 1, "lieux": [], "source": "hydro"},
            "avis": {"total": 1, "alerts": [], "source": "avis"},
            "water_quality": {"total": 1, "stations": [], "source": "qualo"},
            "parks": {"total": 1, "items": [], "source": "parcs"},
            "bixi": {"total": 1, "stations": [], "source": "bixi"},
        }
        with patch(
            "helpers.mtl.neighborhood_api.build_briefing",
            new_callable=AsyncMock,
            return_value=payload,
        ):
            from tools.mtl.neighborhood.briefing import neighborhood_briefing

            return await neighborhood_briefing(latitude=45.5088, longitude=-73.5541, date="2026-07-16")

    # Numbers align with EXAMPLES.md section headers
    return [
        Step(1, "common_get_version", False, version),
        Step(0, "festivals fixtures (offline)", False, _offline_festivals),
        Step(0, "neighborhood briefing (offline mock)", False, offline_neighborhood),
        Step(3, "qc_get_catalog_stats", True, catalog_stats),
        Step(5, "qc_list_organizations(ville)", True, list_orgs),
        Step(7, "qc_find_and_query(actes criminels)", True, find_crime),
        Step(14, "qc_geo_list_layers(MCC)", True, geo_mcc),
        Step(17, "qc_geo_geocode", True, geocode),
        Step(22, "mtl_bixi_nearby (Hotel de Ville)", True, bixi_hotel_ville),
        Step(23, "mtl_parcs_nearby (Hotel de Ville)", True, parcs_hotel_ville),
        Step(25, "qc_nosorigines_search(Champlain)", True, nosorigines),
        Step(48, "qc_nosorigines_get_person(781 Francois Boucher)", True, nosorigines_person),
        Step(49, "qc_nosorigines_get_ancestors(781)", True, nosorigines_ancestors),
        Step(30, "mtl_qualo_nearby (Hotel de Ville)", True, qualo_hotel_ville),
        Step(32, "mtl_labicyclette_overview", True, labicyclette),
        Step(34, "mtl_labicyclette_boroughs", True, labicyclette_boroughs),
        Step(35, "mtl_collecte_find_waste (calendrier)", True, collecte_calendar),
        Step(37, "mtl_murales_search(Plateau)", True, murales),
        Step(39, "autour Hotel de Ville (avis/hydro/qualo/parcs/bixi)", True, autour_hotel_de_ville),
        Step(40, "mtl_piknic_search_off", True, piknic_off, allow_empty_events=True),
        Step(41, "mtl_piknic_search(Mandragora)", True, piknic_main, allow_empty_events=True),
        Step(42, "mtl_piknic_search_petit(2026-07-19)", True, piknic_petit, allow_empty_events=True),
        Step(43, "mtl_jazzfest_search_free", True, jazz_free, allow_empty_events=True),
        Step(44, "mtl_jazzfest_search_paid", True, jazz_paid, allow_empty_events=True),
        Step(45, "mtl_neighborhood_briefing (Hotel de Ville)", True, neighborhood_briefing_live),
    ]


def _parse_only(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def _summary_line(body: dict) -> str:
    if "total_organizations" in body:
        return f" orgs={body['total_organizations']} datasets={body.get('total_datasets')}"
    if "events" in body:
        return f" events={len(body.get('events') or [])}"
    if "boroughs" in body:
        return f" boroughs={len(body.get('boroughs') or [])}"
    if "count" in body:
        return f" count={body['count']}"
    return ""


async def _run(live: bool, only: set[int] | None, *, keep_report: bool) -> int:
    from tools import register_all_tools

    register_all_tools()
    steps = _build_steps()

    fd, path = tempfile.mkstemp(prefix="donneesqc-smoke-", suffix=".md")
    os.close(fd)
    report_path = Path(path)
    print(f"Report: {report_path}")

    parts: list[str] = [
        "# Données Québec MCP - smoke report",
        "",
        f"- live: `{live}`",
        f"- only: `{sorted(only) if only else 'all eligible'}`",
        "",
    ]
    failed = 0
    ran = 0

    for step in steps:
        if step.needs_live and not live:
            continue
        if only is not None:
            if step.number == 0:
                if 0 not in only:
                    continue
            elif step.number not in only:
                continue

        label = f"[{step.number}] {step.title}" if step.number else step.title
        try:
            raw = await step.run()
            body = _ok_or_raise(raw, allow_empty_events=step.allow_empty_events)
            print(f"PASS {label}{_summary_line(body)}")
            parts.append(
                format_step_markdown(
                    number=step.number,
                    title=step.title,
                    status="PASS",
                    body=body,
                )
            )
            ran += 1
        except Exception as exc:
            print(f"FAIL {label}: {exc}")
            parts.append(
                format_step_markdown(
                    number=step.number,
                    title=step.title,
                    status="FAIL",
                    error=str(exc),
                )
            )
            failed += 1
            ran += 1

    parts.append("")
    parts.append(f"**Summary:** {ran - failed}/{ran} passed, {failed} failed")
    report_path.write_text("\n".join(parts) + "\n", encoding="utf-8")

    if ran == 0:
        print("No steps ran. Use --live for network examples, or omit --only.")
        print(f"Report kept: {report_path}")
        return 2

    print(f"Done: {ran - failed}/{ran} passed, {failed} failed")
    if failed or keep_report:
        print(f"Report kept: {report_path}")
        return 1 if failed else 0

    report_path.unlink(missing_ok=True)
    print("Report deleted (all passed)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Hit live upstream APIs")
    parser.add_argument(
        "--only",
        help="EXAMPLES section numbers, e.g. 3,25,32,35,37,40-44",
    )
    parser.add_argument(
        "--keep-report",
        action="store_true",
        help="Keep the temp markdown report even when all steps pass",
    )
    parser.add_argument("--list", action="store_true", help="List steps and exit")
    args = parser.parse_args()
    steps = _build_steps()
    if args.list:
        for s in steps:
            mode = "live" if s.needs_live else "offline"
            print(f"{s.number:>3}  [{mode}]  {s.title}")
        return 0
    only = _parse_only(args.only)
    return asyncio.run(_run(live=args.live, only=only, keep_report=args.keep_report))


if __name__ == "__main__":
    raise SystemExit(main())
