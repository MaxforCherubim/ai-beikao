# -*- coding: utf-8 -*-
"""知识点正文规范化（一次性迁移 + 新增内容后的例行工具）。

做三件事：
1. 引号统一：正文中的 ASCII 引号 " ' → 中文引号 “ ” ‘ ’（按字段内配对转换，
   不配对的字段跳过并告警）
2. 空格清理：删除中文字符/中文标点之间的多余半角空格；连续空格压缩
3. 段落重构：Markdown 会把单个换行渲染成空格，所以正文规范为——
   每个段落独占一行（段落之间空一行），列表项每行一个，
   列表项的缩进续行并入该列表项，不再手动折行

用法: python tools/normalize_points.py
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
POINTS_DIR = ROOT / "data" / "points"

# 中文类字符（含中文标点、全角符号、箭头、带圈数字等）
_CJK = r"\u4e00-\u9fff\u3000-\u303f\uff00-\uffef—…·→←↔⇒↑↓①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
_CJK_SPACE_RE = re.compile(rf"(?<=[{_CJK}]) +(?=[{_CJK}])")
_MULTI_SPACE_RE = re.compile(r" {2,}")

# Markdown 列表行（行首 - * 数字. 中文数字、 表格）
_LIST_RE = re.compile(r"^\s*(?:[-*＋]\s+|\d{1,2}[.、）]\s*|[一二三四五六七八九十]{1,3}[、.．]\s*|\|)")

TEXT_FIELDS = ["original", "why_written", "name_origin", "exam_tips"]


def _is_cjk(ch: str) -> bool:
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF or 0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF or ch in "—…·→←↔⇒↑↓①②③④⑤⑥⑦⑧⑨⑩"
    )


def fix_quotes(s: str) -> tuple:
    """ASCII 引号按出现次序配对转换为中文引号；不配对则原样返回并标记。"""
    out = []
    open_d = open_s = True
    for ch in s:
        if ch == '"':
            out.append("\u201c" if open_d else "\u201d")
            open_d = not open_d
        elif ch == "'":
            out.append("\u2018" if open_s else "\u2019")
            open_s = not open_s
        else:
            out.append(ch)
    if open_d is False and s.count('"') % 2 != 0:
        return s, False  # 双引号不配对
    if open_s is False and s.count("'") % 2 != 0:
        return s, False
    return "".join(out), True


def smart_join(a: str, b: str) -> str:
    """拼接两段：中文—中文直接连；ASCII 词间留一个空格。"""
    if not a:
        return b
    if not b:
        return a
    if _is_cjk(a[-1]) and _is_cjk(b[0]):
        return a + b
    if a[-1].isascii() and a[-1].isalnum() and b[0].isascii() and b[0].isalnum():
        return a + " " + b
    return a + b


def clean_inline(s: str) -> str:
    s = s.replace("\t", " ")
    s = _CJK_SPACE_RE.sub("", s)
    s = _MULTI_SPACE_RE.sub(" ", s)
    return s.rstrip()


def restructure(text: str) -> str:
    """段落重构：按空行分块；块内无列表 → 各行并成一段；块内有列表 →
    列表项每行一个，非列表行并入它前面最近的行（列表项续行/段内折行）。"""
    blocks_out = []
    for block in re.split(r"\n\s*\n", str(text).strip()):
        lines = [l for l in (raw.rstrip() for raw in block.split("\n")) if l.strip()]
        if not lines:
            continue
        out = []  # [(type, text)]，type: 'para' | 'list'
        for raw in lines:
            s = raw.strip()
            if _LIST_RE.match(s):
                out.append(("list", raw.rstrip() if raw.startswith((" ", "\t")) else s))
            elif out and out[-1][0] == "list":
                out[-1] = ("list", smart_join(out[-1][1], clean_inline(s)))
            elif out:
                out[-1] = ("para", smart_join(out[-1][1], clean_inline(s)))
            else:
                out.append(("para", clean_inline(s)))
        blocks_out.append("\n".join(t for _, t in out))
    return "\n\n".join(blocks_out)


def normalize_text(s: str, warn: list, fname: str) -> str:
    fixed, ok = fix_quotes(s)
    if not ok:
        warn.append(f"{fname}: 引号不配对，该字段引号未转换")
    return restructure(clean_inline(fixed))


class _Dumper(yaml.SafeDumper):
    pass


def _repr_str(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _repr_str)


def normalize_point(d: dict, warn: list, fname: str) -> dict:
    for key in TEXT_FIELDS:
        if isinstance(d.get(key), str):
            d[key] = normalize_text(d[key], warn, fname)
    for e in d.get("examples") or []:
        if isinstance(e, dict):
            for key in ("title", "story", "analysis"):
                if isinstance(e.get(key), str):
                    e[key] = normalize_text(e[key], warn, fname)
    for q in d.get("quiz") or []:
        if isinstance(q, dict):
            for key in ("question", "explain"):
                if isinstance(q.get(key), str):
                    q[key] = normalize_text(q[key], warn, fname)
            opts = q.get("options")
            if isinstance(opts, list):
                q["options"] = [
                    normalize_text(o, warn, fname) if isinstance(o, str) else o for o in opts
                ]
    return d


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    warn = []
    files = sorted(POINTS_DIR.rglob("*.yaml"))
    for f in files:
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        rel = f.relative_to(ROOT)
        before = yaml.safe_dump(d, allow_unicode=True, sort_keys=False, width=10**6)
        d = normalize_point(d, warn, str(rel))
        dumped = yaml.dump(
            d, Dumper=_Dumper, allow_unicode=True,
            sort_keys=False, width=10**6,
        )
        # 回读自检：序列化往返必须无损
        if yaml.safe_load(dumped) != d:
            warn.append(f"{rel}: 序列化往返不一致，跳过写入")
            continue
        f.write_text(dumped, encoding="utf-8")
    print(f"已规范化 {len(files)} 个文件")
    for w in warn:
        print(f"[注意] {w}")


if __name__ == "__main__":
    main()
