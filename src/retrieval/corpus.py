"""
Loading, chunking and BM25 retrieval over the official corpus.

Two decisions worth knowing:

- Chunks follow the document's own structure. The "## heading" and "[CASE] ..." markers
  written by the ingest step are natural boundaries, and keeping them in the chunk means
  every hit arrives with its own context.
- Every chunk carries its parent document's metadata forward, above all the official
  update date and the canonical URL. Those two fields are what the whole product's
  claim-by-claim verdicts rest on, so no transformation may drop them.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"

# Common French stopwords, dropped at query time to cut noise
STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "à",
    "au", "aux", "en", "dans", "pour", "par", "sur", "sous", "avec", "sans",
    "ce", "cet", "cette", "ces", "qui", "que", "quoi", "dont", "où", "il",
    "elle", "ils", "elles", "vous", "nous", "je", "tu", "on", "se", "sa", "son",
    "ses", "leur", "leurs", "est", "sont", "être", "avoir", "plus", "moins",
    "si", "ne", "pas", "y", "l", "s", "n", "c", "j", "m", "t", "qu", "vos",
    "votre", "the", "of", "and",
}

# The official themes an international student actually needs
STUDENT_THEMES = {
    "Étranger - Europe",
    "Logement",
    "Social - Santé",
    "Argent - Impôts - Consommation",
    "Travail - Formation",
    "Papiers - Citoyenneté - Élections",
}


def normalize(text):
    """Lowercase and strip accents, so 'séjour' and 'sejour' match each other."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text):
    tokens = re.findall(r"[a-z0-9]+", normalize(text))
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


@dataclass
class Chunk:
    doc_id: str
    title: str
    url: str
    theme: str
    section: str          # the heading or case label this chunk sits under
    text: str
    last_update: str      # official last-updated date — what recency verdicts rest on
    legal_refs: list = field(default_factory=list)
    online_services: list = field(default_factory=list)

    def as_result(self, score=None):
        d = {
            "doc_id": self.doc_id,
            "title": self.title,
            "section": self.section,
            "text": self.text,
            "official_url": self.url,
            "last_official_update": self.last_update or "not stated",
            "theme": self.theme,
        }
        if self.legal_refs:
            d["legal_refs"] = self.legal_refs[:3]
        if self.online_services:
            d["online_services"] = self.online_services[:3]
        if score is not None:
            d["score"] = round(float(score), 3)
        return d


def split_sections(body):
    """Split the body into (section name, text) on "## heading" and "[CASE] ..." markers."""
    sections = []
    current_name = ""
    buf = []

    for line in body.split("\n"):
        heading = None
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        elif line.startswith("[CASE]"):
            heading = line.replace("[CASE]", "").strip()
            heading = f"Case: {heading}"

        if heading:
            if buf:
                sections.append((current_name, "\n".join(buf).strip()))
                buf = []
            current_name = heading
        else:
            buf.append(line)

    if buf:
        sections.append((current_name, "\n".join(buf).strip()))

    return [(n, t) for n, t in sections if t]


def build_chunks(doc, max_chars=1200):
    """Cut one fiche into retrievable chunks, splitting overlong sections by length."""
    chunks = []
    last_update = doc.get("last_major_update") or doc.get("modified") or ""

    sections = split_sections(doc["body"]) or [("", doc["body"])]
    # The summary becomes its own chunk, so "what is this document about" can match
    if doc.get("description"):
        sections.insert(0, ("Summary", doc["description"]))

    for name, text in sections:
        pieces = [text]
        if len(text) > max_chars:
            pieces = [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
        for piece in pieces:
            chunks.append(Chunk(
                doc_id=doc["id"],
                title=doc["title"],
                url=doc["url"],
                theme=doc.get("theme", ""),
                section=name,
                text=piece.strip(),
                last_update=last_update,
                legal_refs=doc.get("legal_refs", []),
                online_services=doc.get("online_services", []),
            ))
    return chunks


class OfficialCorpus:
    """The official corpus and its BM25 index."""

    def __init__(self, path=CORPUS_PATH, themes=None):
        self.docs = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                if themes and not any(t in doc.get("theme", "") for t in themes):
                    continue
                self.docs.append(doc)

        self.chunks = []
        for doc in self.docs:
            self.chunks.extend(build_chunks(doc))

        corpus_tokens = [
            tokenize(f"{c.title} {c.section} {c.text}") for c in self.chunks
        ]
        self.bm25 = BM25Okapi(corpus_tokens)

    def search(self, query, top_k=6, theme=None):
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = []
        seen_sections = set()
        for i in order:
            if scores[i] <= 0:
                break
            chunk = self.chunks[i]
            if theme and theme not in chunk.theme:
                continue
            key = (chunk.doc_id, chunk.section)
            if key in seen_sections:
                continue
            seen_sections.add(key)
            results.append(chunk.as_result(scores[i]))
            if len(results) >= top_k:
                break
        return results

    def stats(self):
        return {"documents": len(self.docs), "chunks": len(self.chunks)}


@lru_cache(maxsize=1)
def get_corpus():
    """Process-wide singleton — building the index costs a second, so do it once."""
    return OfficialCorpus(themes=STUDENT_THEMES)
