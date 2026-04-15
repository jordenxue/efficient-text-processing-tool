asset_layer: base

# 高效文本处理工具

面向中文长文本的结构化知识资产工程，当前主线是把项目收成“可复用、可审计、对 AI 读取友好”的项目骨架，而不是继续堆实验产物。

## 当前 README 的定位

- 本文件提供仓库总览与骨架级说明。
- 本文件不是运行态状态真源。
- 精确当前进度与当前任务，请最后再看运行态文件，而不要先用 README 覆盖长期规则。

## 先读什么

接手本项目时，优先按以下顺序读取：

1. `PROJECT_READING_ORDER.md`
2. `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
3. `universal/specs/staged_engineering_workflow_backbone_v1.md`
4. `ASSET_SOURCE_MAP.md`
5. `review/project_asset_inventory_layering_v1.md`
6. `review/tag_application_guidelines_v1.md`
7. `PROJECT_MODULES.md`
8. `DECISIONS.md`
9. `AI_ROLES.md`
10. 再进入 `STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md`（这三个文件不在 Git 骨架中，git clone 后默认不存在；本地可在 `alpha_test_stage/` 找到）

## 当前结构口径

项目资产层始终只有四层：

- `base`
- `instantiation_mold`
- `novel_instance`
- `experimental`

说明：

- 草案、候选、输入分析、历史实验只是文档地位，不构成第五层。
- 当前 round2 / round3 相关材料仍属于 `experimental`。
- 当前 mold 相关文件仍是草案，不等于正式 `instantiation_mold` 真源。

## 当前建议如何理解仓库

- `universal/specs/staged_engineering_workflow_backbone_v1.md`：当前 workflow 骨架真源，状态为 `frozen baseline`
- `universal/specs/`：正式规范、协议、schema 真源
- `universal/sop/`：当前可作为 base 参考的 SOP / 清单承载区，已有 3 份文件通过准入审计，标注为 `base`
- `Scripts/`：稳定通用脚本能力
- `schema/`：基础 schema（`canon_schema.json`、`style_schema.json`）
- `schema.json`：legacy generic schema / compatibility entry，当前主用 schema 位于 `schema/` 目录，但它本身保留在首批 Git 骨架提交范围内
- `prompts/`：当前脚本依赖的提示词资源（已允许进入首批 Git 骨架提交）
- `kb/characters/template/`：当前模板目录，作为 `instantiation_mold` 骨架样板进入首批提交
- `kb/` 其余长期知识资产：当前允许随首批提交进入 Git，作为具体小说实例数据保留
- `outputs/`：默认主要承接 `experimental`
- `review/`：阶段性混合区，承接复审、结构分析、清理与隔离材料

## 首批 Git 骨架提交口径

首批 Git 提交只上传项目骨架，优先包括：

- `universal/specs/`
- `universal/sop/` 中已通过准入审计的文件
- `Scripts/`
- `schema/` 与 `schema.json`
- `prompts/`
- `kb/` 下长期实例资产，以及 `kb/characters/template/` 中的骨架样板文件
- 根目录入口 / 治理文件
- 少量必要的结构说明与分析文件

当前不纳入（已被 `.gitignore` 排除或不在白名单）：

- `raw/`、`chunks/`
- `outputs/` 中实验输入与运行产物
- `STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md`（运行态文件，git clone 后不存在；本地可在 `alpha_test_stage/` 找到）
- `_pending_delete/`
- `alpha_test_stage/`（本地隔离区，完整不进入 Git）

## 当前边界

- 本项目当前不做大规模目录搬迁
- 涉及 workflow / 流程骨架 / mode 术语时，以 `universal/specs/staged_engineering_workflow_backbone_v1.md` 为准
- 不以 README 取代正式规范或项目决策
- 不把实验层正文内容误写成长期真值
