asset_layer: base

# Generation Context 协议 v1

> 层级：Universal Fixed Asset
> 版本：v1
> 定位：**当前阶段过渡消费协议**（见"协议定位"节）
> 对应脚本：`Scripts/build_generation_context.py`

---

## 一、职责边界

`build_generation_context.py` 是生成层的**最小上下文组装器**。

**做什么：**
- 接受目标角色名 + 生成模式（continue_writing / rewrite）+ 可选原文
- 调用 `query.py` 中的解析函数，从 KB 检索相关事实
- 将检索结果组装为结构化 context JSON + 渲染好的 prompt TXT
- 输出两个文件到 `outputs/generation/`

**不做什么：**
- 不修改 KB
- 不执行模型调用（模型调用由 `generate_from_prompt_lmstudio.py` 负责）
- 不维护多轮对话状态（role-play 系统后置）
- 不做 style 注入（当前为占位，style 管线尚未接入）

---

## 二、输入

| 参数 | 类型 | 说明 |
|------|------|------|
| `character_name` | str | 目标角色名（经 alias 解析）|
| `--mode` | str | `continue_writing`（续写）或 `rewrite`（改写）|
| `--source-text` 或 `--source-file` | str/path | rewrite 模式所需的原始文本 |
| `--appearances` | int | 抽取的 appearance 样本数（默认 3）|
| `--output-dir` | path | 输出目录（默认 `outputs/generation/`）|
| `--prompt-prefix-file` | path | 可选的 prompt 顶部前置文本文件路径 |

---

## 三、输出格式

输出到 `--output-dir` 下的两个文件：

### 3.1 context JSON
`gen_ctx_{character}_{mode}_{timestamp}.json`

关键字段：

| 字段 | 来源 | 说明 |
|------|------|------|
| `character` | KB | 角色 canonical、profiles 摘要、appearance 样本 |
| `relationship_candidates` | relationship_index | 共现聚合，**标注为候选** |
| `location_candidates` | location_index | 共现聚合，**标注为候选** |
| `style_guidance` | 占位 | 当前为空，待 style 管线接入 |
| `task` | 由 mode 决定 | 续写/改写的任务说明 |
| `source_text` | 仅 rewrite 模式 | 待改写的原始文本 |

### 3.2 prompt TXT
`gen_ctx_{character}_{mode}_{timestamp}.txt`

将 context JSON 渲染为模型可直接消费的 prompt 文本。  
若提供了 `--prompt-prefix-file`，则将前置文本注入 prompt 顶部。

---

## 四、关键设计决策

1. **续写和改写共用同一个 context builder**：二者所需事实一致，差异只在 `task` 字段。
2. **relationship / location 只作为候选**：来源是 chunk 共现聚合，非人工验证叙事事实。
3. **不改 query.py 的 `--json` 合同**：generation context 是新消费层，字段语义不同，不强行合并。
4. **alias 解析真值只有一处**：通过 `query.py` 的 `resolve_person_query` 完成，不另起炉灶。

---

## 五、调用链

```
build_generation_context.py
  └── query.py
        ├── resolve_person_query       → canonical 确定
        ├── load_character_profiles_v2 → 人物档案
        ├── load_character_appearance_samples → appearance 样本
        ├── build_relationship_candidates → 关系候选
        └── build_location_candidates  → 地点候选
```

---

## 六、与 generate_from_prompt_lmstudio.py 的分工

| 职责 | 脚本 |
|------|------|
| 上下文组装 + prompt 渲染 | `build_generation_context.py` |
| 读取 prompt → 调用模型 → 写输出文件 | `generate_from_prompt_lmstudio.py` |

两个脚本通过文件系统（prompt TXT）解耦，不相互导入。

---

## 七、协议定位

本协议描述的是**当前阶段的现行消费链**，不是最终唯一终局协议。

**当前状态：**
- `build_generation_context.py` 从 `query.py`（KB v2 索引层）检索数据，组装 context
- 角色主卡（`kb/characters/*/main.json`）的 `generation_data` 尚未接入此消费链

**过渡方向：**
- 未来随着角色档案包规范（preprocess/audit/payload spec）落地，
  `build_generation_context.py` 应逐步从 `generation_data` 直接读取已核查的字段，
  而不是每次从 KB 索引层动态组装
- 两个阶段可以并存：现行 query-based 路径继续服务于没有主卡的人物，
  主卡路径优先服务于已建档的核心人物

**复用到新小说：**
只需确保：
- 新小说的 `kb/` 已建立 v2 索引
- `query.py` 能正确解析新小说的人物 alias
- `config.json` 中配置了正确的模型参数

`build_generation_context.py` 本体不需要修改。
