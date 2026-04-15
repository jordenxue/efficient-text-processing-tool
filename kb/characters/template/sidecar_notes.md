asset_layer: instantiation_mold

# Character Package Notes

这是角色档案包的核心 mold 说明文件，可在复制到 `kb/characters/{name}/` 后继续补充。

## Current Draft Rule

- 当前核心 mold 只包含 `main.json`、`sidecar_notes.md`、`sidecar_open_questions.json`、`sidecar_relations.json`。
- `main.json` 是存储态主卡，不等于生成 prompt；生成时只抽取 `generation_data`。
- `maintenance_data` 与 3 个 sidecar 供维护与审核流程使用，不直接进入生成 payload。
- `sidecar_review.jsonl` 不是模板必备件；如需要持久审计记录，应在实例化后的 audit / review 阶段按需生成。

## State Boundary

- template-state：模板源文件允许保留 `"NULL"` 作为可审计占位。
- instance-state：复制后应第一轮立即替换 `main.json.character`。
- pre-consumption-state：将进入当前轮生成消费的 `generation_data` 字段不得继续保留 `"NULL"`。

## Usage Note

- `sidecar_notes.md` 只承接自由文本维护说明。
- 结构化待定问题应写入 `sidecar_open_questions.json`。
- 结构化关系维护信息应写入 `sidecar_relations.json`。
