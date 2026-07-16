"""Calendrier de collecte des déchets à Montréal via Collecte MTL."""

import logging

from helpers.common.config import COLLECTEMTL_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import collectemtl_api
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="mtl_collecte_find_waste")
async def find_montreal_waste_collection(address: str) -> str:
    """Retourne le calendrier de collecte des dechets pour une adresse montrealaise.

    Source API: https://collectemtl.ca/api/collections
    Donnees amont: Secteurs Info-collectes, Donnees ouvertes de la Ville de Montreal
    (https://donnees.montreal.ca/dataset/info-collectes), CC BY 4.0.
    Actualise ~mensuellement - pas un flux en temps reel; les reports pour jours
    feries peuvent ne pas etre reflechis. Source legale: reglement 16-049.
    Service communautaire Collecte MTL, sans affiliation avec la Ville.

    Parameters:
        address: Adresse sur l'ile de Montreal
            (ex. '1 Place Ville-Marie, Montreal').
    """
    if not address or not address.strip():
        return error("Le parametre 'address' est requis.")

    try:
        data = await collectemtl_api.get_collections(address.strip())
        return ok(
            data,
            source="collectemtl",
            portal_url=COLLECTEMTL_BASE_URL,
            license=_LICENSE,
            dataset_id="info-collectes",
        )
    except Exception:
        logger.exception("Erreur dans find_montreal_waste_collection")
        return error("Impossible de recuperer le calendrier de collecte Collecte MTL.")
