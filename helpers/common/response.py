"""Enveloppe de réponse MCP avec citations / métadonnées source."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

DISCLAIMER = "Community MCP - not an official Gouvernement du Québec service. Verify dataset licence before reuse."


def _retrieved_at(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def ok(
    payload: dict[str, Any],
    *,
    source: str,
    portal_url: str | None = None,
    dataset_id: str | None = None,
    resource_id: str | None = None,
    license: str | None = None,  # noqa: A002 - API field name matches CKAN
    retrieved_at: str | None = None,
    metadata_modified: str | None = None,
) -> str:
    """Sérialise une réponse réussie avec enveloppe `_meta` additive."""
    meta: dict[str, Any] = {
        "source": source,
        "retrieved_at": _retrieved_at(retrieved_at),
        "disclaimer": DISCLAIMER,
    }
    if portal_url is not None:
        meta["portal_url"] = portal_url
    if dataset_id is not None:
        meta["dataset_id"] = dataset_id
    if resource_id is not None:
        meta["resource_id"] = resource_id
    if license is not None:
        meta["license"] = license
    if metadata_modified is not None:
        meta["metadata_modified"] = metadata_modified

    body = {**payload, "_meta": meta}
    return json.dumps(body, ensure_ascii=False, indent=2)


def error(message: str, *, code: str | None = None, **details: Any) -> str:
    """Sérialise une erreur sans citation factice."""
    body: dict[str, Any] = {"error": message}
    if code is not None:
        body["code"] = code
    body.update(details)
    return json.dumps(body, ensure_ascii=False)
