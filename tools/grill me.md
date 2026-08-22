---
tags:
  - 项目
  - Skill
  - Tool
created: 2026-07-24
updated: 2026-08-22
---


### grill-me简介

github链接： [mattpocock/skills: Skills for Real Engineers. Straight from my .agents directory.](https://github.com/mattpocock/skills)  


grill-me和grilling路径：  
```
mattpocock/skills/
└── skills/
    └── productivity/
        ├── grill-me/
        │   └── SKILL.md
        └── grilling/
            └── SKILL.md
```

`grill-me` 是用户手动调用的入口，文件内容很短，主要负责转入 `/grilling`。  
`grilling` 才是具体的追问逻辑，包括一次只问一个问题、提供推荐答案、先查代码再问事实等规则。  
`grill-with-docs` 可以理解为：

> `grill-me` 的追问访谈 + `domain-modeling` 的术语与决策沉淀。
> 比grill-me多了一个using the /domain-modeling skill

仓库里还有对应说明文档：

```
docs/productivity/grill-me.md
docs/productivity/grilling.md
docs/engineering/grill-with-docs.md
```

官方将它描述为一种会“留下书面轨迹”的 grilling：普通访谈结束后，理解可能随着会话消失；`grill-with-docs` 会把已经明确的词汇和重要决策保存到仓库。


### `grill-with-docs`和 `grill-me` 的核心区别

| 方面         | `grill-me` | `grill-with-docs` |
| ---------- | ---------- | ----------------- |
| 逐项追问       | 有          | 有                 |
| 每次只问一个问题   | 有          | 有                 |
| 提供推荐答案     | 有          | 有                 |
| 主动读取代码确认事实 | 有          | 有                 |
| 统一项目术语     | 只在对话中      | 写入 `CONTEXT.md`   |
| 记录重要决策     | 不记录        | 必要时创建 ADR         |
| 是否修改仓库     | 不修改        | 会修改文档             |
| 是否有持久状态    | 无状态        | 有状态               |

### grill skill翻译


> name: grilling
> description: 对用户的计划、决策或想法进行持续深入的压力测试。当用户希望审视自己的方案，或使用 grill、盘问我、挑战这个方案等触发语时使用。

围绕当前计划、决策或想法，对我进行持续而深入的访谈，直到我们对目标、约束、取舍和实施方式形成共同理解。

把方案视为一棵决策树，按照决策之间的依赖关系逐层深入。优先解决上游决策，再讨论依赖于它的下游分支，确保每一条重要分支都被明确处理。

每次只提出一个问题，并等待我的回答后再继续。不要一次列出多个问题，以免破坏决策之间的顺序并增加理解负担。

提出每个问题时，同时给出你推荐的答案及其理由，让我可以对一个具体方案进行确认、修改或否定，而不是从空白开始作答。

对于可以通过读取代码、文件、配置或调用工具确认的客观事实，应主动调查，不要向我询问。对于涉及目标、优先级、风险接受程度和方案取舍的决策，则必须交由我确认。

在我明确确认双方已经达成共同理解之前，不要开始修改文件、编写代码或执行计划。