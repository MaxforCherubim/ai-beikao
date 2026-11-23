# -*- coding: utf-8 -*-
"""汇总 data/points/**/*.yaml 生成 data/outline.json（先自动执行校验）。"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.verify_points import CHAPTER_PREFIX, CN_NUM, run_checks  # noqa: E402


def section_order(section: str) -> int:
    """按节名前的中文数字序号排序，无法解析的排最后。"""
    head = section.split("、", 1)[0]
    return CN_NUM.get(head, 99)


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

    chapters = []
    for ch_title, prefix in CHAPTER_PREFIX.items():
        ch_points = [(str(d["id"]), d) for _, d in points
                     if str(d.get("chapter")) == ch_title]
        if not ch_points:
            continue
        # 节分组
        sections: dict = {}
        for pid, d in ch_points:
            sections.setdefault(str(d["section"]), []).append(pid)
        sec_list = [
            {"title": s, "points": sorted(pids)}
            for s, pids in sections.items()
        ]
        sec_list.sort(key=lambda s: section_order(s["title"]))
        chapters.append({
            "id": prefix,
            "title": ch_title,
            "sections": sec_list,
            "count": len(ch_points),
        })

    outline = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "军队文职人员公开招考笔试经济学专业科目考试大纲（2023-08）第三篇 经济法",
        "total": len(points),
        "chapters": chapters,
    }
    out = ROOT / "data" / "outline.json"
    out.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 已生成 {out.relative_to(ROOT)}（{len(points)} 个知识点，{len(chapters)} 章）")

    # 简单自检：大纲树应覆盖全部知识点
    covered = sum(len(p["points"]) for c in chapters for p in c["sections"])
    if covered != len(by_id):
        print(f"✗ 大纲树覆盖 {covered} != 知识点总数 {len(by_id)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
