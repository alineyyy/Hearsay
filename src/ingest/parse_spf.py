"""
Parse the service-public.fr open data (XML) into a retrievable corpus.

    in:  data/spf_raw/*.xml   (5,552 official fiches)
    out: data/corpus.jsonl    (one document per line)

Source: Service-Public.gouv.fr / DILA, published via data.gouv.fr.
Licence: Licence Ouverte 2.0 (Etalab) — reuse requires naming the source and the date.
"""

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DC = "{http://purl.org/dc/elements/1.1/}"

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "spf_raw"
OUT_PATH = ROOT / "data" / "corpus.jsonl"

# These elements are containers; they contribute no readable text of their own
SKIP_TEXT_TAGS = {"Source", "Commentaire"}


def clean(s):
    """Collapse whitespace and normalise non-breaking spaces."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def node_text(el):
    """Recursively collect all readable text under a node."""
    parts = []
    if el.tag not in SKIP_TEXT_TAGS:
        if el.text:
            parts.append(el.text)
        for child in el:
            parts.append(node_text(child))
            if child.tail:
                parts.append(child.tail)
    return " ".join(p for p in parts if p)


def render_block(el, out, depth=0):
    """
    Flatten the body into text lines that keep their heading hierarchy.

    Cas blocks matter most: the official documents use them to branch by situation
    (student, employee, this nationality, that timeline), which is exactly where the
    answer to an edge-case question lives. Their labels are preserved as [CASE] markers.
    """
    tag = el.tag

    if tag in ("Chapitre", "SousChapitre"):
        title = el.find("Titre")
        if title is not None:
            out.append(("#" * min(depth + 2, 5)) + " " + clean(node_text(title)))
        for child in el:
            if child.tag != "Titre":
                render_block(child, out, depth + 1)

    elif tag == "BlocCas":
        for child in el:
            render_block(child, out, depth)

    elif tag == "Cas":
        title = el.find("Titre")
        label = clean(node_text(title)) if title is not None else ""
        if label:
            out.append(f"[CASE] {label}")
        for child in el:
            if child.tag != "Titre":
                render_block(child, out, depth)

    elif tag in ("Titre", "TitreRiche"):
        t = clean(node_text(el))
        if t:
            out.append(("#" * min(depth + 2, 5)) + " " + t)

    elif tag == "Liste":
        for item in el.findall("Item"):
            t = clean(node_text(item))
            if t:
                out.append("- " + t)

    elif tag == "Tableau":
        for row in el.iter("Rangée"):
            cells = [clean(node_text(c)) for c in row]
            cells = [c for c in cells if c]
            if cells:
                out.append(" | ".join(cells))

    elif tag == "OuSAdresser":
        t = clean(node_text(el))
        if t:
            out.append("[WHERE TO APPLY] " + t)

    elif tag in ("Paragraphe", "Texte", "Introduction"):
        if tag == "Paragraphe":
            t = clean(node_text(el))
            if t:
                out.append(t)
        else:
            for child in el:
                render_block(child, out, depth)

    else:
        # Anything else is a container — keep descending
        for child in el:
            render_block(child, out, depth)


def parse_fiche(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None

    if root.tag != "Publication":
        return None

    def dc(name):
        el = root.find(DC + name)
        return clean(el.text) if el is not None and el.text else ""

    fid = root.get("ID") or dc("identifier")
    title = dc("title")
    if not fid or not title:
        return None

    # Update dates — the fields the recency verdicts depend on
    last_major = (root.get("dateDerniereModificationImportante") or "")[:10]
    modified = ""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", dc("date"))
    if m:
        modified = m.group(1)

    breadcrumb = [
        clean(n.text) for n in root.findall("./FilDAriane/Niveau") if n.text
    ]

    body_lines = []
    intro = root.find("Introduction")
    if intro is not None:
        render_block(intro, body_lines, 0)
    for texte in root.findall("Texte"):
        render_block(texte, body_lines, 0)

    body = "\n".join(l for l in body_lines if l.strip())

    def links(tag):
        res = []
        for el in root.findall(tag):
            t = el.find("Titre")
            res.append({
                "title": clean(node_text(t)) if t is not None else "",
                "url": el.get("URL", ""),
                "cerfa": el.get("numerocerfa", ""),
            })
        return [r for r in res if r["title"] or r["url"]]

    return {
        "id": fid,
        "title": title,
        "description": dc("description"),
        "url": root.get("spUrl", f"https://www.service-public.gouv.fr/particuliers/vosdroits/{fid}"),
        "theme": dc("subject"),
        "doc_type": dc("type"),
        "audience": clean((root.findtext("Audience") or "")),
        "breadcrumb": breadcrumb,
        "last_major_update": last_major,
        "modified": modified,
        "body": body,
        "legal_refs": links("Reference"),
        "online_services": links("ServiceEnLigne"),
        "more_info": links("PourEnSavoirPlus"),
    }


def main():
    files = sorted(RAW_DIR.glob("*.xml"))
    if not files:
        sys.exit(f"No raw data found. Unzip the dataset into {RAW_DIR} first.")

    n_ok = 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for fp in files:
            doc = parse_fiche(fp)
            if doc and doc["body"]:
                out.write(json.dumps(doc, ensure_ascii=False) + "\n")
                n_ok += 1

    print(f"Parsed {n_ok} of {len(files)} files -> {OUT_PATH}")


if __name__ == "__main__":
    main()
