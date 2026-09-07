# 提示词：合并疑似重复人物（merge_characters.md）

## 用途
判断多个候选名称是否指向同一人物，产出待确认候选，避免误合并。

## 输入
- 候选名称列表：{candidate_names}
- 各自出处（章节/原文）：{evidence}

## 任务
判断这些名称是否可能为同一人物的别名（如 林舟 / 小舟 / 林先生 / 队长）。

## 输出
```json
{
  "candidate_entities": ["林舟", "林先生"],
  "suggested_same_entity": true,
  "confidence": 0.71,
  "status": "pending_user_confirmation",
  "reasoning": "判断依据……"
}
```

## 规则
1. **不得直接合并低置信度人物**（confidence < 0.8 或不确定时）。
2. `status` 固定为 `pending_user_confirmation`，交由用户确认。
3. 说明判断依据，供用户参考。
