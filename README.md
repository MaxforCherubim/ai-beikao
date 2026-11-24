# 军队文职备考助手（公共科目 + 经济学）

用 **Streamlit** 搭建的全科目备考工具。两类知识点内容：

- **精写知识点**（经济法 89 个）：六件套学习法——
  **📜 法条原文 → 💡 为什么这么写 → 🏷️ 名词由来 → 🌏 生活案例 → ⚡ 考点提示 → 📝 练一练**，
  通过"完全理解"学透，而不是死记法条。
- **讲义速览**（公共科目 + 经济学讲义自动结构化）：讲义原文按考点切分，含解释与例题，标注来源页码。

- 考试：2026-12-13 · 科目：公共科目 + 专业科目《经济学》
- 范围：公共科目（基本知识·法律国防和军队·岗位能力）+《经济学》（经济学/财政学/金融学/统计学/经济法）
- 刷题：`data/题库/` 下的 PDF（按年份分真题/模拟题），在 reMarkable 上作答；应用内不做在线刷题
- 权威依据：`data/raw/` 下的官方大纲 PDF（含来源登记，可自行核对）

## 快速开始

```bash
# 依赖（pixi ds 环境已装好，见 requirements.txt）
python -m streamlit run app.py
```

浏览器会自动打开 http://localhost:8501。

## 功能

| 功能 | 说明 |
|---|---|
| 科目导航 | 左侧按 科目 → 章 → 节 → 知识点 逐级展开 |
| 精写六件套 | 经济法知识点：法条原文、立法逻辑、名词由来、生活案例、考点提示、练习题 |
| 讲义速览 | 公共科目/经济学讲义原文结构化，含解释与例题，标注来源 PDF 页码 |
| 学习进度 | ✅ 已掌握 / 🔁 待复习，存于 `.progress.考生.json`（删除即重置） |
| 学习笔记 | 每个知识点右栏笔记，自动保存于 `.notes.考生.json` |

## 目录结构 / 维护

见 [CLAUDE.md](CLAUDE.md)（项目规范锚点：数据 schema、法条版本基准、校验与生成命令、迭代日志）。

常用命令：

```bash
python tools/verify_points.py      # 校验全部知识点（精写六件套 + 讲义双 schema）
python tools/verify_points.py --list-articles   # 导出条号清单供人工核对
python tools/build_outline.py      # 重新生成 data/outline.json（科目→章→节）
python tools/build_library.py      # 文字版讲义 PDF → data/library/（3 本）
python tools/organize_data.py      # data/ 资料整理映射（知识点/题库 登记表来源）
python tools/extract_syllabus.py "data/raw/<pdf>" --save   # 官方PDF提取文本
```

## 资料说明

`data/知识点/`、`data/题库/` 为备考资料原件（仅本地，不进 git 仓库）；`data/raw/` 中官方考试大纲版权归中央军委政治工作部所有，本项目仅用于个人备考学习，不得传播。
