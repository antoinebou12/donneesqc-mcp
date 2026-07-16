"""Client NosOrigines - recherche ASP.NET (ViewState + POST) et fiches pid."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from helpers.common.config import NOSORIGINES_BASE_URL
from helpers.common.http_client import fetch_post_form, fetch_text
from helpers.common.urls import NOSORIGINES_BASE

SOURCE = NOSORIGINES_BASE
SEARCH_PATH = "/genealogieSearch.aspx"
PERSON_PATH = "/GenealogieQuebec.aspx"
CHILDREN_LIMIT = 30
_PID_RE = re.compile(r"pid=(\d+)", re.I)
_PRIVATE_NAMES = frozenset({"privé", "prive", "*****", "****"})


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def extract_aspnet_fields(html: str) -> dict[str, str]:
    """Extrait les champs caches ASP.NET necessaires au POST."""
    soup = _soup(html)
    fields: dict[str, str] = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", "__LASTFOCUS"):
        el = soup.find("input", {"name": name})
        if el is None:
            continue
        raw = el.get("value")
        if isinstance(raw, str):
            fields[name] = raw
    fields.setdefault("__EVENTTARGET", "")
    fields.setdefault("__EVENTARGUMENT", "")
    return fields


def _href_str(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return ""


def parse_search_results(html: str, *, limit: int = 20) -> list[dict[str, Any]]:
    """Parse les resultats de recherche NosOrigines."""
    soup = _soup(html)
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = _href_str(link.get("href"))
        if not re.search(r"Genealogie(Individual)?\.aspx|pid=", href, re.I):
            continue
        text = " ".join(link.get_text(" ", strip=True).split())
        if not text or len(text) < 2:
            continue
        url = urljoin(NOSORIGINES_BASE_URL + "/", href)
        if url in seen:
            continue
        seen.add(url)

        row = link.find_parent("tr")
        extra: dict[str, str] = {}
        if row:
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) >= 2:
                extra["row"] = " | ".join(cells[:6])

        results.append({"name": text, "url": url, **extra})
        if len(results) >= limit:
            break

    if not results:
        for row in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
            if len(cells) < 2:
                continue
            name = cells[0]
            if not name or name.lower() in {"nom", "sexe", "naissance"}:
                continue
            link = row.find("a", href=True)
            href = _href_str(link.get("href")) if link else ""
            url = urljoin(NOSORIGINES_BASE_URL + "/", href) if href else ""
            results.append(
                {
                    "name": name,
                    "url": url,
                    "row": " | ".join(cells[:6]),
                }
            )
            if len(results) >= limit:
                break

    return results


async def search_nosorigines(
    *,
    last_name: str = "",
    first_name: str = "",
    spouse_last_name: str = "",
    spouse_first_name: str = "",
    year_from: str = "",
    match_mode: str = "starting",
    limit: int = 20,
) -> dict[str, Any]:
    """Recherche personnes / couples sur NosOrigines."""
    search_url = f"{NOSORIGINES_BASE_URL}{SEARCH_PATH}?lng=fr"
    form_html = await fetch_text(search_url)
    tokens = extract_aspnet_fields(form_html)

    mode_map = {
        "starting": "rbStarting",
        "exact": "rbExact",
        "alias": "rbAlias",
        "soundex": "rbSoundex",
    }
    radio = mode_map.get(match_mode.lower(), "rbStarting")
    couple_search = bool(spouse_last_name or spouse_first_name)

    data: dict[str, Any] = {
        **tokens,
        "grpSpelling": radio,
        radio: radio,
        "txbNameMen": last_name if couple_search else "",
        "txbFirstNameMen": first_name if couple_search else "",
        "txbNameWomen": spouse_last_name,
        "txbFirstNameWomen": spouse_first_name,
        "txbYearInMen": year_from,
        "txbNameChild": "" if couple_search else last_name,
        "txbFirstNameChild": "" if couple_search else first_name,
        "btnSearch": "Rechercher",
    }

    result_html = await fetch_post_form(
        search_url,
        data,
        headers={"Referer": search_url, "Content-Type": "application/x-www-form-urlencoded"},
    )
    results = parse_search_results(result_html, limit=limit)

    return {
        "query": {
            "last_name": last_name,
            "first_name": first_name,
            "spouse_last_name": spouse_last_name,
            "spouse_first_name": spouse_first_name,
            "year_from": year_from,
            "match_mode": match_mode,
        },
        "total_returned": len(results),
        "results": results,
        "source": SOURCE,
        "search_url": search_url,
        "note": "HTML scraping ASP.NET (ViewState) - structure fragile si le site change.",
    }


def validate_pid(pid: str) -> str:
    """Retourne un pid numerique ou leve ValueError."""
    cleaned = (pid or "").strip()
    if not cleaned.isdigit():
        raise ValueError("pid invalide: chiffres uniquement.")
    return cleaned


def _norm_text(value: str | None) -> str:
    return " ".join((value or "").split())


def _is_private_name(name: str) -> bool:
    return _norm_text(name).lower() in _PRIVATE_NAMES or name.strip() == "*****"


def _pid_from_href(href: str) -> str | None:
    match = _PID_RE.search(href)
    return match.group(1) if match else None


def _label_value_map(table: Tag | None) -> dict[str, str]:
    """Mappe les libelles de ligne (Prénom, Nom, …) vers les valeurs td.

    Les doublons (ex. Paroisse/ville naissance vs deces) deviennent
    ``paroisse/ville`` (premiere) et ``paroisse/ville_death`` (suivantes).
    """
    out: dict[str, str] = {}
    if table is None:
        return out
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        raw_label = _norm_text(cells[0].get_text(" ", strip=True)).rstrip(":")
        # Normalise ID No / ID Nº
        label = raw_label.lower().replace("º", "o").replace("°", "o")
        label = re.sub(r"\s+", " ", label)
        value = _norm_text(cells[1].get_text(" ", strip=True))
        if not label:
            continue
        if label in out and label in {"paroisse/ville", "pays"}:
            out[f"{label}_death"] = value
        elif label not in out:
            out[label] = value
        else:
            out[label] = value
    return out


def _parse_pedigree_block(div: Tag | None) -> dict[str, Any] | None:
    """Parse #genealogyMale / #genealogyFemale (parents de la personne ou du conjoint)."""
    if div is None:
        return None
    text = _norm_text(div.get_text(" ", strip=True))
    link = div.find("a", href=True)
    href = _href_str(link.get("href")) if link else ""
    name = _norm_text(link.get_text(" ", strip=True)) if link else ""
    if not name:
        # "Inconnu …" sans lien
        for strong in div.find_all("strong"):
            candidate = _norm_text(strong.get_text(" ", strip=True))
            if candidate.lower() not in {"père", "pere", "mère", "mere"} and not candidate.isdigit():
                name = candidate
                break
    if not name and "inconnu" in text.lower():
        name = text
    pid = _pid_from_href(href)
    birth_m = re.search(r"Naissance:\s*(.*?)(?:Décès:|$)", text, re.I | re.S)
    death_m = re.search(r"Décès:\s*(.*?)$", text, re.I | re.S)
    birth = _norm_text(birth_m.group(1)) if birth_m else ""
    death = _norm_text(death_m.group(1)) if death_m else ""
    if not name and not pid:
        return None
    return {
        "pid": pid,
        "name": "Privé" if _is_private_name(name) else name,
        "birth": birth,
        "death": death,
        "is_private": _is_private_name(name),
        "url": urljoin(NOSORIGINES_BASE_URL + "/", href) if href else None,
    }


def _parse_marriage(div: Tag | None) -> dict[str, str] | None:
    if div is None:
        return None
    lines = [_norm_text(line) for line in div.get_text("\n", strip=True).split("\n") if _norm_text(line)]
    # Drop heading
    body = [ln for ln in lines if ln.lower() not in {"mariage ou union de fait"}]
    if not body:
        return None
    summary = body[0] if body else ""
    date = ""
    place_parts: list[str] = []
    country = ""
    source = ""
    bold = div.find("b")
    if bold:
        date = _norm_text(bold.get_text(" ", strip=True))
    for ln in body[1:]:
        lower = ln.lower()
        if lower.startswith("source:"):
            source = ln.split(":", 1)[-1].strip()
        elif ln == date:
            continue
        elif not place_parts:
            place_parts.append(ln)
        elif not country and ln.lower() in {"canada", "france", "états-unis", "etats-unis", "usa"}:
            country = ln
        elif not country:
            place_parts.append(ln)
    return {
        "date": date,
        "place": ", ".join(place_parts),
        "country": country,
        "summary": summary,
        "source": source,
    }


def _parse_children_table(soup: BeautifulSoup, *, married: bool, limit: int) -> list[dict[str, Any]]:
    """Parse tables enfants mariés (rptKids1) ou célibataires (rptKids1C)."""
    marker = "enfants mariés" if married else "enfants célibataires"
    heading: Tag | None = None
    for strong in soup.find_all("strong"):
        if marker in _norm_text(strong.get_text(" ", strip=True)).lower():
            heading = strong
            break
    if heading is None:
        return []
    # Nearest following table with Nom header
    table = None
    parent_row = heading.find_parent("tr")
    container = parent_row.find_parent("table") if parent_row else heading.find_parent("table")
    search_root = container or soup
    for candidate in search_root.find_all("table"):
        header = _norm_text(candidate.get_text(" ", strip=True)).lower()
        if "nom" in header and "naissance" in header:
            table = candidate
            break
    if table is None:
        # Walk siblings after heading's table
        node = heading
        for _ in range(12):
            node = node.find_next("table")
            if node is None:
                break
            header = _norm_text(node.get_text(" ", strip=True)[:80]).lower()
            if "nom" in header:
                table = node
                break
    if table is None:
        return []

    children: list[dict[str, Any]] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        link = cells[0].find("a", href=True)
        name = _norm_text(cells[0].get_text(" ", strip=True))
        if not name or name.lower() == "nom":
            continue
        href = _href_str(link.get("href")) if link else ""
        child: dict[str, Any] = {
            "pid": _pid_from_href(href),
            "name": "Privé" if _is_private_name(name) else name,
            "birth": _norm_text(cells[1].get_text(" ", strip=True)),
            "death": _norm_text(cells[2].get_text(" ", strip=True)),
            "is_private": _is_private_name(name),
            "url": urljoin(NOSORIGINES_BASE_URL + "/", href) if href else None,
        }
        if married and len(cells) >= 6:
            child["spouse"] = _norm_text(cells[5].get_text(" ", strip=True))
        children.append(child)
        if len(children) >= limit:
            break
    return children


def _fiche_notes(table: Tag | None) -> str:
    if table is None:
        return ""
    for row in table.find_all("tr"):
        text = _norm_text(row.get_text(" ", strip=True))
        if text.lower().startswith("information, autres enfants"):
            # Drop the heading prefix
            rest = re.sub(
                r"^Information,\s*autres enfants,\s*notes,\s*etc\.?\s*",
                "",
                text,
                flags=re.I,
            )
            return _norm_text(rest)
    return ""


def _death_note_from_map(fields: dict[str, str]) -> str:
    for key in ("inh./source", "inh/source", "inh. / source"):
        if key in fields:
            return fields[key]
    for key, value in fields.items():
        if "source" in key and "inh" in key:
            return value
    return ""


def parse_person_page(html: str, *, pid: str, children_limit: int = CHILDREN_LIMIT) -> dict[str, Any]:
    """Parse une fiche GenealogieQuebec.aspx (ancres DOM stables)."""
    soup = _soup(html)
    url = f"{NOSORIGINES_BASE_URL}{PERSON_PATH}?pid={pid}"

    men = soup.find("table", class_="genealogical_Record_Men")
    women = soup.find("table", class_="genealogical_Record_Women")
    men_fields = _label_value_map(men)
    women_fields = _label_value_map(women)

    first_name = men_fields.get("prénom", men_fields.get("prenom", ""))
    last_name = men_fields.get("nom", "")
    if men:
        for row in men.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2 and _norm_text(cells[0].get_text()).lower().startswith("nom"):
                bold = cells[1].find("b")
                if bold:
                    last_name = _norm_text(bold.get_text(" ", strip=True))
                break

    name = _norm_text(f"{first_name} {last_name}")
    title = _norm_text(soup.title.get_text() if soup.title else "")
    title_private = title.lower() in {"privé", "prive"} or title.lower().startswith("privé")
    is_private = _is_private_name(name) or _is_private_name(first_name) or title_private
    if is_private:
        first_name = "Privé"
        last_name = ""
        name = "Privé"

    birth = men_fields.get("baptême", "") or men_fields.get("bapteme", "") or men_fields.get("naissance", "")
    death = men_fields.get("décès", "") or men_fields.get("deces", "")

    father = _parse_pedigree_block(soup.find(id="genealogyMale"))
    mother = _parse_pedigree_block(soup.find(id="genealogyFemale"))
    spouse_father = _parse_pedigree_block(soup.find(id="genealogyMaleB"))
    spouse_mother = _parse_pedigree_block(soup.find(id="genealogyFemaleB"))

    spouse: dict[str, Any] | None = None
    if women is not None:
        s_first = women_fields.get("prénom", women_fields.get("prenom", ""))
        s_last = women_fields.get("nom", "")
        conj_fn = soup.find(id="hlnkConjointFirstname")
        conj_ln = soup.find(id="hlnkConjointName")
        if conj_fn:
            s_first = _norm_text(conj_fn.get_text(" ", strip=True)) or s_first
        if conj_ln:
            s_last = _norm_text(conj_ln.get_text(" ", strip=True)) or s_last
        s_href = ""
        if conj_fn and conj_fn.get("href"):
            s_href = _href_str(conj_fn.get("href"))
        elif conj_ln and conj_ln.get("href"):
            s_href = _href_str(conj_ln.get("href"))
        s_pid = women_fields.get("id no", women_fields.get("id nº", ""))
        s_pid = re.sub(r"\D", "", s_pid) or _pid_from_href(s_href)
        s_name = _norm_text(f"{s_first} {s_last}")
        s_private = _is_private_name(s_name)
        spouse = {
            "pid": s_pid or None,
            "first_name": "Privé" if s_private else s_first,
            "last_name": "" if s_private else s_last,
            "name": "Privé" if s_private else s_name,
            "is_private": s_private,
            "sex": women_fields.get("sexe", ""),
            "occupation": women_fields.get("occupation", ""),
            "birth": women_fields.get("naissance", "") or women_fields.get("baptême", women_fields.get("bapteme", "")),
            "birth_place": women_fields.get("paroisse/ville", ""),
            "birth_country": women_fields.get("pays", ""),
            "death": women_fields.get("décès", women_fields.get("deces", "")),
            "url": urljoin(NOSORIGINES_BASE_URL + "/", s_href) if s_href else None,
        }

    marriage = _parse_marriage(soup.find(id="divMarriage"))

    return {
        "pid": pid,
        "url": url,
        "first_name": first_name,
        "last_name": last_name,
        "name": name,
        "is_private": is_private,
        "sex": men_fields.get("sexe", ""),
        "occupation": men_fields.get("occupation", ""),
        "birth": birth,
        "birth_place": men_fields.get("paroisse/ville", ""),
        "birth_country": men_fields.get("pays", ""),
        "death": death,
        "death_place": men_fields.get("paroisse/ville_death", ""),
        "death_country": men_fields.get("pays_death", ""),
        "death_note": _death_note_from_map(men_fields),
        "notes": _fiche_notes(men),
        "father": father,
        "mother": mother,
        "spouse": spouse,
        "spouse_father": spouse_father,
        "spouse_mother": spouse_mother,
        "marriage": marriage,
        "children_married": _parse_children_table(soup, married=True, limit=children_limit),
        "children_unmarried": _parse_children_table(soup, married=False, limit=children_limit),
        "source": SOURCE,
        "note": "HTML scraping GenealogieQuebec - structure fragile si le site change.",
    }


def _slim_person(person: dict[str, Any]) -> dict[str, Any]:
    return {
        "pid": person.get("pid"),
        "name": person.get("name"),
        "is_private": person.get("is_private", False),
        "birth": person.get("birth", ""),
        "death": person.get("death", ""),
        "url": person.get("url"),
        "father": person.get("father"),
        "mother": person.get("mother"),
    }


async def get_person(pid: str, *, children_limit: int = CHILDREN_LIMIT) -> dict[str, Any]:
    """Recupere et parse une fiche personne NosOrigines."""
    clean = validate_pid(pid)
    url = f"{NOSORIGINES_BASE_URL}{PERSON_PATH}?pid={clean}"
    html = await fetch_text(url)
    return parse_person_page(html, pid=clean, children_limit=children_limit)


async def get_ancestors(
    pid: str,
    *,
    generations: int = 2,
) -> dict[str, Any]:
    """Arbre paternal/maternal via get_person (1-3 generations)."""
    clean = validate_pid(pid)
    gens = max(1, min(int(generations), 3))
    cache: dict[str, dict[str, Any]] = {}

    async def _fetch(target: str) -> dict[str, Any]:
        if target in cache:
            return cache[target]
        data = await get_person(target)
        cache[target] = data
        return data

    async def _branch(target_pid: str | None, depth: int, *, full: bool) -> dict[str, Any] | None:
        if not target_pid or depth < 1:
            return None
        try:
            person = await _fetch(target_pid)
        except Exception as exc:
            return {"pid": target_pid, "error": str(exc), "father": None, "mother": None}
        node_person = person if full else _slim_person(person)
        father_pid = (person.get("father") or {}).get("pid")
        mother_pid = (person.get("mother") or {}).get("pid")
        return {
            "person": node_person,
            "father": await _branch(father_pid, depth - 1, full=False) if depth > 1 else None,
            "mother": await _branch(mother_pid, depth - 1, full=False) if depth > 1 else None,
        }

    root = await _fetch(clean)
    father_pid = (root.get("father") or {}).get("pid")
    mother_pid = (root.get("mother") or {}).get("pid")

    return {
        "pid": clean,
        "generations": gens,
        "person": root,
        "father": await _branch(father_pid, gens, full=False),
        "mother": await _branch(mother_pid, gens, full=False),
        "source": SOURCE,
    }
