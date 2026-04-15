asset_layer: experimental

# Tag 落地规则表 / 应用说明 v1

> 本文件是当前阶段的 Tag 落地应用说明，用于指导人工补写、工具补写与后续脚本自动生成时的统一写法。
> 本文件不重新定义四层语义，只说明当前项目里 Tag 应如何落地。

## 1. 当前范围

- 当前先跑通 Tag 机制，不做全仓大规模补写。
- 当前不因补 Tag 单独重跑 chunk / canon / style / KB。
- 目录归类可用于“待补标判断”，但不能替代文件内正式声明。

## 2. 哪些文件类型必须有 Tag

- 非脚本文件应包含资产层级 Tag。
- 脚本文件当前不强制写 Tag。
- 对已有重要文件，优先补：规范文件、长期资产文件、关键实验协作文档。

## 3. Markdown / txt 的写法

- Markdown / txt 类文件使用文件内固定头部单行写法。
- 当前统一写法为：

```text
asset_layer: base
```

- 该行只表达层级本身，不附带权限、审核状态、真值等级等其他语义。

## 4. JSON 的写法

- JSON 类文件唯一合法字段名为 `_asset_layer`。
- 推荐放在对象顶层最前位置，便于人工与工具稳定读取。

```json
{
  "_asset_layer": "novel_instance"
}
```

## 5. JSONL 的当前建议方案

- JSONL 当前采用保守策略，不为补 Tag 单独改写既有日志正文结构。
- 若后续需要正式落地，可再确定“首条 header record”或“配套 sidecar 声明文件”方案。
- 在正式方案定死前，目录推断与配套说明文件可作为临时辅助，但不视为 JSONL 文件内正式声明。
- 当前首批 Git 骨架存在 3 个按例外放行的 `kb/*.jsonl`：`kb/author_conflict_register_v0.jsonl`、`kb/character_appearances_v2.jsonl`、`kb/clean_canon_testset_v0.jsonl`。
- 这 3 个文件之所以暂按例外处理，是因为该类文件的正式 Tag 方案尚未稳定；现阶段先通过白名单准入与人工判断控制其进入首批提交。
- 此例外不改变总规则：稳定纳入骨架的非脚本文件仍应具备合法层级 Tag。

## 6. 自动补写边界

- 自动补写不得静默覆盖人工已声明 Tag。
- 若文件内已有明确 Tag，自动流程只能校验，不应无提示改写。
- 若对象边界仍模糊，应先进入盘点 / 审阅，再决定是否补 Tag。
- 并非所有当前未补 Tag 的文件都是遗漏；少数文件之所以暂未补 Tag，是因为其设计尚未稳定，当前仍处于待定 / 过渡阶段。
- 对这类文件，现阶段应优先通过白名单准入与人工判断控制其是否进入 Git 骨架，而不是为了形式统一强行补 Tag。
- 这只是稳定性例外口径，不改变总规则：稳定纳入骨架的非脚本文件仍应具备合法层级 Tag。

## 7. 当前项目中的默认层级倾向

- `universal/specs/` 下规范文件：通常为 `base`。
- `kb/characters/` 下具体小说长期资产：通常为 `novel_instance`。
- `outputs/generation/` 与 `outputs/ab_round3/` 下当前 round3 相关文件：通常为 `experimental`。
- 以后由新小说初始化复制出来的骨架文件：归 `instantiation_mold`；由其生成的实例归 `novel_instance`。`kb/characters/template/` 已确认为 `instantiation_mold`。
- `prompts/` 下抽取/生成提示词模板：通常为 `base`（跨小说复用，已纳入 Git 骨架）。
- chunk / canon / style / KB 等某本小说专属基础底料：默认更接近 `novel_instance`。

## 8. 当前执行口径

- 先补关键样本文件，验证写法可执行。
- 不为 Tag 合规单独重跑旧产物。
- 当前不把 Tag 落地扩成制度重写、脚本化改造或全仓重构。
