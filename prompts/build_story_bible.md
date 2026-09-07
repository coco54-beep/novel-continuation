# 提示词：建立故事档案（build_story_bible.md）

## 用途
所有逐章分析完成后，汇总生成 `story_bible/` 下的 10 个 JSON 档案文件。人物别名是否需要合并、存疑实体请配合 `merge_characters.md` 处理。

## 输入
- 全部章节分析：`analysis/chapters/*.json`
- 需要时回查原文：`chapters/original/*.md`
- 输出契约：`schemas/` 目录下对应 schema（键名以此为准）

## 输出文件与契约

| 文件 | 顶层结构 | 契约 schema | 逐元素校验 |
|---|---|---|---|
| `story_bible/characters.json` | 数组 | `schemas/character.schema.json` | 是 |
| `story_bible/relationships.json` | 数组 | `schemas/relationship.schema.json` | 是 |
| `story_bible/events.json` | 数组 | `schemas/event.schema.json` | 是 |
| `story_bible/knowledge.json` | 数组 | `schemas/knowledge.schema.json` | 是 |
| `story_bible/foreshadowing.json` | 数组 | `schemas/foreshadowing.schema.json` | 是 |
| `story_bible/timeline.json` | 数组/对象 | 无 schema，见下方字段约定 | 否 |
| `story_bible/locations.json` | 数组 | 无 schema，见下方字段约定 | 否 |
| `story_bible/factions.json` | 数组 | 无 schema，见下方字段约定 | 否 |
| `story_bible/items.json` | 数组 | 无 schema，见下方字段约定 | 否 |
| `story_bible/world_rules.json` | 数组 | 无 schema，见下方字段约定 | 否 |

## 键名铁律（避免数据污染）
1. **只使用 schema `properties` 中定义的键，一个字段一个键。**
2. **禁止为同一字段写别名键。** 例如关系只写 `relationship_id/from_char/to_char/status/source_chapter`（以 `schemas/relationship.schema.json` 实际键为准），事件只写 `event_id/name/source_chapter/...`（以 `schemas/event.schema.json` 为准）。不要同时保留 `relation_id` 与 `relationship_id`、`from_id` 与 `from_char`、`title` 与 `name`、`result_key` 与 `immediate_result` 等重复字段。
3. 不确定字段名时**先读对应 schema**，不要凭印象造键。
4. 可选字段无内容时**省略该键**，不要写成空值占位——尤其是 `foreshadowing.recommended_resolution_range`（回次未知就整个省略，不要写 `[]`）。
5. 数组无内容就写 `[]`，不写 `null`。
6. 跨文件一律用 `character_id`（形如 `char_xxx`）互相引用；`character_id` 一旦定义，全项目统一，不得另起炉灶或写错。
7. `source_status` 等枚举值严格遵守 schema `enum`（confirmed / strong_implied / inferred / creative / user_confirmed / rejected）。

## 无 schema 文件的字段约定（宁缺毋滥，证据可追溯）
- `timeline.json`：按回次记录 `{chapter, when, events:[...]}` 或等效数组；时序不确定处注明。
- `locations.json`：`{location_id, name, type, belongs_to, description, first_appearance_chapter}`。
- `factions.json`：`{faction_id, name, members:[character_id], description}`；原文无清晰派系则不强行造。
- `items.json`：`{item_id, name, holder_id, description, significance, evidence}`。
- `world_rules.json`：`{rule_id, rule, scope, constraint, evidence}`；只写原文可支撑的规则。

## 校验
所有可校验文件写完后，在技能根目录逐个运行（`--items` 对数组逐元素校验）：
```bash
python scripts/validate_json.py --schema schemas/character.schema.json --input projects/<id>/story_bible/characters.json --items
python scripts/validate_json.py --schema schemas/relationship.schema.json --input projects/<id>/story_bible/relationships.json --items
python scripts/validate_json.py --schema schemas/event.schema.json --input projects/<id>/story_bible/events.json --items
python scripts/validate_json.py --schema schemas/knowledge.schema.json --input projects/<id>/story_bible/knowledge.json --items
python scripts/validate_json.py --schema schemas/foreshadowing.schema.json --input projects/<id>/story_bible/foreshadowing.json --items
```
校验失败必须修正，不得跳过。修正后复查：所有 `character_id` 引用都能在 `characters.json` 中找到。

## 质量要求
- 一律以前十二回/全部已分析章节为事实来源，分析里没有的一律不臆造，宁缺毋滥。
- 无法可靠判断两个名称是否为同一人物时，按 `merge_characters.md` 输出待确认候选，**不得直接合并低置信度人物**。
- 每个重要结论尽量带 1-2 条 `evidence`（回次+关键句摘要）。
- JSON 一律 UTF-8、`ensure_ascii=False`、`indent=2`。
