"""
官方语料库的加载、切块与 BM25 检索。

设计要点:
- 按章节切块:正文里的 "## 标题" 和 "[情况] xxx" 是天然的边界,
  切块时保留这些标签,让检索结果自带上下文。
- 每个块都带回父文档的元数据,尤其是【官方更新日期】和【官方链接】——
  这两个字段是整个产品"可信度分层"的基础,不能丢。
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

# 法语常见停用词(检索时剔除,避免噪音)
STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "à",
    "au", "aux", "en", "dans", "pour", "par", "sur", "sous", "avec", "sans",
    "ce", "cet", "cette", "ces", "qui", "que", "quoi", "dont", "où", "il",
    "elle", "ils", "elles", "vous", "nous", "je", "tu", "on", "se", "sa", "son",
    "ses", "leur", "leurs", "est", "sont", "être", "avoir", "plus", "moins",
    "si", "ne", "pas", "y", "l", "s", "n", "c", "j", "m", "t", "qu", "vos",
    "votre", "the", "of", "and",
}

# 与留学生强相关的主题(检索时可按此过滤)
STUDENT_THEMES = {
    "Étranger - Europe",
    "Logement",
    "Social - Santé",
    "Argent - Impôts - Consommation",
    "Travail - Formation",
    "Papiers - Citoyenneté - Élections",
}


def normalize(text):
    """小写 + 去重音,让 'séjour' 和 'sejour' 能互相命中。"""
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
    section: str          # 该块所属的章节标题 / 情况标签
    text: str
    last_update: str      # 官方最后更新日期 —— 判断时效性用
    legal_refs: list = field(default_factory=list)
    online_services: list = field(default_factory=list)

    def as_result(self, score=None):
        d = {
            "doc_id": self.doc_id,
            "title": self.title,
            "section": self.section,
            "text": self.text,
            "official_url": self.url,
            "last_official_update": self.last_update or "未标注",
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
    """按 '## 标题' 和 '[情况] xxx' 把正文切成 (章节名, 内容) 段落。"""
    sections = []
    current_name = ""
    buf = []

    for line in body.split("\n"):
        heading = None
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        elif line.startswith("[情况]"):
            heading = line.replace("[情况]", "").strip()
            heading = f"情况:{heading}"

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
    """把一份 fiche 切成若干检索块。过长的段落再按字符数切开。"""
    chunks = []
    last_update = doc.get("last_major_update") or doc.get("modified") or ""

    sections = split_sections(doc["body"]) or [("", doc["body"])]
    # 摘要单独成块,便于"这份文档整体讲什么"的匹配
    if doc.get("description"):
        sections.insert(0, ("摘要", doc["description"]))

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
    """官方语料库 + BM25 索引。"""

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
    """全局单例 —— 索引构建有成本,只做一次。"""
    return OfficialCorpus(themes=STUDENT_THEMES)
