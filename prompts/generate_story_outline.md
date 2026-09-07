# 提示词：生成续写总纲（generate_story_outline.md）

## 用途
用户选定结局方案后，生成 `planning/story_outline.json`（续写总纲）。

## 输入
- 选定的结局方案：{selected_ending}
- 故事摘要与当前阶段：{story_summary_and_stage}
- 人物档案：{characters}
- 未回收伏笔：{unrecovered_foreshadowing}

## 任务
在选定结局下，规划从当前到结局的整体走向。

## 输出（遵循 story_outline.schema.json）
```json
{
  "core_theme": "...",
  "ending": "...",
  "ending_proposal_id": "prop_001",
  "remaining_main_plot": ["..."],
  "character_arcs": ["..."],
  "final_conflict": "...",
  "foreshadowing_order": ["..."],
  "turning_points": ["..."],
  "volume_count": 2
}
```

## 要求
- 覆盖重要人物与所有高优先级伏笔。
- 伏笔回收顺序合理，不悬空踢皮球。
- 与选定结局一致；重大新增设定、角色死亡或关系改变须先经用户确认。
