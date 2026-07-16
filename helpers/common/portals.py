"""Portal CKAN configs (Données Québec / Montréal)."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from helpers.common.config import DQ_API_URL, DQ_BASE_URL, MTL_API_URL, MTL_BASE_URL


@dataclass(frozen=True, slots=True)
class Portal:
    """Identifiants et URLs d'un portail CKAN."""

    api_url: str
    base_url: str
    source: str

    def dataset_url(self, name: str | None) -> str:
        slug = name or ""
        return f"{self.base_url.rstrip('/')}/dataset/{slug}"

    def resource_url(self, dataset_name: str | None, resource_id: str) -> str:
        """Page ressource / Data Explorer sur le portail."""
        base = self.dataset_url(dataset_name).rstrip("/")
        return f"{base}/resource/{resource_id}"

    def sql_api_url(self, sql: str) -> str:
        """URL navigable vers datastore_search_sql (aperçu JSON de la requête)."""
        return f"{self.api_url.rstrip('/')}/datastore_search_sql?sql={quote(sql, safe='')}"


DQ_PORTAL = Portal(api_url=DQ_API_URL, base_url=DQ_BASE_URL, source="donnees_quebec")
MTL_PORTAL = Portal(api_url=MTL_API_URL, base_url=MTL_BASE_URL, source="montreal")
