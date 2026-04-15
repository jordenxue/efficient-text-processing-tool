asset_layer: experimental

# 稳定核心实例模具 v0.1 抽取草案

> 本文件用于从当前项目中抽取“每本小说启动时都应复制或生成的稳定骨架”。
> 本文件是模具抽取草案，不是正式 `instantiation_mold` 真源；当前仅服务后续模具定稿与项目结构重构。

## 1. 依据

- `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
- `review/project_asset_inventory_layering_v1.md`
- `review/tag_application_guidelines_v1.md`
- `kb/characters/江涵/` 下现有主卡 + sidecars 骨架

## 2. 本轮只抽什么

- 只抽跨小说可复用的**结构骨架**。
- 只抽当前已相对稳定的**存在性骨架**与**挂接位**。
- 不冻结具体小说内容。
- 不冻结仍明显带有 round3 实验性质的生成细节。

## 3. 候选核心模具对象

### 3.1 新小说独立工作区总文件夹骨架

推荐作为核心模具抽取的稳定目录位：

```text
<novel_workspace>/
├─ raw/
├─ chunks/
├─ state/
├─ logs/
├─ review/
├─ outputs/
│  ├─ canon/
│  ├─ style/
│  └─ generation/
└─ kb/
   ├─ characters/
   └─ docs/
```

说明：

- 这是一份候选骨架，不代表本项目已按此完成重构。
- `outputs/ab_*`、pilot 专用目录、清理隔离目录等应按需生成，不进入核心模具最小骨架。

### 3.2 角色资产容器骨架

推荐纳入核心模具的稳定对象：

- `kb/characters/`
- `kb/characters/<character_name>/`

说明：

- `kb/characters/` 体现长期角色资产的小说级落点。
- 角色目录本身属于实例层容器，但其“存在性骨架”可以由模具层统一提供。

### 3.3 主卡 + sidecars 的基础存在性骨架

推荐纳入核心模具的角色档案包骨架：

- `main.json`
- `sidecar_relations.json`
- `sidecar_open_questions.json`
- `sidecar_review.jsonl`
- `sidecar_notes.md`

当前仅建议冻结以下稳定层级：

- 主卡有 `generation_data / maintenance_data` 两大区
- sidecars 与主卡分离
- review 记录、开放问题、关系维护与说明文档各自独立挂接

当前不建议冻结：

- `generation_data` 内部更细的 generation-facing 字段簇
- 具体关系字段细则
- 仍可能随后续试填与审核变化的角色字段设计

### 3.4 review / audit / logs 基础挂接位

推荐纳入核心模具的稳定挂接位：

- `review/`
- `logs/`

推荐按“存在性骨架”处理，而不是预置大量阶段性文件。

当前只抽稳定需求：

- review 需要有挂接位，便于放审阅、诊断、盘点与结构分析
- logs 需要有挂接位，便于保留运行日志

当前不纳入核心模具：

- `review/_pending_delete/`
- 具体 round2 / round3 复审文件
- 某一轮实验专属清理或迁移报告

### 3.5 基础底料容器骨架

推荐纳入核心模具的基础底料容器位：

- `raw/`
- `chunks/`
- `state/`
- `outputs/canon/`
- `outputs/style/`

说明：

- 这些目录服务于某本小说专属基础底料与处理中间产物。
- 本轮只冻结“容器位存在”，不冻结其中具体字段、文件名细则或自动化流程。

## 4. 刻意排除在模具之外的内容

- `outputs/generation/` 下 round3 prefix / prompt / checkpoint / guardrail 文件
- `outputs/ab_round3/` 下 pilot 输出与日志
- `review/round2_lore_failure_diagnosis.md`
- `review/round3_pilot_review.md`
- `review/round3_pilot_label_table.json`
- `outputs/generation/world_rules_supplement.json`
- `outputs/generation/address_rules_supplement.json`
- `outputs/generation/character_cards/江涵.character_card.v0.1.json`

排除原因：

- 它们属于实验消费层或阶段性分析材料，不属于跨小说稳定模具。
- 即使其中有可复用经验，也应先被提炼成结构原则，再决定是否进入正式模具。

## 5. 当前抽取结论

本轮可稳定抽出的核心模具对象包括：

1. 新小说独立工作区的基础目录骨架
2. `kb/characters/` 与角色目录的存在性骨架
3. 主卡 + sidecars 的基础存在性骨架
4. `review/` 与 `logs/` 的基础挂接位
5. `raw / chunks / state / outputs/canon / outputs/style` 等基础底料容器位

这些对象可直接作为后续正式 `instantiation_mold` 定稿的输入。
