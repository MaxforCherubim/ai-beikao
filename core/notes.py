# -*- coding: utf-8 -*-
"""学习笔记：按「使用者 + 知识点」自动保存，存于项目根 .notes.<user>.json。"""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _file(user: str) -> Path:
    safe = re.sub(r"[^\w\u4e00-\u9fff-]", "_", user or "guest")
    return ROOT / f".notes.{safe}.json"


def _load(user: str) -> dict:
    f = _file(user)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — 损坏文件直接重置
            pass
    return {}


def _save(user: str, d: dict) -> None:
    _file(user).write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def get_text(user: str, pid: str) -> str:
    return _load(user).get(pid, {}).get("text", "")


def set_text(user: str, pid: str, text: str) -> None:
    d = _load(user)
    d[pid] = {
        "text": text,
        "updated_at": datetime.now().strftime("%m-%d %H:%M"),
    }
    _save(user, d)


def updated_at(user: str, pid: str) -> str:
    return _load(user).get(pid, {}).get("updated_at", "")


def has(user: str, pid: str) -> bool:
    return bool(get_text(user, pid).strip())


def count(user: str) -> int:
    return sum(1 for v in _load(user).values() if v.get("text", "").strip())
