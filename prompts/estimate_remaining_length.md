# 提示词：估算剩余篇幅（estimate_remaining_length.md）

## 用途
根据故事当前阶段与推进速度，估算还需多少章、多少字才能完结。

## 输入
- 当前阶段：{current_stage}
- 已完成章节数：{completed_chapters}
- 每章平均字数：{avg_chars}
- 未回收伏笔数 / 未完成人物弧数：{unresolved_count}
- 小说类型：{genre}

## 任务
估算「合理完结」所需的剩余章节数区间与总字数。

## 输出
```json
{
  "estimated_remaining_chapters": 12,
  "min_remaining_chapters": 8,
  "max_remaining_chapters": 18,
  "estimated_remaining_chars": 42000,
  "reasoning": "依据主线完成度约60%……",
  "basis": {
    "main_plot_progress": 0.6,
    "remaining_climax_points": 2,
    "pacing_per_chapter": 0.04
  }
}
```

## 要求
- 宁可少而完整，不要注水。
- 给出区间与依据；最终方案交由用户在多套结局方案中选定。
