# Prompt

[返回仓库总览](../README.md)

## 📌 目录定位

这里存放常用 Prompt、Prompt Engineering 方法与长期思考。

Prompt 适合快速复制、临时使用和持续试验；当一个 Prompt 逐渐拥有稳定的触发条件、工作流程和边界时，可以进一步整理到 [`skills/`](../skills/README.md) 中，形成可复用的 Skill。

## 💬 Prompt 索引

### [`Prompt Prompt.md`](./Prompt%20Prompt.md)

关于 Prompt Engineering 的长期笔记，同时包含一个**用于制作 Prompt 的 Prompt**。

目前主要将 Prompt 拆分为五个相对独立的层次：

```text
知识层
  ↓
目标层
  ↓
行为层
  ↓
协议层
  ↓
规范层
```

分别解决：

- **知识层**：模型需要知道什么
- **目标层**：最终到底要完成什么
- **行为层**：应该按照什么流程完成
- **协议层**：应该以什么风格完成
- **规范层**：明确不能做什么

相比堆砌大量 Prompt 技巧，更关注如何把一个模糊需求逐渐转换成明确、可修改、可调试的任务协议。

### [`find-hide.md`](./find-hide.md)

`find-hide` Skill 最初的原型 Prompt：

> 找出我问题背后那个我没问、但可能更关键的问题，并指出来。

适合临时使用，不需要加载完整 Skill 时直接复制。

## 🚀 使用方式

找到对应 Prompt 后可以直接复制，根据当前任务补充上下文和约束，再观察输出并迭代。

如果一个 Prompt 开始需要固定的参考资料、脚本、检查步骤或明确的完成标准，建议转到 [Skills 索引](../skills/README.md) 查看是否已有对应 Skill，或将它整理成新的 Skill。

## 🗂️ 目录结构

```text
prompt/
├── README.md
├── Prompt Prompt.md
└── find-hide.md
```

