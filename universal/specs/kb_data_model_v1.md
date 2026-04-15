asset_layer: base

# KB 数据模型 v1

> 层级：Universal Fixed Asset
> 版本：v1
> 适用范围：所有使用本工具链的小说项目的 kb/ 目录结构

---

## 一、概述

`kb/` 是小说级知识资产的主目录。其中的文件分属三个语义层：

- **事实层（Fact Layer）**：从原文提取、经 schema 校验的结构化事实，是下游一切推断的来源
- **索引层（Index Layer）**：对事实层数据的聚合/重组，加速查询
- **alias 层（Alias Layer）**：用于查询时的名称解析，不代表叙事事实

---

## 二、文件分层说明

### 2.1 事实层

| 文件 | 说明 |
|------|------|
| `master_kb.json` | 所有 chunk 的 canon + style 提取产物的完整合并包；事实层原始汇总，**体积大，不直接喂给模型** |
| `character_appearances_v2.jsonl` | 每行一条人物出场记录（chunk_id + raw_name + canonical），是人物事实的最细粒度来源 |

### 2.2 索引层

| 文件 | 说明 |
|------|------|
| `character_profiles_v2.json` | 按 canonical 人物聚合的档案，含 aliases（observed）、chunk_ids 列表等；由 rebuild_character_index.py 生成 |
| `event_index.json` | 按事件类型/参与者聚合的事件索引 |
| `location_index.json` | 按地点聚合的位置索引，含出现的 chunk_ids |
| `relationship_index.json` | 按人物对聚合的关系索引，共现推断，**不是高置信叙事事实** |
| `style_summary.json` | 风格特征摘要（聚合自 style 提取产物）|

### 2.3 Alias 层（仅用于 query-time 名称解析）

| 文件 | 说明 |
|------|------|
| `character_alias_map_v2.json` | alias → canonical 的自动映射表 |
| `character_alias_manual_confirmed_v2.json` | 人工确认的高置信 alias 列表 |
| `character_alias_manual_blocklist_v2.json` | 人工屏蔽的 alias，防止误合并 |
| `character_alias_candidates_v2.json` | 低置信候选，待人工核查 |
| `character_query_aliases_v2.json` | **仅用于 query-time 命中**的 alias（如昵称），不写回 observed 事实层 |

### 2.4 角色档案包（长期维护层）

| 路径 | 说明 |
|------|------|
| `characters/{name}/main.json` | 当前阶段新方向：存储态/消费态分离的角色主卡；`generation_data` 字段供生成层消费，`maintenance_data` 字段供人工维护 |
| `characters/{name}/sidecar_*.json/md` | 辅助 sidecar：关系、待解决问题、评审记录等 |

### 2.5 小说级文档（kb/docs/）

可选目录，存放与具体小说数据相关的人工说明文档。典型内容包括：
- 数量口径说明（解释 chunk_total / canon_input / style_input 等统计差异）
- 测试集设计规范（说明本小说的测试用例构建原则）

文档命名与内容随项目而定，不作为 universal 规范的一部分。

### 2.6 其他 kb/ 文件（小说特定）

以下为典型的小说级附加文件，不是所有项目必须存在：

| 文件类型 | 说明 |
|----------|------|
| `author_conflict_register_*.jsonl` | 人工确认发现的 lore 冲突记录 |
| `clean_canon_testset_*.jsonl` | 针对本小说 canon 的测试集样本 |
| `character_alias_review_*.md` | alias 审查过程笔记（非结构化，维护层）|
| `prompt_context.md` | 旧版 prompt 上下文模板（若存在，已被 build_generation_context.py 替代）|

---

## 三、数据流图

```
raw/ ── chunker.py ──→ chunks/
                          │
                    extract_canon.py  ──→ outputs/canon/  ─┐
                    extract_style.py  ──→ outputs/style/  ─┤
                                                            │
                                                      merge.py
                                                            │
                                                     kb/master_kb.json  (事实层原始汇总)
                                                            │
                                              rebuild_character_index.py
                                                            │
                                     kb/character_appearances_v2.jsonl  (事实层)
                                     kb/character_profiles_v2.json      (索引层)
                                                            │
                                                      query.py  (查询层)
                                                            │
                                          build_generation_context.py  (消费层入口)
```

---

## 四、约束与注意事项

1. **master_kb.json 不直接用于生成**：体积过大，通过 query.py 抽取所需字段后再消费。
2. **relationship_index / location_index 是共现推断**：不等于叙事事实，生成时标记为"候选"。
3. **observed alias ≠ query alias**：`character_profiles_v2.json.aliases` 来自 raw_name 真实出现，`character_query_aliases_v2.json` 是 query-only，不写回 observed 层。
4. **character_index.json（v1）已废弃**：只保留为 legacy，不更新，不作为新业务的数据来源。

---

## 五、复用到新小说

| 需要改动 | 说明 |
|----------|------|
| `kb/` 所有数据文件 | 按新小说重新提取 + 合并 |
| `kb/characters/` 目录 | 为新小说人物建新的档案包 |
| 不需要改 | `kb/` 目录结构、文件命名规范、字段 schema |
