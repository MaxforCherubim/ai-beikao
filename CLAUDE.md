# CLAUDE.md — 项目维护文档

> 本文件是 AI 助手与维护者的共同规范。**每次会话开始先读本文件**；改动任何约定后必须更新本文件并追加迭代日志。

## 1. 项目是什么

为「军队文职考试·助理审计岗」备考搭建的**经济法辅助学习工具**（Streamlit）。

核心学习法：每个知识点呈现五件套——
① 法条原文 → ② 为什么这么写（立法逻辑）→ ③ 立法背景 → ④ 生活案例 → ⑤ 考点提示。
目标：通过"完全理解"学透经济法，而不是死记法条。

## 2. 考试信息（固定事实）

- 考试日期：**2026-12-13**
- 科目：公共科目 + **专业科目《经济学》**（用户自述，以此为准）
- 大纲依据：`data/raw/2023-08官方大纲_经济学专业科目.pdf`（中央军委政治工作部，2023-08 发布，军队人才网）
- 经济法范围 = 「经济学类基础综合」第三篇，**共 6 章**：导论 / 物权法 / 招标投标法 / 合同法 / 票据法 / 知识产权法
- 客观题，满分 100，120 分钟
- 完整章节考点目录见 `data/raw/大纲提取_经济学专业科目.txt`（经济法篇在文中搜「第三篇经济法主要测查」）
- 注意：《审计》大纲经济法篇只含前 3 章（子集）；本项目以《经济学》大纲为准（超集覆盖，两个岗位需求都能满足）

## 3. 目录结构规范

```
AI备考辅助学习/
├── CLAUDE.md                  # 本文件（规范锚点）
├── README.md                  # 使用说明（启动、API 配置）
├── requirements.txt           # 依赖清单（记录实际验证过的版本）
├── app.py                     # Streamlit 入口（唯一）
├── core/
│   ├── data.py                # 加载 outline.json + points，内存缓存
│   ├── search.py              # jieba 分词检索，字段加权
│   ├── progress.py            # 学习进度读写 .progress.json
│   └── ai.py                  # 可选 AI 追问（GLM HTTP 接口，requests 直调）
├── tools/
│   ├── extract_syllabus.py    # 官方 PDF → 提取文本（--save 存 data/raw/）
│   ├── build_outline.py       # 汇总 points/ → data/outline.json + 完整性校验
│   └── verify_points.py       # 内容审核辅助：抽取知识点清单供人工核对条号
├── data/
│   ├── raw/                   # ★ 官方原始资料区：只读、只增不删，见其 README.md
│   ├── outline.json           # 大纲树（脚本生成，勿手改）
│   └── points/                # 知识点 YAML，每章一个子目录：
│       ├── 01_导论/           # 文件名 = <id>_<标题>.yaml，如 dl-001_经济法概述.yaml
│       ├── 02_物权法/
│       ├── 03_招标投标法/
│       ├── 04_合同法/
│       ├── 05_票据法/
│       └── 06_知识产权法/
├── .progress.json             # 学习进度（运行时自动生成，可删除重置）
└── .zcode/skills/             # 项目技能（见 §8）
```

规则：
- `data/raw/` 内容永不修改；官方文件重命名必须同步更新其 README.md 登记表
- `data/outline.json` 只由 `tools/build_outline.py` 生成
- 知识点文件新增/修改后必须跑校验命令（见 §6）
- 不引入新依赖除非必要；当前依赖：streamlit、pyyaml、jieba、requests（后三者为 pdf/yaml/检索/接口）

## 4. 知识点数据 Schema（data/points/**/*.yaml）— v2

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
related: [wq-014, wq-016]   # 内部关联 id（应用不再单独展示；联动关系直接写进 why_written 分点）
```

字段硬性要求：
- `original` 引用法条必须注明法律名 + 条号（如《民法典》第三百九十四条）；法律名用简称（《民法典》《招标投标法》《票据法》《著作权法》《专利法》《商标法》）
- `original` 引用条文时条号一律用**中文数字**（与法条原文一致）；`why_written`/`name_origin`/`exam_tips`/`quiz.explain` 中的简注式条号（如"535条""（402）"）可用阿拉伯数字
- `why_written` 必须分点（markdown 列表），每点以加粗小标题开头；跨章节联动直接在分点里用文字写明（如"联动第四章违约责任的定金罚则"），不要只留 id
- `name_origin` 解释术语得名缘由（拆字、构词、字面即规则），不写立法沿革；原 background 已废止（v1.2），新旧法变化点如重要可并入 why_written 分点
- `quiz` 1~2 道单选，题干场景化，干扰项迷惑但明确错误，答案 A/B/C/D 均衡分布，解析点明规则
- 章前缀约定：`dl`=导论 `wq`=物权法 `zbtb`=招标投标法 `ht`=合同法 `pj`=票据法 `zscq`=知识产权法
- 序号章内连续（01, 02, …），插入新知识点用未占用号，不重排已有 id（id 是进度记录和 related 的锚）

正文排版规范（Markdown 渲染约束，v1.1 起）：
- **每段一行**：一个段落独占一行，段与段之间空一行；**不要在段内手动折行**——Markdown 会把单个换行渲染成空格，导致中文句子中间出现空格
- **引号一律中文引号**：“ ” ‘ ’；正文里不出现 ASCII 引号 " '（YAML 语法层面还要求标量值不能以 ASCII 引号开头）
- **行内不留多余空格**：中文字符与中文标点之间不要有空格
- **首行缩进由 app 渲染**（CSS text-indent 自动处理），YAML 里不要手写缩进；列表项不缩进
- 列表项每行一个（`- ` 或 `1. `），列表项的续行并入该行，不要单独成行
- 新增/修改内容后运行 `python tools/normalize_points.py` 兜底规范化（引号转换、空格清理、段落重构），再跑校验

## 5. 法条版本基准（写作时唯一依据）

| 法律 | 现行版本 | 生效/修正 |
|---|---|---|
| 《民法典》 | 2020-05-28 通过 | 2021-01-01 施行（物权编=第二编、合同编=第三编） |
| 《招标投标法》 | 2017 修正 | 原法 2000-01-01 施行 |
| 《招标投标法实施条例》 | 2019 修订 | 2012 施行 |
| 《票据法》 | 2004 修正 | 原法 1996-01-01 施行 |
| 《著作权法》 | 2020 修正 | 2021-06-01 施行 |
| 《专利法》 | 2020 修正 | 2021-06-01 施行 |
| 《商标法》 | 2019 修正 | 2019-11-01 施行 |

**条号零差错规则**：写入 `original` 前必须核对条号。记忆不确定时，宁可只写法律名+规则内容、不写条号，也不许编条号。审核用 `tools/verify_points.py` 抽取全部条号清单人工核对。

## 6. 工作流命令

```bash
# 正文规范化（新增/修改知识点后先跑：引号→中文引号、删中文间空格、段落重构）
python tools/normalize_points.py

# 校验全部知识点（id 唯一、必填字段、related 引用、章名与大纲一致）
python tools/verify_points.py

# 汇总生成大纲树（校验通过后执行）
python tools/build_outline.py

# 启动应用
python -m streamlit run app.py

# 官方 PDF 提取（新增资料时）
python tools/extract_syllabus.py "data/raw/<文件>.pdf" --save
```

校验不过 → 修复后重跑，禁止跳过校验生成 outline.json。

## 7. 环境与启动

- Python 3.12.16（pixi `ds` 环境，`python` 直用）
- 已装：streamlit 1.67.0 / pyyaml 6.0.3 / jieba 0.42.1 / requests 2.34.2（由用户 pixi 安装，勿重装勿换环境）
- 启动：`python -m streamlit run app.py`
- 项目在百度网盘同步盘内：`.progress.json`、`data/outline.json` 等小文件同步开销可忽略，不要在项目里放大体积缓存文件

## 8. Skill 与 MCP 登记

**项目 Skill（`.zcode/skills/`）**
- `exam-kp`：知识点写作规范技能——固化 §4 schema、§5 条号规则、校验流程，供后续新增/修订知识点时调用
- `streamlit-app`：**Streamlit 官方 agent skill**（从本机已装 streamlit 1.67.0 包内复制，Apache 2.0，来源见其 PROVENANCE.md）——开发/调试/美化 UI 时使用

**MCP 决策记录**
- 本项目为本地数据型应用（YAML + Streamlit），Bash/文件工具已覆盖全部操作，**现阶段不建 MCP**
- 未来触发条件（满足其一再建）：① 需要频繁调用外部法规数据库 API 做条号校验；② 需要把学习进度同步到外部系统；③ 出现多项目共享的专用工具链

## 9. 迭代日志（每次改动追加一条，新条目在最上）

### 2026-11-24 v1.9 图解交互定稿 + 界面精简 + 云端公开生效
- 图解最终方案：框内 st.image 适应宽度（大小图观感统一）+ 图下「新标签打开大图」链接（浏览器原生缩放看细节）。
  曾尝试 st.html 内嵌自写 pan/zoom JS 查看器，初始适配在沙箱 iframe 里不可靠，弃用
- 移除每页底部「问 AI」面板（core/ai.py 模块保留备用）；侧栏顶部加「🏠 首页」按钮；「数据依据」说明从侧栏移到首页
- 云端公开已生效：匿名浏览器实测首页完整渲染（curl 无 cookie 首跳 303 属正常，不代表未公开）
- 本地 cloudflared 临时隧道已停止（云端为唯一入口）；如需临时本地分享用 .tools-bin/cloudflared/启动分享.bat

### 2026-11-24 v1.8 图解改静态 PNG（用户反馈：不需要交互、加载慢）
- 交互版 HTML（0.9MB/张）→ archify export-svg → Chrome 无头 2x 截 PNG（60~304KB/张）
- 嵌入方式 st.iframe → st.image（@st.cache_data 读仓库字节），不依赖云端 /app/static 路由
  （该路由在应用未公开时会陷入登录 303 重定向死循环，表现为"图解里套了一个 Streamlit"）
- 仓库瘦身：static/diagrams 下 *.html/*.svg/*.json 只留本地（gitignore），云端仅 PNG
- st.image 用 width='stretch'（use_container_width 已弃用 2025-12-31 移除）

### 2026-11-23 v1.7 archify 交互式图解（4 张）
- 工具：archify skill 3.3 装于 ~/.zcode/skills/archify（全局仅留 ZCode 一份；CLI 需 TTY，用 PowerShell Start-Process 跑 finalize；输出 candidate 放 .archify/，已 gitignore）
- 四张图（static/diagrams/，archify validate/deliver/check/browser-check 全过）：
  knowledge-tree（tree，六章30节全景，首页）/ bidding-workflow（workflow 三泳道，zbtb-001）/ contract-lifecycle（lifecycle 合同一生，ht-001）/ note-sequence（票据流转追索，pj-001）
- 集成：st.iframe("/app/static/diagrams/xxx") 嵌入 expander（旧 st.components.v1.iframe 2026-06 移除）；DIAGRAMS 映射在 app.py
- archify 经验：workflow v1 同泳道相邻列节点固定列距 70px，宽节点必撞 column-capacity——跨泳道隔列排布、每格≤1节点；nodeIcon 仅白名单（calendar/clock/person/briefcase/flag/moon+组件语义图标）；长流程 meta.viewBox 调宽高比解决纵向 viewport-overflow；lifecycle schema_version=3

### 2026-11-23 v1.6 侧栏精简 + 缩进误伤修复（用户截图反馈）
- 移除侧栏搜索框（用户明确不需要；检索模块 core/search.py 保留，AI 追问仍用其分词）
- 修复首行缩进 2em 漏进列表/折叠框/按钮的问题：根因是 `div[data-testid="stMarkdownContainer"] p` 特异性（0,1,2）高于 `li p/summary p`（0,0,2），排除规则失效；改用 `li p, summary *, .stButton p, .stRadio p, .stCheckbox p { text-indent:0 !important }`
- 效果：列表圆点与文字、expander 箭头与标题、按钮文字与边框间距全部恢复正常；按钮文字在框内左对齐（padding 12px）
- sticky 笔记栏 top 从 1rem 调到 3.5rem，避开 Streamlit 顶栏遮挡；加 z-index:50 与背景色防滚动穿透

### 2026-11-23 v1.5 排版精修 + 字体自托管 + 单身份化（用户截图 6 条反馈）
- 顶部大空白收紧（block-container padding-top 1.6rem、stHeader 2.6rem）
- 倒计时从侧栏移除（首页 metric 已有）
- 删除「你是谁」多用户切换：用户与弟弟共用单身份「考生」（.notes.考生.json/.progress.考生.json），旧分身份文件已合并删除；弟弟云端直接点评即可
- 字体自托管：ZeoSeven CDN 按需切片下载到 static/fonts/（思源黑 24MB/482片、得意黑 1.5MB/26片、文楷 14MB/240片），经 `/app/static/` 提供（.streamlit/config.toml 开 enableStaticServing），`<link>` 引入；font-display swap→optional，彻底消除 CDN 慢导致的字形闪烁发虚
- 踩坑：①50万字符 CSS 内联 `<style>` 会被 Streamlit HTML 管线截断泄漏成页面文本，必须用 link；②h3-h6 不指定中文字体时回退 Source Sans→日文字体，中文显示成日文变体；③Streamlit 1.67 列容器 testid 是 stColumn 不是 column；sticky 需 align-self:flex-start、不能加 overflow
- 笔记栏 sticky 跟随滚动：`div[data-testid="stColumn"]:has(textarea){position:sticky;top:1rem;align-self:flex-start}`
- expander 箭头/列表圆点后的 2em 空隙修复：li p、summary p 排除 text-indent
- 侧栏按钮左对齐
- 注：自动化浏览器截图中 sticky 层标题出现过字形撕裂伪影（码点/字体/canvas 绘制均正常），真实 Chrome 不受影响，以用户浏览器为准

### 2026-11-23 v1.4 分享上线（Cloudflare 免费隧道 + 多用户隔离）
- 用户决定：不做 GitHub 仓库、不做云持久化——采用「本机运行 + cloudflared 快速隧道」分享链接
- 多用户隔离：侧栏「你是谁」选择（弟弟/MaxforCherubim/游客），笔记/进度按人分文件（.notes.<user>.json / .progress.<user>.json，widget key 含 user）；旧 .notes/.progress.json 已迁移至 MaxforCherubim 名下
- 部署：cloudflared 2026.11.1（.tools-bin/cloudflared/，GitHub 直连失败改用镜像源下载）→ 快速隧道 → 公网链接验证 200；端到端公网访问截图验证通过
- 一键重启脚本：.tools-bin/cloudflared/启动分享.bat（自动拉起 streamlit + 前台隧道，打印新链接）
- 运维要点：链接在电脑重启/隧道重开后会变化（重新分享即可）；电脑关机则链接失效；数据都在本地（弟弟笔记在 .notes.弟弟.json）
- 教训：改代码后同样必须重启 streamlit 服务（旧进程持有旧模块代码，公网验证时暴露 load() 签名不匹配报错）

### 2026-11-23 v1.3 中文字体方案 + 页脚署名
- 三种字体各司其职（ZeoSeven Fonts CDN，国内直连可用、unicode-range 切片按需加载、开源可商用）：
  正文=思源黑体（#69）/ 页面标题=得意黑（#92）/ 法条原文引用块=霞鹜文楷（#292，文书感）
- 实现：app.py `_INJECT_CSS` 注入 @import + font-family 规则；CDN 失效自动回退系统字体；字体文件不进仓库
- 踩坑记录：`.stApp div/span` 通配选择器会覆盖 Streamlit 的 Material Symbols 图标字体导致 expander 箭头乱码——只对明确文本容器设置 font-family（继承传播），不放通配
- 页脚署名（侧栏+首页）：「由 [MaxforCherubim](https://github.com/MaxforCherubim) 制作 · 基于 [Streamlit](https://streamlit.io) 构建」；首页「怎么用」文案同步为 v2 六件套学习流程
- 侧栏倒计时文案缩短避免换行

### 2026-11-23 v1.2 应试导向重构（用户 8 条反馈）
- UI：页眉简化（面包屑"物权法 › 担保物权制度"、去掉掌握/复习/返回按钮，状态按钮移至页尾）；法条原文折叠为 expander（默认收起，应试可跳过）；删除"相关知识点"按钮区（联动关系改为 why_written 末点文字说明）；新增右侧笔记栏（core/notes.py，.notes.json 自动保存，侧栏 📝 标记有笔记的知识点）
- 新增答题系统：每知识点 1~2 道场景化单选（quiz 字段，共 178 题），提交后 ✓/✗ 反馈+解析；AppTest 验证答对/答错双路径
- 内容 v2 迁移（89 文件全量）：why_written 散文→分点列表（末点跨章联动）；background→name_origin（术语得名缘由，纯历史沿革删除，重要修法热点并入 why_written）；重要新旧变化点保留在分点中
- 规范更新：§4 schema v2（六件套：原文/为什么分点/名词由来/案例/考点/练习题）；exam-kp skill 同步；verify_points 校验 name_origin+quiz 必填
- 修复：normalize restructure 重写为按空行分块+块内续行并入（修列表续行被块标量去缩进打断的问题）
- 验证：89 文件校验通过；浏览器截图确认（面包屑/分点/名词由来/笔记栏/底部按钮）；quiz 双路径 + 笔记自动保存 AppTest 验证
- 教训：Streamlit 运行中的进程 lru_cache 不随文件热更失效——改数据后必须重启服务或点侧栏"重新加载数据"

### 2026-11-23 v1.1 正文排版规范化（用户反馈修复）
- 问题：①正文段首无缩进；②中文句子中间出现空格（根因：YAML 段内手动折行，Markdown 把单个换行渲染成空格）；③正文大量使用 ASCII 引号（1598 处）
- 修复：新增 `tools/normalize_points.py`——引号全部转中文引号、删除中文间空格（516 处）、段落重构为"每段一行"；首行缩进用 CSS `text-indent: 2em` 注入实现（注：不能用全角空格字符——Streamlit 会 strip 整个 markdown 字符串开头的空白，段首缩进恰好落在字符串开头时失效）
- 规范固化：§4 新增正文排版规范五条 + 条号数字表述微调（original 用中文数字、简注可阿拉伯数字）；exam-kp skill 同步红线；新增/改内容后先跑 normalize 再 verify
- 验证：浏览器截图检查 ht-012 详情页，缩进/空格/引号三项全部确认修复

### 2026-11-22 v1.0 首个完整版本（89 个知识点全量上线）
- 内容：导论 7 + 物权法 19 + 招标投标法 13 + 合同法 19 + 票据法 14 + 知识产权法 17 = 89 个知识点，覆盖官方大纲经济法篇全部章节点
- 条号审核：物权法/合同法/票据法/知识产权法四章由生产代理对照权威全文逐字核对（维基文库民法典/票据法2004修正/专利法2020/商标法2019/著作权法2020）；招标投标法章对照最高法公报版全文修正 5 处（66条补"国家秘密"、23条"招标文件收受人"、代理机构规则归位14条2款/15条、48条"就分包项目负责"、履约保证金规则=60条非64条）；导论章核对反垄断法第一条（2022修正）与民法典 133/143/162/172 条
- 修正记录（生产代理对我初始锚点的纠错，后续勿再沿用）：民法典共有推定=308条、权利质权基金份额股权登记设立=443条、要约撤回475/撤销477、承诺迟到486/487、条件拟制159；票据法部分背书/附条件背书=33条、本票绝对记载=75条、支票绝对记载=84条、空头支票=87条、提示付款10日=91条、涉外票据定义=94条2款、17条时效无"1年"档（2年/6个月/6个月/3个月）、53条见票即付提示付款=1个月；专利法法定赔偿=3万-500万（71条）、优先权副本期限16/3个月（30条）、实审请求3年（35条）；著作权法2020重编号（合理使用=24条、报刊转载=35条2款、法定赔偿500元-500万=54条）
- 应用：AppTest 三页（首页/票据背书/国防知产）零异常；检索验证「抵押/串通投标/背书/第五百八十七条/居住权」命中准确
- 流程教训：YAML 标量值以英文引号开头会解析报错（4 个文件踩坑后修复，红线已写入 exam-kp skill）

### 2026-11-22 v0.1 项目初始化
- 下载并核验 4 份官方大纲 PDF → `data/raw/`（含来源登记）
- 确认经济法篇 6 章完整结构（《经济学》大纲为准）
- 搭建骨架：app.py + core/4 模块 + tools/3 脚本
- 创建 `exam-kp`、`streamlit-app` 两个项目 skill
