# -*- coding: utf-8 -*-
"""关键词检索：jieba 分词 + 字段加权打分 + 片段高亮。"""
import logging

import jieba

from core.data import load_points

jieba.setLogLevel(logging.ERROR)

# 字段 -> 权重（命中该字段时的分值）
FIELD_WEIGHTS = [
    ("title", 5),
    ("keywords", 4),
    ("section", 2),
    ("exam_tips", 1),
    ("original", 1),
    ("why_written", 1),
    ("background", 1),
    ("examples", 1),
]

_DICT_READY = False


def _init_dict() -> None:
    """把知识点标题与关键词喂给 jieba，保证"背书""留置权"这类专业词不被切碎。"""
    global _DICT_READY
    if _DICT_READY:
        return
    for p in load_points().values():
        jieba.add_word(p.get("title", ""), freq=1000)
        for kw in p.get("keywords", []) or []:
            jieba.add_word(kw, freq=1000)
    for w in ["背书", "承兑", "留置权", "抵押权", "质权", "表见代理", "建筑物区分所有权",
              "不安抗辩", "代位权", "撤销权", "缔约过失", "串通投标", "中标通知书",
              "善意取得", "公示公信", "物权法定", "一物一权", "效力待定", "无权代理",
              "追索权", "票据抗辩", "空头支票", "涉外票据", "合理使用", "邻接权",
              "惩罚性赔偿", "注册商标", "著作权", "专利权", "商标权", "实用新型",
              "外观设计", "国防专利", "流押", "提存", "抵销", "除斥期间"]:
        jieba.add_word(w, freq=1000)
    _DICT_READY = True


def _field_text(point: dict, field: str) -> str:
    v = point.get(field)
    if field == "keywords" and isinstance(v, list):
        return " ".join(str(x) for x in v)
    if field == "examples" and isinstance(v, list):
        parts = []
        for e in v:
            if isinstance(e, dict):
                parts.append(str(e.get("title", "")) + " " + str(e.get("story", "")) + " " + str(e.get("analysis", "")))
        return " ".join(parts)
    return str(v) if v else ""


def tokenize(query: str) -> list:
    _init_dict()
    return [t for t in jieba.cut_for_search(query.strip()) if t.strip()]


def search(query: str, limit: int = 15) -> list:
    """返回 [{id, score}]，按得分降序。空查询返回空列表。"""
    query = query.strip()
    if not query:
        return []
    tokens = tokenize(query)
    if not tokens:
        return []
    points = load_points()
    results = []
    for pid, p in points.items():
        score = 0
        texts = {}
        for field, w in FIELD_WEIGHTS:
            text = _field_text(p, field)
            texts[field] = text
            for t in tokens:
                if t in text:
                    # 标题/关键词按命中次数计分（同一词重复出现说明强相关）
                    score += w * (text.count(t) if field in ("title", "keywords") else 1)
        full = "  ".join(texts[f] for f, _ in FIELD_WEIGHTS)
        # 整句原样命中（如"第三百九十四条""串通投标"）额外加分
        if query in full:
            score += 10
        if score > 0:
            results.append({"id": pid, "score": score})
    results.sort(key=lambda r: -r["score"])
    return results[:limit]


def make_snippet(point: dict, query: str, width: int = 50) -> str:
    """取命中字段中第一次出现的上下文片段（去空白），无命中则回退到 why_written 开头。"""
    tokens = tokenize(query) or [query.strip()]
    for field, _ in FIELD_WEIGHTS:
        text = "".join(str(_field_text(point, field)).split())
        if not text:
            continue
        for t in tokens:
            i = text.find(t)
            if i >= 0:
                start = max(0, i - width // 2)
                frag = text[start : i + width]
                return ("…" if start > 0 else "") + frag + "…"
    fallback = "".join(str(point.get("why_written", "")).split())
    return fallback[:width] + ("…" if len(fallback) > width else "")
