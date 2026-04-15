asset_layer: base

# AI 协作角色与切换规则
> 本文件是项目级协作规则，适用于所有参与本项目的 AI 与人工执行者。
> 每次启动新任务前，应优先读取本文件与握手文件。
> workflow / 流程骨架 / `draft_mode` / `finalize_mode` / `task_mode` 的正式口径，以 `universal/specs/staged_engineering_workflow_backbone_v1.md` 为准。

## 适用范围
本文件同时定义两层规则：
1. 执行器层：Claude Code / Codex / GPT / 人类如何分工与交接
2. Claude 模型层：Claude Sonnet 与 Claude Opus 在什么情况下切换

## 角色分工
- Claude Code：默认主执行器，负责结构搭建、文档与规范文件更新、脚本维护、运行与审计辅助。
- Codex：备用执行器，适合短链路落地、目录结构整理、模板骨架、状态同步、迁移辅助与运行产物收集。
- GPT：偏审查、复核、对比与结构性反馈，不默认承担主实现。
- 人类：最终决策者，负责确认边界、批准规范与采纳候选更新。

## 当前生成侧主线
- 当前生成侧主线不是“继续补更多规则”，而是证据驱动角色建模。
- 当前生成侧相关材料可分为三类承载对象：
  1. 主卡：长期角色资产主脑，长期落点在 `kb/characters/<角色>/main.json`
  2. sidecars：维护、审查、细关系、开放问题等从属资产
  3. 实验消费层：当前阶段的 prompt / checkpoint / pilot 产物，用于实验消费，不等于终局资产结构
- 这里描述的是生成侧承载分工，不是项目资产层新增第五层；正式资产层仍只有 `base`、`instantiation_mold`、`novel_instance`、`experimental` 四层。
- 主卡内部固定分为：
  - `generation_data`
  - `maintenance_data`

## AI 在当前阶段的职责口径
- 预处理型 AI：负责从原文、旧卡、规则材料、实验结果中提出候选更新，但不直接把候选写成主卡真值。
- 审核型 AI：负责判断候选应进入主卡、sidecar，还是继续留在开放问题区；重点审查证据强度、边界与可维护性。
- 生成型 AI：只消费整理后的 generation payload，不直接吃维护区与 sidecars 原文，也不直接消费审计笔记。
- Codex / Claude Code：当前阶段更偏结构搭建、规范文件、审计与迁移辅助，而不是把工作重心放在 round3 prompt / pilot 本身。

## 当前执行优先级
1. 先证据
2. 再主卡
3. 再 sidecars 与审查结果
4. 再 generation payload 组装
5. 最后才是 prompt 层微调

## 当前明确不做
- 不把 AI 分工继续主要写成“谁负责 round3 prompt / pilot”
- 不把 `physical_appearance` 引入当前主卡必填结构
- 不扩成大型规则地狱
- 不引入 graph / checker / planner / 多智能体 / XML 强隔离等架构升级
- 不把 role play 拉回当前主线

## 执行器切换规则
- 默认优先使用 Claude Code。
- 当 Claude Code 当前不可继续稳定执行，且任务局部、明确、低歧义时，可切换到 Codex。
- 若任务涉及根因不清的系统性诊断、需要比较多个中长期方案、或需要从大量结果中找规律，应建议切到 Claude Opus。

## 双重受限时的降级策略
若 Claude Code 和 Codex 都不适合继续推进，则只做低消耗工作：
- 更新 `STATE.json`
- 更新 `CURRENT_STATE.md`
- 更新 `NEXT_ACTION.md`
- 必要时追加 `DECISIONS.md`
- 拆小任务、收口边界、准备下一轮最小执行指令

（注意：`STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md` 已被 `.gitignore` 排除，不在 Git 骨架中；git clone 后不存在，本地可在 `alpha_test_stage/` 找到。）

## 协作入口文件
所有执行器在新任务开始前应优先读取：
1. `PROJECT_READING_ORDER.md`
2. `universal/specs/project_asset_layering_and_novel_bootstrap_v1.md`
3. `universal/specs/staged_engineering_workflow_backbone_v1.md`
4. `ASSET_SOURCE_MAP.md`
5. `PROJECT_MODULES.md`
6. 再按 `PROJECT_READING_ORDER.md` 进入当前任务相关文件

如文件之间存在冲突：
- 机器可读状态以 `STATE.json` 为准
- 项目决策以 `DECISIONS.md` 为准
- 当前主任务以 `NEXT_ACTION.md` 为准
- 人类快速摘要以 `CURRENT_STATE.md` 为准

（注意：`STATE.json`、`CURRENT_STATE.md`、`NEXT_ACTION.md` 已被 `.gitignore` 排除，不在 Git 骨架中；git clone 后不存在，本地可在 `alpha_test_stage/` 找到。）
