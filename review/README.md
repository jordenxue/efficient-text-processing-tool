asset_layer: experimental

# review 目录说明

> `review/` 当前是阶段性混合区，用于承接复审、结构分析、清理与隔离材料。
> 它不是长期规范真源的默认承载面。

## 当前主要内容类型

### 1. 实验复审

示例：

- `round2_lore_failure_diagnosis.md`
- `round3_pilot_review.md`
- `round3_pilot_label_table.json`

这些文件主要服务于实验诊断、A/B 评审与错误标签复审。

### 2. 结构分析

示例：

- `project_asset_inventory_layering_v1.md`
- `tag_application_guidelines_v1.md`
- `stable_core_instantiation_mold_v0_1_draft.md`
- `conditional_generation_guidance_container_v0_1_draft.md`
- `project_structure_refactor_input_v1.md`

这些文件主要服务于资产归位、Tag 规则、模具抽取与结构重构输入。

### 3. 清理 / 隔离 / 审计

示例：

- `_pending_delete/`
- 各类 cleanup / reorg / audit 报告与 manifest

这些对象主要服务于历史实验分流、清理审计与后续人工确认。

## 当前使用口径

- 若任务涉及 workflow 骨架、六步主流程或 `draft_mode` / `finalize_mode` / `task_mode` 术语，不在 `review/` 内找真源，直接回到 `universal/specs/staged_engineering_workflow_backbone_v1.md`。
- 若任务是看实验表现，优先进入“实验复审”类文件。
- 若任务是看结构、层级、模具与重构输入，优先进入“结构分析”类文件。
- 若任务涉及历史文件去留，进入“清理 / 隔离 / 审计”类对象。

本轮不在 `review/` 内做大规模搬迁；先通过说明文件帮助 AI 正确读取。
