# 经济法备考助手（军队文职·助理审计）

用 **Streamlit** 搭建的经济法辅助学习工具。核心学习法：每个知识点按五步走——
**📜 法条原文 → 💡 为什么这么写 → 🏛️ 立法背景 → 🌏 生活案例 → ⚡ 考点提示**，
通过"完全理解"学透，而不是死记法条。

- 考试：2026-12-13 · 科目：公共科目 + 专业科目《经济学》
- 范围：《经济学》大纲「经济学类基础综合」第三篇 经济法（导论 / 物权法 / 招标投标法 / 合同法 / 票据法 / 知识产权法，共 6 章）
- 权威依据：`data/raw/` 下的官方大纲 PDF（含来源登记，可自行核对）

## 快速开始

```bash
# 依赖（pixi ds 环境已装好 streamlit / pyyaml / jieba / requests，见 requirements.txt）
python -m streamlit run app.py
```

浏览器会自动打开 http://localhost:8501。

## 功能

| 功能 | 说明 |
|---|---|
| 大纲导航 | 左侧按官方大纲的章→节→知识点逐级展开 |
| 关键词检索 | 支持法条名、关键词、场景词（如"抵押""背书""串通投标"），命中片段高亮并标注章节 |
| 五件套详解 | 每个知识点呈现法条原文、立法逻辑、背景、生活案例、考点提示 |
| 学习进度 | ✅ 已掌握 / 🔁 待复习，存于 `.progress.json`（删除即重置） |
| 可选 AI 追问 | 配置智谱 Key 后，可在任意知识点页面继续追问（见下） |

## 可选：配置 AI 追问

不配置不影响任何功能。配置后每个知识点页面底部出现"问 AI"面板：

1. 在[智谱开放平台](https://open.bigmodel.cn)注册并获取 API Key（`glm-4-flash` 模型免费）
2. 二选一：
   - 设环境变量 `ZHIPUAI_API_KEY=你的Key`
   - 项目下创建 `.streamlit/secrets.toml`：`ZHIPUAI_API_KEY = "你的Key"`

## 目录结构 / 维护

见 [CLAUDE.md](CLAUDE.md)（项目规范锚点：数据 schema、法条版本基准、校验与生成命令、迭代日志）。

常用命令：

```bash
python tools/verify_points.py      # 校验全部知识点（id/字段/引用/章名）
python tools/verify_points.py --list-articles   # 导出条号清单供人工核对
python tools/build_outline.py      # 重新生成 data/outline.json
python tools/extract_syllabus.py "data/raw/<pdf>" --save   # 官方PDF提取文本
```

## 资料版权说明

`data/raw/` 中官方考试大纲版权归中央军委政治工作部所有，本项目仅将其用于个人备考学习，不得传播。
