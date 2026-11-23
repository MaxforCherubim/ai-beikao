# -*- coding: utf-8 -*-
"""从官方考试大纲 PDF 提取文本，用于核对知识点大纲结构。

用法:
    python tools/extract_syllabus.py <pdf路径> [--save] [--section 起始标记,结束标记]

示例:
    # 提取审计大纲中"第三篇经济法"到"第二部分"之间的文本
    python tools/extract_syllabus.py "data/raw/2023-08官方大纲_审计专业科目.pdf" \
        --section "第三篇经济法,第二部分"

--save 会把全文写入 data/raw/大纲提取_<文件名>.txt（UTF-8）。
"""
import argparse
import sys
from pathlib import Path

import pymupdf  # PyMuPDF 2.x，替代旧 fitz 接口

ROOT = Path(__file__).resolve().parent.parent


def extract_text(pdf_path: Path) -> str:
    doc = pymupdf.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    # 去掉每页重复出现的版权水印行
    watermark = "本大纲内容版权归中央军委政治工作部所有未经书面协议授权不得违法转载或使用"
    cleaned = []
    for p in pages:
        p = p.replace(watermark, "")
        cleaned.append(p.strip())
    return "\n".join(cleaned)


def _normalize(s: str) -> str:
    """去除所有空白，规避 PDF 换行把标题拆开的问题（中文文本可安全去空白）。"""
    return "".join(s.split())


def slice_section(text: str, marker: str) -> str:
    """按 '起始标记,结束标记' 截取片段；只给起始标记则截到文末。

    匹配在去空白后的文本上进行，返回的也是去空白文本。
    """
    if "," in marker:
        start_m, end_m = marker.split(",", 1)
    else:
        start_m, end_m = marker, None
    text = _normalize(text)
    start_m, end_m = _normalize(start_m), _normalize(end_m or "")
    i = text.find(start_m)
    if i < 0:
        raise SystemExit(f"未找到起始标记: {start_m}")
    j = text.find(end_m, i + len(start_m)) if end_m else -1
    return text[i : j if j > 0 else len(text)]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="提取官方大纲 PDF 文本")
    ap.add_argument("pdf", type=Path, help="PDF 文件路径")
    ap.add_argument("--save", action="store_true", help="保存全文到 data/raw/")
    ap.add_argument("--section", help="片段标记: 起始[,结束]")
    ap.add_argument("--head", type=int, default=600, help="预览前 N 字符")
    args = ap.parse_args()

    pdf_path = args.pdf if args.pdf.is_absolute() else ROOT / args.pdf
    text = extract_text(pdf_path)
    if args.section:
        text = slice_section(text, args.section)

    print(f"=== {pdf_path.name} 共 {len(text)} 字符 ===")
    print(text[: args.head])
    if args.save:
        out = ROOT / "data" / "raw" / f"大纲提取_{pdf_path.stem}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"[已保存] {out}")


if __name__ == "__main__":
    main()
