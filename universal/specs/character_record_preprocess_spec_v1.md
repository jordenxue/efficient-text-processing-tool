asset_layer: base

# 角色档案包预处理规范 v1

> 层级：Universal Fixed Asset
> 版本：v1（骨架版，待随实践完善）
> 适用范围：`kb/characters/{name}/main.json` 的 generation_data 字段填充
> 当前文档只统一**current draft rule**，不把角色档案包字段设计写成最终冻结版。

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

## 二-A、当前 draft 合同补充

### 1. 当前核心 mold 组成件

当前有效 draft 口径下，角色包核心 mold 由以下 4 件组成：

- `main.json`
- `sidecar_notes.md`
- `sidecar_open_questions.json`
- `sidecar_relations.json`

`sidecar_review.jsonl` 当前**不是**核心 mold 必备件；它应在后续 audit / review 阶段按需生成。

### 2. 正式 JSON 占位规则

- 正式 JSON 中，当前只允许 `"NULL"` 作为可审计占位。
- `"TODO"` 不再作为正式 JSON 的合法值。
- 若从历史骨架复制出的 JSON 中仍残留 `"TODO"`，应在写入实例目录的首轮整理中清洗为 `"NULL"`、空数组或空对象。
- `main.json.character` 在实例化时必须第一轮立即替换，不得在实例目录中长期保留 `"NULL"`。

### 3. 当前 draft 语义定义

| 字段 | 当前 draft 语义 |
|------|-----------------|
| `scope_anchor` | 记录当前角色包的适用范围与验证边界，用于说明“这份主卡当前锚定到什么稳定状态” |
| `evidence_pack` | 维护侧证据包，用于记录字段与 chunk / 证据来源的对应关系，不直接进入生成 payload |
| `source_artifacts` | 维护侧来源清单，用于记录本次角色包整理实际依赖过的文件、索引、查询结果或中间材料 |

补充说明：

- `evidence_pack` 与 `source_artifacts` 的详细 entry schema 目前仍是 open design question。
- 本规范当前只要求它们作为结构位与维护语义存在，不要求一次性定死最终字段设计。

## 三、字段填充原则

1. **只填有 chunk 证据的字段**：每个填入 `generation_data` 的事实，必须可以追溯到具体 chunk_id。
2. **候选信息明确标注为候选**：relationship / location 共现推断，不得写成事实。
3. **不发明细节**：KB 中无据的信息，宁可留空，不在预处理阶段填入推断。
4. **覆盖范围优先于精细度**：宁可有 10 个粗略事实，也不要有 2 个被过度加工的"精准"事实。

---

## 四、最小步骤骨架

```
Step 0: 从 kb/characters/template/ 复制 4 件 core mold 到 kb/characters/{name}/，立即替换 main.json.character，并清理历史 TODO
Step 1: 从 appearances_v2 聚合该人物所有出场 chunk_id
Step 2: 从 profiles_v2 提取 aliases、chunk 列表
Step 3: 按字段簇（身份、关系、行为模式、外貌等）逐一从 chunk 文本中抽取证据
Step 4: 把字段 -> chunk / 来源引用写入 maintenance_data.evidence_pack，而不是回写到 generation_data
Step 5: 区分 generation_data（直接消费）与 maintenance_data（辅助维护）
Step 6: 按需要更新 sidecar_open_questions / sidecar_relations / sidecar_notes
Step 7: 写入 kb/characters/{name}/main.json
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
