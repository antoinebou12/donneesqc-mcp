"""Détail d'une ressource spécifique."""

import logging

from helpers.common import ckan_api
from helpers.common.config import DQ_API_URL
from helpers.common.response import error, ok
from tools import mcp

logger = logging.getLogger(__name__)


@mcp.tool(name="qc_get_resource_info")
async def get_resource_info(resource_id: str) -> str:
    """Informations détaillées sur une ressource de Données Québec.

    Retourne format, taille, type MIME, URL, association au jeu de données
    et disponibilité via le DataStore.

    Parameters:
        resource_id: Identifiant de la ressource.
    """
    try:
        res = await ckan_api.resource_show(DQ_API_URL, resource_id)

        return ok(
            {
                "id": res.get("id"),
                "name": res.get("name"),
                "description": res.get("description"),
                "format": res.get("format"),
                "mimetype": res.get("mimetype"),
                "size": res.get("size"),
                "url": res.get("url"),
                "datastore_active": res.get("datastore_active", False),
                "package_id": res.get("package_id"),
                "created": res.get("created"),
                "last_modified": res.get("last_modified"),
            },
            source="donnees_quebec",
            portal_url=res.get("url"),
            dataset_id=res.get("package_id"),
            resource_id=res.get("id"),
            metadata_modified=res.get("last_modified"),
        )
    except Exception:
        logger.exception("Erreur dans get_resource_info")
        return error(f"Impossible de récupérer la ressource '{resource_id}'.")
