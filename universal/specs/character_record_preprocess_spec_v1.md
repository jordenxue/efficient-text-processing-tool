asset_layer: base

# 角色档案包预处理规范 v1

> 层级：Universal Fixed Asset
> 版本：v1（骨架版，待随实践完善）
> 适用范围：`kb/characters/{name}/main.json` 的 generation_data 字段填充

---

## 一、目标

将 KB 事实层数据（`character_appearances_v2.jsonl`、`character_profiles_v2.json` 等）
转化为结构化、可复用的角色主卡字段，供生成层消费。

---

## 二、输入

| 输入 | 来源 |
|------|------|
| 人物出场记录 | `kb/character_appearances_v2.jsonl`（按 canonical 过滤）|
| 人物档案 | `kb/character_profiles_v2.json`（对应 canonical 条目）|
| 原始 chunk 文本 | `chunks/{bookname}_{NNNN}.txt`（按需抽取）|
| 关系候选 | `kb/relationship_index.json`（共现推断，标注为候选）|
| query layer | `query.py` 输出的 `--json` 结构，可作为入口 |

---

## 三、字段填充原则

1. **只填有 chunk 证据的字段**：每个填入 `generation_data` 的事实，必须可以追溯到具体 chunk_id。
2. **候选信息明确标注为候选**：relationship / location 共现推断，不得写成事实。
3. **不发明细节**：KB 中无据的信息，宁可留空，不在预处理阶段填入推断。
4. **覆盖范围优先于精细度**：宁可有 10 个粗略事实，也不要有 2 个被过度加工的"精准"事实。

---

## 四、最小步骤骨架

```
Step 1: 从 appearances_v2 聚合该人物所有出场 chunk_id
Step 2: 从 profiles_v2 提取 aliases、chunk 列表
Step 3: 按字段簇（身份、关系、行为模式、外貌等）逐一从 chunk 文本中抽取证据
Step 4: 每个字段附 chunk_id 列表作为来源
Step 5: 区分 generation_data（直接消费）与 maintenance_data（辅助维护）
Step 6: 写入 kb/characters/{name}/main.json
```

---

## 五、自动化与人工分工

| 步骤 | 建议方式 |
|------|----------|
| 出场 chunk 聚合 | 自动（query.py）|
| 字段值抽取 | LLM 辅助 + 人工核查 |
| chunk_id 引用验证 | 自动（verify 脚本）|
| generation_data / maintenance_data 边界判断 | 人工 |

---

## 六、产物

`kb/characters/{name}/main.json` 中的 `generation_data` 字段簇（首轮试填）。  
试填后通过 audit spec 核查，再决定是否调整字段结构。
