---
name: constellate
description: 为个人 Markdown 或 Obsidian 笔记库构建、查询和维护内容完整、可追溯且语义互联的百科式 Wiki。用于初始化 Wiki、把指定原始笔记重组为 concepts、claims、domains、syntheses 与必要的 summaries、沿有类型的关系查询和综合知识、lint 文章质量/结构/证据/图连接、兼容或迁移旧版 sources 格式，或讨论并执行已批准的 schema 演化；支持自然语言及 `/constellate --init|--ingest|--query|--lint|--schema`。普通单篇 Markdown 排版、改标题或补通用 frontmatter 时不要使用。

metadata:
  version: "2.1"
  author: Lanning
  language: zh-CN
  category: knowledge-management
  tags:
    - personal-wiki
    - knowledge-graph
    - note-synthesis
---

# Constellate

把分散笔记重组为可独立阅读、可追溯、持续演化的知识文章，再用有类型的语义关系连接这些文章。坚持“文章优先”：先完整回答页面承诺的知识问题，再把图谱作为导航、证据与推理网络；只沉淀能增加理解、结构、证据关系或跨来源增量的知识。

## 坚守边界

1. 把目标 Vault 中 `wiki/` 之外的现有内容视为只读来源；只在 `<vault>/wiki/` 写入知识产物。只有用户针对具体原始文件明确授权后才修改来源。
2. 以当前磁盘内容为准，保留用户未提交和手工编辑的内容。不得用 Git 历史覆盖当前工作区，也不得把 `wiki/` 重新作为原始来源 ingest。
3. 默认只使用本地内容。只有 `--web` 或用户本次明确授权后才联网；搜索查询不得包含 Vault 私人原文、身份信息、凭据或未公开内容。
4. 默认执行“分析 → 用户确认 → 写入”。`--apply` 只授权普通新增和更新直接落盘；schema 变更、删除、合并和来源修改仍逐项确认。
5. 把取消或否决作为零写入终点：默认不创建 ingest 记录、不追加日志、不更新索引，也不修改任何文件。只有用户另行明确要求保留审计记录时，才把记录作为新的写入方案再次确认。
6. 允许临时阅读 Vault 外文件，但不把它写入 `sources`、直接 ingest 或留下绝对路径依赖。新写入的正式本地来源必须在 Vault 内，并以带引号的 Obsidian Wiki 链接写入 `sources`，使其可直接跳转。读取旧版相对路径时保持兼容并报告迁移警告；未经迁移预览和明确批准不得批量改写。
7. 关系真实性优先于图谱密度。不得为满足出边、邻居数或连通性指标编造关系；稀疏连接只作为人工复核信号，不作为全局硬错误。
8. 展示可审查的结论、证据、关系依据、不确定性和实际改动；不声称或输出隐藏的逐字推理。

## 开始任务

1. 把本文件所在目录解析为绝对路径 `<skill-dir>`，并从该目录定位所有脚本、参考和资产。
2. 确认 Vault 根目录与请求范围，完整读取目标文件适用的 `AGENTS.md` 或同类规则，并检查当前工作区状态。
3. 一次只选择一个主操作。读取 [references/workflows.md](references/workflows.md) 的对应章节；遇到未知参数、歧义路径或互斥参数时先澄清。
4. 处理知识类型、证据、关系、建页或内容充分性判断时，完整读取 [references/knowledge-model.md](references/knowledge-model.md)。初始化、写入或 lint 页面时，同时读取 [references/schema-reference.md](references/schema-reference.md) 与适用 schema 的“内容充分性”；Wiki 已存在时优先读取 `wiki/schema.md`，其中缺少该节时回退到 `assets/wiki/schema.md` 的默认契约。
5. 按“当前用户指令 → 仓库规则 → Vault 本地 schema → 本 Skill 默认规则”解决普通差异。任何层级都不能放宽本节边界；发现真实冲突时停止写入并说明。

完成本阶段的标准：Vault、主操作、适用规则、写入授权和需要读取的参考均已确定。

## 执行分支

- `--init`：预览并非覆盖地创建基础结构。
- `--ingest`：逐篇理解、重组为知识文章、整体连接并提交一次方案；只有获批后才写入。
- `--query`：沿索引、文本命中和语义边回答；默认不写回。
- `--lint`：先运行确定性检查，再审查需要语义判断的知识问题；默认只报告。
- `--schema`：用真实案例提出变更；批准 schema 与迁移是两个独立确认点。

严格执行 [references/workflows.md](references/workflows.md) 中所选分支，直到该分支的完成标准全部满足。

## 完成任务

1. 查看本任务涉及的文件差异或写入清单，确认没有覆盖用户已有修改。
2. 只要 Wiki 发生写入，就运行 `python '<skill-dir>/scripts/lint_wiki.py' <vault>`；脚本为零错误后，逐页处理内容充分性警告并完成所选工作流规定的语义检查。新建或实质更新页低于适用 schema 的机械预警线时，扩充有来源支撑的内容，或在 ingest 中记录“来源受限例外”及缺失模块；不得把警告直接当作通过。若用户取消或否决且尚未写入，跳过这一步以保持零写入。
3. 汇报实际修改、检查结果、尚未解决的矛盾或缺口，以及未执行的建议。若未获批准，明确汇报“未写入任何文件”。
4. 不自动暂存、提交或推送 Git。若执行删除或合并，逐项说明删除、保留、迁移、入站链接更新和 Git 可恢复性。

完成标准：所有授权改动均可追溯；每个新建或实质更新的知识页既能独立充当知识文章，又满足适用内容契约或记录了保真例外；lint 无错误，用户内容未被覆盖，且未授权事项保持未写入。
