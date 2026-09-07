# 提示词：一致性检查（review_chapter.md）

## 用途
检查 `chapters/generated/{chapter_id}/draft_v1.md`，产出 `reviews/{chapter_id}_v1.json`。

## 输入
- 待查正文：{chapter_text}
- 本章章纲：{chapter_outline}
- 场景卡：{scene_cards}
- 当前故事状态：{current_state}
- 相关人物档案：{characters}
- 人物关系档案：{relationships}   ← 必须读取, 用于核对称呼/辈分是否与世系一致(见 references/consistency_rules.md 第1类)
- 知识边界：{knowledge_boundary}
- 本章伏笔：{foreshadowing}
- 全书风格指纹：{style_profile}

## 任务
逐类检查六类问题（人物一致性、知识边界、时间空间、世界规则、情节伏笔、语言风格），见 `references/consistency_rules.md`。

## 输出（遵循 review_report.schema.json）
```json
{
  "chapter_id": "0051",
  "version": "draft_v1",
  "overall_score": 82,
  "decision": "revision_required",
  "issues": [
    {
      "issue_id": "issue_001",
      "type": "knowledge_boundary",
      "severity": "high",
      "location": "第14段",
      "description": "林舟提到了他尚未获得的仓库编号。",
      "evidence": ["fact_0012"],
      "suggestion": "删除具体编号，或补充合理的信息获得过程。",
      "status": "open"
    }
  ]
}
```

## 要求
- `decision`：approved / revision_required / major_revision_required / rejected。
- 每个问题必须给 `type`、`severity`、`description`、`suggestion`。
- critical 问题必须高亮；`overall_score` 0–100。
