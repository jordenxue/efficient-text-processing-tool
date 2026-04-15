asset_layer: base

# 角色档案包审核规范 v1

> 层级：Universal Fixed Asset
> 版本：v1（骨架版）
> 适用范围：`kb/characters/{name}/main.json` 的字段值核查

---

## 一、目标

核查预处理填入的字段值是否准确、有据、无漂移，确保生成层消费到的是高置信事实。

---

## 二、audit 触发时机

| 时机 | 说明 |
|------|------|
| 首次填充后 | 预处理完成后必须过一轮 audit |
| 原始 KB 更新后 | appearances_v2 / profiles_v2 有重大更新时重新 audit |
| 生成结果反馈后 | 发现 generation 输出与 KB 不符时，追溯 audit 对应字段 |

---

## 三、核查维度

### 3.1 事实准确性
- 每个 `generation_data` 字段值，是否能在 `maintenance_data.evidence_pack` 或对应 sidecar 中找到 chunk_id 支撑？
- chunk_ids 等证据链应存放在 `maintenance_data.evidence_pack`，**不回流到 `generation_data`**（消费区保持干净）
- 若找不到任何 chunk 证据，该字段需降级（移入 `maintenance_data`）或删除

### 3.2 覆盖率
- 当前填入字段是否覆盖了人物主要出场情境？
- 重要出场章节有无遗漏？

### 3.3 字段语义边界
- `generation_data` 中是否混入了维护层信息（如待确认问题、编辑注记）？
- `maintenance_data` 中是否有本该消费的事实被遗漏？

### 3.4 候选标注完整性
- relationship / location 候选是否都有"候选"标注？
- 是否有推断被误写成事实？

---

## 四、证据标准

证据链存放位置：`maintenance_data.evidence_pack`（或相关 sidecar），**不放在 `generation_data`**。

- **必须**：`generation_data` 中每个有实质内容的字段，在 `evidence_pack` 中有对应的 chunk_id 记录（至少 1 个）
- **建议**：关键字段（如 `identity_core.hard_facts`、`hard_boundaries`）引用 2+ 个 chunk 互相印证
- **不接受**：`generation_data` 有内容，但 `evidence_pack` 中完全找不到对应来源

---

## 五、产物

- `kb/characters/{name}/sidecar_review.jsonl`：audit 发现记录（每条含字段名、问题类型、建议处置）
- `kb/characters/{name}/sidecar_open_questions.json`：无法 audit 解决的待定问题

---

## 六、常见问题类型

| 问题类型 | 处置方式 |
|----------|----------|
| 无 chunk 证据 | 降级为 maintenance_data 或删除 |
| 候选信息被写成事实 | 改回候选标注 |
| 字段值与 chunk 实际内容不符 | 修正字段值或删除 |
| 覆盖率不足 | 补充 chunk 引用 |
