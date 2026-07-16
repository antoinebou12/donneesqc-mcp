"""Génère une URL d'image cartographique WMS."""

import logging

from helpers.common.config import GEO_WMS_URL
from helpers.common.response import error, ok
from helpers.qc.geo import geo_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_geo_get_map_url")
async def get_map_url(
    layers: str,
    bbox: str,
    width: int = 800,
    height: int = 600,
) -> str:
    """Génère une URL d'image cartographique WMS pour visualiser des couches.

    Retourne une URL GetMap qui produit une image PNG de la zone demandée
    avec les couches spécifiées superposées.

    Parameters:
        layers: Couches à afficher (séparées par des virgules).
        bbox: Emprise 'minx,miny,maxx,maxy' en EPSG:4326.
              Ex: '-73.7,45.4,-73.4,45.6' pour la grande région de Montréal.
        width: Largeur de l'image en pixels (défaut 800).
        height: Hauteur de l'image en pixels (défaut 600).
    """
    try:
        url = geo_api.build_wms_url(layers=layers, bbox=bbox, width=width, height=height)

        return ok(
            {"map_url": url, "layers": layers, "bbox": bbox},
            source="igo",
            portal_url=GEO_WMS_URL,
        )
    except Exception:
        logger.exception("Erreur dans get_map_url")
        return error("Impossible de générer l'URL de la carte.")
