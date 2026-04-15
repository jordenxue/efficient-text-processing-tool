asset_layer: base

# 角色档案包生成消费规范 v1

> 层级：Universal Fixed Asset
> 版本：v1
> 核心原则：存储态 / 消费态分离；生成层只看消费区

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
3. 对 `key_relationships` 等候选性字段，保留"候选"标注注入 prompt
4. style guidance 目前为占位，待 style 管线接入后填充

---

## 五、sidecar 文件说明

| 文件 | 说明 |
|------|------|
| `sidecar_notes.md` | 人工维护的自由文本注记 |
| `sidecar_relations.json` | 详细关系条目（比 main.json 中的摘要更完整）|
| `sidecar_open_questions.json` | 待解决的知识空缺列表 |
| `sidecar_review.jsonl` | audit 发现记录（按时间追加）|

sidecar 文件均为维护层，不进入生成 payload。

---

## 六、复用到新小说

`generation_data` 和 `maintenance_data` 的分区结构是 universal 约定，  
具体字段簇根据新小说的叙事结构和复杂度决定。  
每个新小说的首个角色（样板角色）应作为字段簇验证的参考基准，再推广到其他角色。
