# 提示词：生成场景卡（generate_scene_cards.md）

## 用途
为某章生成若干个场景卡，保存到 `scenes/{chapter_id}.json`。写正文前**必须**有场景卡。

## 输入
- 本章章纲：{chapter_outline}
- 当前故事状态：{current_state}
- 相关人物档案：{characters}
- 本章相关伏笔：{foreshadowing}

## 任务
将本章拆分为 1–N 个按时间/地点/视角划分的场景，每场景一张卡。

## 输出（数组，遵循 scene_card.schema.json）
```json
[
  {
    "scene_id": "scene_0051_01",
    "chapter_id": "0051",
    "scene_number": 1,
    "time": "...",
    "place": "...",
    "pov_character": "...",
    "characters": ["..."],
    "objective": "...",
    "per_character_goals": [{"name": "...", "goal": "..."}],
    "known_by_characters": ["..."],
    "unknown_by_characters": ["..."],
    "misconceptions": ["..."],
    "conflict": "...",
    "action": "...",
    "emotion_changes": ["..."],
    "result": "...",
    "foreshadowing_to_advance": ["..."],
    "next_scene_link": "...",
    "target_chars": 1200
  }
]
```

## 要求
- 每场景一个主动作节拍，场景之间衔接自然。
- 明确各人物已知/未知/误解，避免知识越界。
- 标注需推进的伏笔。
