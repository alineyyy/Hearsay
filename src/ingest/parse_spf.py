"""
把 service-public.fr 的开放数据(XML)解析成可检索的语料库。

输入: data/spf_raw/*.xml   (5552 份官方 fiche)
输出: data/corpus.jsonl    (每行一份文档)

数据来源: Service-Public.gouv.fr / DILA, 通过 data.gouv.fr 发布
许可: Licence Ouverte 2.0 (Etalab) —— 使用时须注明来源与更新日期
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

# 正文里这些标签本身不产出文字,只是容器
SKIP_TEXT_TAGS = {"Source", "Commentaire"}


def clean(s):
    """压缩空白,去掉不间断空格。"""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def node_text(el):
    """递归取出一个节点下的所有可读文字。"""
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
    把正文结构展开成带标题层级的纯文本行。
    重点保留 Cas(情况分支)的标签 —— 官方文档用它区分不同身份/情形,
    这正是"特殊情况"问题的答案所在。
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
            out.append(f"[情况] {label}")
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
            out.append("[在哪办] " + t)

    elif tag in ("Paragraphe", "Texte", "Introduction"):
        if tag == "Paragraphe":
            t = clean(node_text(el))
            if t:
                out.append(t)
        else:
            for child in el:
                render_block(child, out, depth)

    else:
        # 其他容器继续往下走
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

    # 更新日期 —— 判断信息时效性的关键字段
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
        sys.exit(f"找不到原始数据,请先解压到 {RAW_DIR}")

    n_ok = 0
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for fp in files:
            doc = parse_fiche(fp)
            if doc and doc["body"]:
                out.write(json.dumps(doc, ensure_ascii=False) + "\n")
                n_ok += 1

    print(f"解析完成: {n_ok} / {len(files)} 份 -> {OUT_PATH}")


if __name__ == "__main__":
    main()
