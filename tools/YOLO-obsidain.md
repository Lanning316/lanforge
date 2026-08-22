---
tags:
  - Obsidian
  - Agent
  - Tool
created: 2026-08-17
updated: 2026-08-17
---
## 简介

Agent-native AI assistant for Obsidian — 对话、写作、知识库、编排，一站式搞定。

支持工具调用、MCP、Skills、桌面 Bash、Subagent、联网搜索、长上下文记忆等。也就是说 Agent 不只是“读取你的笔记回答问题”，而是可以**实际操作你的 Vault、调用外部工具、执行任务**。


### ## Features

完整的 Agent 体验｜在 OB 内使用 Codex/Claude Code  
不止回答问题。YOLO 能理解并操作你的 Vault，调用工具与 MCP，并通过 Skills 按你的方式完成任务。桌面端还能一键切到你已登录的 Claude Code 或 Codex，让它们直接在 Vault 里工作。（已配置）  
YOLO 有两套 AI 执行体系：YOLO 自己的 Agent Runtime，以及 Claude Code / Codex 等 CLI Runtime。前者由你在插件里配置模型、Tools、Skills、MCP、RAG；后者是把你电脑上已经能运行的 Codex / Claude Code 接进 Obsidian。

YOLO 保留了很多 Smart Composer 那类功能，包括 Quick Ask、Cursor Chat、Tab Completion、Smart Space。

例如选中一段文字之后，可以直接让 AI 修改；写 Markdown 时可以实时 Tab 补全；编辑器里输入 `@` 就能快速提问，不必一直切到聊天窗口。

除了上述核心能力，YOLO 还提供：

| 特性                        | 说明                                                                            |
| ------------------------- | ----------------------------------------------------------------------------- |
| 🖥️ CLI Agent（桌面端）        | 复用本机已登录的 Claude Code / Codex，直接在 Obsidian 里和 CLI Agent 对话                     |
| 🔌 外部 Agent 支持            | 通过 MCP，让 Hermes、OpenClaw 等外部 Agent 使用 YOLO 的 Vault 搜索，或派遣已配置的 YOLO Agent 执行任务 |
| ⚡ Quick Ask 与 Smart Space | 无需离开编辑器即可提问、修改和续写内容                                                           |
| 🔎 Vault RAG              | 检索整个 Vault，让回答建立在你自己的笔记之上                                                     |
| 多窗口对话                     | 在独立对话窗口中并行处理不同任务与上下文                                                          |
| 🧠 记忆系统                   | 让 YOLO 记住你的偏好、习惯与长期上下文，让连续对话更稳定、更懂你                                           |
| Cursor Chat               | 一键添加上下文，触手可得的对话体验                                                             |
| ⌨️ Tab 补全                 | 实时 AI 智能补全，让写作更加流畅自然                                                          |
| 🎛️ 多模型支持                 | OpenAI、Claude、Gemini、DeepSeek 等主流模型，自由切换                                      |
| 🌍 i18n 国际化               | 原生多语言支持                                                                       |

Learning Mode 也挺有意思

1.6 还加入了一套专门的学习模式。

它不是简单让 AI “总结一篇笔记”，而是可以围绕一个主题和参考资料生成：

**结构化学习大纲 → 知识点 → Flashcards → 知识地图 → FSRS 间隔复习**

## 个人使用

### Model配置

分两个，一个是Chat Model，一个是Embedding Model，负责：Vault 知识库向量化和RAG 检索。

只想聊天，不需要 Embedding。想让 YOLO 搜索整个 Obsidian 知识库，就需要 Embedding

### 侧边栏

Ask 可以理解成：普通 AI 助手模式。不会主动拿一堆工具折腾你的文件。

Agent 模式，AI 就不仅仅“回答”。它开始可以：读取文件、搜索 Vault、、创建文件、、修改文件、执行 Bash、调用 RAG、调用 MCP、调用 Skills、调用 Subagent、操作 Memory、联网搜索、……

Agent 模式旁边还有一个很容易让人误解的：YOLO

YOLO 是 Agent 模式下“自动批准 Tool Call”的独立开关。熟悉自己的 Agent 权限以后再开。


**当前文件会自动进入 Agent Context**，也就是说你当前正在编辑的笔记，可以自动成为 Agent 上下文的一部分。这也是为什么 YOLO 在 Obsidian 里比单独开 ChatGPT 更自然。  
你打开：DINOv3研究.md。直接说：这里的实验设计还有什么问题？  
它就知道“这里”指哪个文件。

### Quick Ask

默认 Trigger：@

正在写笔记的时候，在某个空行输入`@`，就可以直接唤起 Quick Ask。

可以Ask，agent模式。还有多种续写模式

例如：@ 这里帮我补充一下 Harness Engineering 的定义

不用：```
```
切侧边栏
→ 新对话
→ 添加笔记
→ 问问题
```
这就是它相比普通聊天插件舒服的地方。

默认 Quick Ask 会截取光标附近的文本作为 Context，目前默认大约：光标前 5000 字符;光标后 2000 字符。而且都可以在 Editor 设置中调整。

### cursor chat
选中一段文字，可以执行一下命令

### 快捷指令
对话框输入`/`，可以调用skill、快捷指令（翻译和code review）以及命令（压缩上下文）

可在[snippets](../../YOLO/snippets.md)配置快捷指令


### 知识库 

RAG  “从大量笔记里找语义相关内容”   
Agent 文件工具  “主动探索目录、读取指定文件、组合任务”

比如：什么是我笔记里的 MCP？  偏 RAG。

而：找到 Projects 下最近修改的 10 篇 Agent 笔记，逐篇总结，然后创建 weekly-summary.md。偏 Agent。  

两者组合才是 YOLO 真正厉害的地方。

### 切到 Codex

聊天页面顶部实际上有两层选择。

包括Agent模式和CLI模式，可以切换到本机的Claude Code、Codex，看到的仍然是 YOLO 聊天 UI，但背后已经不是 YOLO Agent Runtime：已经是Codex CLI了

最大的价值不是：“在 Obsidian 里又多一个聊天窗口。”   
而是：**Codex 可以直接以当前 Vault 作为工作空间。**   
这时候 Obsidian 就开始有点像：**知识库版 IDE。**

Claude Code 还有 Plan Mode




