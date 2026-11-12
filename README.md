# bigdata-homework

《大数据与人工智能》课程作业仓库。

## 目录结构

```
bigdata-homework/
├── scripts/
│   ├── 01.py              # Python 作业（第一个程序）
│   ├── 01.ipynb           # 同内容的 notebook，含已执行输出
│   ├── 06_类别变量清洗.py       # 类别变量作业：清洗 → 归一 → 归大类 → 编码
│   ├── 07_父母职业关联分析.py   # 列联表 → 卡方 → 置换检验 → 残差分解
│   ├── _check.py              # 结果一致性校验（7 项）
│   └── _verify_chi2.py        # 用 scipy 独立复核手写的卡方计算
├── data/
│   └── 类别变量练习数据.csv    # 原始数据（53 行 × 2 列，GB18030 编码）
├── output/                    # 分析产出（8 个 CSV，含编码后数据与检验结果）
├── 对话.md                    # 本次作业的 AI 对话记录（含被推翻的错误结论）
├── learning-materials/
│   ├── hdfs.html             # 概念学习资料：HDFS（大数据四件套之一）
│   ├── mapreduce.html        # 概念学习资料：MapReduce（大数据四件套之二，含 Streaming 实跑）
│   ├── python-运算符.html     # Python 语法地基：七类运算符
│   ├── python-变量类型.html   # Python 语法地基：八种常用类型 + 可变/不可变
│   └── python-流程控制.html   # Python 语法地基：分支 / 循环 / 跳转
├── python-4次学习地图.html  # 四次课学完 Python 的路线图
├── .workbuddy/skills/     # 【仓库级 Skill】随仓库走，克隆即可用
│   ├── git-push-flow/
│   └── concept-learner/
└── .gitignore
```

## 作业：类别变量的清理、转化与关联分析

针对「父母工作单位」这份自由文本数据（53 行 × 2 列）做的一次完整处理，两轮需求：先清理转化，再分析父母职业之间是否存在关联。

### 数据本身的问题

原文件是 GB18030 编码（不是 UTF-8），第 7 行两个单元格内嵌换行符，第 36 行有尾随空格，第 16 行母亲工作为空。更麻烦的是**类别爆炸**：53 行数据里父亲有 48 种不同写法、母亲 43 种，等于每行一个新类别，直接 one-hot 会得到 96 列稀疏矩阵。

### 处理流程

1. **清洗**：编码识别 → 去内嵌换行 → 去首尾空格 → 空串转缺失 → 别名归一（`公安局`→`市公安局`、`个体`→`个体经营`）
2. **归类**：把单位名称按性质归到 8 类——党政机关 / 事业单位 / 国有企业 / 金融保险 / 私营企业 / 个体经营 / 家庭·未就业 / 其他。「家庭主妇」「无」「家庭父母」作为有效信息归「家庭/未就业」，真空白单独标「未填写」，不混在一起。
3. **编码**：序号编码（0–7，缺失留空）+ 独热编码（18 列）
4. **关联分析**：列联表 + 卡方独立性检验 + Cramér's V + 置换检验（20000 次），再做调整标准化残差分解

归类靠**有序关键词规则 + 白名单**，不是逐条猜。规则顺序有两个必须注意的点，写在脚本注释里：国企规则要排在党政机关之前（否则「水利水电第三工程局」被「局$」吃掉），个体店铺规则要排在学校之前（否则「第十一中学北侧校园书店」被判成学校）。

### 主要结论

父母单位性质存在统计显著的关联：

| 分析 | n | χ² | df | 渐近 p | 置换 p | Cramér's V |
|---|---|---|---|---|---|---|
| 8 类完整表 | 52 | 56.403 | 35 | 0.0124 | 0.0182 | 0.466 |
| 合并 3 类表 | 51 | 18.048 | 4 | 0.0012 | 0.0004 | 0.421 |

父母同类比例 60.8%，独立时期望仅 39.4%。关联集中在两个极端：「双体制内」偏多（21 户 vs 期望 14.3），「体制外男方 + 家务女方」也偏多（8 户 vs 期望 4.7）。父亲在体制内时母亲不就业率 7.1%，父亲在体制外时 40.0%（OR=8.67，Fisher p=0.010）。

**局限**：n=52 小样本、非随机抽样（父亲党政机关占 40%，高度偏向体制内），8 类表有 98% 的格子期望频数小于 5。所以结论只是样本内的描述性关联，不作因果解释。

### 运行方式

```bash
python scripts/06_类别变量清洗.py      # 清洗 + 归类 + 编码 → output/
python scripts/07_父母职业关联分析.py  # 列联表 + 卡方 + 置换检验 → output/
python scripts/_check.py               # 7 项一致性校验
python scripts/_verify_chi2.py         # 用 scipy 复核卡方计算
```

四个脚本都能独立运行，`_check.py` 与 `_verify_chi2.py` 是自检工具，改归类规则后建议重跑。

### 过程记录

`对话.md` 记录了完整对话过程，包括**五次被推翻的错误判断**——空行让 p 值从 0.0124 变成 0.218、校验脚本口径错把「清洗生效」报成「数据丢失」、把「都不就业」说成「夫妻共同经营」等。这些比最终结论更有参考价值。

## 仓库级 Skill

两个 Skill 放在 `.workbuddy/skills/` 下，属于**项目级（随仓库提交）**，任何打开本仓库的 WorkBuddy 会话都会自动识别。

### 1. git-push-flow —— 本地仓库推送全流程

覆盖「检查状态 → 暂存 → 提交 → 推送 → 验证同步」的完整 Git 流程，内置弱网判定与重试策略。

调用方式（直接说人话即可触发）：

> 提交推送 / push 到 GitHub / 同步到远程仓库 / 走一遍 git 流程

核心规则（血泪经验）：**推送是否成功只看远程 SHA 是否等于本地 SHA，绝不看命令退出码**——本机网络下 push 常常超时（exit 124）但 refs 其实已写入远程。配套脚本 `scripts/verify_push.sh` 用于自动比对。

### 2. concept-learner —— 概念学习资料生成器

给一个概念名，按固定流程检索官方来源，生成结构化、可核查、自包含的 HTML 学习资料（八个板块：学习目标 / 核心问题 / 通俗解释 / 核心机制 / 应用场景 / 概念辨析 / 自测问题 / 参考来源）。

调用方式：

> 用 concept-learner 学习「MapReduce」 / 生成「Spark」的概念学习资料

已生成：`learning-materials/hdfs.html`（HDFS）、`learning-materials/mapreduce.html`（MapReduce）。计划中的四件套：**HDFS → MapReduce → Spark → NoSQL**，最后用目录页 `index.html` 串起概念之间的联系。

## 开发环境

- Python 3.12.10（`C:\Users\lxy20\AppData\Local\Programs\Python\Python312\`）
- pip 已配置清华 TUNA 国内源（用户级 `pip.ini`）
- Jupyter：内核 `Python 3.12.10` 已注册，VS Code 选该内核即可运行 notebook

## AI 使用情况说明

本仓库以下内容由 WorkBuddy（AI 助手）协助生成，均已人工审阅：

| 内容 | AI 角色 | 人工核查 |
|---|---|---|
| `git-push-flow` Skill | 根据本机真实踩坑记录生成骨架与规则，并持续迭代 | 全部流程在真实仓库实测过；验证脚本输出 SYNCED |
| `concept-learner` Skill | 生成流程框架与八板块结构 | 逐条执行过一次（HDFS），结构可用 |
| `learning-materials/hdfs.html` | 起草正文与可视化图 | **所有参考来源链接逐条 curl 验证返回 200**，访问日期标注在文内 |
| `python-4次学习地图.html` | 起草编排与练习设计 | 已按四次课的课时约束复核 |
| `learning-materials/python-运算符.html` | 起草正文、优先级表与易混辨析 | 待本人复核（第 1 次课配套） |
| `learning-materials/python-变量类型.html` | 起草正文、类型地图与练习 | **所有代码示例在本地 Python 3.13 实跑，输出逐条核对**；**4 条 python.org 来源 curl 验证 200**（访问日期 2026-10-10）；正文待本人复核 |
| `learning-materials/python-流程控制.html` | 起草正文、执行路线图与练习答案 | **13 组代码示例 + 5 道练习答案在本地 Python 3.13.14 实跑**，输出取自真实运行结果；**5 条 python.org 来源 curl 验证 200**（访问日期 2026-10-15）；正文待本人复核 |
| `learning-materials/mapreduce.html` | 起草正文、两张数据流图与练习答案 | **4 条 hadoop.apache.org 官方来源 curl 验证 200**（访问日期 2026-10-18）；**全部代码在本地 Python 3.13.12 实跑**，输出取自真实运行结果（词频统计 13→5 个键值对、Combiner 前后一致 True、平均值反例 4.0 vs 4.5、Streaming mapper/reducer 管道）；HTML 标签闭合与 2 张内联 SVG 的 XML 合法性已用解析器自检通过；**正文待本人复核**（原始论文链接因本机无法访问 research.google / usenix.org 未列入来源表） |
| `scripts/06_类别变量清洗.py` | 起草清洗流程、8 类归类体系与关键词规则、编码实现 | **7 项一致性校验全部通过**（`_check.py`：无残留脏字符、编码与类别一一对应、独热每行唯一 1、原值无丢失、逐行对齐）；**53 行归类结果待本人逐条复核** |
| `scripts/07_父母职业关联分析.py` | 起草列联表、卡方检验、Cramér's V、置换检验、残差分解 | **卡方值与 p 值经 scipy 独立复算一致**（差 1.8e-16）；置换检验 20000 次；**「体制内联姻」等解释性结论待本人复核** |
| `scripts/_check.py`、`_verify_chi2.py` | 编写两个自检工具 | 曾因比对口径错误把「清洗生效」误报成「数据丢失」，已修正（见 `对话.md` 第五节） |
| `data/类别变量练习数据.csv` | **非 AI 生成**，课程练习数据 | 原始数据，仅做格式转换后入库 |
| `output/*.csv` | 由上述脚本运行生成 | 重跑脚本可完全复现，未手工修改 |
| `对话.md` | 依据本次会话整理，含对 AI 自身五处错误的记录 | **待本人复核** |
| `scripts/01.py` | **本人手写** | 第一行代码，非 AI 代写 |

Skill 的定位是「把可复用的方法固化下来」，不是替人完成作业——概念资料仍需本人在理解后修订。

## 提交记录

- `62f0d8b` feat: 类别变量清理、编码与父母职业关联分析
- `ffa0ad2` feat: submit homework 01 py and ipynb
- `d87caed` chore: add project-level skills (git-push-flow, concept-learner)
- `72dbfa5` docs: add README, python learning roadmap and hdfs concept material
- `541a67e` docs(git-push-flow): add file-tree verification and second-round push experience
- `264b251` feat: add Python operator material and homework 02 scripts
- `c55869c` docs: add python variable types material and sync README
- `7b2c51a` docs(concept-learner): record lightweight form for syntax topics
