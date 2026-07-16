"""Endpoint /version - informations sur le serveur MCP."""

import logging
import sys

from helpers.common.response import error, ok
from helpers.common.urls import source_capabilities, source_labels
from tools import mcp

logger = logging.getLogger(__name__)


def _get_version() -> str:
    """Lit la version depuis _version.py ou retourne un fallback."""
    try:
        from _version import version
    except Exception:
        return "0.0.0-dev"
    else:
        return version


@mcp.tool(name="common_get_version")
async def get_version() -> str:
    """Retourne les informations de version du serveur MCP Donnees Quebec.

    Inclut la version du serveur, la version Python, et les capacites disponibles.
    """
    try:
        return ok(
            {
                "name": "donneesqc-mcp",
                "version": _get_version(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "capabilities": source_capabilities(),
                "sources": source_labels(),
            },
            source="donneesqc_mcp",
        )
    except Exception:
        logger.exception("Erreur dans get_version")
        return error("Impossible de recuperer les informations de version.")
