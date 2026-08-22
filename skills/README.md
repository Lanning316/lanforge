# Skills

[返回仓库总览](../README.md)

## 📌 目录定位

这里存放可直接复用的 Agent Skills，也是 Lanforge 当前的核心内容。

一个 Prompt 如果逐渐演化出明确的**触发条件、工作流程、使用边界、Reference 和 Scripts**，就可以进一步整理成 Skill。每个 Skill 的具体行为以其目录中的 `SKILL.md` 为准；README 用于提供人类可读的定位、索引和使用入口。

## 🧩 Skills 索引

### [`constellate`](./constellate/README.md)

面向 Markdown / Obsidian 笔记库的个人知识管理 Skill。

将分散笔记重新组织为内容完整、可追溯、语义互联的 Wiki，支持知识重组、查询、Lint、关系维护以及 Schema 演化。

入口：[`SKILL.md`](./constellate/SKILL.md) · [详细 README](./constellate/README.md)

### [`find-hide`](./find-hide/SKILL.md)

当思考、开发或排错陷入瓶颈时，寻找：

> **当前问题背后那个尚未提出、但可能更加关键的问题。**

强调讲清楚因果机制，而不是为了显得深刻而堆砌抽象层级。适合反复尝试仍没有进展、怀疑自己可能一直在错误搜索空间中解决问题的场景。

### [`karpathy-guidelines`](./karpathy-guidelines/SKILL.md)

面向 AI Coding 的工程行为约束。

核心思想包括：

- Think Before Coding
- Simplicity First
- Surgical Changes
- 明确假设和不确定性
- 避免无关重构
- 用可验证的结果判断任务是否真正完成

目标是减少 AI Coding 中常见的过度设计、擅自扩展需求和大范围修改问题。

### [`project-tutor-for-intern`](./project-tutor-for-intern/README.md)

面向实习生、新人以及刚接手陌生项目开发者的交互式项目导师，帮助理解项目定位、整体架构、业务流程、代码调用链、模块职责、阅读顺序以及修改影响。

入口：[`SKILL.md`](./project-tutor-for-intern/SKILL.md) · [详细 README](./project-tutor-for-intern/README.md)

### [`writing-tutorials`](./writing-tutorials/README.md)

面向现有代码库生成深度技术教程。它更关注生成可以真正保存进项目中的 Markdown 教程，例如：

```text
docs/learn/<topic>/<topic>.md
```

教程可以包含源码证据、主流程、模块职责、设计决策、常见问题，并可按需结合 Git 历史解释模块的演进过程。

入口：[`SKILL.md`](./writing-tutorials/SKILL.md) · [详细 README](./writing-tutorials/README.md)

### [`writing-for-agents`](./writing-for-agents/SKILL.md)

用于编写**给 Agent 阅读的文档**，适用于 Skills、`AGENTS.md`、`CLAUDE.md`、Agent Workflow 以及 Agent 会进一步读取的 Reference 文档。

重点关注 Context Pointer、Progressive Disclosure、Information Hierarchy、Completion Criteria 等概念，让 Agent 更稳定地按照预期流程执行。

### [`writing-great-skills`](./writing-great-skills/SKILL.md)

关于如何设计高质量 Agent Skill 的参考指南。

它把一个好 Skill 的核心目标定义为：

> **不是让 Agent 每次产生相同输出，而是让 Agent 每次采用可预测的过程。**

重点讨论 Skill 的触发方式、Context Load、Cognitive Load、Progressive Disclosure、Skill Granularity、Completion Criteria，以及如何控制 Skill 长度和复杂度。

## 🚀 如何使用

进入对应 Skill 目录，先阅读其中的 `SKILL.md`，再根据需要查看 `references/`、`scripts/`、`assets/` 或其他辅助文件。

不同 Agent / Coding 工具对 Skills 的安装方式不同，可以根据对应工具的 Skill 机制进行安装或引用。

## 🗂️ 目录结构

```text
skills/
├── README.md
├── constellate/
├── find-hide/
├── karpathy-guidelines/
├── project-tutor-for-intern/
├── writing-for-agents/
├── writing-great-skills/
└── writing-tutorials/
```

