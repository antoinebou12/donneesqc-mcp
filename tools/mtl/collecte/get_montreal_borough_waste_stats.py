"""Statistiques de récupération par arrondissement via Collecte MTL."""

import logging

from helpers.common.config import COLLECTEMTL_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import collectemtl_api
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="mtl_collecte_borough_waste_stats")
async def get_montreal_borough_waste_stats(address: str) -> str:
    """Retourne le bilan massique (taux de recuperation) de l'arrondissement pour une adresse.

    Source API: https://collectemtl.ca/api/borough
    Donnees amont: Matieres residuelles - bilan massique, Donnees ouvertes de la
    Ville de Montreal (CC BY 4.0). Estimations modelisees - directionnelles, pas
    precises. Null si le point n'est pas dans l'un des 19 arrondissements.
    Service communautaire Collecte MTL, sans affiliation avec la Ville.

    Parameters:
        address: Adresse sur l'ile de Montreal
            (ex. '1 Place Ville-Marie, Montreal').
    """
    if not address or not address.strip():
        return error("Le parametre 'address' est requis.")

    try:
        data = await collectemtl_api.get_borough_stats(address.strip())
        return ok(
            data,
            source="collectemtl",
            portal_url=COLLECTEMTL_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans get_montreal_borough_waste_stats")
        return error("Impossible de recuperer les stats d'arrondissement Collecte MTL.")
