"""Smoke: tous les outils prefixes sont enregistres."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_all_tools_exposes_prefixed_names():
    from tools import mcp, register_all_tools

    register_all_tools()
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert len(names) >= 50
    assert "qc_search_datasets" in names
    assert "mtl_search_datasets" in names
    assert "qc_geo_geocode" in names
    assert "mtl_murales_search" in names
    assert "mtl_avis_nearby" in names
    assert "mtl_neighborhood_briefing" in names
    assert "mtl_parcs_nearby" in names
    assert "mtl_bixi_nearby" in names
    assert "mtl_qualo_nearby" in names
    assert "mtl_piknic_search" in names
    assert "mtl_jazzfest_search_free" in names
    assert "mtl_evenements_search" in names
    assert "mtl_calendar_week" in names
    assert "mtl_events_soon" in names
    assert "common_get_context" in names
    assert "common_list_tools_with_examples" in names
    assert all(n.startswith(("qc_", "mtl_", "common_")) for n in names), (
        f"unexpected names: {[n for n in names if not n.startswith(('qc_', 'mtl_', 'common_'))]}"
    )
