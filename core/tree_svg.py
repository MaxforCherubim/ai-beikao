# -*- coding: utf-8 -*-
"""知识点内容树 → 横向思维导图 SVG（纯标准库，无新依赖）。

输入为 fused/auto 知识点的 content 字段（markdown 嵌套列表：两级缩进一层，"- " 起头，
分支标签可 **加粗**）。输出内联 SVG 字符串，由 app 经 st.markdown(unsafe_allow_html)
嵌入——内联 SVG 继承页面 CSS 字体（自托管思源黑），无需系统字体。
"""
import html
import re

FS = 13.0            # 字号
LINE_H = FS * 1.45   # 行高
PAD_X, PAD_Y = 9.0, 6.0
GAP_X = 42.0         # 层间连接线长度
GAP_Y = 10.0         # 兄弟节点垂直间距
WRAP_W = 30.0        # 每行最大"字宽单位"（CJK=1，ASCII≈0.55）

# 每层底色/描边（柔和六色循环）
FILLS = ["#e8f0fe", "#e6f4ea", "#fef7e0", "#f3e8fd", "#e0f7f4", "#fde8e8"]
STROKES = ["#5b8def", "#4caf7d", "#e0a63a", "#9d6fd8", "#3aa9a0", "#e07a7a"]

RE_ITEM = re.compile(r"^(\s*)-\s+(.*)$")


def _width_units(text: str) -> float:
    return sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in text)


def _wrap(text: str) -> list[str]:
    """按字宽单位折行。"""
    lines, cur, cur_w = [], "", 0.0
    for ch in text:
        w = 1.0 if ord(ch) > 0x2E7F else 0.55
        if cur_w + w > WRAP_W and cur:
            lines.append(cur)
            cur, cur_w = "", 0.0
        cur += ch
        cur_w += w
    if cur:
        lines.append(cur)
    return lines or [""]


class _Node:
    __slots__ = ("lines", "bold", "children", "x", "y", "w", "h")

    def __init__(self, label: str, bold: bool):
        self.lines = _wrap(label)
        self.bold = bold
        self.children = []
        self.x = self.y = self.w = self.h = 0.0


def parse_tree(content: str) -> _Node:
    root = _Node("·", False)
    stack = [(-1, root)]
    for raw in str(content).splitlines():
        m = RE_ITEM.match(raw)
        if not m:
            continue
        level = len(m.group(1)) // 2
        label = m.group(2).strip()
        bold = label.startswith("**") and label.endswith("**")
        if bold:
            label = label[2:-2]
        node = _Node(label, bold)
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack[-1][1].children.append(node)
        stack.append((level, node))
    if not root.children:  # 非列表内容：整段作单列
        return _Node("（见文字版）", False)
    return root


def _measure(node: _Node) -> None:
    node.w = max(_width_units(l) for l in node.lines) * FS + PAD_X * 2
    node.h = len(node.lines) * LINE_H + PAD_Y * 2
    for c in node.children:
        _measure(c)


def _layout(node: _Node, x: float, cursor: list) -> None:
    """后序布局：叶子按游标堆叠，父节点垂直居中于子节点跨度。"""
    node.x = x
    if not node.children:
        node.y = cursor[0]
        cursor[0] += node.h + GAP_Y
    else:
        for c in node.children:
            _layout(c, x + node.w + GAP_X, cursor)
        first, last = node.children[0], node.children[-1]
        node.y = (first.y + last.y + last.h) / 2 - node.h / 2


def _depths(node: _Node, d: int, acc: dict) -> None:
    acc[d] = max(acc.get(d, 0.0), node.w)
    for c in node.children:
        _depths(c, d + 1, acc)


def _x_offsets(depth_widths: dict) -> list:
    xs, x = [], 8.0
    for d in range(len(depth_widths)):
        xs.append(x)
        x += depth_widths[d] + GAP_X
    return xs


def _place(node: _Node, d: int, xs: list, dy: dict) -> None:
    """列内统一左边界（同层盒子左对齐），记录全局 y 偏移。"""
    node.x = xs[d]
    node.y += dy[0]
    for c in node.children:
        _place(c, d + 1, xs, dy)


def _emit(node: _Node, d: int, out: list) -> None:
    fill, stroke = FILLS[d % 6], STROKES[d % 6]
    out.append(
        f'<rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.w:.1f}" height="{node.h:.1f}" '
        f'rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
    )
    for i, line in enumerate(node.lines):
        ty = node.y + PAD_Y + FS * 0.82 + i * LINE_H
        weight = ' font-weight="600"' if (node.bold and i == 0) else ""
        out.append(
            f'<text x="{node.x + PAD_X:.1f}" y="{ty:.1f}" font-size="{FS:.0f}"{weight} '
            f'fill="#222">{html.escape(line)}</text>'
        )
    cx, cy = node.x + node.w, node.y + node.h / 2
    for c in node.children:
        ex, ey = c.x, c.y + c.h / 2
        mx = (cx + ex) / 2
        out.append(
            f'<path d="M{cx:.1f},{cy:.1f} C{mx:.1f},{cy:.1f} {mx:.1f},{ey:.1f} {ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{STROKES[(d + 1) % 6]}" stroke-width="1.3" opacity="0.75"/>'
        )
        _emit(c, d + 1, out)


def render_svg(content: str) -> str:
    root = parse_tree(content)
    # 匿名根不画：单子提为根，多子作森林（多根并列，无根框无根连线）
    roots = root.children if len(root.children) >= 1 else [root]
    for r in roots:
        _measure(r)
    cursor = [8.0]
    for r in roots:
        _layout(r, 0.0, cursor)
    dw: dict = {}
    for r in roots:
        _depths(r, 0, dw)
    xs = _x_offsets(dw)
    dy = [8.0]  # _layout 已从 8 起算，无需再偏移
    for r in roots:
        _place(r, 0, xs, dy)
    total_w = max(xs[-1] + dw[len(dw) - 1], max(r.w for r in roots)) + 16
    total_h = cursor[0] + 8
    out = [
        '<div style="overflow-x:auto;">',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.0f} {total_h:.0f}" '
        f'role="img" style="width:{total_w:.0f}px;min-width:100%;height:auto;display:block;">',
    ]
    for r in roots:
        _emit(r, 0, out)
    out.append("</svg></div>")
    return "".join(out)
