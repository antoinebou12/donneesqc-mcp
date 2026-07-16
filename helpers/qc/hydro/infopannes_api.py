"""Client HTTP pour l'API publique Info-pannes (Hydro-Québec)."""

from __future__ import annotations

import uuid
from typing import Any

from helpers.common.config import HYDRO_INFOPANNES_API_URL, HYDRO_INFOPANNES_PORTAL_URL
from helpers.common.http_client import fetch_json
from helpers.qc.hydro.address_resolve import normalize_postal_code

ETAT_LABELS: dict[str, str] = {
    "A": "alimenté",
    "N": "non alimenté",
}

INFO_NOTE = (
    "Donnees Info-pannes approximatives; wrapper communautaire non affilie a Hydro-Quebec. "
    f"Verifiez toujours sur {HYDRO_INFOPANNES_PORTAL_URL}"
)


def _api_base() -> str:
    return HYDRO_INFOPANNES_API_URL.rstrip("/")


async def lookup_lieux_conso(
    *,
    street_number: str,
    street: str,
    postal_code: str,
    appartement: str | None = None,
    hq_token: str | None = None,
) -> list[dict[str, Any]]:
    """GET /api/v1/lieux-conso - lieux de consommation pour une adresse civique."""
    token = hq_token or str(uuid.uuid4())
    params = {
        "codePostal": normalize_postal_code(postal_code),
        "numeroCivique": street_number.strip(),
        "nomRue": street.strip(),
        "numeroAppartement": (appartement or "").strip(),
        "hqToken": token,
    }
    data = await fetch_json(f"{_api_base()}/api/v1/lieux-conso", params=params)
    if not isinstance(data, list):
        msg = "Reponse inattendue de lieux-conso (liste JSON attendue)."
        raise TypeError(msg)
    return data


async def get_etats(lieu_ids: list[str]) -> list[dict[str, Any]]:
    """GET /api/v1/lieux-conso/etats/{id}[,{id2},…] - états de service."""
    cleaned = [lid.strip() for lid in lieu_ids if lid and str(lid).strip()]
    if not cleaned:
        msg = "Aucun identifiant de lieu de consommation fourni."
        raise ValueError(msg)
    path_ids = ",".join(cleaned)
    data = await fetch_json(f"{_api_base()}/api/v1/lieux-conso/etats/{path_ids}")
    if not isinstance(data, list):
        msg = "Reponse inattendue de lieux-conso/etats (liste JSON attendue)."
        raise TypeError(msg)
    return data


def format_lieu_status(
    lieu: dict[str, Any],
    etat: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fusionne un lieu de conso et son état pour la réponse MCP."""
    code = (etat or {}).get("etat")
    interruptions = (etat or {}).get("interruptions") or []
    return {
        "lieu_consommation": lieu.get("lieuConsommation") or (etat or {}).get("idLieuConso"),
        "adresse_complete": lieu.get("adresseCompleteFr") or lieu.get("adresseCompleteEn"),
        "eligible": lieu.get("eligible"),
        "etat": code,
        "etat_label": ETAT_LABELS.get(str(code), str(code) if code is not None else None),
        "date": (etat or {}).get("date"),
        "reprise_graduelle_possible": (etat or {}).get("repriseGraduellePossible"),
        "interruptions": interruptions,
        "has_outage": bool(interruptions) or code == "N",
    }


async def outage_status_for_civic(
    *,
    street_number: str,
    street: str,
    postal_code: str,
    appartement: str | None = None,
) -> dict[str, Any]:
    """Lookup lieux + états pour des champs civiques déjà résolus."""
    lieux = await lookup_lieux_conso(
        street_number=street_number,
        street=street,
        postal_code=postal_code,
        appartement=appartement,
    )
    if not lieux:
        msg = (
            "Aucun lieu de consommation Hydro-Quebec trouve pour cette adresse. "
            "Verifiez le numero, la rue, le code postal et l'appartement."
        )
        raise ValueError(msg)

    ids = [str(item.get("lieuConsommation") or "") for item in lieux]
    ids = [i for i in ids if i]
    etats = await get_etats(ids) if ids else []
    etat_by_id = {str(e.get("idLieuConso")): e for e in etats}

    formatted = [format_lieu_status(lieu, etat_by_id.get(str(lieu.get("lieuConsommation")))) for lieu in lieux]
    return {
        "total": len(formatted),
        "lieux": formatted,
        "note": INFO_NOTE,
    }
