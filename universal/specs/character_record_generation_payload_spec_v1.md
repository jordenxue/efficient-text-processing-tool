asset_layer: base

# 角色档案包生成消费规范 v1

> 层级：Universal Fixed Asset
> 版本：v1
> 核心原则：存储态 / 消费态分离；生成层只看消费区
> 当前文档只统一**current draft rule**，不把角色包消费合同写成最终冻结设计。

---

## 一、核心原则

`kb/characters/{name}/main.json` 分两个顶级区域：

| 区域 | 用途 | 是否发给模型 |
|------|------|-------------|
| `generation_data` | 生成层直接消费的事实 | **是** |
| `maintenance_data` | 人工维护辅助信息 | **否** |

**生成时永远不要把整个 main.json 直接喂给模型。**  
生成层（`build_generation_context.py`）只从 `generation_data` 中抽取需要的字段。

---

## 一-A、当前 draft 合同补充

- 当前核心 mold 组成件为：`main.json`、`sidecar_notes.md`、`sidecar_open_questions.json`、`sidecar_relations.json`。
- `sidecar_review.jsonl` 当前**不是**核心 mold 必备件；若需要持久审计记录，应在 audit / review 阶段按需生成。
- 正式 JSON 中当前只允许 `"NULL"` 作为可审计占位；`"TODO"` 不再作为正式 JSON 合法值。
- `main.json.character` 在实例化后必须立即替换，不得带着 `"NULL"` 进入生成消费。
- 任何将被当前轮 payload 选中的 `generation_data` 字段，在进入生成消费前不得继续保留 `"NULL"`。

## 二、generation_data 字段要求

| 要求 | 说明 |
|------|------|
| 事实层 | 每个字段值必须有 chunk 证据（audit spec 已核查）|
| 简洁 | 每个字段值长度适合注入 prompt，不写冗长叙述 |
| 无歧义 | 避免"可能"、"大概"等模糊表述出现在 generation_data |
| 可组合 | 字段结构支持生成层按需选取部分字段，不依赖全部字段同时存在 |

**当前已接受的字段簇（以 `kb/characters/*/main.json` 为准）：**

| 字段名 | 说明 |
|--------|------|
| `identity_core` | 身份核心：summary、hard_facts、family_structure |
| `capability_profile` | 能力画像：known_competence、operational_constraints、avoid_overclaim |
| `voice_profile` | 声音画像：external_expression、inner_monologue、register_preferences、register_avoidances |
| `relationship_stance` | 关系立场列表（高置信关系，非共现候选）|
| `hard_boundaries` | 硬边界列表（不可违反的 lore 约束）|
| `focus_notes` | 生成焦点注记（当前场景特别需要注意的点）|

> 这些字段名是当前已接受结构，不是抽象示例。
> 新小说复用时，可在此基础上增减字段，但应保留 `identity_core` 和 `hard_boundaries` 作为最小核心。

---

## 三、maintenance_data 字段类型

当前 draft 语义补充：

| 字段 | 当前 draft 语义 |
|------|-----------------|
| `scope_anchor` | 记录当前角色包的适用范围与验证边界，帮助说明当前主卡锚定到什么稳定状态 |
| `evidence_pack` | 维护侧证据包，用于记录字段与 chunk / 证据来源的对应关系，不进入生成 payload |
| `source_artifacts` | 维护侧来源清单，用于记录本次角色包整理实际依赖过的文件、索引、查询结果或中间材料 |

补充说明：

- `evidence_pack` 与 `source_artifacts` 的详细 entry schema 仍是 open design question。
- 当前文档先统一它们的维护语义，不要求一次性定死最终字段设计。

以下类型的内容应放在 `maintenance_data`，不发给模型：

- 待核实的字段（标注 `"confidence": "uncertain"` 的条目）
- 编辑注记（如"此处需人工核查"）
- chunk 引用列表（用于 audit，不用于生成）
- 开放问题（sidecar_open_questions 的摘要）
- 历史版本字段

---

## 四、消费端调用约定

`build_generation_context.py` 调用角色档案时：

1. 读取 `generation_data` 中指定的字段簇
2. 不读取 `maintenance_data`
3. 如未来下游临时引入候选关系信息，必须保留"候选"标注，且不应把维护侧候选直接伪装成高置信事实
4. style guidance 目前为占位，待 style 管线接入后填充

---

## 五、sidecar 文件说明

| 文件 | 说明 |
|------|------|
| `sidecar_notes.md` | 人工维护的自由文本注记 |
| `sidecar_relations.json` | 详细关系条目（比 main.json 中的摘要更完整）|
| `sidecar_open_questions.json` | 待解决的知识空缺列表 |

sidecar 文件均为维护层，不进入生成 payload。

补充说明：

- `sidecar_review.jsonl` 如存在，应按 audit / review 阶段的按需产物理解，而不是核心 mold 必备件。

---

## 六、复用到新小说

`generation_data` 和 `maintenance_data` 的分区结构是 universal 约定，  
具体字段簇根据新小说的叙事结构和复杂度决定。  
每个新小说的首个角色（样板角色）应作为字段簇验证的参考基准，再推广到其他角色。
