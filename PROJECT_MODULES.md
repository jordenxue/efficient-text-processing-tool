asset_layer: base

# 项目模块说明

> 文件版本：v1.4（四层资产口径校正版）
> 创建时间：2026-04-13，最后更新：2026-04-14
> 维护者：Claude Code + Codex + 人类协作
> 说明：本文件用于描述仓库当前主要目录/模块的用途与定位。
> 本文件是结构导览，不是正式 `base` 规范真源。

## 读前说明

- 项目资产层始终只有四层：`base`、`instantiation_mold`、`novel_instance`、`experimental`。
- “草案”“候选”“阶段分析”“历史实验”只是文档地位或当前状态，不构成第五层。
- 当前仓库里已经出现了一批 mold 抽取草案，但它们仍是草案，不等于正式 `instantiation_mold` 真源。

## 根目录入口文件

| 文件 | 用途 |
|------|------|
| `PROJECT_READING_ORDER.md` | AI 进仓后的推荐阅读顺序入口。 |
| `ASSET_SOURCE_MAP.md` | 区分正式真源、草案候选、实验参考与运行态状态文件。 |
| `AI_ROLES.md` | AI 协作角色与交接口径。 |
| `DECISIONS.md` | 项目级决策日志。 |
| `PROJECT_MODULES.md` | 当前模块与目录用途导览。 |

## `universal/`

`universal/` 用于承接跨小说复用、且不依赖某本小说具体内容的材料。

### `universal/specs/`

- 当前已落地稳定的 `base` 承载面。
- 适合放正式规范、协议、schema、数据模型与资产分层总则。

### `universal/sop/`

- 当前仓库里已有该目录，但本轮不把它写成“已稳定收口完成的真源区”。
- 当前更合适的口径是：`universal/sop/` 是一个**建议中的 / 待继续收口的 base 承载面**。
- 适合未来承接跨小说 SOP、验收清单、启动流程，但其内容是否全部升级为正式真源，仍需后续逐项确认。

### 路径受限但概念上属于 `base` 的对象

- `Scripts/`
- `prompts/`
- `schema/`
- `schema.json`
- `config.json`

其中：
- `prompts/`、`schema/` 与 `schema.json` 当前允许进入首批 Git 骨架提交。
- `config.json` 虽保留在主项目，但因包含本地运行配置，不进入首批 Git 骨架提交。

这些对象因路径依赖或历史原因暂留原位，但其中相当一部分承担跨小说稳定能力。

## 根目录运行态状态文件

| 文件 | 说明 |
|------|------|
| `STATE.json` | 机器可读的当前执行状态。 |
| `CURRENT_STATE.md` | 人类可读的当前状态摘要。 |
| `NEXT_ACTION.md` | 当前最高优先级动作清单。 |

这些文件用于理解”当前在做什么”，不用于覆盖 `base` 规范、资产分层总则或正式结构边界。
**注意：这三个文件已被 `.gitignore` 排除，不在 Git 骨架中；git clone 后不存在，本地可在 `alpha_test_stage/` 找到。**

## `Scripts/`

当前仍以现有主链脚本为准，不引入新后端：

- `query.py`：核心查询入口
- `build_generation_context.py`：generation context builder
- `generate_from_prompt_lmstudio.py`：prompt-file -> output-file 的现有生成入口
- 其余脚本继续服务于 canon / style / merge / query 既有主线

概念上，这些稳定通用脚本能力更接近 `base`；物理路径暂不调整。

## `kb/`

`kb/` 当前主要承接某本小说的长期结构化知识资产与基础底料。

### `kb/characters/`

- `kb/characters/` 当前同时承接具体小说长期实例资产与模板目录。
- `kb/characters/template/` 当前作为 `instantiation_mold` 骨架样板进入首批提交（原 `kb/characters/江涵/`，已由人类重命名并泛化）。
- `kb/characters/` 下其余长期角色 / 关系 / 侧写资产继续按具体小说实例数据理解，并允许进入首批提交。

### 其他 `kb/` 对象

- `character_appearances_v2.jsonl`
- `character_profiles_v2.json`
- `character_query_aliases_v2.json`
- relationship / location / event 等索引

这些对象当前更接近某本小说专属的长期实例资产或其支撑底料，而不是 `experimental`。

## `raw/`、`chunks/`、`state/`、`logs/`

- 这些目录当前承接某本小说的原始输入、处理中间产物、运行状态与日志。
- 它们更接近小说工作区内部的基础容器位。
- 后续正式 `instantiation_mold` 应考虑为这些目录提供存在性骨架，但本轮不做目录迁移。
- **当前状态：这些目录的主体内容已迁移至 `alpha_test_stage/`，主项目中不再保留其完整内容；首批 Git 骨架提交不包含这些目录。**

## `outputs/`

`outputs/` 当前应默认理解为 `experimental` 的主要承载面。

### `outputs/generation/`

- 当前承接 round3 prefix、pilot prompts、checkpoint cards、补充卡与旧角色卡样板。
- 这些都是实验消费输入或过渡材料，不等于长期真值或正式 mold 真源。

### `outputs/ab_round3/`

- 承接 round3 pilot 的输出与日志。
- 明确属于实验运行产物。

### `outputs/canon/` 与 `outputs/style/`

- 当前可视为历史位置中的小说专属基础底料 / 中间产物目录。
- 后续应进一步裁清其长期物理落点，但本轮不搬迁、不重跑。

## `review/`

`review/` 当前是阶段性混合区，不是长期规范真源默认承载面。

当前至少混有三类内容：

- 实验复审：如 round2 / round3 的诊断与评审
- 结构分析：如资产归位表、Tag 落地规则、mold 抽取草案、结构重构输入
- 清理 / 隔离 / 审计：如 `_pending_delete/` 与各类清理报告

后续若做结构重构，应优先澄清这些子类型，而不是直接默认 `review/` 是长期稳定层。

## 当前模块边界

- 正式 `base` 真源，优先看 `universal/specs/`。
- 正式 `instantiation_mold` 真源当前尚未落库；现有相关材料仍是草案或候选输入。
- 具体小说长期资产，优先看 `kb/characters/` 与相关 `kb/` 对象。
- round3 与其他阶段实验材料，继续留在 `outputs/` 与 `review/` 的实验区理解。
