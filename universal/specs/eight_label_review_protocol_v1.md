asset_layer: base

# 8 标签评审协议 v1

> 层级：Universal Fixed Asset
> 版本：v1
> 适用范围：所有使用本工具链的生成输出评审（continue_writing / rewrite）

---

## 一、用途

用于对生成文本进行结构化标注，识别哪类问题导致了生成失败。  
每条 finding 使用一个标签；一段生成文本可有多个 finding（多标签）。

---

## 二、8 个标签定义

| 标签 | 含义 |
|------|------|
| `core_world_rule_violation` | 违反了世界观核心设定（如物理规则、社会制度、不可更改的历史事件）|
| `speaker_conditioned_address_violation` | 称呼方式与说话者身份/关系不符（如角色使用了不该用的昵称或敬称）|
| `relationship_register_violation` | 人际关系呈现与 KB 中的事实层关系不符（如陌生人表现出亲密、敌人表现出友善）|
| `unsupported_lore_densification` | 在 KB 无据的情况下，对世界观细节进行了"合理化扩写"（即 KB 外编造）|
| `knowledge_boundary_violation` | 角色知道了其叙事位置上不该知道的信息（知识边界穿越）|
| `context_omission` | 生成文本省略了 context 中明确提供的关键信息（忽略 checkpoint 或 prompt 指定内容）|
| `model_override_despite_context` | 模型用自身预训练知识覆盖了 context 中明确提供的 KB 事实（context 被自动替换）|
| `scene_default_completion` | 模型用"场景默认完成"的方式结束生成（未到场景边界就收尾，如无理由停止）|

---

## 三、打标规则

1. **每条 finding 选且只选一个主标签**。若一个问题跨越多个标签，选最主要的原因。
2. **标签不代表严重程度**，只代表问题类型。严重程度单独评估（轻微/中度/严重）。
3. **只标注生成文本中实际观察到的问题**，不标注"可能出现"的风险。
4. **evidence 字段必须引用原文片段**，不能凭印象打标。

---

## 四、适用阶段

| 阶段 | 是否适用 |
|------|----------|
| continue_writing 输出 | ✓ |
| rewrite 输出 | ✓ |
| canon/style 提取输出 | ✗（提取有独立的 schema validation）|
| KB 内容本身 | ✗（KB 有独立的 audit 流程）|

---

## 五、输出格式（参考）

每条 finding 至少包含：

```json
{
  "label": "unsupported_lore_densification",
  "severity": "medium",
  "location": "第3段第2句",
  "evidence": "原文片段...",
  "explanation": "为什么这是此类问题"
}
```

---

## 六、复用到新小说

标签定义是通用的，不含具体小说内容。  
新小说可直接沿用本协议。若需新增标签，先验证现有 8 个无法覆盖再扩展，避免标签膨胀。
