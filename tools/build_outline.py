# -*- coding: utf-8 -*-
"""汇总 data/points（精写）+ data/library（讲义）生成 data/outline.json（先自动执行校验）。

outline v2 结构：subjects（公共科目/经济学）→ chapters → sections → points。
精写经济法 6 章归入「经济学」科目，按官方大纲章序排前；讲义章按 id 首现顺序排后。
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.verify_points import CHAPTER_PREFIX, CN_NUM, run_checks  # noqa: E402

SUBJECTS = [("public", "公共科目"), ("econ", "经济学")]


def section_order(section: str) -> int:
    """按节名前的中文数字序号排序，无法解析的排最后。"""
    head = section.split("、", 1)[0]
    return CN_NUM.get(head, 99)


def group_chapters(entries, crafted_order):
    """entries: [(pid, point)] 已按文件序；返回章列表（保序）。"""
    chapters: dict = {}
    for pid, d in entries:
        ch = str(d.get("chapter", "?"))
        chapters.setdefault(ch, {"title": ch, "sections": {}, "count": 0})
        chapters[ch]["sections"].setdefault(str(d.get("section", "?")), []).append(pid)
        chapters[ch]["count"] += 1
    ordered_titles = [t for t in crafted_order if t in chapters]
    ordered_titles += [t for t in chapters if t not in crafted_order]
    out = []
    for i, title in enumerate(ordered_titles, 1):
        c = chapters[title]
        is_crafted = title in CHAPTER_PREFIX
        sec_list = [{"title": s, "points": pids} for s, pids in c["sections"].items()]
        if is_crafted:
            sec_list.sort(key=lambda s: section_order(s["title"]))
        for s in sec_list:
            s["points"] = sorted(s["points"])
        out.append({
            "id": CHAPTER_PREFIX.get(title, f"ch{i:02d}"),
            "title": title,
            "sections": sec_list,
            "count": c["count"],
        })
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errors, warnings, points, files = run_checks()
    if errors:
        print("✗ 校验未通过，先修复再生成大纲：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    by_id = {str(d["id"]): d for _, d in points}
    subjects = []
    for sid, stitle in SUBJECTS:
        entries = [(str(d["id"]), d) for _, d in points if str(d.get("subject", "经济学")) == stitle]
        crafted_entries = [(pid, d) for pid, d in entries if d.get("kind") == "crafted"]
        auto_entries = [(pid, d) for pid, d in entries if d.get("kind") == "auto"]
        chapters = group_chapters(crafted_entries, list(CHAPTER_PREFIX))
        chapters += group_chapters(auto_entries, [])
        subjects.append({
            "id": sid,
            "title": stitle,
            "chapters": chapters,
            "count": sum(c["count"] for c in chapters),
        })

    outline = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "军队文职笔试大纲（2023-08）+ 备考讲义（data/知识点/，见各目录 README 登记表）",
        "total": len(by_id),
        "subjects": subjects,
    }
    out = ROOT / "data" / "outline.json"
    out.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ch = sum(len(s["chapters"]) for s in subjects)
    print(f"✓ 已生成 {out.relative_to(ROOT)}（{len(by_id)} 个知识点，{len(subjects)} 科目 {n_ch} 章）")

    covered = sum(len(p["points"]) for s in subjects for c in s["chapters"] for p in c["sections"])
    if covered != len(by_id):
        print(f"✗ 大纲树覆盖 {covered} != 知识点总数 {len(by_id)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
