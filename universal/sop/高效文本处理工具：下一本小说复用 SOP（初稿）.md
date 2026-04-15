asset_layer: base

# 高效文本处理工具：下一本小说复用 SOP（初稿）

> 本文件当前作为 `base` 层 SOP 参考保留；文件名中的“初稿”仅反映历史命名，不单独表示实验层或其他资产层。

一、目的

本 SOP 用于把“高效文本处理工具”项目当前已经验证通过的第一阶段流程，整理成一套可复用于下一本小说的标准操作流程。

本 SOP 服务的不是单次抽取，而是后续长期复用。其目标包括：

1. 稳定产出结构化知识库
2. 保持 query 层可用
3. 为后续续写、改写、交互叙事、风格控制提供干净底座
4. 尽量避免每接入一本新书都重新发明流程

二、适用范围

本 SOP 适用于：

1. 中文长篇小说
2. 以 `.txt` 为主的原始文本输入
3. 需要构建人物、地点、事件、时间等知识库的文本项目
4. 需要后续接 query、续写、改写、RP/交互叙事能力的项目

本 SOP 当前不专门处理：

1. PDF / DOCX 直接抽取
2. 多模态内容
3. 多本书混合成统一世界观库的复杂并库
4. 架构级改造
5. 图数据库接入
6. LiteLLM / Kuzu / Ragas / LangGraph 等后续扩展框架

三、阶段边界补充说明（新增）
   
   本 SOP 当前主要覆盖的是“第一阶段稳定底座复用”，即：
   1. chunk
   2. canon
   3. style
   4. merge
   5. query
   6. 必要时的 section_type 最小审计
   
   这意味着：
   
   1. 通过本 SOP，并不自动等于“续写 / 改写 / 交互叙事已经可用”
   2. 第一阶段通过，只代表结构化知识库与 query 基线可复用
   3. 如项目目标包含 continue_writing / rewrite / RP 等生成能力，则必须进入独立的“生成验证阶段”
   4. 生成验证阶段的重点不再是底座是否存在，而是 lore fidelity、漂移控制、候选信息硬化、局部 OOC、世界规则禁区是否会被模型违背
   
   当前项目经验已经证明：以下信息维度不属于“有了 canon/style/merge 就自然解决”的内容，而是生成阶段需要单独审视的高风险盲区：
   
   1. 家庭结构与人物关系图
   2. 核心世界规则禁区（例如某类角色/设定绝对不能出现）
   3. alias 的使用者语境（谁会这样叫，谁不会）
   4. 双向称呼规则
   5. 关系语域边界（什么称呼/语气绝对不该出现）
   6. 候选信息与硬事实的边界
   7. 场景级禁止补写项
   
   因此，下一本书若目标包含生成，不应把“第一阶段通过”误判成“生成就绪”。

三、当前默认原则

1. 第一阶段主线已经验证完成，后续复用以稳定为先，不再默认做架构级大改。
2. 机器可读状态以 `STATE.json` 为准。
3. 当前任务以 `NEXT_ACTION.md` 为准。
4. 项目决策以 `DECISIONS.md` 为准。
5. 人类快速浏览以 `CURRENT_STATE.md` 为准。
6. 新任务启动时，必须先读：
   * `AI_ROLES.md`
   * `STATE.json`
   * `NEXT_ACTION.md`
   * `DECISIONS.md`
   * `CURRENT_STATE.md`

四、复用时的总流程

下一本小说接入时，按以下顺序推进：

1. 新书接入前检查
2. chunk 切分
3. canon 抽取
4. style 抽取
5. merge 汇总
6. 如进入角色档案包整理，则在 merge 后插入角色模具实例化与首轮角色包整理
7. query 接入与 smoke test
8. 必要时做 section_type 分层审计
9. 归档、checkpoint、状态写回

五、新书接入前检查

在开始处理新书前，先确认以下事项：

1. 原始文本来源明确，文件路径固定
2. 文本编码可读
3. 当前项目根目录和状态文件无冲突
4. 不把旧书的中间状态误用到新书
5. 当前模型配置已确认
6. 当前是否沿用既有脚本，还是只允许小修补

最低检查项：

1. `STATE.json` 中 active_local_model / active_context_length 是否符合当前运行条件
2. `chunks/`、`outputs/`、`logs/`、`state/` 是否需要清理或隔离
3. 当前新书是否需要单独命名空间或单独目录策略
4. 当前协作文件是否已同步到真实状态

六、chunk 阶段 SOP

1. 目标

把原始文本稳定切成后续抽取可用的 chunk，并生成对应 `.meta.json`。

2. 默认要求
3. chunk 数应可复核
4. chunk 输入集一旦冻结，不再随意变更
5. 每个 chunk 都应有明确 `chunk_id`
6. chunk 的 `.txt` 与 `.meta.json` 一一对应
7. 注意事项
8. 不要在 chunk 阶段混入知识抽取逻辑
9. 不要为了局部异常轻易重切全书
10. 如果发现极短 chunk、标题页、版权页、附录、说明性文本，不要立刻改主流程，先保留证据
11. chunk 总数一旦进入正式 full run，应记录并冻结
12. 产物
13. `chunks/*.txt`
14. `chunks/*.meta.json`

七、canon 阶段 SOP

1. 目标

抽取偏事实层的信息，服务于后续 merge 和知识库主层。

2. 默认原则
3. canon 是事实抽取，不承担风格模仿职责
4. 不重跑已通过的稳定主线，除非明确发现输入集或脚本逻辑有硬错误
5. canon 的成功与失败应可在状态文件或运行状态源中追踪
6. 注意事项
7. canon 与 style 是双管线，不回退成单脚本
8. 不因为 style 的问题反向污染 canon 的 schema
9. canon 的输入计数应与 chunk 冻结集可对账
10. 产物
11. `outputs/canon/*`
12. `state/processed_canon.jsonl`
13. 相关日志与失败记录

八、style 阶段 SOP

1. 目标

抽取叙事风格、语气、表达特征等，服务于后续风格分析与生成控制。

2. 默认原则
3. style 与 canon 分离
4. style 的稳定性问题优先用最小后处理修补，不放宽 schema
5. 不让低质量 style 输出污染 taxonomy
6. backfill 属于例外修补，不应改写主线完成的事实
7. 注意事项
8. style 可存在 backfill / retry / holes 归档
9. style 计数可能和 canon 不同，原因必须在后续文档中解释清楚
10. 极短 chunk、元数据 chunk、说明性 chunk 可能影响 style 可信度，需要谨慎处理
11. 产物
12. `outputs/style/*`
13. `state/processed_style.jsonl`
14. `logs/bad_chunks_style.jsonl` 或其他失败记录
15. backfill 相关归档

九、merge 阶段 SOP

1. 目标

将 canon/style 的有效结果汇总成知识库主产物，并形成 query 可消费的数据层。

2. 默认原则
3. merge 是主线闭环步骤，不在收口阶段轻易重做
4. 第一阶段完成后，`kb/*` 视为稳定产物
5. 旧 `character_index.json` 只保留为 legacy summary，不再作为真源
6. 重点产物
7. `kb/master_kb.json`
8. `kb/character_appearances_v2.jsonl`
9. `kb/character_profiles_v2.json`
10. `kb/character_query_aliases_v2.json`
11. 其他 location / event / relationship 相关索引

九-A、角色模具实例化补充（current draft rule）

1. 适用时机

当项目已经完成 merge，并准备为某个角色建立 `kb/characters/{name}/` 长期角色目录时，应先按当前 draft 口径从 `kb/characters/template/` 实例化角色包，再进入该角色的首轮预处理 / audit。

2. 当前核心 mold 组成件

当前有效 draft 口径下，`kb/characters/template/` 的核心 mold 由以下 4 件组成：

1. `main.json`
2. `sidecar_notes.md`
3. `sidecar_open_questions.json`
4. `sidecar_relations.json`

`sidecar_review.jsonl` 当前**不是**核心 mold 必备件；它更接近实例化后在 audit / review 阶段按需生成的过程性产物。

3. 当前实例化动作链

1. 从 `kb/characters/template/` 复制上述 4 件到 `kb/characters/{name}/`
2. 第一轮立即替换 `main.json.character`
3. 清理历史 JSON 占位写法：正式 JSON 中不再保留 `"TODO"`，仅允许 `"NULL"` 作为当前 draft 口径下的可审计占位
4. 首轮预处理开始后，逐步填充 `generation_data`、`maintenance_data` 与 3 个 sidecar
5. 首轮 audit 发生在预处理初稿之后、生成消费之前；如需要持久发现记录，可在此阶段按需生成 `sidecar_review.jsonl`

4. 当前 draft 占位与字段语义

- `"NULL"`：当前 draft 口径下唯一允许出现在正式 JSON 中的占位值，用于表示“该字段当前尚未完成实例化 / 预处理 / 审阅”。
- `main.json.character`：复制后必须第一轮立即替换，不允许在实例目录中长期保留 `"NULL"`。
- 将在当前轮生成消费中被选入 payload 的 `generation_data` 字段：进入生成消费前不得继续保留 `"NULL"`。
- `scope_anchor`：记录当前角色包的适用范围与验证边界，帮助说明“本卡当前锚定到什么稳定状态”。
- `evidence_pack`：维护侧证据包，用于记录字段与 chunk / 来源证据的对应关系，不直接进入生成 payload。
- `source_artifacts`：维护侧来源清单，用于记录本次角色包整理实际依赖过的文件、索引、查询结果或中间材料。

5. 当前保留的 open design question

1. `evidence_pack` 与 `source_artifacts` 的详细条目 schema 仍可继续迭代。
2. `sidecar_review` 的最终承载形态是否长期保留 JSONL，仍是 to be decided。

十、query 阶段 SOP

1. 目标

让知识库具备最小可用查询能力，并可供人工或后续 AI 使用。

2. 当前稳定基线

人物查询解析顺序固定为：

1. canonical
2. observed aliases
3. query aliases
4. 别名边界
5. observed aliases 来源于 `character_profiles_v2.json`
6. query aliases 来源于 `character_query_aliases_v2.json`
7. query-only 昵称不得强行回写到 observed aliases
8. 查询命中需求与事实层证据不是同一层
9. 当前已确认能力
10. `appearance_samples`
11. `--json` 结构化输出
12. 最小 smoke test
13. query 阶段注意事项
14. 不让 evidence dump 变成新主数据层
15. 不把 query 层的小增强误做成知识库重构
16. query 层优先做低风险、低侵入、可核查增强

十一、section_type 分层标注 SOP

1. 目的

对少数非叙事类 chunk 进行最小分层标注，避免异质文本与 story_scene 混层。

2. 当前定稿原则
3. 只落地 `section_type`
4. 不把 `source_scope` 作为独立字段写入 `meta.json`
5. `source_scope` 由代码层 `SCOPE_MAP` 从 `section_type` 推导
6. 扫描使用纯规则，不调 LLM
7. 不做全量标注
8. 未标注 chunk 默认为 `story_scene`
9. 当前 section_type 枚举
10. `story_scene`
11. `front_matter`
12. `in_universe_document`
13. `setting_exposition`
14. `author_meta`
15. 适用策略
16. 默认大多数 chunk 不标
17. 只对明显异质 chunk 做标注
18. 先扫描生成待审清单
19. 人工确认后再写入
20. 写入前必须备份原 `meta.json`
21. 写入后必须 verify
22. 写入后打 checkpoint
23. 原则性禁止事项
24. 不把所有说明性文本都视为污染
25. 不用 LLM 做大规模自动分类扫描
26. 不因为 section_type 审计而重跑 canon/style/merge
27. 不修改 kb 现有主产物

十二、冻结边界

以下内容默认视为冻结基线，不随意改动：

1. `chunks/` 正式输入集
2. canon full run 主线产物
3. style full run 主线产物
4. merge 主产物
5. `character_appearances_v2.jsonl`
6. `character_profiles_v2.json`
7. query v2 解析顺序
8. observed aliases 与 query aliases 分层语义

允许的小改动类型包括：

1. 低风险脚本增强
2. 查询输出友好化
3. section_type 审计类增量标注
4. 日志、验证、checkpoint、状态写回
5. SOP 和验收清单整理

十三、状态写回规则

每次完成一个明确阶段或 checkpoint 后，应同步更新：

1. `STATE.json`
2. `NEXT_ACTION.md`
3. `CURRENT_STATE.md`
4. `DECISIONS.md`（仅在新增决策时）
5. `CHECKPOINTS.md`（仅在新增 checkpoint 时）

原则：

1. 不靠聊天历史充当状态源
2. 不允许两个执行器同时各自推进同一主任务而不写回状态
3. 当前任务完成后，必须明确写回 `done`；若下一项小增强尚未由人类选定，可以暂时没有新的活跃工程实现任务，但不能把旧任务伪装成仍在进行

十四、checkpoint 规则

在以下情况应考虑打 checkpoint：

1. 样本阶段通过
2. full run 完成
3. backfill 收敛
4. character_index v2 冻结
5. query v2 integration 完成
6. appearance_samples 落地
7. section_type 审计完成

原则：

1. checkpoint 应表示语义冻结点，不只是打包文件
2. 没有清晰验收结果时，不急着打 checkpoint
3. checkpoint 名称必须反映阶段语义

十五、下一本书复用时的推荐顺序

推荐按以下顺序执行：

1. 新书接入与状态初始化
2. chunk
3. canon sample
4. style sample
5. phase2 sample pass
6. full run
7. style backfill
8. merge
9. 如进入角色档案包整理：从 `kb/characters/template/` 复制角色包 core mold，并完成首轮预处理 / audit
10. character/query 层接入
11. query smoke test
12. 必要时做 section_type 审计
13. 收口归档
14. 更新 SOP / 验收清单 / 状态文件

十六、当前不要做

1. 不重跑 canon/style/merge 主线
2. 不继续修旧 `kb/character_index.json`
3. 不把 query alias 提升为 observed alias
4. 不在收口阶段开启架构级大改
5. 不在没有明确收益时接入 LiteLLM / Kuzu / Ragas / LangGraph
6. 不把 section_type 扩张成高耦合重构工程

十七、当前轮收口结果与后续边界

本轮收口已完成以下配套文档与同步工作：

1. 固定验收清单正文
2. 数量对账说明
3. SOP 第一版收口

后续如继续演进，只把以下事项视为可选后续议题，而不是当前待办：

1. 新书目录隔离策略是否需要标准化
2. chunking 阶段是否需要加入 section_type 预标注规则
3. query relationship / location / event 轻量联动的验收边界

十八、一句话收口

本 SOP 的核心目的，不是重新设计这套系统，而是把已经验证通过的稳定流程整理成一套可复用、可续接、可审计的标准做法，使下一本小说接入时优先复用现有基线，而不是回到空白探索。
