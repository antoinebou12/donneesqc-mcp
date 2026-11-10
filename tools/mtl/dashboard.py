"""Montréal MCP App and browser dashboard."""

from pathlib import Path
from typing import Any, Literal

from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from helpers.mtl.dashboard import build_dashboard
from tools import mcp

RESOURCE_URI = "ui://mtl-mcp/montreal.html"


@mcp.resource(
    RESOURCE_URI,
    name="Montréal dashboard",
    mime_type="text/html;profile=mcp-app",
    meta={
        "ui": {
            "prefersBorder": False,
            "csp": {"connectDomains": [], "resourceDomains": [], "frameDomains": ["https://www.openstreetmap.org"]},
        }
    },
)
def dashboard_html() -> str:
    """Self-contained UI; embedded data requests go through the MCP host."""
    return (Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8")


@mcp.tool(
    name="mtl_show_dashboard",
    title="Explorer Montréal",
    meta={"ui": {"resourceUri": RESOURCE_URI}},
    structured_output=True,
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
)
async def show_dashboard(
    address: str = "Hôtel de Ville de Montréal",
    radius_m: int = 800,
    view: Literal["all", "daily", "move", "out"] = "all",
) -> dict[str, Any]:
    """Open Montréal's MCP App with a map and live neighborhood cards.

    address: Public place or address in Montréal.
    radius_m: Nearby search radius, 100 to 3000 metres.
    view: Initial cards: all, daily (weather/311), move (parking/transit), out (parks/tourism).
    Returns source links and section errors even in clients without MCP Apps.
    """
    return await build_dashboard(address, radius_m, view)


@mcp.custom_route("/montreal", methods=["GET"])
async def dashboard_page(_request: Request) -> HTMLResponse:
    """Browser entry point using the existing same-origin tool endpoint."""
    return HTMLResponse(dashboard_html())


@mcp.custom_route("/montreal/api", methods=["POST"])
async def dashboard_api(request: Request) -> JSONResponse:
    """Browser counterpart of the dashboard tool, with the same input validation."""
    from pydantic import ValidationError

    try:
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse({"error": "La requête doit être un objet JSON."}, status_code=400)
        # The tool runner applies its generated schema before any upstream calls.
        tool = mcp._tool_manager._tools["mtl_show_dashboard"]
        arguments = tool.fn_metadata.arg_model.model_validate(body)
        result = await show_dashboard(**arguments.model_dump())
    except (ValueError, ValidationError):
        return JSONResponse({"error": "Vérifiez le lieu, le rayon et la vue demandés."}, status_code=400)
    except TimeoutError:
        return JSONResponse({"error": "La recherche a expiré. Réessayez."}, status_code=504)
    return JSONResponse(result)
