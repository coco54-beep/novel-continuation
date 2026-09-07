# 提示词：生成单章大纲（generate_chapter_outline.md）

## 用途
为下一章生成 `planning/chapter_outlines.json` 中的一条章纲。

## 输入
- 分卷大纲/续写总纲：{volume_or_story_outline}
- 当前故事状态：{current_state}
- 本章序号 & 目标字数：{chapter_number}, {target_chars}
- 本章必须处理的伏笔：{required_foreshadowing}

## 输出（遵循 chapter_outline.schema.json）
```json
{
  "chapter_id": "0051",
  "chapter_number": 51,
  "chapter_name": "...",
  "goal": "...",
  "characters": ["..."],
  "time_place": "...",
  "core_events": [
    {"event": "...", "cause": "...", "result": "..."}
  ],
  "character_mental_changes": ["..."],
  "relationship_changes": ["..."],
  "information_delta": ["..."],
  "foreshadowing_ops": [
    {"foreshadowing_id": "foreshadow_0003", "op": "reinforce"}
  ],
  "environment_features": "...",
  "language_pacing": "...",
  "hook": "...",
  "target_chars": 3500,
  "volume_number": 1
}
```

## 要求
- 人物状态承接上一章结尾。
- 事件有因果；事件强度符合当前剧情阶段。
- 本章必须推进指定伏笔。
- 章末钩子承接下一章。
