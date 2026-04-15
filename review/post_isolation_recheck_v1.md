asset_layer: experimental

# 隔离后复核报告 v1

## 结论

- 当前主项目已经基本收成 Git 骨架区。
- 主体保留内容已以规范、入口、结构说明、稳定脚本、schema 与少量长期骨架样板为主。
- 但主项目中仍有少量边界对象未进入白名单，也未进入本轮隔离；它们需要在下一轮小范围处理或由人类拍板。

## 主项目当前骨架级内容概览

- `universal/`：当前保留的 base 规范与 SOP 参考文件
- `Scripts/`：白名单保留的稳定通用脚本
- `schema/`：当前保留的 schema 文件
- `kb/characters/template/`：保留的模板骨架样板
- 根目录入口/治理文件：`README.md`、`AI_ROLES.md`、`DECISIONS.md`、`PROJECT_READING_ORDER.md`、`ASSET_SOURCE_MAP.md`、`PROJECT_MODULES.md`、`.gitignore`
- `review/`：当前保留的结构说明、治理与分析文件
- `outputs/README.md`：保留的目录说明文件

## `alpha_test_stage/` 当前主要类别概览

- 原文与切块工作数据：`raw/`、`chunks/`
- 运行态状态文件：`STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md`
- 实验输出与生成材料：`outputs/ab_round3/`、`outputs/canon/`、`outputs/generation/`、`outputs/style/`
- 阶段性 review 材料与 `_pending_delete/`
- 暂缓纳入白名单的 schema / JSONL
- 辅助、历史与测试脚本

## 仍留在主项目中的边界对象

| 对象 | 当前观察 | 建议 |
|---|---|---|
| `artifacts/` | 明显为 style holes 相关实验/失败样本集合 | 下轮隔离到 `alpha_test_stage/` |
| `prompts/` | 当前稳定脚本直接依赖的提示词资源；曾被误迁入 `alpha_test_stage/`，现已按人类明确意图迁回主项目 | 允许进入首批 Git 骨架提交；`prompts/*.txt` 已补 `asset_layer: base` |
| `.claude/` | 本地协作/工具状态目录，已被 `.gitignore` 忽略 | 下轮隔离到 `alpha_test_stage/` |
| `CHECKPOINTS.md` | 阶段性 checkpoint 档案，偏运行/历史协作材料，未入白名单 | 下轮隔离到 `alpha_test_stage/` |
| `config.json` | 当前脚本直接依赖，但含本地运行配置与模型/接口信息 | 需人类拍板后决定 |
| `schema.json` | 旧的 legacy schema；当前主保留脚本不再以它为主 | 保留在主项目，并进入首批 Git 骨架提交；定位为 legacy generic schema / compatibility entry |
| `项目资产分层与新小说启动总则（修正版）.txt` | 已被 `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md` 取代 | 下轮隔离到 `alpha_test_stage/` |

## 额外发现

- `review/confirmed_section_types.jsonl` 仍留在主项目中，但它不属于当前白名单，也更像阶段性确认产物。
- 该文件建议纳入下轮小隔离候选。

## 第二轮小隔离建议

建议做第二轮小隔离，但范围保持克制，仅优先处理以下对象：

- `artifacts/`
- `.claude/`
- `CHECKPOINTS.md`
- `项目资产分层与新小说启动总则（修正版）.txt`
- `review/confirmed_section_types.jsonl`

以下对象建议先由人类拍板，再决定是否隔离：

- `config.json`

## 迁回补记

- `prompts/` 曾在一次隔离执行中被误迁入 `alpha_test_stage/`。
- 现已按人类明确意图迁回主项目原位。
- 当前 `prompts/` 保留在主项目中，**已允许进入首批 Git 骨架提交**。
- `prompts/` 曾因设计未稳定而被视为可暂缓补 Tag 的例外；当前 3 个 prompt 文件已补 `asset_layer: base`，不再构成该项阻塞。

## 角色目录更名补记

- `kb/characters/江涵/` 已由人类手动重命名为 `kb/characters/template/`。
- 目录内所有文件的角色名字段已替换为 `NULL`，内容已泛化为通用骨架样板。
- 白名单中所有 `kb/characters/江涵/` 路径引用应理解为 `kb/characters/template/`。
- `kb/characters/江涵/sidecar_review.jsonl` 已随隔离进入 `alpha_test_stage/`，不再属于主项目。

## 白名单口径补记（2026-04-14）

- `prompts/` 当前保留在主项目并允许进入首批 Git 骨架提交；`prompts/*.txt` 已补 `asset_layer: base`。
- `schema.json` 当前保留在主项目，并按 legacy generic schema / compatibility entry 理解；它保留在首批提交范围内，但不是当前主用 schema。
- 旧的 `kb/characters/江涵/` 路径引用应统一理解为 `kb/characters/template/`；该目录当前按 `instantiation_mold` 模板目录理解。
- 本报告仍是隔离后复核快照；首批提交最终边界以后续 `first_commit_whitelist_refresh_v1.md` 为准。

## 复核口径

- 本报告只做隔离后复核，不改白名单原则。
- 本报告不构成新的隔离规则，只服务下一步人工判断与小范围补隔离。
