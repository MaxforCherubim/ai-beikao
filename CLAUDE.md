# CLAUDE.md — 项目维护文档

> 本文件是 AI 助手与维护者的共同规范。**每次会话开始先读本文件**；改动任何约定后必须更新本文件并追加迭代日志。

## 1. 项目是什么

为「军队文职考试·助理审计岗」备考搭建的**全科目备考助手**（Streamlit，本地运行）。
覆盖：公共科目（基本知识·法律国防和军队·岗位能力）+ 专业科目《经济学》（含经济法）。

两类知识点内容：
- **精写知识点**（经济法 89 个，`data/points/`）：六件套——① 法条原文 → ② 为什么这么写 → ③ 名词由来 → ④ 生活案例 → ⑤ 考点提示 → ⑥ 练一练。目标：通过"完全理解"学透，而不是死记法条。
- **融合知识点**（`data/library/`，kind: fused）：以**官方大纲测查点**为单位，把多本讲义（文字版管线提取 + 图版读图转写的碎片）去重融合而成；应用内以自绘 SVG 思维导图为主视图（`core/tree_svg.py`），文字版折叠备查，sources 标注各书页码。

导航骨架 = 官方大纲（`data/outline_official.json`，subjects → parts → chapters → 测查点），不用讲义自带章节。

备考策略（2026-11-24 定）：**以做题为重**——刷题用 `data/题库/` 的 PDF 在 reMarkable 上做，应用内不做在线刷题；考点复习优先级降低。

## 2. 考试信息（固定事实）

- 考试日期：**2026-12-13**
- 科目：公共科目 + 专业科目《经济学》
- 大纲依据：`data/raw/2023-08官方大纲_经济学专业科目.pdf`、`data/raw/2023-08官方大纲_公共科目.pdf`（中央军委政治工作部，2023-08 发布，军队人才网）
- 经济法范围 = 「经济学类基础综合」第三篇，共 6 章：导论 / 物权法 / 招标投标法 / 合同法 / 票据法 / 知识产权法
- 客观题，满分 100，120 分钟
- 注意：《审计》大纲经济法篇只含前 3 章（子集）；本项目以《经济学》大纲为准（超集覆盖）

## 3. 目录结构规范

```
AI备考辅助学习/
├── CLAUDE.md                  # 本文件（规范锚点）
├── README.md                  # 使用说明
├── requirements.txt           # 依赖清单（记录实际验证过的版本）
├── app.py                     # Streamlit 入口（唯一）
├── core/
│   ├── data.py                # 加载 points/ + library/ + outline.json，内存缓存
│   ├── tree_svg.py            # 知识点内容树 → 横向思维导图 SVG（纯标准库）
│   ├── search.py              # jieba 分词检索（备用，无 UI）
│   ├── progress.py            # 学习进度读写 .progress.考生.json
│   ├── notes.py               # 笔记读写 .notes.考生.json
│   └── ai.py                  # 可选 AI 追问（备用，无 UI）
├── tools/
│   ├── extract_syllabus.py    # 官方 PDF → 提取文本（--save 存 data/raw/）
│   ├── extract_official_outline.py  # 官方大纲 txt → data/outline_official.json（导航/融合唯一骨架）
│   ├── build_library.py       # 文字版讲义 PDF → 碎片 YAML（融合的中间步骤，融合完删碎片）
│   ├── organize_data.py       # data/ 资料整理映射（移动+重命名+登记表，可重跑）
│   ├── build_outline.py       # 官方骨架挂点 → data/outline.json v3（subjects→parts→chapters）
│   ├── verify_points.py       # 三 schema 校验（精写 11 必填 / fused 8 必填 / auto 8 必填）
│   └── normalize_points.py    # 精写正文规范化（引号/空格/段落）
├── data/
│   ├── raw/                   # ★ 官方原始资料区：只读、只增不删，见其 README.md
│   ├── outline_official.json  # 官方大纲树（extract_official_outline.py 生成，勿手改）
│   ├── outline.json           # 应用大纲树 v3（官方骨架+挂点，build_outline.py 生成）
│   ├── points/                # 精写知识点 YAML（经济法 6 章子目录，89 个）
│   ├── library/               # 融合知识点 YAML（每官方测查点一个文件）
│   │   ├── 公共科目/          # gk-（基本知识）gn-（岗位能力）
│   │   └── 经济学/            # wg-微观 hg-宏观 cz-财政 jr-金融 tj-统计（经济法=精写，不融合）
│   ├── 知识点/                # 教材讲义 PDF 原件（8 本，仅本地；README 登记表）
│   └── 题库/                  # 题库 PDF（年份/真题|模拟题 分级；综合/ 无年份；综合/备用/ 重复来源）
├── static/fonts/              # 自托管字体切片（仅本地，gitignore）
├── .progress.考生.json / .notes.考生.json   # 运行时数据（gitignore）
└── .zcode/skills/             # 项目技能（见 §8）
```

规则：
- `data/raw/`、`data/知识点/`、`data/题库/` 内容永不修改、永不上传（版权+体积）；原件移动/重命名必须走 `tools/organize_data.py` 并同步登记表
- `data/outline.json` 只由 `tools/build_outline.py` 生成
- `data/library/` 下 YAML 只由 `tools/build_library.py` 或读图转写产出；重跑 build_library 会清空对应书目录
- 知识点文件新增/修改后必须跑校验命令（见 §6）
- 不引入新依赖除非必要；当前依赖：streamlit、pyyaml、jieba、requests；tools 侧另需 pymupdf（均由用户 pixi 安装）

## 4. 知识点数据 Schema

### 4.1 精写六件套（data/points/**/*.yaml）— v2

```yaml
id: wq-015                  # 章前缀小写拼音缩写 + 两位序号，全库唯一
chapter: 第二章 物权法       # 必须与官方大纲章名一致
section: 四、担保物权制度     # 与官方大纲节名一致
title: 抵押权
keywords: [抵押, 不动产登记, 抵押登记, 最高额抵押]   # 4~8 个检索词
original: |                 # ① 法条原文：现行法律条文，逐字准确，标注条号（应用中默认折叠）
  《民法典》第三百九十四条　为担保债务的履行，……
why_written: |              # ② 为什么这么写：**分点列表**，3~6 点，每点 "- **小标题**：一两句话"
  - **不转移占有是抵押的灵魂**：房子抵押给银行你照样住——……
name_origin: |              # ③ 名词由来：这个术语为什么叫这个名字（拆词/构词/直觉解释），80~150字
  抵押 = "抵"+"押"：把财产押在那里……
examples:                   # ④ 生活案例 1~3 个，用买房/网购/开店/借钱等日常场景
  - title: 小王买房按揭
    story: ...
    analysis: ...
exam_tips: |                # ⑤ 考点提示：必背数字、情形列举、易混淆对比
quiz:                       # ⑥ 练一练：1~2 道单选题（学习反馈）
  - question: 老李把汽车抵押给老周……（场景化题干）
    options: [选项A, 选项B, 选项C, 选项D]
    answer: B               # 字母，对应 options 下标
    explain: 解析——口语化，点明对应规则/条号
related: [wq-014, wq-016]   # 内部关联 id
```

字段硬性要求：
- `original` 引用法条必须注明法律名 + 条号；条号一律用**中文数字**；`why_written`/`name_origin`/`exam_tips`/`quiz.explain` 中的简注式条号可用阿拉伯数字
- `why_written` 必须分点（markdown 列表），每点以加粗小标题开头；跨章节联动直接在分点里用文字写明
- `quiz` 1~2 道单选，题干场景化，干扰项迷惑但明确错误，答案 A/B/C/D 均衡分布
- 章前缀约定：`dl`=导论 `wq`=物权法 `zbtb`=招标投标法 `ht`=合同法 `pj`=票据法 `zscq`=知识产权法
- 序号章内连续，插入新知识点用未占用号，不重排已有 id（id 是进度记录和 related 的锚）

### 4.2 融合知识点（data/library/**/*.yaml）— fused

```yaml
id: wg-005                  # 域前缀 + 三位序号：gk 基本知识 gn 岗位能力 wg 微观 hg 宏观
kind: fused                 # cz 财政 jr 金融 tj 统计（经济法不融合，用精写）
subject: 经济学              # 公共科目 | 经济学
part: 第一篇微观经济学       # 官方大纲 part 名（逐字）
chapter: 第二章均衡价格理论   # 官方大纲章名（逐字，无空格）
section: ""                 # 官方节名（公共科目基本知识有节；其余留空）
node: 二、供给               # 官方测查点名（逐字）；章级单元填章名
title: 供给                  # = node 去「一、」前缀
content: |                  # 融合后的内容树（嵌套列表），应用渲染为思维导图
  - **供给**
    - **供给的概念及影响因素**
      - 主体：生产者
sources:                    # 融合用到的来源（书+页码，或「官方大纲 2023-08」）
  - 经济学-专业教材.pdf p.5
```

硬性要求：
- 一个**官方测查点** = 一个 YAML（outline_official.json 的 node；无 node 的章按章级单元）
- 内容只许来自讲义碎片与官方大纲，不许编造；多书重复取信息量最大表述，互补子点取并集
- ★重点、口诀、数字、公式逐字保留；原文截断/不清处标注（原文转写不全）等，不补写
- 碎片未覆盖的官方子主题用大纲分号子主题兜底作骨架，sources 加「官方大纲 2023-08」

### 4.3 正文排版规范（两种 schema 通用，Markdown 渲染约束）

- **每段一行**：一个段落独占一行，段与段之间空一行；**不要在段内手动折行**——Markdown 会把单个换行渲染成空格，导致中文句子中间出现空格
- **引号一律中文引号**：“ ” ‘ ’；正文里不出现 ASCII 引号
- **行内不留多余空格**：中文字符与中文标点之间不要有空格
- **首行缩进由 app 渲染**（CSS text-indent 自动处理），YAML 里不要手写缩进；列表项不缩进
- 列表项每行一个（`- `），列表项的续行并入该行，不要单独成行
- 精写内容新增/修改后先跑 `python tools/normalize_points.py` 兜底规范化，再跑校验

## 5. 法条版本基准（精写写作时唯一依据）

| 法律 | 现行版本 | 生效/修正 |
|---|---|---|
| 《民法典》 | 2020-05-28 通过 | 2021-01-01 施行（物权编=第二编、合同编=第三编） |
| 《招标投标法》 | 2017 修正 | 原法 2000-01-01 施行 |
| 《招标投标法实施条例》 | 2019 修订 | 2012 施行 |
| 《票据法》 | 2004 修正 | 原法 1996-01-01 施行 |
| 《著作权法》 | 2020 修正 | 2021-06-01 施行 |
| 《专利法》 | 2020 修正 | 2021-06-01 施行 |
| 《商标法》 | 2019 修正 | 2019-11-01 施行 |

**条号零差错规则**：写入 `original` 前必须核对条号。记忆不确定时，宁可只写法律名+规则内容、不写条号，也不许编条号。审核用 `tools/verify_points.py --list-articles` 抽取全部条号清单人工核对。

## 6. 工作流命令

```bash
# 官方大纲骨架（大纲更新时）
python tools/extract_official_outline.py

# 讲义碎片提取（新增文字版讲义时；图版书读图转写；碎片融合进 library 后删除）
python tools/build_library.py

# 正文规范化（精写知识点新增/修改后先跑）
python tools/normalize_points.py

# 校验全部知识点（精写 11 必填 + auto 8 必填、id 唯一、引用）
python tools/verify_points.py

# 汇总生成大纲树 v2（校验通过后执行）
python tools/build_outline.py

# 启动应用
python -m streamlit run app.py

# 官方 PDF 提取（新增资料时）
python tools/extract_syllabus.py "data/raw/<文件>.pdf" --save
```

校验不过 → 修复后重跑，禁止跳过校验生成 outline.json。

## 7. 环境与启动

- Python 3.12.16（pixi `ds` 环境，`python` 直用）
- 已装：streamlit 1.67.0 / pyyaml 6.0.3 / jieba 0.42.1 / requests 2.34.2 / pymupdf 2.1.0（由用户 pixi 安装，勿重装勿换环境）
- 启动：`python -m streamlit run app.py`（本地使用；不再维护 Streamlit Cloud 部署）
- 字体：static/fonts/ 自托管三件套（#69 思源黑正文 / #92 得意黑标题 / #292 霞鹜文楷引用块），仅本地、gitignore；缺失时回退系统字体，**无需用户安装任何字体**
- 项目在百度网盘同步盘内：不要在项目里放大体积缓存文件；资料 PDF 一律放 data/知识点/ 与 data/题库/（已 gitignore）

## 8. Skill 与 MCP 登记

**项目 Skill（`.zcode/skills/`）**
- `exam-kp`：精写知识点写作规范技能——固化 §4.1 schema、§5 条号规则、校验流程
- `streamlit-app`：**Streamlit 官方 agent skill**（从本机已装 streamlit 1.67.0 包内复制，Apache 2.0）——开发/调试/美化 UI 时使用

**MCP 决策记录**
- 本项目为本地数据型应用（YAML + Streamlit），Bash/文件工具已覆盖全部操作，**现阶段不建 MCP**

## 9. 迭代日志（每次改动追加一条，新条目在最上）

### 2026-11-24 v2.1 官方大纲骨架 + 讲义融合 + 思维导图渲染（用户 4 条反馈）
- 删会计学内容（27 点，源自《财经必背考点》书，不在考纲）；删经济法重复碎片 32 个（精写 89 点即最优版）
- 导航改官方大纲树：tools/extract_official_outline.py 从大纲 txt 提取 outline_official.json（公共 8 章 42 测查点 + 岗位能力 4 章；经济学 6 篇 40 章 136 测查点）；侧栏/进度表/导航全挂官方树
- 讲义融合：以官方测查点为单位合并多书碎片（156 个 fused 点：gk46/gn4/wg24/hg20/cz18/jr21/tj23），去重取 richest、互补取并集、★/公式/口诀逐字保留、无碎片节点用大纲子主题兜底；碎片目录与 tmp 脚手架已删，data/library 只留 公共科目/经济学 两目录
- 思维导图渲染：core/tree_svg.py（纯标准库 SVG 横向树，多根森林、超宽横滚、继承页面字体）；fused 页 = 导图主视图 + 折叠文字版 + sources 页码
- 坑：官方大纲提取文本标题无空格（第二章物权法）而 YAML 带空格——build_outline 比较前 norm() 去空格；岗位能力章官方无「一、」节点，按章级单元融合
- 总计 245 点（精写 89 + 融合 156），2 科目 48 章，校验全过；v2.0 已推送 GitHub（81f572d）

### 2026-11-24 v2.0 全科目大改（去图解 + 资料整理 + 讲义入库）
- 定位升级：经济法助手 → 军队文职全科备考助手（公共科目 + 经济学）；备考策略改为做题为重（reMarkable 刷 PDF，应用不做在线刷题）
- 移除全部 archify 图解（app.py DIAGRAMS/render_diagram/首页全景图、static/diagrams/、.archify/）
- 资料整理：`tools/organize_data.py` 移动+重命名 211 个 PDF → data/知识点/（8 本教材）+ data/题库/（年份/真题|模拟题 分级，综合/ 无年份，综合/备用/ 重复来源），登记表自动生成于两处 README
- 讲义入库双通道：①`tools/build_library.py` 文字版管线（考点集锦/财经必背/金融学必背 155 点：清洗页眉水印填空下划线图碎片→断行合并→按书配置切分）；②图版思维导图 5 本（无文字层）读图转写（ff/fl/gw/js/jc 前缀）
- PDF 实测教训：公共科目三本+经济学思维导图两本是**图版**（文字层仅标题，正文在思维导图图片里；书签完整可作骨架）；千题库/25蓝军卷是纯扫描版（只整理不提取）
- outline.json v2：subjects（公共科目/经济学）→ chapters → sections → points；精写经济法 6 章归入经济学科目
- verify_points 双 schema：精写 11 必填不变；auto 8 必填（id/subject/book/chapter/section/title/content/source）
- app.py：科目树侧栏、auto 讲义速览渲染（content + 来源页码 caption）、首页按科目分组进度表；笔记/进度/上下条导航天然兼容新 id
- git 瘦身：.gitignore 新增 data/知识点/、data/题库/、data/**/*.pdf、static/fonts/（约 40MB 字体切片只留本地）
- 验证：AppTest 三页零异常；浏览器截图首页/精写/讲义/公共科目转写页；ff-005 转写与原 PDF p.8 思维导图逐项核对一致

### 2026-11-24 v1.9 图解交互定稿 + 界面精简 + 云端公开生效
- 图解最终方案：框内 st.image 适应宽度 + 图下「新标签打开大图」链接
- 移除每页底部「问 AI」面板（core/ai.py 模块保留备用）；侧栏顶部加「🏠 首页」按钮
- 云端公开已生效；本地 cloudflared 临时隧道已停止

### 2026-11-24 v1.8 图解改静态 PNG（用户反馈：不需要交互、加载慢）
- 交互版 HTML → archify export-svg → Chrome 无头 2x 截 PNG；st.iframe → st.image
- 仓库瘦身：static/diagrams 下 *.html/*.svg/*.json 只留本地

### 2026-11-23 v1.7 archify 交互式图解（4 张）
- 四张图（knowledge-tree/bidding-workflow/contract-lifecycle/note-sequence）；集成 st.iframe 嵌入 expander

### 2026-11-23 v1.6 侧栏精简 + 缩进误伤修复（用户截图反馈）
- 移除侧栏搜索框；修复首行缩进 2em 漏进列表/折叠框/按钮（`li p, summary *, .stButton p, .stRadio p, .stCheckbox p { text-indent:0 !important }`）

### 2026-11-23 v1.5 排版精修 + 字体自托管 + 单身份化（用户截图 6 条反馈）
- 顶部大空白收紧；倒计时移首页 metric；删除多用户切换（单身份「考生」）
- 字体自托管 static/fonts/（思源黑/得意黑/文楷切片），link 引入；font-display swap→optional
- 踩坑：50万字符 CSS 内联会被截断泄漏；h3-h6 不指定中文字体会回退日文字形；sticky 需 align-self:flex-start

### 2026-11-23 v1.4 分享上线（Cloudflare 免费隧道 + 多用户隔离）
- cloudflared 快速隧道分享；多用户隔离（后于 v1.5 简化为单身份）；一键脚本 .tools-bin/cloudflared/启动分享.bat

### 2026-11-23 v1.3 中文字体方案 + 页脚署名
- 三字体各司其职（ZeoSeven CDN → v1.5 改自托管）；页脚署名；侧栏倒计时文案缩短

### 2026-11-23 v1.2 应试导向重构（用户 8 条反馈）
- 页眉简化、法条折叠、删除相关知识点按钮区、新增右栏笔记栏；答题系统（quiz 178 题）；内容 v2 迁移（why_written 分点、background→name_origin）

### 2026-11-23 v1.1 正文排版规范化（用户反馈修复）
- 首行缩进 CSS 方案、段内折行空格修复、ASCII 引号转中文引号；normalize_points.py 诞生

### 2026-11-22 v1.0 首个完整版本（89 个知识点全量上线）
- 经济法 6 章 89 知识点；条号对照权威全文逐字核对；AppTest 三页验证

### 2026-11-22 v0.1 项目初始化
- 4 份官方大纲 PDF 入 data/raw/；骨架搭建；exam-kp、streamlit-app 技能创建
