# -*- coding: utf-8 -*-
"""从官方大纲提取文本生成 data/outline_official.json（侧栏导航与知识点融合的唯一骨架）。

源：data/raw/大纲提取_公共科目.txt、data/raw/大纲提取_经济学专业科目.txt（extract_syllabus.py 产物）。
结构：subjects → parts → chapters → sections(可空) → nodes（官方「一、××」测查点）。
经济学大纲的「篇」即 part（微观/宏观/经济法/财政学/金融学/统计学）；
公共科目大纲的「部分」即 part（基本知识/岗位能力），章下另有「节」。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

RE_PART = re.compile(r"^第[一二三四五六七八九十]+部分$")
RE_PIN = re.compile(r"^第[一二三四五六七八九十]+篇$")
RE_CH = re.compile(r"^第[一二三四五六七八九十]+章$")
RE_SEC = re.compile(r"^第[一二三四五六七八九十]+节$")
RE_NODE = re.compile(r"^[一二三四五六七八九十]+、\S")
SKIP = ("本大纲内容版权", "未经书面协议", "—", "军队文职人员公开招考笔试")


def clean_lines(path: Path) -> list[str]:
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(SKIP):
            continue
        if re.fullmatch(r"\d+", line) or re.search(r"\.{5,}", line):
            continue
        out.append(line)
    return out


def parse(lines: list[str], part_is_pin: bool) -> list[dict]:
    """返回 parts 列表；part 标题取 部分/篇 + 下一行合并。

    目录块里的 部分/篇 行下一行仍是标题行（第二部分/第二篇…），据此排除；
    正文里 part 行的下一行是 part 名（基本知识/微观经济学…）。
    """
    parts: list[dict] = []
    cur_part = cur_ch = cur_sec = None

    def is_heading(s: str) -> bool:
        return bool(RE_PART.match(s) or RE_PIN.match(s) or RE_CH.match(s) or RE_SEC.match(s))

    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if (RE_PIN.match(line) if part_is_pin else RE_PART.match(line)) and nxt and not is_heading(nxt):
            cur_part = {"title": line + nxt, "chapters": []}
            parts.append(cur_part)
            cur_ch = cur_sec = None
            i += 2
            continue
        if RE_CH.match(line) and nxt and not is_heading(nxt):
            cur_ch = {"title": line + nxt, "sections": []}
            if cur_part is None:
                cur_part = {"title": "", "chapters": []}
                parts.append(cur_part)
            cur_part["chapters"].append(cur_ch)
            cur_sec = {"title": "", "nodes": []}
            cur_ch["sections"].append(cur_sec)
            i += 2
            continue
        if RE_SEC.match(line) and nxt and not is_heading(nxt) and cur_ch is not None:
            cur_sec = {"title": line + nxt, "nodes": []}
            cur_ch["sections"].append(cur_sec)
            i += 2
            continue
        if RE_NODE.match(line) and cur_ch is not None:
            cur_sec["nodes"].append(line)
            i += 1
            continue
        i += 1
    # 去掉空 section 容器与目录块产生的空 part
    for p in parts:
        for c in p["chapters"]:
            c["sections"] = [s for s in c["sections"] if s["nodes"] or s["title"]]
    parts = [p for p in parts if p["chapters"]]
    return parts


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pub_lines = clean_lines(RAW / "大纲提取_公共科目.txt")
    eco_lines = clean_lines(RAW / "大纲提取_经济学专业科目.txt")
    # 公共科目 txt 前半是目录（带页码点线已滤），正文从第一个「第一部分」开始；目录行的下一行也是标题会重复建 part——
    # 目录里的 部分/章 行后面跟的是页码行（已滤掉），nxt 会是下一个标题，故用「nxt 不是章/节标题」过滤不可靠；
    # 改为：只取正文段（第二个「第一部分」之后）。
    idx = [i for i, l in enumerate(pub_lines) if l == "第一部分"]
    pub_body = pub_lines[idx[1]:] if len(idx) > 1 else pub_lines
    idx = [i for i, l in enumerate(eco_lines) if l == "第一篇"]
    eco_body = eco_lines[idx[1]:] if len(idx) > 1 else eco_lines

    outline = {
        "source": "军队文职人员公开招考笔试大纲（2023-08，军队人才网）",
        "subjects": [
            {"id": "public", "title": "公共科目", "parts": parse(pub_body, part_is_pin=False)},
            {"id": "econ", "title": "经济学", "parts": parse(eco_body, part_is_pin=True)},
        ],
    }
    out = ROOT / "data" / "outline_official.json"
    out.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
    for s in outline["subjects"]:
        n_part = len(s["parts"])
        n_ch = sum(len(p["chapters"]) for p in s["parts"])
        n_node = sum(len(sec["nodes"]) for p in s["parts"] for c in p["chapters"] for sec in c["sections"])
        print(f"{s['title']}: {n_part} 部分 {n_ch} 章 {n_node} 个官方测查点")
    print(f"✓ {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
