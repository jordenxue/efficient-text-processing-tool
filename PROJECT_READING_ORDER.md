asset_layer: base

# 仓库推荐阅读顺序

> 本文件提供 AI 进入仓库后的最短正确阅读链。
> 原则是：先读长期规则与真源，再读运行态状态文件。

## 推荐顺序

1. `PROJECT_READING_ORDER.md`
   说明当前推荐阅读链本身。
2. `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
   先确立四层资产总则与新小说启动顺序。
3. `universal/specs/staged_engineering_workflow_backbone_v1.md`
   先确认当前 workflow 骨架真源、六步主流程与 mode 术语口径。
4. `ASSET_SOURCE_MAP.md`
   再分清正式真源、草案候选、实验参考、运行态状态文件。
5. `review/project_asset_inventory_layering_v1.md`
   再看当前关键资产归位表。
6. `review/tag_application_guidelines_v1.md`
   再看 Tag 的当前落地规则。
7. `PROJECT_MODULES.md`
   再理解当前目录与模块的现实分布。
8. `DECISIONS.md`
   再确认项目级定案，避免沿用已驳回路线。
9. `AI_ROLES.md`
   再看当前协作分工与交接口径。
10. `STATE.json`
11. `CURRENT_STATE.md`
12. `NEXT_ACTION.md`
   最后再进入运行态状态文件，了解”当前在做什么”。
   **注意：这三个文件已被 `.gitignore` 排除，不在 Git 骨架中。git clone 后不存在；本地可在 `alpha_test_stage/` 找到。**

## 读取原则

- `base` 规范、资产总则、正式结构边界优先级高于运行态状态文件。
- 涉及 workflow / 流程骨架 / `draft_mode` / `finalize_mode` / `task_mode` 时，以 `universal/specs/staged_engineering_workflow_backbone_v1.md` 为准。
- `STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md` 只用于理解当前执行进度，不用于覆盖长期结构规则。
- 若任务不直接涉及实验验证，不要先跳进 `outputs/` 或 `review/` 的 round2 / round3 材料。
