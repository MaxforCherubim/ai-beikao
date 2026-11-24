# -*- coding: utf-8 -*-
"""按官方大纲骨架生成 data/outline.json v3（先自动执行校验）。

骨架 = data/outline_official.json（subjects → parts → chapters → 官方测查点），
由 tools/extract_official_outline.py 从官方大纲提取文本生成。
挂点规则：
- fused 知识点按 (subject, part, chapter) 挂到官方章下，章内按官方测查点顺序（node 字段匹配）；
- 精写知识点（经济法六件套）挂到 经济学·第三篇经济法 对应章下，按 id 序、以 section 分组；
- 官方章下暂无知识点的跳过（侧栏不显示空章）。
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.verify_points import run_checks  # noqa: E402

OFFICIAL = ROOT / "data" / "outline_official.json"


def norm(s: str) -> str:
    """标题比较归一化：官方大纲提取文本无空格（第二章物权法），YAML 里常带空格。"""
    return re.sub(r"\s+", "", str(s))


def node_index(chapter: dict) -> dict:
    idx = {}
    for sec in chapter["sections"]:
        for n, node in enumerate(sec["nodes"]):
            idx[norm(node)] = n
    return idx


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errors, warnings, points, files = run_checks()
    if errors:
        print("✗ 校验未通过，先修复再生成大纲：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    by_id = {str(d["id"]): d for _, d in points}

    subjects = []
    for osub in official["subjects"]:
        s_points = [(str(d["id"]), d) for _, d in points if str(d.get("subject", "经济学")) == osub["title"]]
        parts = []
        for opart in osub["parts"]:
            chapters = []
            for och in opart["chapters"]:
                nidx = node_index(och)
                fused = [(pid, d) for pid, d in s_points
                         if d.get("kind") == "fused"
                         and norm(d.get("part")) == norm(opart["title"])
                         and norm(d.get("chapter")) == norm(och["title"])]
                fused.sort(key=lambda t: nidx.get(norm(t[1].get("node")), 900))
                crafted = sorted([(pid, d) for pid, d in s_points
                                  if d.get("kind") == "crafted"
                                  and osub["title"] == "经济学" and opart["title"] == "第三篇经济法"
                                  and norm(d.get("chapter")) == norm(och["title"])],
                                 key=lambda t: t[0])
                entries = fused + crafted
                if not entries:
                    continue
                sections: dict = {}
                for pid, d in entries:
                    sections.setdefault(str(d.get("section") or ""), []).append(pid)
                sec_list = [{"title": t, "points": pids} for t, pids in sections.items()]
                chapters.append({
                    "title": och["title"],
                    "sections": sec_list,
                    "count": len(entries),
                })
            if chapters:
                parts.append({
                    "title": opart["title"],
                    "chapters": chapters,
                    "count": sum(c["count"] for c in chapters),
                })
        subjects.append({
            "id": osub["id"],
            "title": osub["title"],
            "parts": parts,
            "count": sum(p["count"] for p in parts),
        })

    outline = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": official["source"] + " + 备考讲义融合（data/知识点/ 登记表）",
        "total": len(by_id),
        "subjects": subjects,
    }
    out = ROOT / "data" / "outline.json"
    out.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ch = sum(len(p["chapters"]) for s in subjects for p in s["parts"])
    covered = sum(len(sec["points"]) for s in subjects for p in s["parts"]
                  for c in p["chapters"] for sec in c["sections"])
    print(f"✓ 已生成 {out.relative_to(ROOT)}（入库 {covered}/{len(by_id)} 个知识点，{len(subjects)} 科目 {n_ch} 章）")
    if covered != len(by_id):
        missing = [pid for pid in by_id
                   if not any(pid in sec["points"] for s in subjects for p in s["parts"]
                              for c in p["chapters"] for sec in c["sections"])]
        print(f"✗ 未挂到大纲树的知识点 {len(missing)} 个，示例: {missing[:10]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
