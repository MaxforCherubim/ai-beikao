# -*- coding: utf-8 -*-
"""军队文职备考·经济法学习助手（Streamlit）。

启动: python -m streamlit run app.py
数据: data/points/*.yaml（规范见 CLAUDE.md §4），大纲树 data/outline.json 由脚本生成。
"""
import re
from datetime import date
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent

from core import data as dmod
from core import notes as nmod
from core import progress as pmod
from core import search as smod

st.set_page_config(page_title="经济法备考助手", page_icon="⚖️", layout="wide")

EXAM_DATE = date(2026, 12, 13)
USER = "考生"  # 单一身份：本地与云端访客共用同一套笔记/进度

# archify 导出的静态图解（SVG）：知识点 id → (文件, 说明)
# 用图片而非交互式 HTML：体积小 4~5 倍、秒开、不依赖云端静态路由
DIAGRAMS = {
    "zbtb-001": ("bidding-workflow.png", "本章导览：招标投标全流程"),
    "ht-001": ("contract-lifecycle.png", "本章导览：合同的一生"),
    "pj-001": ("note-sequence.png", "本章导览：票据流转与追索"),
}


@st.cache_data
def _diagram_bytes(filename: str) -> bytes:
    return (ROOT / "static" / "diagrams" / filename).read_bytes()


def render_diagram(filename: str, caption: str) -> None:
    with st.expander(f"🗺️ {caption}", expanded=True):
        st.image(_diagram_bytes(filename), width="stretch")
        st.markdown(
            f'<a href="/app/static/diagrams/{filename}" target="_blank" '
            f'rel="noreferrer">🔍 在新标签打开大图（浏览器原生缩放/拖动，看细节用这个）</a>',
            unsafe_allow_html=True,
        )


# ---------- 渲染辅助 ----------

def quote_block(text: str) -> str:
    return "\n".join(f"> {line}" for line in str(text).strip().splitlines())


# 中文首行缩进：用 CSS text-indent 实现（每段自动缩进 2 字符）。
# 不能用全角空格字符方案——Streamlit 会 strip 整个 markdown 字符串开头的空白，
# 段首缩进恰好位于字符串开头时会失效。
# 字体：ZeoSeven CDN（国内直连可用，unicode-range 切片按需加载，不进仓库）。
#   #69 思源黑体=正文阅读清晰；#92 得意黑=标题精神；#292 霞鹜文楷=法条文书感。
#   CDN 失效时自动回退到系统字体（微软雅黑/苹方），不影响使用。
def _load_font_css() -> str:
    """本地自托管字体（static/fonts，由 tools 下载自 ZeoSeven）：用 link 引用，
    不内联——三个 result.css 合计 50 万+字符，内联会被 Streamlit HTML 渲染截断。"""
    links = []
    for fid in ("69", "92", "292"):
        if (ROOT / "static" / "fonts" / fid / "result.css").exists():
            links.append(
                f'<link rel="stylesheet" href="/app/static/fonts/{fid}/result.css">'
            )
    return "\n".join(links)


_INJECT_CSS = """
<style>
/* 收紧页面顶部大空白 */
.block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
[data-testid="stHeader"] { height: 2.6rem; }
[data-testid="stHeader"] > div { height: 2.6rem; }

/* 正文：思源黑体。只对文本容器显式设置（不碰 span/div 通配，
   否则会覆盖 Streamlit 的 Material Symbols 图标字体导致箭头乱码） */
.stApp, [data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stSidebar"], [data-testid="stSidebar"] p,
[data-testid="stCaptionContainer"],
.stButton>button, .stRadio label, .stTextArea textarea, .stTextInput input,
.stAlert, [data-testid="stExpander"] summary,
[data-testid="stMetric"], [data-testid="stMetricValue"],
[data-testid="stMetricLabel"], .stTabs button {
  font-family: "Noto Sans CJK", "Source Han Sans SC", "MiSans",
    "HarmonyOS Sans SC", "PingFang SC", "Microsoft YaHei UI", sans-serif;
}

/* 标题：h1/h2 得意黑；h3-h6 思源黑体（不指定的话 Streamlit 默认 Source Sans
   无中文字形，浏览器会回退到日文字体，中文显示成日文变体） */
h1, h2, .stApp h1, .stApp h2 {
  font-family: "Smiley Sans Oblique", "Noto Sans CJK", "Microsoft YaHei UI", sans-serif;
  letter-spacing: 0.02em;
}
h3, h4, h5, h6, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
  font-family: "Noto Sans CJK", "Source Han Sans SC", "Microsoft YaHei UI", sans-serif;
}

/* 法条引用块：霞鹜文楷（文书感） */
.stMarkdown blockquote, [data-testid="stMarkdownContainer"] blockquote,
.stMarkdown blockquote p {
  font-family: "LXGW WenKai", "KaiTi", "STKaiti", "Noto Sans CJK", serif;
}

div[data-testid="stMarkdownContainer"] p,
section[data-testid="stMarkdownContainer"] p {
  text-indent: 2em;
}

/* 修正：列表项、折叠框标题、按钮、单选项内的段落不缩进。
   必须 !important——上面规则的特异性（div[attr] p）高于普通后代选择器，
   不加 !important 会漏进去，导致圆点/箭头/按钮文字后出现 2em 大空隙 */
li p, summary *, .stButton p, .stRadio p, .stCheckbox p {
  text-indent: 0 !important;
}

.stMarkdown blockquote p { text-indent: 2em; }
.stMarkdown blockquote { line-height: 1.9; }

/* 侧栏知识点按钮文字左对齐 */
[data-testid="stSidebar"] button { text-align: left; }
[data-testid="stSidebar"] button p { text-align: left; width: 100%; }

/* 右栏学习笔记 sticky：随页面滚动悬浮跟随。
   Streamlit columns 是 flex 布局，sticky 需要 align-self:flex-start
   防止子项被拉伸导致 sticky 失效；不设 overflow（否则 sticky 参照系错乱）。
   top 避开 Streamlit 顶栏（3.5rem），z-index+背景防止滚动内容穿透遮挡 */
div[data-testid="stColumn"]:has(textarea) {
  position: sticky;
  top: 3.5rem;
  align-self: flex-start;
  z-index: 50;
  background: var(--background-color, #fff);
  padding-top: 0.4rem;
}
</style>
"""

_FONT_CSS = _load_font_css()


def status_badge(user: str, pid: str) -> str:
    s = pmod.status_of(user, pid)
    return {"mastered": "✅ 已掌握", "review": "🔁 待复习"}.get(s, "")


def _note_mark(user: str, pid: str) -> str:
    return " 📝" if nmod.has(user, pid) else ""


def _short_chapter(ch: str) -> str:
    """「第二章 物权法」→「物权法」。"""
    return re.sub(r"^第.+?章\s*", "", str(ch))


def _short_section(sec: str) -> str:
    """「四、担保物权制度」→「担保物权制度」。"""
    return re.sub(r"^[一二三四五六七八九十]+、\s*", "", str(sec))


def _clear_quiz_result(key: str) -> None:
    st.session_state.pop(f"{key}-result", None)


def render_quiz(p: dict) -> None:
    letters = "ABCD"
    for qi, q in enumerate(p.get("quiz") or []):
        key = f"quiz-{p['id']}-{qi}"
        st.markdown(f"**第{qi + 1}题**　{q['question']}")
        choice = st.radio(
            "你的答案", q["options"], key=key, index=None,
            label_visibility="collapsed", on_change=_clear_quiz_result, args=(key,),
        )
        result = st.session_state.get(f"{key}-result")
        if result is not None:
            idx, ok = result
            if ok:
                st.success(f"✓ 答对了！{q['explain']}")
            else:
                st.error(f"✗ 正确答案是 {q['answer']}。{q['explain']}")
        if st.button("提交答案", key=f"{key}-btn"):
            if choice is None:
                st.warning("先选一个答案再提交")
            else:
                idx = q["options"].index(choice)
                st.session_state[f"{key}-result"] = (idx, idx == letters.index(q["answer"]))
                st.rerun()


def render_notes(pid: str) -> None:
    st.markdown("#### 🗒️ 学习笔记")
    key = f"note-{pid}"

    def _save() -> None:
        nmod.set_text(USER, pid, st.session_state[key])

    text = nmod.get_text(USER, pid)
    st.text_area(
        "笔记", value=text, key=key, on_change=_save, height=420,
        label_visibility="collapsed",
        placeholder="用你自己的话写：这里在讲什么？容易错在哪？案例怎么记？……",
    )
    if (st.session_state.get(key) or "").strip():
        st.caption(f"📝 已自动保存 · {nmod.updated_at(USER, pid)}")
    else:
        st.caption("边学边记，自动保存，下次打开本页还在")


# ---------- 侧栏 ----------

def sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### ⚖️ 经济法备考助手")

        prog = pmod.load(USER)
        total = len(dmod.load_points())
        m, r = len(prog["mastered"]), len(prog["review"])
        st.caption(f"已掌握 {m}/{total} · 待复习 {r}")

        if st.button("🏠 首页（总览 · 知识体系图）", key="home", use_container_width=True):
            st.query_params.clear()
            st.rerun()

        outline = dmod.load_outline()
        for ch in outline["chapters"]:
            with st.expander(f"{ch['title']}（{ch['count']}）"):
                for sec in ch["sections"]:
                    st.caption(f"**{sec['title']}**")
                    for pid in sec["points"]:
                        p = dmod.get_point(pid)
                        if st.button(
                            f"{p['title']}　{status_badge(USER, pid)}{_note_mark(USER, pid)}",
                            key=f"tree-{pid}",
                            use_container_width=True,
                        ):
                            st.query_params["p"] = pid
                            st.rerun()

        if st.button("🔄 重新加载数据（改了 YAML 后点这里）"):
            dmod.clear_cache()
            st.rerun()
        st.caption("由 [MaxforCherubim](https://github.com/MaxforCherubim) 制作 · 基于 [Streamlit](https://streamlit.io) 构建")


# ---------- 知识点详情 ----------

def render_point(pid: str) -> None:
    p = dmod.get_point(pid)
    prev_id, next_id = dmod.neighbors(pid)

    left, right = st.columns([0.72, 0.28], gap="large")

    with left:
        st.caption(f"{_short_chapter(p['chapter'])} › {_short_section(p['section'])}")
        st.title(f"{p['title']}　{status_badge(USER, pid)}")

        if pid in DIAGRAMS:
            render_diagram(*DIAGRAMS[pid])

        with st.expander("📜 法条原文（先理解逻辑，再回看原文；赶进度可跳过）", expanded=False):
            st.markdown(quote_block(p["original"]))

        st.markdown("#### 💡 为什么这么写")
        st.markdown(p.get("why_written", ""))

        name_origin = p.get("name_origin")
        if name_origin:
            st.markdown("#### 🏷️ 名词由来")
            st.markdown(name_origin)

        examples = p.get("examples") or []
        if examples:
            st.markdown("#### 🌏 生活中的案例")
            for i, e in enumerate(examples, 1):
                with st.expander(f"案例{i}：{e['title']}", expanded=len(examples) <= 2):
                    st.markdown(f"**场景**：{e['story']}")
                    st.markdown(f"**分析**：{e['analysis']}")

        exam_tips = p.get("exam_tips")
        if exam_tips:
            st.markdown("#### ⚡ 考点提示")
            st.info(exam_tips)

        if p.get("quiz"):
            st.markdown("#### 📝 练一练")
            render_quiz(p)

        st.markdown("---")
        b1, b2, _sp = st.columns([1, 1, 4])
        status = pmod.status_of(USER, pid)
        if b1.button("✅ 掌握了", key=f"m-{pid}",
                     type="primary" if status == "mastered" else "secondary",
                     use_container_width=True):
            pmod.set_status(USER, pid, "" if status == "mastered" else "mastered")
            st.rerun()
        if b2.button("🔁 待复习", key=f"r-{pid}",
                     type="primary" if status == "review" else "secondary",
                     use_container_width=True):
            pmod.set_status(USER, pid, "" if status == "review" else "review")
            st.rerun()

        n1, n2 = st.columns(2)
        if prev_id and n1.button(f"← {dmod.get_point(prev_id)['title']}", key=f"prev-{pid}",
                                 use_container_width=True):
            st.query_params["p"] = prev_id
            st.rerun()
        if next_id and n2.button(f"{dmod.get_point(next_id)['title']} →", key=f"next-{pid}",
                                 use_container_width=True):
            st.query_params["p"] = next_id
            st.rerun()
        st.caption("学习法：先理解 💡 → 看案例 🌏 → 做题 📝 → 有空再读原文 📜")

    with right:
        render_notes(pid)


# ---------- 首页 ----------

def welcome() -> None:
    outline = dmod.load_outline()
    st.title("⚖️ 经济法备考助手")
    days = (EXAM_DATE - date.today()).days
    c1, c2, c3 = st.columns(3)
    c1.metric("距考试", f"{days} 天")
    c2.metric("知识点总数", f"{outline['total']}")
    prog = pmod.load(USER)
    c3.metric("已掌握", f"{len(prog['mastered'])}")

    st.markdown(
        """
**怎么用**：左侧点「🏠 首页」回到本页，点各章大纲进入知识点。每个知识点这样学：
💡 为什么这么写（分点讲透）→ 🏷️ 名词由来 → 🌏 生活案例 → ⚡ 考点提示 → 📝 练一练；
吃不准时再展开 📜 法条原文 回看原文。学完点 ✅ 已掌握（吃不准的点 🔁 待复习），
重要内容写进右栏笔记。图解自动适应框宽，点图下链接可新标签放大看细节。

**范围**：官方《经济学》科目考试大纲「经济学类基础综合」第三篇 经济法，共 6 章。
"""
    )
    st.caption("数据依据：官方《经济学》科目考试大纲（2023-08，军队人才网）· 原始 PDF 与提取文本见本地 data/raw/")

    st.markdown("### 各章进度")
    rows = ["| 章 | 知识点 | 已掌握 | 待复习 |", "|---|---|---|---|"]
    for ch in outline["chapters"]:
        pids = [pid for sec in ch["sections"] for pid in sec["points"]]
        rows.append(
            f"| {ch['title']} | {len(pids)} "
            f"| {sum(1 for x in pids if pmod.status_of(USER, x) == 'mastered')} "
            f"| {sum(1 for x in pids if pmod.status_of(USER, x) == 'review')} |"
        )
    st.markdown("\n".join(rows), unsafe_allow_html=False)

    st.markdown("### 法条版本基准")
    st.markdown(
        """
| 法律 | 现行版本 | 说明 |
|---|---|---|
| 《民法典》 | 2021-01-01 施行 | 物权编、合同编、总则编（代理） |
| 《招标投标法》 | 2017 修正 | 配套《实施条例》2019 修订 |
| 《票据法》 | 2004 修正 | — |
| 《著作权法》 | 2020 修正 | 2021-06-01 施行 |
| 《专利法》 | 2020 修正 | 2021-06-01 施行 |
| 《商标法》 | 2019 修正 | 2019-11-01 施行 |
"""
    )

    st.markdown("---")
    with st.expander("🗺️ 经济法知识体系全景", expanded=True):
        st.image(_diagram_bytes("knowledge-tree.png"), width="stretch")
        st.markdown(
            '<a href="/app/static/diagrams/knowledge-tree.png" target="_blank" '
            'rel="noreferrer">🔍 在新标签打开大图（浏览器原生缩放/拖动）</a>',
            unsafe_allow_html=True,
        )

    st.caption("由 [MaxforCherubim](https://github.com/MaxforCherubim) 制作 · 本应用基于 [Streamlit](https://streamlit.io) 构建")


def main() -> None:
    st.markdown(_INJECT_CSS + _FONT_CSS, unsafe_allow_html=True)
    # 首次进入时若 outline 缺失给出明确提示
    try:
        dmod.load_outline()
        dmod.load_points()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    sidebar()
    pid = st.query_params.get("p")
    if pid and dmod.get_point(pid):
        render_point(pid)
    else:
        welcome()


if __name__ == "__main__":
    main()
