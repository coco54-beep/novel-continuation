# 提示词：生成结局方案（propose_endings.md）

## 用途
生成三套不同篇幅的完结方案，写入 `planning/ending_proposals.json`。**生成后必须暂停等待用户选择，不得跳过。**

## 输入
- 故事摘要与当前阶段：{story_summary_and_stage}
- 人物档案：{characters}
- 未回收伏笔：{unrecovered_foreshadowing}
- 剩余篇幅估算：{length_estimate}

## 任务
生成三套有明显差异的方案：

1. **快速收束（quick）**：尽快完成主线，回收核心伏笔，完成主要人物弧，尽量不扩展新设定。
2. **标准完结（standard）**：完成主线，处理重要支线，回收主要伏笔，给予核心人物完整结局。
3. **长篇展开（expanded）**：扩展世界与配角，允许新增阶段性冲突，仍保持原有主题与因果。

## 输出（数组，遵循 ending_proposal.schema.json）
```json
[
  {
    "proposal_id": "prop_001",
    "name": "标准完结方案",
    "type": "standard",
    "suggested_remaining_chapters": 12,
    "estimated_remaining_chars": 42000,
    "summary": "...",
    "final_conflict": "...",
    "main_character_ending": "...",
    "other_character_endings": ["..."],
    "main_plot_resolution": "...",
    "subplot_handling": "...",
    "foreshadowing_plan": ["..."],
    "new_settings_needed": ["..."],
    "source_support": ["(原文支撑点)"],
    "inferred_parts": ["(推断部分)"],
    "risk": "...",
    "match_score": 0.85,
    "match_notes": "..."
  }
]
```

## 要求
- 三套方案差异明显，不能只是章节数不同。
- 每个方案说明依据、原文支撑、推断部分、风险与前文匹配度。
- 不未经用户确认生成正式大纲。
