# -*- coding: utf-8 -*-
"""学习进度：按「使用者」读写项目根 .progress.<user>.json。"""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _file(user: str) -> Path:
    safe = re.sub(r"[^\w\u4e00-\u9fff-]", "_", user or "guest")
    return ROOT / f".progress.{safe}.json"


def load(user: str) -> dict:
    default = {"mastered": [], "review": [], "updated_at": None}
    f = _file(user)
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            d.setdefault("mastered", [])
            d.setdefault("review", [])
            return d
        except Exception:  # noqa: BLE001 — 损坏文件直接重置
            pass
    return default


def save(user: str, d: dict) -> None:
    d["updated_at"] = datetime.now().isoformat(timespec="seconds")
    _file(user).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def set_status(user: str, pid: str, status: str) -> None:
    """status: 'mastered' | 'review' | ''（清除）。"""
    d = load(user)
    for key in ("mastered", "review"):
        if pid in d[key]:
            d[key].remove(pid)
    if status:
        d[status].append(pid)
    save(user, d)


def status_of(user: str, pid: str) -> str:
    d = load(user)
    if pid in d["mastered"]:
        return "mastered"
    if pid in d["review"]:
        return "review"
    return ""
