# bigdata-homework

《大数据与人工智能》课程作业仓库。

## 目录结构

```
bigdata-homework/
├── scripts/
│   ├── 01.py              # Python 作业（第一个程序）
│   └── 01.ipynb           # 同内容的 notebook，含已执行输出
├── learning-materials/
│   └── hdfs.html          # 概念学习资料：HDFS（大数据四件套之一）
├── python-4次学习地图.html  # 四次课学完 Python 的路线图
├── .workbuddy/skills/     # 【仓库级 Skill】随仓库走，克隆即可用
│   ├── git-push-flow/
│   └── concept-learner/
└── .gitignore
```

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

已生成：`learning-materials/hdfs.html`（HDFS）。计划中的四件套：**HDFS → MapReduce → Spark → NoSQL**，最后用目录页 `index.html` 串起概念之间的联系。

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
| `scripts/01.py` | **本人手写** | 第一行代码，非 AI 代写 |

Skill 的定位是「把可复用的方法固化下来」，不是替人完成作业——概念资料仍需本人在理解后修订。

## 提交记录

- `ffa0ad2` feat: submit homework 01 py and ipynb
