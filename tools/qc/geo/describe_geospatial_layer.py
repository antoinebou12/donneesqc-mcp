"""Décrit le schéma d'une couche géospatiale."""

import logging

from helpers.common.config import GEO_WFS_URL
from helpers.common.response import error, ok
from helpers.qc.geo import geo_api
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_geo_describe_layer")
async def describe_geospatial_layer(layer_name: str) -> str:
    """Décrit le schéma d'une couche géospatiale (champs et types).

    Utile avant d'interroger une couche pour connaître les attributs
    disponibles et construire des filtres CQL pertinents.

    Parameters:
        layer_name: Nom de la couche WFS (ex: 'ms:CASERNE').
    """
    try:
        schema_xml = await geo_api.describe_feature_type(layer_name)

        return ok(
            {"layer": layer_name, "schema_xml": schema_xml[:5000]},
            source="igo",
            portal_url=GEO_WFS_URL,
        )
    except Exception:
        logger.exception("Erreur dans describe_geospatial_layer")
        return error(f"Impossible de décrire la couche '{layer_name}'.")
