# -*- coding: utf-8 -*-
"""文字版考点讲义 → data/library/ 自动结构化（2026-11-24 大改）。

处理 3 本文字版 PDF（考点集锦/财经必背/金融学必背）：
提取文本 → 清洗（页眉/水印/填空下划线/图碎片）→ 断行合并 → 按书配置切分知识点 → YAML。

图版思维导图讲义（公共科目三本、经济学思维导图两本）不走本脚本，
由读图转写直接产出同 schema 的 YAML（见 data/library/ 各目录）。

auto 知识点 schema：
  id / kind: auto / subject / book / chapter / section / title / content / source
"""
import re
import sys
from pathlib import Path

import pymupdf
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LIB = DATA / "library"

# 通用垃圾行
RE_UNDERSCORE = re.compile(r"^[_＿\s]+$")
RE_PAGE_NUM = re.compile(r"^第\s*\d+\s*页$")
RE_STANDALONE_NUM = re.compile(r"^\d{1,3}$")
RE_HEADER_KD = re.compile(r"^(军队文职笔试考点集锦|《经济学》|目\s*录|目|录)$")
RE_HEADER_CB = re.compile(r"^(农信社考试·?\s*财经必背考点|银行考试·?\s*金融必背考点|\d+\s*$)")
RE_TOC_DOTS = re.compile(r"\.{5,}|…{3,}")
RE_FIG_FRAGMENT = re.compile(r"^[A-Za-z0-9（）()%≤≥＋+=×÷\-·\s]{1,6}$")

# 结构行（用于断行合并的边界）
RE_KD_PART = re.compile(r"^第[一二三四五六七八九十]+部分\s*\S")
RE_KD_POINT = re.compile(r"^考点[一二三四五六七八九十]+：")
RE_L1 = re.compile(r"^[一二三四五六七八九十]+、\S")
RE_L2 = re.compile(r"^（[一二三四五六七八九十]+）\S")
RE_L3 = re.compile(r"^\d+[\.、]\s*\S")
RE_L4 = re.compile(r"^（\d+）\S")
RE_NUM_ITEM = re.compile(r"^\d+[\.、]\s*\S")
RE_TIP = re.compile(r"^【[^】]{1,12}】")

END_PUNCT = "。！】"


def is_struct(line: str, mode: str) -> bool:
    if mode == "kd":
        return bool(RE_KD_PART.match(line) or RE_KD_POINT.match(line) or RE_L1.match(line)
                    or RE_L2.match(line) or RE_L3.match(line) or RE_L4.match(line))
    return bool(RE_NUM_ITEM.match(line) or RE_TIP.match(line) or line in ("经济学", "金融学", "会计学"))


def clean_lines(doc, mode: str) -> list[tuple[str, int]]:
    """逐页提取并清洗，返回 (行, pdf页码)。"""
    out = []
    for pno, page in enumerate(doc, 1):
        for raw in page.get_text().splitlines():
            line = raw.strip()
            if not line:
                continue
            if RE_UNDERSCORE.match(line) or RE_PAGE_NUM.match(line) or RE_STANDALONE_NUM.match(line):
                continue
            if RE_TOC_DOTS.search(line):
                continue
            if mode == "kd" and RE_HEADER_KD.match(line):
                continue
            if mode == "num" and (RE_HEADER_CB.match(line) or line in ("目 录", "目录")):
                continue
            if RE_FIG_FRAGMENT.match(line):
                continue
            out.append((line, pno))
    return out


def merge_paragraphs(lines: list[tuple[str, int]], mode: str) -> list[tuple[str, int]]:
    """断行合并：非结构行且上一行未以句末标点收尾 → 并入上一行。"""
    merged = []
    for line, pno in lines:
        if merged and not is_struct(line, mode):
            prev, ppno = merged[-1]
            if not is_struct(prev, mode) and prev and prev[-1] not in END_PUNCT:
                merged[-1] = (prev + line, max(ppno, pno))
                continue
        merged.append((line, pno))
    return merged


def md_escape_title(line: str) -> str:
    return line.replace('"', '\\"')


def build_kd(lines):
    """考点集锦：chapter=部分，section=考点，point=考点内「一、」块（无则整考点成一点）。"""
    points, chapter, section, sec_page = [], "", "", 0
    cur, cur_title, cur_pages = [], "", []

    def flush():
        nonlocal cur, cur_title, cur_pages
        if cur and cur_title:
            # 结构行做加粗列表项，正文段落挂在最近的结构行下作子项，保持讲义层级感
            rebuilt = []
            struct_indent = 0
            for kind, text in cur:
                if kind == "body":
                    rebuilt.append(" " * (struct_indent + 2) + "- " + text)
                else:
                    struct_indent = {"l1": 0, "l2": 2, "l3": 4, "l4": 6}[kind]
                    mark = " " * struct_indent + "- "
                    rebuilt.append(mark + ("**" + text + "**" if kind != "l4" else text))
            points.append({
                "chapter": chapter, "section": section, "title": cur_title,
                "content": "\n".join(rebuilt), "pages": (min(cur_pages), max(cur_pages)),
            })
        cur, cur_title, cur_pages = [], "", []

    for line, pno in lines:
        if RE_KD_PART.match(line):
            flush()
            chapter = line
            continue
        if RE_KD_POINT.match(line):
            flush()
            section, sec_page = line, pno
            continue
        if RE_L1.match(line):
            if cur:
                flush()
            cur_title = f"{section} · {line}" if section else line
            cur.append(("l1", line))
            cur_pages.append(pno)
            continue
        if not cur:
            # 考点下没有「一、」层级：整考点成一点
            if cur_title == "":
                cur_title = section or line
            cur.append(("body", line))
            cur_pages.append(pno)
            continue
        if RE_L2.match(line):
            cur.append(("l2", line))
        elif RE_L3.match(line):
            cur.append(("l3", line))
        elif RE_L4.match(line):
            cur.append(("l4", line))
        else:
            cur.append(("body", line))
        cur_pages.append(pno)
    flush()
    return points


def build_num(lines, group_size=10):
    """必背考点册：chapter=篇（经济学/金融学/会计学），section=每 group_size 个条目一组，point=条目。"""
    points, chapter = [], ""
    items = []  # (num, title, [body...], pages)
    cur = None
    for line, pno in lines:
        if line in ("经济学", "金融学", "会计学"):
            chapter = line
            continue
        m = RE_NUM_ITEM.match(line)
        if m and not line.startswith(("（", "(")):
            if cur:
                items.append(cur)
            cur = {"title": line, "body": [], "pages": [pno], "chapter": chapter or "综合"}
            continue
        if cur is None:
            continue
        cur["body"].append(line)
        cur["pages"].append(pno)
    if cur:
        items.append(cur)
    # 先按章分组，章内每 group_size 条一组做 section
    chapters = []
    for it in items:
        if not chapters or chapters[-1][0] != it["chapter"]:
            chapters.append((it["chapter"], []))
        chapters[-1][1].append(it)
    for chap, ch_items in chapters:
        for start in range(0, len(ch_items), group_size):
            chunk = ch_items[start:start + group_size]
            sec = f"条目 {chunk[0]['title'].split('.')[0]}–{chunk[-1]['title'].split('.')[0]}"
            for it in chunk:
                rebuilt = [f"- **{it['title']}**"]
                for b in it["body"]:
                    rebuilt.append("  - " + b)
                points.append({
                    "chapter": chap, "section": sec, "title": it["title"],
                    "content": "\n".join(rebuilt), "pages": (min(it["pages"]), max(it["pages"])),
                })
    return points


BOOKS = [
    {"file": "知识点/经济学-笔试考点集锦.pdf", "prefix": "kd", "subject": "经济学",
     "book": "经济学-笔试考点集锦", "dir": "经济学/笔试考点集锦", "mode": "kd"},
    {"file": "知识点/经济学-财经必背考点.pdf", "prefix": "cb", "subject": "经济学",
     "book": "经济学-财经必背考点", "dir": "经济学/财经必背考点", "mode": "num"},
    {"file": "知识点/经济学-金融学必背考点.pdf", "prefix": "jb", "subject": "经济学",
     "book": "经济学-金融学必背考点", "dir": "经济学/金融学必背考点", "mode": "num"},
]

DUMPER = yaml.SafeDumper


def _str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


DUMPER.add_representer(str, _str_representer)


def sanitize(name: str) -> str:
    for ch in '/\\:*?"<>| ':
        name = name.replace(ch, "")
    return name[:60]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for cfg in BOOKS:
        if only and only not in cfg["file"]:
            continue
        doc = pymupdf.open(DATA / cfg["file"])
        lines = clean_lines(doc, cfg["mode"])
        lines = merge_paragraphs(lines, cfg["mode"])
        points = build_kd(lines) if cfg["mode"] == "kd" else build_num(lines)
        outdir = LIB / cfg["dir"]
        if outdir.exists():
            for old in outdir.glob("*.yaml"):
                old.unlink()
        outdir.mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(points, 1):
            pid = f"{cfg['prefix']}-{i:03d}"
            rec = {
                "id": pid, "kind": "auto", "subject": cfg["subject"], "book": cfg["book"],
                "chapter": p["chapter"], "section": p["section"], "title": p["title"],
                "content": p["content"],
                "source": f"{cfg['book']}.pdf p.{p['pages'][0]}-{p['pages'][1]}" if p["pages"][0] != p["pages"][1]
                else f"{cfg['book']}.pdf p.{p['pages'][0]}",
            }
            (outdir / f"{pid}_{sanitize(p['title'])}.yaml").write_text(
                yaml.dump(rec, Dumper=DUMPER, allow_unicode=True, sort_keys=False, width=1000),
                encoding="utf-8")
        print(f"{cfg['book']}: {len(points)} 个知识点 → {outdir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
