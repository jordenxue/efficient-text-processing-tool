asset_layer: experimental

# Git 首批骨架白名单与准入审计 v1

> 本文件服务于“Git 首批只上传项目骨架”的当前口径。
> 本文件不是长期不变的法律文本，而是当前这一轮提交范围的显式白名单与准入审计结果。
> 本文件保留为 v1 审计快照；若与后续首批提交刷新清单冲突，以 `first_commit_whitelist_refresh_v1.md` 为准。

## v1 后续补记（2026-04-14）

- `prompts/` 当前允许进入首批 Git 骨架提交，且 `prompts/*.txt` 已补 `asset_layer: base`。
- `schema.json` 当前保留在主项目，并纳入首批提交范围；定位仍是 legacy generic schema / compatibility entry。
- `kb/characters/template/` 应按 `instantiation_mold` 模板目录理解；旧的 `kb/characters/江涵/` 路径引用已失效。

## 1. 白名单原则

- 白名单只接纳“项目骨架”对象，不接纳测试文本本体、实验运行产物、阶段性运行态文件。
- 白名单必须显式列出，不采用“剩下的都算”。
- 非脚本文件的准入条件之一是：具备当前项目认可的合法层级 Tag。
- 草案、候选、阶段分析、历史实验只是文档地位，不构成第五层资产。

## 2. 当前显式白名单

### 2.1 `universal/specs/` 下已准入的正式规范

- `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
- `universal/specs/character_record_preprocess_spec_v1.md`
- `universal/specs/character_record_audit_spec_v1.md`
- `universal/specs/character_record_generation_payload_spec_v1.md`
- `universal/specs/chunking_protocol_v1.md`
- `universal/specs/generation_context_protocol_v1.md`
- `universal/specs/eight_label_review_protocol_v1.md`
- `universal/specs/kb_data_model_v1.md`

### 2.2 `Scripts/` 下当前建议纳入的稳定通用脚本

- `Scripts/chunker.py`
- `Scripts/extract_canon.py`
- `Scripts/extract_style.py`
- `Scripts/merge.py`
- `Scripts/generate_alias_map.py`
- `Scripts/build_character_query_aliases.py`
- `Scripts/rebuild_character_index.py`
- `Scripts/query.py`
- `Scripts/build_generation_context.py`
- `Scripts/generate_from_prompt_lmstudio.py`
- `Scripts/paths.py`
- `Scripts/apply_section_types.py`
- `Scripts/scan_section_types.py`
- `Scripts/verify_section_types.py`

### 2.3 `schema/` 下当前已准入的 schema

- `schema/canon_schema.json`
- `schema/style_schema.json`

### 2.4 根目录入口 / 结构说明文件

- `AI_ROLES.md`
- `DECISIONS.md`
- `README.md`
- `PROJECT_READING_ORDER.md`
- `ASSET_SOURCE_MAP.md`
- `PROJECT_MODULES.md`
- `schema.json`
- `.gitignore`

### 2.5 长期骨架样板

- `kb/characters/template/main.json`
- `kb/characters/template/sidecar_relations.json`
- `kb/characters/template/sidecar_open_questions.json`
- `kb/characters/template/sidecar_notes.md`

备注：原 `kb/characters/江涵/` 已由人类手动重命名为 `kb/characters/template/`，内容已泛化（角色名字段替换为 `NULL`）。

### 2.6 `prompts/` 下当前提示词资源文件

- `prompts/extract_canon_prompt.txt`
- `prompts/extract_prompt.txt`
- `prompts/extract_style_prompt.txt`

备注：`prompts/` 已允许进入首批 Git 骨架提交；`prompts/*.txt` 已补 `asset_layer: base`，当前按跨小说可复用提示词资源处理。

### 2.7 少量必要的 `review/` 结构说明与分析文件

- `review/README.md`
- `review/project_asset_inventory_layering_v1.md`
- `review/tag_application_guidelines_v1.md`
- `review/stable_core_instantiation_mold_v0_1_draft.md`
- `review/conditional_generation_guidance_container_v0_1_draft.md`
- `review/project_structure_refactor_input_v1.md`
- `review/git_preflight_low_risk_cleanup_plan_v1.md`
- `review/git_skeleton_whitelist_and_admission_audit_v1.md`
- `review/git_skeleton_isolation_migration_dry_run_v1.md`
- `review/alpha_test_stage_reentry_guide_v1.md`

### 2.8 少量必要的目录说明文件

- `outputs/README.md`

### 2.9 `universal/sop/` 下当前已准入的 base 参考文件

- `universal/sop/固定验收清单（初稿）.md`
- `universal/sop/高效文本处理工具：下一本小说复用 SOP（初稿）.md`
- `universal/sop/新小说启动资产清单_v1.md`

## 3. 准入审计结论

### 3.1 已通过准入审计

| 对象类别 | 骨架属性 | 口径状态 | Tag 状态 | 结论 |
|------|------|------|------|------|
| `universal/specs/` 中本轮列出的 8 份正式规范 | 是 | 当前口径正确 | 已补 `asset_layer: base` | 准入 |
| 本轮列出的稳定通用脚本 | 是 | 当前口径可接受 | 脚本不要求 Tag | 准入 |
| `schema/canon_schema.json`、`schema/style_schema.json` | 是 | 当前口径正确 | 已补 `_asset_layer: "base"` | 准入 |
| `AI_ROLES.md`、`DECISIONS.md`、`README.md` | 是 | 当前口径已修正 | 已补 `asset_layer: base` | 准入 |
| `PROJECT_READING_ORDER.md`、`ASSET_SOURCE_MAP.md`、`PROJECT_MODULES.md` | 是 | 当前口径正确 | 已补 `asset_layer: base` | 准入 |
| `kb/characters/template/` 中 4 份骨架文件（原 `kb/characters/江涵/`，已由人类重命名并泛化） | 是 | 当前定位明确 | JSON / Markdown Tag 已补齐 | 准入 |
| `prompts/` 下 3 份提示词资源文件 | 是 | 已允许进入首批 Git 骨架提交 | 已补 `asset_layer: base` | 准入 |
| 本轮列出的 `review/` 结构说明与分析文件 | 是 | 当前定位清晰 | 已补 `asset_layer: experimental` | 准入 |
| `outputs/README.md` | 是 | 当前定位清晰 | 已补 `asset_layer: experimental` | 准入 |
| `universal/sop/` 下本轮列出的 3 份参考文件 | 是 | 旧口径已修正到当前四层框架 | 已补 `asset_layer: base` | 准入 |

### 3.2 审计发现的问题对象：建议先修正后再决定是否纳入

| 路径 | 问题 | 建议 |
|------|------|------|
| `universal/specs/character_card_v0_schema.md` | 缺少合法层级 Tag，且表述仍明显绑定旧 round3 阶段 | 暂缓纳入 |
| `universal/specs/minimal_lore_break_testset_v0.schema.json` | 缺少 `_asset_layer`，且更偏历史测试集 schema | 暂缓纳入 |
| ~~`kb/characters/江涵/sidecar_review.jsonl`~~ | 已随隔离进入 `alpha_test_stage/`，不再属于主项目 | 已解决，无需处理 |

### 3.3 额外核查点

- `outputs/generation/pilot_prompts/*.prompt.txt` 当前未补 Tag，且本身属于实验输入，不纳入首批骨架白名单。
- `prompts/` 曾被误迁入 `alpha_test_stage/`，现已按人类明确意图迁回主项目；**已允许进入首批 Git 骨架白名单**（见 2.6 节）；`prompts/*.txt` 现已补齐 `asset_layer: base`。
- `schema.json` 保留在主项目根目录，定位为 legacy generic schema；当前主用 schema 位于 `schema/` 目录（`canon_schema.json`、`style_schema.json`）。`schema.json` 当前纳入首批骨架白名单。
- `STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md` 属于运行态状态文件，不纳入首批骨架白名单（已被 `.gitignore` 排除）。
- `kb/characters/江涵/sidecar_review.jsonl` 已随隔离进入 `alpha_test_stage/`，原 3.2 节的”待人工确认”问题已自然解决。
- 本轮未发现白名单内对象仍残留”第五层资产”写法。
- 本轮已把 `AI_ROLES.md`、`DECISIONS.md`、`README.md` 与 `universal/sop/` 下 3 份高价值文件从”阻塞项”修正为”可纳入白名单”。

## 4. 当前白名单结论

- 当前可以直接作为首批 Git 骨架提交候选的，是本文件第 2 节列出的对象。
- `outputs/`、运行态状态文件、实验 prompt / 输出、待删隔离区与历史清理材料，不属于当前骨架白名单。
