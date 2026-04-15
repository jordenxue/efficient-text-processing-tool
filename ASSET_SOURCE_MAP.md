asset_layer: base

# 资产真源地图

> 本文件用于区分正式真源、草案候选、实验参考与运行态状态文件。
> 这里区分的是文档地位与用途，不是第五层资产；项目资产层仍然只有四层。

## 1. 正式真源

这些文件或目录用于定义长期规则、正式边界或项目级定案：

- `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
- 已收口的 `universal/specs/` 规范文件
- `DECISIONS.md`

说明：

- 这些对象优先级高于运行态状态文件。
- 若与阶段性说明冲突，应优先按正式真源理解。

## 2. 草案候选

这些文件可为后续定稿提供输入，但当前不等于正式真源：

- `review/stable_core_instantiation_mold_v0_1_draft.md`
- `review/conditional_generation_guidance_container_v0_1_draft.md`
- `review/project_structure_refactor_input_v1.md`

补充说明：

- “草案候选”是文档地位，不是资产层级。
- 这些文件可服务后续 `instantiation_mold` 定稿，但当前不能直接当成正式 mold 真源。

## 3. 实验参考

这些对象属于实验消费、实验复审或阶段性分析参考：

- `outputs/generation/`
- `outputs/ab_round3/`
- `review/round2_lore_failure_diagnosis.md`
- `review/round3_pilot_review.md`
- `review/round3_pilot_label_table.json`
- `review/project_asset_inventory_layering_v1.md`
- `review/tag_application_guidelines_v1.md`
- `review/README.md`
- `outputs/README.md`

说明：

- 这些对象可以帮助理解项目走到哪里、遇到过什么问题、当前怎么读仓库。
- 但它们不自动升级为正式结构真源。

## 4. 运行态状态文件

这些文件用于说明当前项目阶段、正在执行的任务与近期动作（已被 `.gitignore` 排除，不在 Git 骨架中；git clone 后不存在，本地可在 `alpha_test_stage/` 找到）：

- `STATE.json`
- `CURRENT_STATE.md`
- `NEXT_ACTION.md`

说明：

- 它们帮助 AI 快速对齐当前进度。
- 它们不用于覆盖 `base` 规范、资产分层总则或正式结构边界。

## 5. 关于 `schema.json`

- `schema.json` 是根目录的 legacy generic schema。
- 当前主链脚本（`extract_canon.py`、`extract_style.py`）直接引用 `schema/canon_schema.json` 与 `schema/style_schema.json`，不依赖根目录 `schema.json` 作为主用 schema。
- `schema.json` 保留在主项目，并允许进入首批 Git 骨架提交；其定位仍是 legacy compatibility entry，而不是当前主用 schema。

## 6. 关于 `universal/sop/`

- 当前仓库里已有 `universal/sop/` 目录。
- 其中 3 份文件已通过准入审计，标注为 `asset_layer: base`，允许进入首批 Git 骨架提交。
- 其余文件仍待逐项确认，当前更合适的口径是：`universal/sop/` 作为一个**可部分升级为正式 base 真源的承载面**，需逐项确认。
