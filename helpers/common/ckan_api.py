"""Helper pour les API CKAN (Données Québec et Montréal).

Les deux portails utilisent CKAN 2.10+. Ce helper expose des fonctions
réutilisables par les tools individuels.
"""

import json
import logging
import re
from typing import Any

from helpers.common.http_client import fetch_json

logger = logging.getLogger(__name__)


def _extract_result(data: dict[str, Any]) -> Any:
    """Extrait le champ 'result' d'une réponse CKAN."""
    if not data.get("success"):
        error = data.get("error", {})
        msg = error.get("message", "Erreur CKAN inconnue")
        raise RuntimeError(f"Erreur API CKAN: {msg}")
    return data["result"]


async def package_search(
    api_url: str,
    query: str = "*:*",
    rows: int = 20,
    start: int = 0,
    sort: str = "score desc, metadata_modified desc",
    fq: str | None = None,
    facet_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Recherche de jeux de données.

    Parameters:
        facet_fields: Noms de facettes CKAN (ex. ``["groups"]``). Les compteurs
            apparaissent dans ``search_facets`` / ``facets`` de la réponse.
    """
    params: dict[str, Any] = {"q": query, "rows": min(rows, 1000), "start": start, "sort": sort}
    if fq:
        params["fq"] = fq
    if facet_fields:
        # Données Québec exige une liste JSON encodée en chaîne (sinon 409 Validation Error).
        params["facet.field"] = json.dumps(facet_fields)
    data = await fetch_json(f"{api_url}/package_search", params=params)
    return _extract_result(data)


async def package_show(api_url: str, package_id: str) -> dict[str, Any]:
    """Métadonnées complètes d'un jeu de données."""
    data = await fetch_json(f"{api_url}/package_show", params={"id": package_id})
    return _extract_result(data)


async def resource_show(api_url: str, resource_id: str) -> dict[str, Any]:
    """Détail d'une ressource spécifique."""
    data = await fetch_json(f"{api_url}/resource_show", params={"id": resource_id})
    return _extract_result(data)


async def datastore_search(
    api_url: str,
    resource_id: str,
    q: str | None = None,
    filters: dict[str, str] | None = None,
    fields: list[str] | None = None,
    sort: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Interrogation du DataStore avec filtres."""
    params: dict[str, Any] = {"resource_id": resource_id, "limit": min(limit, 32000), "offset": offset}
    if q:
        params["q"] = q
    if filters:
        params["filters"] = json.dumps(filters)
    if fields:
        params["fields"] = ",".join(fields)
    if sort:
        params["sort"] = sort
    data = await fetch_json(f"{api_url}/datastore_search", params=params)
    return _extract_result(data)


_SQL_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|COPY|MERGE)\b",
    re.IGNORECASE,
)
_SQL_COMMENT_LINE = re.compile(r"--[^\n]*")
_SQL_COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_sql_comments(sql: str) -> str:
    """Retire les commentaires SQL (-- et /* */) avant validation."""
    without_blocks = _SQL_COMMENT_BLOCK.sub(" ", sql)
    return _SQL_COMMENT_LINE.sub(" ", without_blocks)


def validate_sql(sql: str) -> None:
    """Valide qu'une requête SQL est en lecture seule (SELECT / WITH … SELECT).

    Utilise sqlglot (dialecte Postgres, proche du DataStore CKAN) pour une
    analyse AST, puis une ceinture de mots-clés interdits en défense en profondeur.

    Raises:
        ValueError: Si la requête n'est pas une lecture seule sûre.
    """
    import sqlglot
    from sqlglot import exp

    from helpers.common.config import SQL_MAX_LENGTH

    if not sql or not sql.strip():
        msg = "Seules les requêtes SELECT sont autorisées."
        raise ValueError(msg)

    if len(sql) > SQL_MAX_LENGTH:
        msg = f"Requête SQL trop longue ({len(sql)} > {SQL_MAX_LENGTH} caractères max)."
        raise ValueError(msg)

    cleaned = _strip_sql_comments(sql).strip().rstrip(";").strip()
    if not cleaned:
        msg = "Seules les requêtes SELECT sont autorisées."
        raise ValueError(msg)

    try:
        statements = sqlglot.parse(cleaned, read="postgres")
    except sqlglot.errors.ParseError as e:
        msg = f"Requête SQL invalide ou non analysable: {e}"
        raise ValueError(msg) from e

    # Filtrer les statements vides (None) que sqlglot peut produire
    statements = [s for s in statements if s is not None]
    if len(statements) == 0:
        msg = "Seules les requêtes SELECT sont autorisées."
        raise ValueError(msg)
    if len(statements) > 1:
        msg = "Une seule instruction SQL est autorisée."
        raise ValueError(msg)

    root = statements[0]

    def _is_readonly(node: exp.Expr) -> bool:
        """SELECT, UNION/INTERSECT/EXCEPT, ou WITH envelopant une lecture seule."""
        if isinstance(node, exp.Select):
            return True
        if isinstance(node, exp.Union | exp.Intersect | exp.Except):
            return True
        if isinstance(node, exp.With):
            return node.this is not None and _is_readonly(node.this)
        return False

    if not _is_readonly(root):
        msg = "Seules les requêtes SELECT (ou WITH … SELECT) sont autorisées."
        raise ValueError(msg)

    # Rejeter SELECT … INTO (écriture) si présent dans l'AST
    if list(root.find_all(exp.Into)):
        msg = "SELECT INTO n'est pas autorisé."
        raise ValueError(msg)

    # Ceinture de mots-clés interdits (défense en profondeur)
    if _SQL_FORBIDDEN.search(cleaned):
        msg = "La requête contient des instructions interdites (INSERT, UPDATE, DELETE, DROP, etc.)."
        raise ValueError(msg)


async def datastore_search_sql(api_url: str, sql: str) -> dict[str, Any]:
    """Requête SQL directe sur le DataStore (SELECT uniquement)."""
    validate_sql(sql)
    # Pas de cache : résultats dynamiques / potentiellement volumineux
    data = await fetch_json(f"{api_url}/datastore_search_sql", params={"sql": sql}, use_cache=False)
    return _extract_result(data)


async def organization_list(api_url: str, all_fields: bool = False) -> list[Any]:
    """Liste des organisations."""
    data = await fetch_json(f"{api_url}/organization_list", params={"all_fields": str(all_fields).lower()})
    return _extract_result(data)


async def organization_show(api_url: str, org_id: str, include_datasets: bool = False) -> dict[str, Any]:
    """Détail d'une organisation."""
    data = await fetch_json(
        f"{api_url}/organization_show",
        params={"id": org_id, "include_datasets": str(include_datasets).lower()},
    )
    return _extract_result(data)


async def tag_list(api_url: str, query: str | None = None) -> list[str]:
    """Liste des tags."""
    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    data = await fetch_json(f"{api_url}/tag_list", params=params)
    return _extract_result(data)


async def site_read(api_url: str) -> Any:
    """Santé du portail CKAN."""
    data = await fetch_json(f"{api_url}/site_read")
    return _extract_result(data)
