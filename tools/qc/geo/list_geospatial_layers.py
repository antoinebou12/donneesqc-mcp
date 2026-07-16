"""Liste les couches géospatiales IGO du gouvernement du Québec."""

import logging

from helpers.common.config import GEO_WFS_URL, GEO_WMS_URL
from helpers.common.response import error, ok
from helpers.qc.geo import geo_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_geo_list_layers")
async def list_geospatial_layers(service: str = "wfs", query: str | None = None) -> str:
    """Liste les couches géospatiales disponibles via IGO.

    L'Infrastructure Géomatique Ouverte (IGO) du Québec expose des centaines
    de couches de données géographiques couvrant le territoire québécois :
    casernes, patrimoine culturel, territoires agricoles, écoles, etc.

    Parameters:
        service: 'wfs' (données vectorielles) ou 'wms' (images). Défaut 'wfs'.
        query: Filtre optionnel sur le nom ou titre de la couche.
    """
    try:
        if service.lower() == "wms":
            caps = await geo_api.get_wms_capabilities()
        else:
            caps = await geo_api.get_wfs_capabilities()

        layers = caps.get("layers", [])

        if query:
            q_lower = query.lower()
            layers = [
                layer
                for layer in layers
                if q_lower in layer.get("name", "").lower()
                or q_lower in layer.get("title", "").lower()
                or q_lower in layer.get("abstract", "").lower()
            ]

        return ok(
            {"service": service.upper(), "total": len(layers), "layers": layers[:50]},
            source="igo",
            portal_url=GEO_WMS_URL if service.lower() == "wms" else GEO_WFS_URL,
        )
    except Exception:
        logger.exception("Erreur dans list_geospatial_layers")
        return error("Impossible de lister les couches géospatiales IGO.")
