"""Écocentres les plus proches via Collecte MTL."""

import logging

from helpers.common.config import COLLECTEMTL_BASE_URL
from helpers.common.response import error, ok
from helpers.mtl import collectemtl_api
from helpers.mtl.citations import MTL_OPEN_DATA_LICENSE as _LICENSE
from tools import mcp

logger = logging.getLogger(__name__)


_LIMIT_MIN = 1
_LIMIT_MAX = 8


@mcp.tool(name="mtl_collecte_find_ecocentres")
async def find_montreal_ecocentres(
    lat: float,
    lng: float,
    limit: int = 3,
) -> str:
    """Retourne les ecocentres (points de depot) les plus proches d'un point a Montreal.

    Source API: https://collectemtl.ca/api/ecocentres
    Donnees amont: Ecocentres et points de depot municipaux / montreal.ca (CC BY 4.0).
    Service communautaire Collecte MTL, sans affiliation avec la Ville.

    Parameters:
        lat: Latitude WGS84 (doit etre sur l'ile de Montreal).
        lng: Longitude WGS84.
        limit: Nombre de resultats (1 a 8, defaut 3).
    """
    clamped = max(_LIMIT_MIN, min(_LIMIT_MAX, int(limit)))

    try:
        data = await collectemtl_api.get_ecocentres(lat, lng, clamped)
        return ok(
            data,
            source="collectemtl",
            portal_url=COLLECTEMTL_BASE_URL,
            license=_LICENSE,
        )
    except Exception:
        logger.exception("Erreur dans find_montreal_ecocentres")
        return error("Impossible de recuperer les ecocentres Collecte MTL.")
