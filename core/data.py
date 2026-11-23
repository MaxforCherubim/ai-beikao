# -*- coding: utf-8 -*-
"""数据加载：知识点 YAML 与大纲树 outline.json。"""
import json
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
POINTS_DIR = DATA_DIR / "points"
OUTLINE_FILE = DATA_DIR / "outline.json"


@lru_cache(maxsize=1)
def load_points() -> dict:
    """加载全部知识点 -> {id: point dict}。id 以 YAML 内容为准。"""
    points = {}
    for f in sorted(POINTS_DIR.rglob("*.yaml")):
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"知识点文件解析失败: {f} — {e}") from e
        if not isinstance(d, dict) or "id" not in d:
            raise RuntimeError(f"知识点文件缺少 id 字段: {f}")
        if d["id"] in points:
            raise RuntimeError(f"知识点 id 重复: {d['id']}（{f}）")
        d["_file"] = f.name
        points[d["id"]] = d
    return points


@lru_cache(maxsize=1)
def load_outline() -> dict:
    """加载大纲树（由 tools/build_outline.py 生成）。"""
    if not OUTLINE_FILE.exists():
        raise RuntimeError("data/outline.json 不存在，请先运行: python tools/build_outline.py")
    return json.loads(OUTLINE_FILE.read_text(encoding="utf-8"))


def get_point(pid: str):
    return load_points().get(pid)


def ordered_ids() -> list:
    """按大纲树顺序返回全部知识点 id（用于上一处/下一处导航）。"""
    ids = []
    for ch in load_outline().get("chapters", []):
        for sec in ch.get("sections", []):
            ids.extend(sec.get("points", []))
    return ids


def neighbors(pid: str) -> tuple:
    """返回 (上一处, 下一处) 知识点 id，边界为 None。"""
    ids = ordered_ids()
    if pid not in ids:
        return None, None
    i = ids.index(pid)
    prev_id = ids[i - 1] if i > 0 else None
    next_id = ids[i + 1] if i < len(ids) - 1 else None
    return prev_id, next_id


def clear_cache() -> None:
    load_points.cache_clear()
    load_outline.cache_clear()
