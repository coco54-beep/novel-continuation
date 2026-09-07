# 提示词：生成分卷大纲（generate_volume_outlines.md）

## 用途
基于续写总纲，生成 `planning/volume_outlines.json`。规划各卷的起止与阶段目标。

## 输入
- 续写总纲：{story_outline}
- 当前故事状态：{current_state}

## 输出
```json
[
  {
    "volume_number": 1,
    "volume_name": "卷一",
    "start_chapter": "{start_chapter_id}",
    "end_chapter": "{end_chapter_id}",
    "stage_goal": "...",
    "core_conflict": "...",
    "key_turning_point": "...",
    "character_changes": ["..."],
    "end_volume_state": "..."
  }
]
```

## 要求
- 起止章节连续覆盖剩余区间。
- 每卷有明确阶段目标与卷末状态，可衔接下一卷。
