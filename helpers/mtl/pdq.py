"""Dictionnaire SPVM des postes de quartier (PDQ).

Noms complets tirés des titres des pages officielles
``https://spvm.qc.ca/fr/PDQ{n}`` (consultées 2026-07-16).

Territoires / polygones : jeu ouvert
https://donnees.montreal.ca/dataset/limites-pdq-spvm
(attention : le champ ``NOM_PDQ`` du CSV vaut seulement ``PDQ-N``,
pas le nom de quartier - d'où ce dictionnaire statique).
"""

from __future__ import annotations

from typing import Any

# Titres multi-secteurs officiels SPVM.
PDQ_NAMES: dict[str, str] = {
    "1": "Baie-D'Urfé, Beaconsfield, Kirkland, Sainte-Anne-de-Bellevue, Senneville",
    "3": "L'Île-Bizard, Pierrefonds, Sainte-Geneviève, Roxboro",
    "4": "Dollard-Des Ormeaux",
    "5": "Dorval, L'Île-Dorval, Pointe-Claire",
    "7": "Arrondissement de Saint-Laurent",
    "8": "Lachine, Saint-Pierre",
    "9": "Notre-Dame-De-Grâce, Côte Saint-Luc, Hampstead, Montréal-Ouest",
    "10": "Bordeaux, Cartierville",
    "12": "Ville-Marie Ouest, Westmount",
    "13": "LaSalle",
    "15": "Saint-Paul, Petite-Bourgogne, Pointe-Saint-Charles, Saint-Henri, Ville-Émard",
    "16": "Île-des-Sœurs, Verdun",
    "20": "Centre-ville (Ville-Marie Ouest), parc du Mont-Royal",
    "21": "Centre-ville (Ville-Marie Est), Centre-Sud, Île Notre-Dame, Île Sainte-Hélène, Vieux-Montréal",
    "23": "Hochelaga-Maisonneuve",
    "26": "Côte-des-Neiges, Mont-Royal, Outremont",
    "27": "Ahuntsic",
    "30": "Saint-Michel",
    "31": "Villeray, Parc-Extension",
    "35": "La Petite-Italie, La Petite-Patrie, Outremont (3 rues)",
    "38": "Le Plateau-Mont-Royal",
    "39": "Arrondissement de Montréal-Nord",
    "42": "Saint-Léonard",
    "44": "Rosemont - La Petite-Patrie",
    "45": "Rivière-des-Prairies",
    "46": "Anjou",
    "48": "Arrondissement de Mercier-Hochelaga-Maisonneuve",
    "49": "Ville de Montréal-Est, Pointe-aux-Trembles",
    "50": "Métro de Montréal",
}

# Libellés courts pour tableaux (secteur principal).
PDQ_SHORT: dict[str, str] = {
    "1": "Ouest-de-l'Île",
    "3": "Pierrefonds / Île-Bizard",
    "4": "Dollard-Des Ormeaux",
    "5": "Pointe-Claire / Dorval",
    "7": "Saint-Laurent",
    "8": "Lachine",
    "9": "NDG / Côte Saint-Luc",
    "10": "Cartierville",
    "12": "Ville-Marie Ouest / Westmount",
    "13": "LaSalle",
    "15": "Sud-Ouest",
    "16": "Verdun",
    "20": "Ville-Marie Ouest",
    "21": "Centre-Sud / Ville-Marie Est",
    "23": "Hochelaga-Maisonneuve",
    "26": "Côte-des-Neiges / Outremont",
    "27": "Ahuntsic",
    "30": "Saint-Michel",
    "31": "Villeray / Parc-Extension",
    "35": "Petite-Patrie",
    "38": "Plateau-Mont-Royal",
    "39": "Montréal-Nord",
    "42": "Saint-Léonard",
    "44": "Rosemont",
    "45": "Rivière-des-Prairies",
    "46": "Anjou",
    "48": "Mercier-Hochelaga-Maisonneuve",
    "49": "Pointe-aux-Trembles",
    "50": "Métro",
}


def _normalize_pdq(pdq: Any) -> str:
    """Normalise un code PDQ en chaîne sans zéro inutile."""
    if pdq is None:
        return ""
    text = str(pdq).strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except (TypeError, ValueError):
        return text


def pdq_name(pdq: Any) -> str | None:
    """Retourne le titre SPVM complet, ou None si inconnu."""
    key = _normalize_pdq(pdq)
    return PDQ_NAMES.get(key)


def pdq_label(pdq: Any) -> str:
    """Libellé tableau ``N (secteur)`` ; code seul si inconnu."""
    key = _normalize_pdq(pdq)
    if not key:
        return ""
    short = PDQ_SHORT.get(key)
    if short:
        return f"{key} ({short})"
    return key


def enrich_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ajoute ``pdq_name`` / ``pdq_label`` aux lignes qui ont une colonne PDQ.

    Ne mute pas les dictionnaires d'origine.
    """
    enriched: list[dict[str, Any]] = []
    for row in records:
        copy = dict(row)
        if "PDQ" in copy and copy["PDQ"] is not None and str(copy["PDQ"]).strip() != "":
            name = pdq_name(copy["PDQ"])
            if name is not None:
                copy["pdq_name"] = name
            copy["pdq_label"] = pdq_label(copy["PDQ"])
        enriched.append(copy)
    return enriched
