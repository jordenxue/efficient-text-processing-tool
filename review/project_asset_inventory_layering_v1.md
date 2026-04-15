asset_layer: experimental

# 当前项目关键资产归位表 v1

> 本盘点是“当前关键资产归位表”，用于服务后续 Tag 补齐、模具抽取、审计与新小说启动 SOP 落地。
> 当前只做关键资产归位，不处理脚本化与大规模重构。
> 本文件属于当前阶段的归位审阅产物 / 协作盘点文件，不构成长期固定规范真源。

## 1. 说明

- 本表优先覆盖当前项目的关键目录、关键文件与协作真源。
- 建议层级仅使用四层：`base`、`instantiation_mold`、`novel_instance`、`experimental`。
- 若对象边界暂不够稳定，可标为“待定”，并写明原因。

## 2. Base

| 路径 | 建议层级 | 简短理由 |
|------|----------|----------|
| `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md` | `base` | 当前资产分层与新小说启动总则的正式规范真源。 |
| `universal/specs/staged_engineering_workflow_backbone_v1.md` | `base` | 当前 workflow 骨架真源，统一六步主流程与 mode 术语。 |
| `universal/specs/character_record_preprocess_spec_v1.md` | `base` | 跨小说可复用的角色档案包预处理规范。 |
| `universal/specs/character_record_audit_spec_v1.md` | `base` | 跨小说可复用的角色档案包审核规范。 |
| `universal/specs/character_record_generation_payload_spec_v1.md` | `base` | 跨小说可复用的 generation payload 组装规范。 |
| `universal/specs/chunking_protocol_v1.md` | `base` | 通用切块协议，属于基础流程规范。 |
| `universal/specs/generation_context_protocol_v1.md` | `base` | 通用 generation context 协议，属于跨小说流程规范。 |
| `universal/specs/eight_label_review_protocol_v1.md` | `base` | 当前统一复审标签协议，作为通用审计口径使用。 |
| `universal/specs/kb_data_model_v1.md` | `base` | KB 数据模型规范，属于长期通用结构约束。 |
| `Scripts/query.py` | `base` | 当前稳定的查询主入口，属于跨小说通用脚本能力。 |
| `Scripts/paths.py` | `base` | 当前关键通用路径收口能力脚本，服务跨小说目录与路径解析。 |
| `Scripts/chunker.py` | `base` | 通用切块能力脚本，服务所有小说实例化前处理。 |
| `Scripts/build_generation_context.py` | `base` | 通用生成上下文构造能力，属于稳定脚本入口。 |
| `Scripts/generate_from_prompt_lmstudio.py` | `base` | 通用 prompt-file 到 output-file 生成入口，已跨多轮实验复用。 |
| `AI_ROLES.md` | `base` | 项目级 AI 协作与职责分工规范，作用于全项目。 |
| `DECISIONS.md` | `base` | 项目级决策日志，承载当前正式采用的规则与边界。 |
| `PROJECT_MODULES.md` | `base` | 项目模块说明文档，作为项目结构真源之一。 |

## 3. Instantiation Molds

| 路径 | 建议层级 | 简短理由 |
|------|----------|----------|
| `kb/characters/template/` | `instantiation_mold` | 当前模板目录骨架样板（原 `kb/characters/江涵/`，已由人类重命名并泛化，角色名字段替换为 `NULL`）。 |
| `kb/characters/template/main.json` | `instantiation_mold` | 主卡骨架样板，供后续实例化复制使用。 |
| `kb/characters/template/sidecar_relations.json` | `instantiation_mold` | 细关系 sidecar 骨架样板，内容已泛化。 |
| `kb/characters/template/sidecar_open_questions.json` | `instantiation_mold` | 开放问题 sidecar 骨架样板，内容已泛化。 |
| `kb/characters/template/sidecar_notes.md` | `instantiation_mold` | 模板维护说明骨架样板，内容已泛化。 |

备注：`NULL` 是当前人工使用的占位值，不作为本轮必须重构的问题。

## 4. Novel Instance

- `kb/` 下大量具体小说长期实例数据当前允许进入首批提交，仍按 `novel_instance` 理解。
- 这份 v1 盘点不逐项展开全部 `kb/` 实例文件；若涉及首批提交范围，以 `first_commit_whitelist_refresh_v1.md` 为准。

## 5. Experimental

| 路径 | 建议层级 | 简短理由 |
|------|----------|----------|
| `outputs/generation/world_rules_supplement.json` | `experimental` | 当前 round3 前置修正包中的世界规则补充卡，服务实验消费。 |
| `outputs/generation/address_rules_supplement.json` | `experimental` | 当前 round3 前置修正包中的称呼规则补充卡，服务实验消费。 |
| `outputs/generation/character_cards/江涵.character_card.v0.1.json` | `experimental` | 旧生成侧角色卡样板，仍属于实验消费层资产。 |
| `outputs/generation/round3_prefix_v1.txt` | `experimental` | round3 共享 prefix，属于实验消费输入。 |
| `outputs/generation/pilot_prompts/` | `experimental` | round3 pilot prompt 集合，属于实验消费输入。 |
| `outputs/generation/checkpoint_cards/` | `experimental` | round3 checkpoint cards，属于实验消费边界材料。 |
| `outputs/generation/minimal_generation_validation_hard_fact_guardrail_v1.txt` | `experimental` | 旧 A/B guardrail 文本，仍服务于实验链路。 |
| `outputs/ab_round3/` | `experimental` | round3 pilot 输出与日志目录，属于实验运行产物。 |
| `review/round2_lore_failure_diagnosis.md` | `experimental` | 对 round2 失败根因的诊断文档，属于实验分析产物。 |
| `review/round3_pilot_review.md` | `experimental` | round3 pilot 复审记录文件，属于实验评审产物。 |
| `review/round3_pilot_label_table.json` | `experimental` | round3 pilot 标签表，属于实验评审产物。 |
| `review/_pending_delete/` | `experimental` | 当前清理隔离区，服务历史实验与历史日志分流，不属于长期真值资产。 |
| `STATE.json` | `experimental` | 当前项目运行状态文件，随阶段推进持续变化，不是跨小说固定真源。 |
| `CURRENT_STATE.md` | `experimental` | 当前人类可读状态摘要，属于阶段性协作产物。 |
| `NEXT_ACTION.md` | `experimental` | 当前最高优先级动作清单，属于阶段性执行口径。 |

## 6. 待定对象

| 路径 | 当前状态 | 模糊原因 |
|------|----------|----------|
| `universal/specs/character_card_v0_schema.md` | 待定 | 该文件具有 schema 性质，但当前长期主线已转向“主卡 + sidecars”；是否继续作为 `base` 真源，还是仅保留为历史参考，尚未正式定案。 |
| `universal/specs/minimal_lore_break_testset_v0.schema.json` | 待定 | 该文件位于 `universal/specs/`，但其用途更接近特定验证阶段的测试集 schema；是否继续保留在 `base`，还是视为历史实验资产，尚需后续裁定。 |

## 7. 当前归位结论

- 当前 `base` 层已具备规范、协议、稳定脚本能力与项目级协作真源。
- workflow 骨架真源已落在 `universal/specs/staged_engineering_workflow_backbone_v1.md`，其口径高于本盘点文件。
- 当前 `instantiation_mold` 层已有 `kb/characters/template/` 作为模板目录样板（原 `kb/characters/江涵/`，已泛化）。
- 当前 `novel_instance` 层仍主要对应 `kb/` 下的具体小说长期实例数据。
- 当前 round3 相关 prefix、prompt、checkpoint、输出、review 仍应留在 `experimental`，不应误归为 `base` 或 `novel_instance`。
