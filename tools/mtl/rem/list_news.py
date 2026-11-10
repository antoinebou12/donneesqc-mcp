"""Actualites REM (RSS puis HTML)."""

from __future__ import annotations

from helpers.common.tool_call import run_tool
from helpers.mtl import rem_html
from helpers.mtl.citations import rem_ok
from tools import mcp


@mcp.tool(name="mtl_rem_news")
async def list_rem_news(
    lang: str = "fr",
    limit: int = 15,
) -> str:
    """Actualites officielles du REM (RSS puis scrape HTML si le flux est vide).

    Parameters:
        lang: 'fr' (defaut) ou 'en'.
        limit: Nombre max d'articles (1-50, defaut 15).
    """

    async def _run() -> str:
        data = await rem_html.list_news(lang=lang, limit=limit)
        return rem_ok(data)

    return await run_tool(
        "list_rem_news",
        _run,
        generic_error="Impossible d'obtenir les actualites REM.",
    )
