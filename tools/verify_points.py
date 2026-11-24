# -*- coding: utf-8 -*-
"""知识点数据校验：精写六件套（data/points）与自动结构化讲义（data/library）双 schema。

用法:
    python tools/verify_points.py                 # 全量校验，出错退出码 1
    python tools/verify_points.py --list-articles # 额外打印全部法条条号清单（供人工核对）
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
POINTS_DIR = ROOT / "data" / "points"
LIBRARY_DIR = ROOT / "data" / "library"

REQUIRED_FIELDS = ["id", "chapter", "section", "title", "keywords",
                   "original", "why_written", "name_origin", "examples", "exam_tips", "quiz"]
AUTO_REQUIRED_FIELDS = ["id", "subject", "book", "chapter", "section", "title", "content", "source"]
FUSED_REQUIRED_FIELDS = ["id", "subject", "part", "chapter", "node", "title", "content", "sources"]

# 官方大纲经济法 6 章名 -> id 前缀（精写知识点）
CHAPTER_PREFIX = {
    "第一章 导论": "dl",
    "第二章 物权法": "wq",
    "第三章 招标投标法": "zbtb",
    "第四章 合同法": "ht",
    "第五章 票据法": "pj",
    "第六章 知识产权法": "zscq",
}

# 自动结构化讲义的 id 前缀（book 目录 -> 前缀）
AUTO_PREFIX = ("ff", "fl", "gw", "js", "jc", "kd", "cb", "jb")
# 融合知识点（按官方大纲节点）的 id 前缀
FUSED_PREFIX = ("gk", "gn", "wg", "hg", "cz", "jr", "tj")
SUBJECTS = ("公共科目", "经济学")

# 大纲节名 -> 排序序号（按官方大纲中"一、二、三…"顺序）
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

ARTICLE_RE = re.compile(r"《[^》]+》[^。；\n]{0,24}第[零一二三四五六七八九十百]+条")


def run_checks() -> tuple:
    """返回 (errors, warnings, points, files)。errors 非空则校验失败。"""
    errors, warnings = [], []
    files = sorted(POINTS_DIR.rglob("*.yaml")) + sorted(LIBRARY_DIR.rglob("*.yaml"))
    points = []
    for f in files:
        rel = f.relative_to(ROOT)
        is_auto = LIBRARY_DIR in f.parents
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{rel}: YAML 解析失败 — {e}")
            continue
        if not isinstance(d, dict):
            errors.append(f"{rel}: 顶层不是映射")
            continue
        d.setdefault("kind", "auto" if is_auto else "crafted")
        if is_auto and d["kind"] not in ("auto", "fused"):
            errors.append(f"{rel}: library 下 kind 应为 auto/fused（{d['kind']}）")
        if not is_auto and d["kind"] != "crafted":
            errors.append(f"{rel}: points 下 kind 应为 crafted（{d['kind']}）")
        points.append((rel, d))
        pid = str(d.get("id", ""))
        if d["kind"] == "fused":
            for key in FUSED_REQUIRED_FIELDS:
                if key not in d or d[key] in (None, "", []):
                    errors.append(f"{rel}: 缺必填字段 {key}")
            if not re.fullmatch(r"(gk|gn|wg|hg|cz|jr|tj)-\d{3}", pid):
                errors.append(f"{rel}: id 格式非法（应为 {'|'.join(FUSED_PREFIX)}-三位数字）: {pid}")
            if d.get("subject") not in SUBJECTS:
                errors.append(f"{rel}: subject 应为 {'/'.join(SUBJECTS)}: {d.get('subject')}")
            if not isinstance(d.get("sources"), list) or not d.get("sources"):
                errors.append(f"{rel}: sources 应为非空列表")
            continue
        if d["kind"] == "auto":
            for key in AUTO_REQUIRED_FIELDS:
                if key not in d or d[key] in (None, "", []):
                    errors.append(f"{rel}: 缺必填字段 {key}")
            if not re.fullmatch(r"(ff|fl|gw|js|jc|kd|cb|jb)-\d{3}", pid):
                errors.append(f"{rel}: id 格式非法（应为 {'|'.join(AUTO_PREFIX)}-三位数字）: {pid}")
            if d.get("subject") not in SUBJECTS:
                errors.append(f"{rel}: subject 应为 {'/'.join(SUBJECTS)}: {d.get('subject')}")
            continue
        # ---- 精写六件套 ----
        for key in REQUIRED_FIELDS:
            if key not in d or d[key] in (None, "", []):
                errors.append(f"{rel}: 缺必填字段 {key}")
        m = re.fullmatch(r"(dl|wq|zbtb|ht|pj|zscq)-\d{3}", pid)
        if not m:
            errors.append(f"{rel}: id 格式非法（应为 dl|wq|zbtb|ht|pj|zscq-三位数字）: {pid}")
        prefix = CHAPTER_PREFIX.get(str(d.get("chapter", "")))
        if d.get("chapter") not in CHAPTER_PREFIX:
            errors.append(f"{rel}: chapter 不在官方大纲 6 章内: {d.get('chapter')}")
        elif prefix and pid and not pid.startswith(prefix):
            errors.append(f"{rel}: id 前缀与章不匹配（应为 {prefix}-xxx）: {pid}")
    # id 全局唯一
    ids = [str(d.get("id", "")) for _, d in points]
    for pid, n in Counter(ids).items():
        if n > 1:
            owners = [str(rel) for rel, d in points if str(d.get("id", "")) == pid]
            errors.append(f"id 重复 {n} 次: {pid} — {owners}")
    idset = set(ids)
    for rel, d in points:
        if d.get("kind") in ("auto", "fused"):
            continue
        for rid in d.get("related", []) or []:
            if rid not in idset:
                errors.append(f"{rel}: related 指向不存在的 id: {rid}")
        ex = d.get("examples")
        if isinstance(ex, list):
            for i, e in enumerate(ex):
                if not isinstance(e, dict) or not {"title", "story", "analysis"} <= set(e):
                    errors.append(f"{rel}: examples[{i}] 缺 title/story/analysis")
        quiz = d.get("quiz")
        if not isinstance(quiz, list) or not quiz:
            errors.append(f"{rel}: 缺 quiz 练习题（1~2 道单选）")
        else:
            letters = "ABCD"
            for i, q in enumerate(quiz):
                if not isinstance(q, dict) or not {"question", "options", "answer", "explain"} <= set(q):
                    errors.append(f"{rel}: quiz[{i}] 缺 question/options/answer/explain")
                    continue
                opts = q.get("options")
                if not isinstance(opts, list) or len(opts) < 2 or len(opts) > 4:
                    errors.append(f"{rel}: quiz[{i}] 选项数量应为 2~4")
                elif q.get("answer") not in letters[: len(opts)]:
                    errors.append(f"{rel}: quiz[{i}] answer 应为 A~{letters[len(opts)-1]}")
        kw = d.get("keywords")
        if isinstance(kw, list) and len(kw) < 3:
            warnings.append(f"{rel}: keywords 少于 3 个（建议 4~8 个）")
        if isinstance(d.get("original"), str) and "《" not in d["original"]:
            warnings.append(f"{rel}: original 未注明法律名（《…》）")
    return errors, warnings, points, files


def list_articles(points) -> None:
    """打印所有 original 中的条号引用清单，供人工逐条核对。"""
    print("=" * 60)
    print("法条条号清单（人工核对用）")
    print("=" * 60)
    for rel, d in sorted(points, key=lambda x: str(x[0])):
        text = str(d.get("original", "")) + " " + str(d.get("examples", ""))
        found = ARTICLE_RE.findall(text)
        if found:
            print(f"\n{d.get('id')}  {d.get('title')}")
            for a in found:
                print(f"   - {a}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-articles", action="store_true", help="打印条号清单")
    args = ap.parse_args()

    errors, warnings, points, files = run_checks()
    crafted = [(r, d) for r, d in points if d.get("kind") == "crafted"]
    auto = [(r, d) for r, d in points if d.get("kind") == "auto"]
    fused = [(r, d) for r, d in points if d.get("kind") == "fused"]
    by_chapter = Counter(str(d.get("chapter", "?")) for _, d in crafted)
    print(f"知识点文件: {len(files)} 个（精写 {len(crafted)} + 讲义 {len(auto)} + 融合 {len(fused)}）")
    for ch in CHAPTER_PREFIX:
        print(f"  {ch}: {by_chapter.get(ch, 0)}")
    by_book = Counter(str(d.get("book", "?")) for _, d in auto)
    for book, n in by_book.items():
        print(f"  讲义·{book}: {n}")
    by_part = Counter(str(d.get("part", "?")) for _, d in fused)
    for part, n in by_part.items():
        print(f"  融合·{part}: {n}")
    print(f"总计: {len(points)} 个知识点")
    for w in warnings:
        print(f"[警告] {w}")
    if errors:
        print(f"\n✗ 校验失败，{len(errors)} 个错误:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\n✓ 校验通过")
    if args.list_articles:
        list_articles(crafted)


if __name__ == "__main__":
    main()
