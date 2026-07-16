"""Recuperation d'une fiche Vitrine linguistique (OQLF)."""

import logging

from helpers.common.config import VITRINE_BASE_URL
from helpers.common.response import error, ok
from helpers.qc.oqlf import vitrine_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_oqlf_get_entry")
async def get_vitrine_entry(url: str) -> str:
    """Recupere le titre et un extrait d'une fiche de la Vitrine linguistique.

    Source: https://vitrinelinguistique.oqlf.gouv.qc.ca/

    Parameters:
        url: URL complete d'une fiche sur le domaine Vitrine linguistique.
    """
    try:
        if not url or not url.strip():
            return error("Le parametre url est requis.")
        cleaned = url.strip()
        if not cleaned.startswith(VITRINE_BASE_URL):
            return error(f"URL invalide: doit commencer par {VITRINE_BASE_URL}")
        data = await vitrine_api.get_vitrine_entry(cleaned)
        return ok(
            data,
            source="vitrine_linguistique",
            portal_url=cleaned,
        )
    except Exception:
        logger.exception("Erreur dans get_vitrine_entry")
        return error(f"Impossible de recuperer la fiche '{url}'.")
