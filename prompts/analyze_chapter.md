# 提示词：章节分析（analyze_chapter.md）

## 用途
对单章 `{chapter_id}` 生成结构化分析，产物保存到 `analysis/chapters/{chapter_id}.json`。

## 输入
- 章节标题：{title}
- 章节正文：{content}
- 上文情节简述（可选）：{context}

## 任务
提取本章在剧情、人物、事件、关系、信息、伏笔、风格、环境上的全部特征。每个重要结论给出原文证据或标记为推断。

## 输出（严格 JSON，遵循 chapter_analysis.schema.json）
```json
{
  "chapter_id": "{chapter_id}",
  "order": {order},
  "title": "{title}",
  "one_line_summary": "...",
  "summary": "详细剧情梗概...",
  "narrative_function": "开端/铺垫/转折/收束/高潮(择一)",
  "time_place": "...",
  "point_of_view": "...",
  "characters": [
    {"name": "...", "goal": "...", "mental_state": "...", "behavior": "...", "state_change": "..."}
  ],
  "events": [
    {"event": "...", "cause": "...", "immediate_result": "...", "long_term_impact": "..."}
  ],
  "information": {"learned": ["..."], "misconceptions": ["..."]},
  "style": {
    "environment_description": "...",
    "language_features": "...",
    "emotion_curve": "...",
    "pacing": "...",
    "hook": "..."
  },
  "foreshadowing": {"new": ["..."], "reinforced": ["..."], "resolved": ["..."]},
  "evidence": ["(引用关键句或其摘要)"],
  "confidence": 0.9
}
```

## 要求
1. 忠实原文，不臆造。
2. 置信度 0–1，反映对原文解读的确信程度。
3. 中英文均可，正文理解以原文语言为准。
