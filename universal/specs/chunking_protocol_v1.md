asset_layer: base

# Chunking Protocol v1

> 层级：Universal Fixed Asset
> 版本：v1
> 适用范围：所有使用本工具链的小说项目

---

## 一、职责边界

`chunker.py` 负责将 `raw/` 下的单一 txt 原文切分为 `chunks/` 下的固定大小文本块。  
chunking 是纯文本切割，不调用 LLM，不修改任何内容，不做语义判断。

---

## 二、输入 / 输出

| 项目 | 说明 |
|------|------|
| **输入** | `raw/{bookname}.txt`（单文件，UTF-8 或 GB18030）|
| **输出** | `chunks/{bookname}_{NNNN}.txt` + `chunks/{bookname}_{NNNN}.meta.json` |
| **命名规则** | 书名去掉 `.txt` 后缀，序号 4 位零填充，从 `0001` 起 |
| **配置来源** | `config.json` → `max_chunk_chars`（默认 4900）|

---

## 三、切割规则

1. **优先在章节标题前切割**：检测 `CHAPTER_RE` 正则匹配的行（"第X章"、"Chapter N"、"楔子"、"序章"等），在其前插入切割点。
2. **超长 chunk 强制切割**：若当前段落超出 `max_chunk_chars`，在换行处就近截断。
3. **不跨章节合并**：章节是自然切割单位，不会把多个章节合并进同一 chunk。

---

## 四、Structural Chunk（结构性块）

满足以下**全部**条件的 chunk，视为 structural chunk：

- 字符数 ≤ 200
- 行数 ≤ 2
- 内容匹配章节标题正则

Structural chunk 在 extract 阶段**跳过 LLM API 调用**，直接记录为 `structural_chunk` 状态。  
实际占比取决于小说的章节密度，通常极少（< 1%）。

> **当前项目实例（全民魔女1994）**：共 1722 个 chunk，其中 7 个为 structural chunk（0.4%）。

---

## 五、meta.json 字段说明

每个 chunk 生成配套的 `.meta.json`，字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `chunk_id` | str | 格式 `{bookname}_{NNNN}`，唯一标识符 |
| `source_file` | str | 原始 txt 文件名 |
| `char_count` | int | 本 chunk 字符数 |
| `start_line` | int | 在原文中的起始行（1-based）|
| `title_hint` | str | 检测到的章节标题（若无则为空字符串）|
| `section_type` | str | 内容类型标签，默认 `"narrative"`，由独立的 section_type audit 写入 |
| `is_structural_chunk` | bool | 是否为 structural chunk |

> `section_type` 不由 chunker 写入，由独立的 `apply_section_types.py` 脚本在 audit 后回填。

---

## 六、复用到新小说

| 需要改动 | 说明 |
|----------|------|
| `raw/` 下的文件 | 替换为新小说的 txt 文件 |
| `config.json.max_chunk_chars` | 根据新小说章节密度调整（长章小说可适当增大）|
| `CHAPTER_RE` 正则 | 若新小说章节标题格式特殊，可在 chunker.py 顶部扩展正则 |
| 不需要改 | 脚本主体逻辑、meta schema、命名规则 |
