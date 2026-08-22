---
tags:
  - Agent
  - Skill
  - Vibe-Coding
created: 2026-08-22
updated: 2026-08-22
---

## ponytail简介

github链接： **[ponytail](https://github.com/DietrichGebert/ponytail)**

它是干什么的？  
**Ponytail 是一套给 AI 编程 Agent 使用的“反过度设计”插件/Skill。**
它会把 Claude Code、Codex、OpenCode、Qoder 等 Agent 调整成一种所谓的 **“懒惰高级工程师模式”**：

> 在保证正确、安全和可维护的前提下，尽量不写代码、少写代码、复用现有代码，不为了“看起来专业”而增加抽象层、依赖和脚手架。

所以它不是一个业务项目，也不是传统的代码压缩或代码格式化工具。它主要是在 **AI 开始写代码之前和写代码过程中，约束 Agent 的决策方式**。

强调最短的正确实现，而不是单纯最短的代码。

Ponytail（马尾辫）在 GitHub 已经有 106k Stars，旨在让 Agent 用更少的代码完成功能开发，官方宣传语：

> You know him. Long ponytail. Oval glasses. Has been at the company longer than the version control. You show him fifty lines; he looks at them, says nothing, and replaces them with one. Ponytail puts him inside your AI agent.
> 
> 你认识他。长长的马尾辫。椭圆形眼镜。在公司待的时间比版本控制系统的历史还长。你给他看五十行代码；他看了看，什么也没说，然后把它们替换成一行。Ponytail 把他放进了你的 AI Agent 里

## 具体介绍
### 核心规则

和其它 Skill 一样，核心规则位于 SKILL.md 中。

它的触发描述词写的比较长，并且要求**任何**编码任务都触发，也明确说明了不适用的任务范围。

正文首先是一个身份说明：

> You are a lazy senior developer. Lazy means efficient, not careless. You have seen every over-engineered codebase and been paged at 3am for one. The best code is the code never written.
> 
> 你是一位懒惰的高级开发人员。懒惰指的是效率高，而不是粗心大意。你见过各种过度设计的代码库，甚至凌晨三点还被叫去处理过。最好的代码就是从未写过的代码。


然后是和 Caveman Skill 一样的持续触发激活——要求**所有回复都激活**（ACTIVE EVERY RESPONSE.），它也支持强度选择，一共有 lite、full、ultra 三档，默认是 full。

接下来是核心的 7 条规则，它们是阶梯（ladder）式渐进的：

1. **Does this need to exist at all?** Speculative need = skip it, say so in one line. (YAGNI)
2. **Already in this codebase?** A helper, util, type, or pattern that already lives here → reuse it. Look before you write; re-implementing what's a few files over is the most common slop.
3. **Stdlib does it?** Use it.
4. **Native platform feature covers it?** over a picker lib, CSS over JS, DB constraint over app code.
5. **Already-installed dependency solves it?** Use it. Never add a new one for what a few lines can do.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

简略一点说，即先判断需求是否真的成立（YAGNI: You aren't gonna need it），然后依次在代码库、标准库、原生平台、已安装依赖寻找可复用的能力，最后才考虑写新的功能代码，并且能一行搞定就只写一行（lazy）。

七条规则之后，补充说明应该优先阅读代码和任务要求理解问题，之后再考虑如何使用最少的代码实现。也专门指出了「Bug 修复 = 根本原因，而非症状。」，要求找出根本原因并修复它，而不是只修复报告中提及的路径。

还有一些其他的rules，比如：
- 删除比添加更重要。枯燥比巧妙更重要，巧妙的东西是凌晨三点才能看懂的。
- 两个标准库选项大小相同？选择在边界情况下正确的那个。偷懒意味着编写更少的代码，而不是选择更脆弱的算法。

### 支持三个强度

| 模式      | 行为                          |
| ------- | --------------------------- |
| `lite`  | 正常完成需求，但提醒你还有更简单的方案         |
| `full`  | 默认模式，严格执行“复用→标准库→原生能力→最小实现” |
| `ultra` | 极端 YAGNI，优先删除和拒绝不必要需求       |
Example: "Add a cache for these API responses."
- lite: "Done, cache added. FYI: functools.lru_cache covers this in one line if you'd rather not own a cache class."
- full: "@lru_cache(maxsize=1000) on the fetch function. Skipped custom cache class, add when lru_cache measurably falls short."
- ultra: "No cache until a profiler says so. When it does: @lru_cache. A hand-rolled TTL cache class is a bug farm with a hit rate."


### 配套 Skill

仓库不只有一个提示词，还提供了一组配套能力：

- `ponytail-review`：审查一次改动中存在的过度设计。
- `ponytail-audit`：扫描整个仓库，列出可以删除或简化的部分。
- `ponytail-debt`：收集代码里的 `ponytail:` 简化标记，形成技术债清单。
- `ponytail-gain`：统计减少了多少代码、成本和时间。
- `ponytail-help`：展示使用帮助。

### 不适用情况

一共四类：
- 信任边界处的输入验证、防止数据丢失的错误处理、安全措施、基本可访问性，以及任何用户明确要求的功能。
- 硬件永远无法在纸面上达到理想状态，保留校准旋钮，而不仅仅是减少代码，物理世界需要调整，而最少代码无法做到这一点。
- 不能为了最小 diff 而跳过问题理解与全链路追踪，必须先完整阅读并理解问题，再考虑能否简短实现。
- 不允许省略需要的测试，但是测试代码也应该遵循上述 YAGNI 原则。

最后是边界，指出该 Skill 不约束 Agent 如何说话，但是也指出可和 Caveman Skill 一起使用达到这个效果。

### Hooks

该 Skill 在 Codex 和 Claude 环境下的 Hook 一样，共三个 Hook，触发条件和功能分别为：

SessionStart 触发 ponytail-activate.js，将 Skill 强度写入标志文件，将 Ponytail 规则集作为隐藏的 SessionStart 上下文发出。在 Claude Code 环境还会检测状态行配置缺失并发出设置提示。

SubagentStart 触发 ponytail-subagent.js，当 Ponytail 模式激活时，将相同的规则集注入到每个子 Agent 中，并支持使用正则筛选影响的子 Agent 类型。

UserPromptSubmit 触发 ponytail-mode-tracker.js，跟踪当前激活的 Ponytail 模式，并检查用户输入的 /ponytail 命令，将模式写入标志文件。

这三个 Hook 都注意静默捕获异常和有限等待，避免阻塞对话。此外，它们还依赖 Skill 内的其它模块，例如提供指令的 ponytail-instructions.js 等。

## 总结

最近应该也都刷到过这个形容：
```
gpt 5.6最让我受不了的就是：  
我让它做一盘番茄炒蛋，它往里还加了东坡肉。我说有必要加东坡肉吗?它说你说得对，然后把东坡肉去掉。  
我说好，你提PR吧。再一看，它PR写着「番茄炒蛋（无东坡肉）」并且注释里会写一大堆为什么本道菜不需要加东坡肉。
```

就是模型虽然厉害了，但总会添油加醋，过度修改一些东西，但实际上完全没必要。

Ponytail SKILL.md 的末尾有一句话，我认为可以视作该 Skill 的设计理念：

> The shortest path to done is the right path.
> 通往成功的最短路径就是正确的路径。

不过感觉说的有点绝对了，有时候可能不太好。

所以如果感觉ai总在过度修改代码，可以试一下这个，Ponytail 就是用来约束 Agent 的代码修改的。