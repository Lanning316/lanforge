# Schema 操作参考

本文件说明如何应用 schema；默认字段与关系格式以 [assets/wiki/schema.md](../assets/wiki/schema.md) 为单一权威。Wiki 已初始化时，以 `<vault>/wiki/schema.md` 取代默认 schema。

## 目录与模板

```text
wiki/
├── schema.md
├── index.md
├── log.md
├── concepts/
├── claims/
├── domains/
├── syntheses/
├── ingests/
└── summaries/
```

按 `type` 选用 `assets/wiki/templates/<type>.md`。保持模板必需二级标题不变，以便 lint 确定性检查；保留或调整模板中的三级写作模块，使其匹配当前材料。初始化不创建占位页面。

## 填写规则

- 使用 UTF-8 与 `.md`；知识页文件名等于 H1 标题，ingest 例外使用 `YYYY-MM-DD-简短标题.md`。
- 把 `tags`、`sources` 和 `outputs` 写成块状 YAML 列表；空列表写成 `[]`。
- 新写入的 `sources` 每项使用带引号的 Obsidian Wiki 链接，如 `"[[notes/原始笔记.md]]"`，使属性可直接跳转；目标只允许 Vault 内、`wiki/` 外的现有 Markdown。旧版 Vault 相对路径继续可读，但 lint 产生 `source-legacy-path` 警告。`outputs` 仍使用 Vault 根目录相对路径，只列本次实际创建或实质修改的 Wiki 页面。
- 保持 `created` 不变；只在知识内容实质变化时更新 `updated`。
- 先沿用现有标签。技术名使用官方英文；用途或个人发展可使用中文。避免 type 同名标签及中英文、大小写、空格、下划线或连字符变体。
- 把每条语义边单独写入 `## 语义关系`，严格使用适用 schema 的格式与受控类型，并按 [knowledge-model.md](knowledge-model.md) 判断方向和依据。
- 把外部来源写入正文，包含来源名、完整 URL、访问日期和证据作用；不放入 `sources`。
- 按适用 schema 的“内容充分性”先完成正文，再写语义关系与演化记录。Wiki 已存在但本地 schema 缺少该节时，使用 `assets/wiki/schema.md` 的默认契约；本地 schema 明确给出该节时以本地规则为准。
- 把页面篇幅视为规划基线而非填字配额。低于机械预警线时补充可追溯的背景、机制、论证、边界、实例、来源差异或综合增量；材料不足时保持保真，并在 ingest 记录来源受限例外和缺失模块。

## Ingest 记录

只在方案获批并发生写入后创建 ingest。`outputs` 与实际改动逐项一致，正文保存接受和放弃的关系、用户纠正、限制与检查结果。

`cancelled` 与 `rejected` 仅用于兼容旧记录，或用户在取消后另行明确批准的审计记录；取消或否决本身默认不产生文件。例外审计记录必须使用空 `outputs`，且不能触发 index 或知识页演化更新。

## Index 与 Log

- Index 按 Domains、Concepts、Claims、Syntheses 分区。每个核心页出现一次，使用“链接 — 一句话说明”；claim 与 synthesis 同时写“状态：值”。
- Ingests 与 Summaries 只保留目录入口，不逐项加入核心索引。
- Log 只追加已经实际写入的 ingest、query、lint、schema、migration 与 correction 事件。普通查询、未执行方案、取消和否决不记录。
- Log 标题使用 `## [YYYY-MM-DD HH:MM] 类型 | 简短标题`。旧记录有实质错误时追加 correction，不重写历史。

## 写入检查

写入前验证：模板与字段值匹配本地 schema；文章简报覆盖适用内容模块并标明来源贡献与跨来源增量；所有已提出关系的目标存在且为核心页，类型、方向和依据成立；不因出边或邻居数量补写关系；方案中的 outputs 与预期改动一致。

写入后验证：运行 lint；逐页处理内容充分性警告；检查 index 分区与状态；确认每个实质变化页链接本次 ingest；核对 ingest outputs、log 事件和实际文件清单。

完成标准：所有必填字段和章节可由 lint 解析；新建或实质更新页满足内容契约或记录来源受限例外；语义边可机器读取，记录只描述实际发生的写入。

## Sources 格式迁移

先运行 `python '<skill-dir>/scripts/migrate_sources.py' <vault> [--scope <范围>]` 获取只读预览。核对每个目标与阻断项并获得明确批准后，追加 `--apply`；脚本只改写 `sources` 列表值，保留正文、换行与 UTF-8 BOM，并在任一待迁移目标无效时整体拒绝写入。完成后再次运行 lint，确认 `source-legacy-path` 警告清零。

这种格式迁移不改变知识内容，因此不更新页面 `updated`、index 或 ingest；执行成功后向 `log.md` 追加一条 migration 事件，记录范围、文件数和检查结果。不得手工全局替换，也不得把无效旧路径包装成 Wiki 链接。
