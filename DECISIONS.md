asset_layer: base

# 已确认决策

## 格式说明

- 每条决策包含：决策内容 / 原因 / 明确不做什么

---

## D001 - 采用 4+1 协作文档方案

- 决策：项目协作层采用以下 5 个文件：
  - `AI_ROLES.md`
  - `STATE.json`
  - `NEXT_ACTION.md`
  - `DECISIONS.md`
  - `CURRENT_STATE.md`
- 原因：既要保留项目级元规则，也要有机器可读状态源和显式任务入口。
- 不做：不把长期协作规则只留在聊天上下文里。

## D002 - STATE.json 作为机器可读主状态源

- 决策：项目阶段、脚本状态、模型配置、主任务等机器可读状态，以 `STATE.json` 为准。
- 原因：便于自动化、跨模型接力和续接。
- 不做：不让脚本依赖解析 `CURRENT_STATE.md` 的自然语言内容。

## D003 - CURRENT_STATE.md 只做人类快速浏览

- 决策：`CURRENT_STATE.md` 只保留人类快速查看当前真实基线所需的信息。
- 原因：避免退化成长篇进度报告。
- 不做：不让它承担精确真值职责。

## D004 - extract 拆分为 canon / style 双管线

- 决策：保留 `extract_canon.py` 与 `extract_style.py` 双管线，不回退到单一 `extract.py`。
- 原因：canon 与 style 的目标、schema、质量问题不同，拆分后更稳。
- 不做：不把二者重新揉回单脚本。

## D005 - style 管道接受最小后处理修补，不放宽 schema

- 决策：style 的稳定性问题优先在脚本侧做最小修补，不通过放宽 schema 吸收漂移输出。
- 原因：能把质量问题关在局部，不污染 taxonomy。
- 不做：不把 schema 扩成宽松兜底词表。

## D006 - 旧 character_index.json 视为 legacy

- 决策：`kb/character_index.json` 只保留为 legacy summary，不再作为 v2 真源。
- 原因：其 actions/emotions 平行数组和 alias 未归一结构不适合继续演进。
- 不做：不再修补旧 index 作为主线方案。

## D007 - observed aliases 与 query aliases 严格分层

- 决策：
  - `character_profiles_v2.json` 中的 `aliases` 只表示 observed aliases
  - `character_query_aliases_v2.json` 只用于 query-time 命中
- 原因：查询命中需求与事实层证据不是同一层。
- 不做：不把 query-only 昵称强行回写到 observed aliases。

## D008 - alias 优先级固定

- 决策：alias 合并优先级固定为：
  - `manual_blocklist > manual_confirmed > alias_map_auto`
- 原因：误合并代价远高于漏合并。
- 不做：不让自动候选覆盖人工阻断或人工确认。

## D009 - 第一阶段完成后不再进行架构级大改

- 决策：第一阶段完成后，主线进入收口归档与复用 SOP 整理，不再进行架构级大改。
- 原因：canon/style/merge/query 主链已经跑通，继续大改只会提高回归风险。
- 不做：不重跑 canon/style/merge 主线；不再重新设计主数据流。

## D010 - 人物查询以 v2 数据为准

- 决策：人物查询主路径以 v2 为准：
  1. canonical
  2. observed_alias
  3. query_alias
- 原因：v2 的 profile 与 alias 分层已经可用且经过验证。
- 不做：不再以旧 `character_index.json` 作为人物查询真源。

## D011 - query 证据层以 appearance 抽样方式暴露

- 决策：`query.py` 的人物查询可附带少量 `appearance_samples` 作为证据抽样。
- 原因：这样可以让 query 从“可用”进入“可核查”，同时保持输出轻量。
- 不做：不一次性输出全部 appearances；不把 evidence dump 变成新的主数据层。

## D012 - 小增强优先选择低风险、低侵入、可核查方向

- 决策：第一阶段之后的功能推进，只做低风险、低侵入、可核查的小增强。
- 原因：当前更重要的是稳态、可续接与复用性。
- 不做：不在收口阶段开启新的高耦合重构。

## D013 - section_type 分层标注作为最小审计机制

- 决策：在 chunks/*.meta.json 中增加可选字段 `section_type`，用于标注非叙事类 chunk。
- 枚举值：`story_scene`（默认）/ `front_matter` / `in_universe_document` / `setting_exposition` / `author_meta`
- 落地方式：sidecar 标注，不改主 schema，不重跑 pipeline，不修改 kb/ 已有文件。
- source_scope 不作为独立字段写入 meta.json，改为代码层映射（SCOPE_MAP）。
- 原因：知识库缺少文本类型维度，导致异质内容（附录、设定说明等）与叙事场景混层，影响 appearance 统计与 style 分析的可信度。
- 不做：不全量标注；不调 LLM 做自动分类；不重跑 canon/style/merge。
- 审阅来源：Claude Opus 4.6 独立审阅确认。

## D014 - query 默认人类可读输出做展示层友好化增强

- 决策：允许对 `query.py` 的默认人类可读输出做低风险展示层增强，让人物查询结果与 appearance 样本更易读、更易核查。
- 保持：
  - 人物解析顺序仍固定为 `canonical -> observed_alias -> query_alias`
  - `observed aliases` 与 `query aliases` 继续严格分层
  - `--json` 既有字段合同保持不变
- 允许：
  - 只在默认文本输出层重排字段与分组
  - 若 chunk `meta.json` 中已有非默认 `section_type`，仅作为 appearance 样本展示标签出现
- 原因：query v2 主路径已经可用，当前更需要提升人工核查与日常使用体验，而不是继续改动主查询流程。
- 不做：不改 evidence 选取逻辑；不把 `section_type` 变成新的查询过滤系统；不扩成 relationship / location / event 联动；不把 query-only alias 伪装成 observed aliases。

## D015 - query 首版轻量联动只做 relationship/location 候选展示

- 决策：允许在人物查询命中后，于默认文本输出末尾追加 relationship / location 的轻量候选区块。
- 保持：
  - 人物解析顺序仍固定为 `canonical -> observed_alias -> query_alias`
  - `observed aliases` 与 `query aliases` 的分层语义保持不变
  - `--json` 既有字段合同保持不变
  - `section_type` 仅作为证据展示标签出现
- 首版只做：
  - relationship 候选
  - location 候选
- 细化规则：
  - relationship 按 `related_person` 聚合去重后再排序
  - location 以人物 appearance chunk 集与 location `chunks` 的最低风险共现聚合为准
  - event 暂不实现
- 原因：relationship 索引已具备可读的人物对与互动摘要，location 也能用现有 `location_name -> {count, chunks}` 结构做低风险共现提示；继续把 event 硬挂到默认输出会明显放大噪音。
- 不做：不扩成新的查询系统；不把候选共现写成高置信事实；不改 kb 结构；不重跑 canon/style/merge；不把 `section_type` 变成逻辑控制项。



## D016 - 在冻结事实底座之上新增作者协作协议层

- 决策：在已冻结的 KB / query / generation context builder 之上，允许新增一个“作者协作协议层（authoring protocol layer）”，用于承载人类确认后的创作意图、剧情锚点、风格偏移和 lore 冲突处理策略，并作为续写 / 改写生成链的上游输入。
- 保持：
  - 冻结事实底座不变：`kb/*` 继续作为第一阶段冻结产物，`query.py` 主路径与真值源不变，`build_generation_context.py` 继续作为最小下游消费框架
  - 人物解析顺序仍固定为 `canonical -> observed_alias -> query_alias`
  - `observed aliases` 与 `query aliases` 继续严格分层
  - `--json` 既有字段合同保持不变
  - relationship / location 当前仍只视为候选展示，不升格为高置信事实系统
  - event 仍暂未实现
- 允许：
  - 在 generation context builder 之前增加轻量 authoring 输入层
  - 该层可以承载 `creative_intent`、`current_plot_anchor`、`target_style_guidance`、`lore_conflict_policy`
  - 该层可以服务于续写、改写、规划式生成实验与最小一致性检查前置条件
- 原因：
  - 当前项目主线已经从“搭底座”转为“把续写 / 改写做稳”
  - 现有 KB / query 已足以作为冻结事实底座
  - 下一阶段更需要补的是“作者意图与事实约束之间的协作协议”，而不是重写底层流水线
- 不做：
  - 不把该协议层定义为 RP 系统
  - 不实现多轮状态记忆、RP 状态机、RP 专用 CLI / UI
  - 不重写 query 主路径
  - 不重构 KB
  - 不把 exploration 分支的结果直接写回冻结 `kb/`
  - 不把 relationship / location 候选当作 lore gate
  - 不开启架构级大改



## D017 - 创作意图与剧情锚点写入 STATE.json 的 authoring_state，而不是写入 DECISIONS.md 或冻结 KB

- 决策：对卷 / 章级别的创作意图、剧情锚点、风格偏移与 lore 冲突策略，采用 `STATE.json.authoring_state` 作为机器可读承载层；`DECISIONS.md` 继续只记录项目级正式决策，冻结 `kb/` 继续只承载第一阶段 canon 底座。
- 保持：
  - `STATE.json` 继续作为机器可读主状态源
  - `DECISIONS.md` 继续记录项目级规则、边界与正式决策
  - `CURRENT_STATE.md` 继续只做人类快速浏览
  - `kb/*` 继续作为冻结事实底座，不直接吸收探索性剧情或风格实验结果
- 允许：
  - 在 `STATE.json` 中新增 `authoring_state`
  - 仅写入“经人类确认”的创作状态，例如 `creative_intent`、`current_plot_anchor`、`target_style_guidance`、`lore_conflict_policy`、`approved_branch_id`
  - 将该状态作为后续生成实验、A/B 测试或一致性检查的上游输入
- 原因：
  - 章节级创作意图不是项目级决策，不适合写进 `DECISIONS.md`
  - 探索性剧情分支不是冻结 canon，不适合直接写入 `kb/`
  - `STATE.json` 本来就是机器可读主状态源，最适合承载可续接、可消费、可覆盖的 authoring 状态
- 不做：
  - 不把未确认分支写入 `authoring_state`
  - 不把 authoring_state 误当项目级长期决策
  - 不把 exploration 结果直接升格为 canon
  - 不把 query 候选联动结果自动写成 plot anchor
  - 不把 `creative_intent`、`current_plot_anchor` 之类字段平铺到 `STATE.json` 根层

## D018 - continue_writing 当前最有效的改进来源是微场景锚定，而不是继续堆通用守则

- 决策：round2 之后，continue_writing 的优先优化方向确定为“微场景锚定 / 不可绕开样本设计”，而不是继续向 prompt 顶部叠加更长的通用守则。
- 原因：
  - round1 已暴露：若样本只提出抽象问题，模型可以通过回避目标 pair / 目标场景来规避测试点
  - round2 已确认：把目标人物、目标称呼和目标互动压进同一拍短场景后，测试点命中率显著提高
  - B guardrail 有增益，但不能替代能触发压力点的样本设计
- 不做：
  - 不把“守则更长”误当成主改进方向
  - 不把 continue_writing 的核心问题重新定义为基础设施不足
  - 不回头扩写通用 prompt 系统来掩盖样本设计问题

## D019 - lore fidelity 采用硬 lore / 软 lore / 开放 lore 三层理解与约束

- 决策：从 round3 起，lore fidelity 不再笼统处理，而是按三层区分：
  - 硬 lore：不可违背的已确认事实，如人物分离、canonical 归属、明确身份约束
  - 软 lore：应尽量贴合但允许轻微弹性的行为、语气、关系张力与局部表达
  - 开放 lore：知识库未封死、允许在边界内自由续写的留白区域
- 原因：
  - 当前问题已经从“会不会命中测试点”转为“命中后是否发生漂移”
  - 若不分层，会把硬事实错误、候选信息硬化、局部 OOC 和正常创作留白混成一类，导致评估失真
  - 分层后更容易判断是“硬违规”还是“软偏移”，也更适合最小验证
- 不做：
  - 不把所有一致性问题都按同一严重度处理
  - 不把开放 lore 区域误判成必须冻结的事实层
  - 不把软 lore 偏移直接等同于硬 lore 违例

## D020 - round3 起优先采用 Checkpoint 卡写法约束 qwen/qwen3-8b，而不是只用开放式禁止句

- 决策：从 round3 起，针对 `qwen/qwen3-8b` 的 continue_writing 约束，优先采用“闭合白名单 + 知识地图 + 禁止动作清单”的 Checkpoint 卡写法，而不是只依赖开放式禁止句。
- Checkpoint 卡的最小核心包括：
  - `allowed_characters`
  - `time_window`
  - `action_chain_whitelist`
  - `knowledge_map`
  - `allowed_information_types`
  - `forbidden_actions`
- 原因：
  - 当前模型并不总是违反“不要乱加设定”的字面禁令，但会在开放空间里自然外扩
  - 把场景闭合、把允许动作写成白名单、把知识边界写清楚，更适合压制知识库外扩写、候选信息硬化与局部 OOC
  - 这属于样本卡层的最小约束增强，不需要改基础设施
- 不做：
  - 不为此扩写新的 planner、checker 或 graph layer
  - 不把 Checkpoint 卡误写成新的工程级配置系统
  - 不把开放式禁止句完全移除，而是把它降为补充约束

## D021 - 生成侧主线从规则扩表转向证据驱动角色建模

- 决策：当前生成侧主线从“继续扩规则表”转为“证据驱动角色建模”。
- 当前三层分工固定为：
  - Character Card：生成侧主脑
  - World Rule Card：少量世界红线
  - Checkpoint Card：场景级边界
- 原因：
  - round2 诊断已表明，问题不只是规则数量不足，而是角色进入感、场景边界与知识边界没有被分层承载
  - 角色卡更适合承载行为、语域、关系默认值
  - 世界规则卡与场景卡只保留必要红线，能降低规则堆砌风险
- 不做：
  - 不再把“继续扩 WR-xxx 规则表”写成当前主线
  - 不把 prompt 顶部规则块继续当作主脑

## D022 - ConStory-Bench 在当前阶段降级为远期参考，而不接入 round3 主评审

- 决策：不把 ConStory-Bench 的 19 子类接入当前 round3 主评审。
- 当前 round3 直接使用项目内已稳定形成的 8 个诊断标签做复审。
- 原因：
  - 当前目标是先把项目内真实错误类型稳定压住，而不是引入更大的外部评审框架
  - 现有 8 标签已经能覆盖当前 pilot 的主要错误模式
- 不做：
  - 不把 ConStory 子类写入当前主评审流程
  - ConStory 仅保留为远期 judge / checker 参考

## D023 - Gemini 强隔离 / XML 路线不进入当前主线

- 决策：不采用 XML 强隔离 / 类安全拒绝架构作为当前生成主线，也不为此改 builder 主体。
- 原因：
  - 当前问题不是 prompt 封装形式本身，而是证据、角色、场景边界的分层承载
  - 此类路线会引入新的提示结构与额外复杂度，不符合当前最小验证目标
- 不做：
  - 不把 XML 强隔离写回当前计划
  - 不为此改 `build_generation_context.py` 主体

## D024 - DeepSeek 的重型基础设施路线延后

- 决策：图数据库 / GraphRAG / 多智能体 / checker / planner 不进入当前阶段。
- 原因：
  - 当前阶段仍是最小生成验证，不是基础设施升级
  - 当前阻塞点可以通过角色卡、世界规则卡和场景卡的最小组合继续推进
- 不做：
  - 不把图数据库 / GraphRAG / checker / planner 写成当前待办
  - 不为当前 pilot 引入新执行器编排系统

## D025 - physical_appearance 当前不进入角色卡主 schema

- 决策：`physical_appearance` 当前不进入角色卡主 schema。
- 原因：
  - 当前 round3 更优先解决身份红线、称呼语域、关系边界、候选硬化与 OOC
  - 外观字段会消耗结构与证据预算，但不是当前 pilot 的关键阻塞点
- 不做：
  - 仅把该项保留为后续可选扩展接口
  - 不占用当前工程资源推动其正式化

## D026 - 江涵角色卡 v0.1 作为首张样板服务 round3 pilot，而不是当前无限精修对象

- 决策：`outputs/generation/character_cards/江涵.character_card.v0.1.json` 作为首张样板，用于服务当前 round3 pilot。
- 原因：
  - 它已经足以承担“角色卡主脑”的样板作用
  - 当前更重要的是把它与世界规则卡、场景卡一起落到 pilot，而不是继续无限精修单卡
- 不做：
  - 不把“继续修江涵卡”写成当前主任务
  - 不据此立即铺开全书角色卡


## D027 - 长期角色资产采用主卡 + sidecars

- 决策：长期角色资产采用“主卡 + sidecars”结构，而不是继续把角色约束拆散在单一实验卡或补充规则文件里。
- 原因：主卡便于承载稳定生成所需的薄核心信息，sidecars 更适合承载细关系、开放问题、维护与审查记录。
- 不做：不把所有角色信息继续堆进单一大卡；不把 round3 实验消费材料直接等同于长期角色资产。

## D028 - 主卡内部采用 generation_data / maintenance_data 分离

- 决策：主卡内部固定区分 `generation_data` 与 `maintenance_data`。
- 原因：生成消费与维护审查的职责不同，分离后更利于稳定 payload、复审与后续迁移。
- 不做：不让生成模型直接消费维护区原文；不把证据包、迁移说明与生成约束混放在同一层。

## D029 - 长期角色资产路径采用 kb/characters/

- 决策：长期角色资产统一落在 `kb/characters/` 下，以角色目录承载主卡与 sidecars。
- 原因：该路径更符合长期维护、按角色扩展与存储态管理需求。
- 不做：不继续把长期角色资产只放在 `outputs/generation/`；不把实验消费层目录当成长期角色库。

## D030 - relationship_stance 在主卡中只保留薄摘要，细关系外移

- 决策：`relationship_stance` 在主卡中只保留薄摘要，细关系、待定关系与审查痕迹外移到 sidecars。
- 原因：主卡应保持可消费、可控、低噪声；细关系更适合放在维护侧做逐步沉淀。
- 不做：不把完整细关系网、开放争议与长审查记录直接塞进主卡生成区。

## D031 - 当前优先级为续写/改写，role play 后置

- 决策：项目当前仍以 `continue_writing / rewrite` 为最高优先级，`role play / 互动式 use case` 后置。
- 原因：续写/改写的稳定性仍是当前基础能力目标，role play 必须在这条主线基本稳定后再推进。
- 不做：不把 RP 拉回当前主线；不为 RP 提前引入新系统或新架构。

## D032 - round3 材料属于当前阶段实验消费层，不等于终局资产结构

- 决策：round3 的 prefix、prompt、checkpoint、pilot 输出归类为当前阶段实验消费层资产。
- 原因：这些材料服务于验证与对照，不应直接定义长期角色资产结构。
- 不做：不把 round3 材料表述为最终主架构；不以其实验分层替代长期主卡 + sidecars 方案。
