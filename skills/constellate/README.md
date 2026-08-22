# Constellate

[返回 Skills 索引](../README.md) · [返回仓库总览](../../README.md)

Constellate 是一个面向个人 Markdown / Obsidian 笔记库的 Codex Skill。它把散落的原始笔记重组为**内容完整、来源可追溯、语义互联**的百科式 Wiki，并支持持续查询、检查和演化。

它不是简单的笔记分类器或自动摘要器。Constellate 采用“文章优先”的方法：先让每个页面能够独立回答一个知识问题，再用有类型的语义关系把页面连接成知识图谱。

## Skill 介绍

Constellate 适合以下任务：

- 初始化个人知识库的 `wiki/` 结构；
- 将指定原始笔记重组为知识文章，而不是逐篇机械摘要；
- 区分概念、可检验主张、知识领域、跨来源综合和必要的来源摘要；
- 记录来源、证据状态、矛盾、不确定性和知识演化过程；
- 沿有方向、有类型的语义关系查询和综合知识；
- 检查页面结构、内容充分性、来源路径、链接、索引和知识图谱；
- 安全迁移旧版 `sources` 相对路径格式；
- 基于真实案例讨论并执行经过批准的 schema 演化。

Constellate 不适合只修改一篇 Markdown 的排版、标题或通用 frontmatter；这些工作不需要启用本 Skill。

### 知识页面类型

| 类型 | 目录 | 用途 |
| --- | --- | --- |
| `concept` | `wiki/concepts/` | 定义概念、说明边界与适用语境 |
| `claim` | `wiki/claims/` | 表达可讨论、可验证或可被反驳的主张 |
| `domain` | `wiki/domains/` | 组织一个知识领域的问题、页面与缺口 |
| `synthesis` | `wiki/syntheses/` | 综合多个来源或页面，形成新的理解 |
| `summary` | `wiki/summaries/` | 为确有必要的复杂来源提供独立摘要 |
| `ingest` | `wiki/ingests/` | 记录一次导入的方案、决策、输出与限制 |

页面之间可以使用 `supports`、`challenges`、`depends-on`、`qualifies`、`part-of`、`synthesizes` 等关系。关系必须有内容依据；图谱密度不是目标，真实、可解释和可追溯才是。

## 核心原则

- **只写 Wiki：** 默认只在目标 Vault 的 `wiki/` 中写入，`wiki/` 外的原始笔记保持只读。
- **先确认再写入：** 默认先分析并展示方案，用户确认后才落盘；`--apply` 只跳过普通新增与更新的二次确认。
- **默认离线：** 只使用本地内容。只有明确使用 `--web` 或在本轮授权后才联网，且不会把私人原文放入搜索查询。
- **来源可跳转：** 正式本地来源必须位于 Vault 内，并在 `sources` 中保存为带引号的 Obsidian Wiki 链接。
- **取消即零写入：** 方案被取消或否决时，不创建记录、不更新索引，也不修改文件。
- **高影响操作单独确认：** schema 变更、删除、合并、迁移和来源修改不会被 `--apply` 自动授权。

## 安装

### 前置条件

- 支持 Skills 的 Codex 环境；
- Python 3（用于初始化、lint、迁移和测试脚本）；
- 一个 Markdown 或 Obsidian Vault。

### 安装 Skill

将本仓库完整复制或克隆到 Codex 的 Skills 目录，并确保最终路径中的入口文件为：

```text
<CODEX_HOME>/skills/constellate/SKILL.md
```

例如，在默认配置下通常对应：

```text
~/.codex/skills/constellate/SKILL.md
```

安装后重新加载 Codex。可以通过直接提到 `$constellate`、使用 `/constellate` 命令，或描述符合本 Skill 的知识库任务来调用它。

> 请保留 `assets/`、`references/`、`scripts/` 和 `agents/`；Skill 会相对于 `SKILL.md` 查找这些资源。

## 使用指南

Constellate 支持自然语言，也支持显式命令。显式命令的一般形式如下：

```text
/constellate --init [Vault 路径]
/constellate --ingest 路径一 [路径二 ...]
/constellate --query 问题
/constellate --lint [wiki 内范围]
/constellate --schema 变更意图
```

路径相对于 Vault 根目录解析。一次请求只使用一个主操作。

### 1. 初始化 Wiki

```text
/constellate --init D:/Notes/MyVault
```

Skill 会先展示拟创建的目录和基础文件。确认后，它以非覆盖方式创建：

```text
wiki/
├── schema.md
├── index.md
├── log.md
├── concepts/
├── claims/
├── domains/
├── syntheses/
├── summaries/
└── ingests/
```

如果 `wiki/` 已经存在，Skill 会先报告兼容性和缺失项，不会覆盖已有文件。

### 2. 导入并重组笔记

```text
/constellate --ingest notes/认知负荷.md notes/间隔学习.md
```

也可以直接用自然语言：

```text
使用 $constellate，把 research/学习方法/ 下的笔记整理进 Wiki。
```

典型流程是：

1. 读取指定来源，并在必要时读取少量明显相关的本地笔记；
2. 提取概念、主张、论证、证据、限制和候选关系；
3. 提交一次完整的建页与更新方案；
4. 获得确认后写入知识页、ingest、索引和日志；
5. 运行 lint，核对实际输出与获批方案。

如果希望普通新增和更新在分析后直接写入，可以添加 `--apply`：

```text
/constellate --ingest notes/学习系统.md --apply
```

`--apply` 不授权删除、合并、schema 变更、批量迁移或修改原始来源。

### 3. 查询知识库

```text
/constellate --query 间隔学习为什么能降低遗忘？
```

查询会从索引和文本命中定位相关页面，再沿语义关系扩展，并在需要时回到原始笔记核对证据。回答会区分来源内容、用户观点与 Agent 综合。查询默认不会写回 Wiki。

### 4. 检查 Wiki

```text
/constellate --lint
/constellate --lint claims
```

Lint 包含两层：

- 确定性检查：schema、frontmatter、必需章节、来源格式、链接、索引和关系格式等；
- 语义审查：页面是否独立可读、证据是否支持主张、关系是否准确、是否存在重复节点、矛盾或内容缺口等。

默认只报告问题和修复计划。添加 `--apply` 也只会执行普通新增或更新，高影响改动仍需单独确认。

### 5. 演化 Schema

```text
/constellate --schema 为 claim 增加置信度字段
```

Skill 会先用真实案例说明现有 schema 的不足，并列出规则、影响范围、迁移、回退和验证方法。批准 schema 变更与批准旧页面迁移是两个独立步骤。

### 可选参数

| 参数 | 含义 |
| --- | --- |
| `--apply` | 允许普通新增和更新在方案分析后直接落盘 |
| `--web` | 授权本轮联网；外部来源优先选择原始、官方或学术材料 |
| `--offline` | 明确禁止本轮联网，不能与 `--web` 同时使用 |

## 维护与脚本

通常应让 Codex 按 Skill 工作流调用脚本。开发、排错或自动化检查时，也可以直接运行：

```bash
# 非覆盖初始化；Vault 默认为当前目录
python scripts/init_wiki.py <vault>

# 检查整个 Wiki 或指定范围
python scripts/lint_wiki.py <vault>
python scripts/lint_wiki.py <vault> --scope claims

# 预览旧版 sources 格式迁移；确认后才添加 --apply
python scripts/migrate_sources.py <vault>
python scripts/migrate_sources.py <vault> --apply

# 运行脚本回归测试
python scripts/test_scripts.py
```

三个工具均支持 `--json`，便于 Agent 或其他自动化程序解析结果。初始化工具还支持 `--add-missing` 和 `--only`，迁移与 lint 工具支持 `--scope`。

## 项目结构

```text
constellate/
├── SKILL.md                 # Skill 入口、边界与执行规则
├── agents/openai.yaml       # Codex 展示与默认提示配置
├── assets/wiki/             # Wiki 基础文件和页面模板
├── references/
│   ├── workflows.md         # 各主操作的完整工作流
│   ├── knowledge-model.md   # 知识类型、证据与关系模型
│   └── schema-reference.md  # Schema 与内容契约参考
└── scripts/
    ├── init_wiki.py         # 非覆盖初始化
    ├── lint_wiki.py         # 确定性检查
    ├── migrate_sources.py   # 旧版来源格式迁移
    └── test_scripts.py      # 回归测试
```

更完整的安全边界和行为规范见 [`SKILL.md`](SKILL.md)，各操作的详细步骤见 [`references/workflows.md`](references/workflows.md)。
