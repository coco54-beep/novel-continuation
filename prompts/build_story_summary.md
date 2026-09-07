# 提示词：构建故事摘要与当前阶段（build_story_summary.md）

## 用途
在所有章节分析完成后，汇总生成 `analysis/story_summary.md` 与 `analysis/current_stage.json`。

## 输入
- 全部章节分析：{all_chapter_analyses}
- 人物档案：{characters}
- 事件/伏笔：{events_and_foreshadowing}

## 任务
1. 撰写全书至今的故事摘要（主线、支线、核心矛盾、关键转折）。
2. 判断当前故事阶段。

## 输出

### story_summary.md（Markdown）
- 一句话梗概
- 主线回顾
- 支线回顾
- 核心矛盾
- 关键转折点
- 已揭示秘密 / 未揭示秘密
- 当前未解决问题

### current_stage.json
```json
{
  "stage": "development",
  "reasoning": "判断依据：主线完成度约X%……",
  "main_plot_progress": 0.6,
  "unresolved_conflicts": ["..."],
  "unrevealed_secrets": ["..."],
  "unfinished_character_arcs": ["..."],
  "unrecovered_foreshadowing": ["..."]
}
```

## 要求
- 必须说明判断依据，不能只给结论。
- 阶段枚举：`opening | development | midpoint | escalation | pre_climax | climax | resolution | unknown`。
