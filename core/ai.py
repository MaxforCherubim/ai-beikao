# -*- coding: utf-8 -*-
"""可选 AI 追问：直调智谱 GLM 开放接口（requests，无 SDK 依赖）。

配置方式（二选一）：
1. 环境变量 ZHIPUAI_API_KEY（可用 ZHIPUAI_MODEL 覆盖默认模型）
2. 项目下 .streamlit/secrets.toml 写  ZHIPUAI_API_KEY = "..."
"""
import os

import requests

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-4-flash"
CONTEXT_MAX_CHARS = 2400

SYSTEM_PROMPT = (
    "你是一名经济法学习助教，帮考生理解军队文职考试《经济学》科目中的经济法知识点。"
    "回答要口语化、直击问题，能举生活案例就举；涉及法条条号时，只给确定无误的条号，"
    "不确定就说明条文内容而不写条号，绝不编造。回答控制在 400 字以内，除非用户要求展开。"
)


def get_api_key() -> str | None:
    key = os.environ.get("ZHIPUAI_API_KEY")
    if key:
        return key.strip()
    try:
        import streamlit as st

        if "ZHIPUAI_API_KEY" in st.secrets:
            return str(st.secrets["ZHIPUAI_API_KEY"]).strip()
    except Exception:  # noqa: BLE001 — 未启用 secrets 或非 streamlit 环境
        pass
    return None


def ask(question: str, point: dict | None = None) -> str:
    """question: 用户追问；point: 当前知识点（自动携带为上下文）。"""
    key = get_api_key()
    if not key:
        raise RuntimeError(
            "尚未配置 AI 接口。请任选其一：\n"
            "① 设置环境变量 ZHIPUAI_API_KEY；\n"
            "② 在项目下创建 .streamlit/secrets.toml，写入 ZHIPUAI_API_KEY = \"你的Key\"\n"
            "（Key 在智谱开放平台 bigmodel.cn 获取，glm-4-flash 免费）"
        )

    user_content = question
    if point:
        ctx_parts = [
            f"【当前知识点】{point.get('title', '')}",
            f"【章节】{point.get('chapter', '')} {point.get('section', '')}",
            f"【法条原文】{str(point.get('original', ''))[:800]}",
            f"【为什么这么写】{str(point.get('why_written', ''))[:800]}",
        ]
        ctx = "\n".join(ctx_parts)[:CONTEXT_MAX_CHARS]
        user_content = f"{ctx}\n\n【我的问题】{question}"

    model = os.environ.get("ZHIPUAI_MODEL", DEFAULT_MODEL)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.6,
    }
    resp = requests.post(
        API_URL,
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
