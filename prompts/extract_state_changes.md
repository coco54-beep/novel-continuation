# 提示词：提取状态变化（extract_state_changes.md）

## 用途
从已确认章节正文中提取状态变化，供 `scripts/update_state.py` 应用，更新 `state/current_state.json`。

## 输入
- 已确认章节正文：{confirmed_chapter}
- 当前故事状态：{current_state}

## 任务
对比当前状态与本章结束后，提取所有状态变化，包括人物位置、身体/心理状态、目标、信息、误解、关系、道具归属、势力状态、事件结果、未解决冲突、伏笔状态、世界新增事实。

## 输出（遵循 story_state.schema.json 的部分字段）
```json
{
  "after_chapter": "0051",
  "characters": [
    {
      "name": "林舟",
      "location": "旧车站仓库",
      "physical_condition": "轻伤",
      "mental_state": "坚定",
      "current_goal": "追查失踪者下落",
      "known_information": ["仓库编号为17"],
      "misconceptions": ["误以为信件是警方设局"]
    }
  ],
  "facts": ["失踪者曾出现在仓库附近"],
  "conflicts": ["幕后势力尚未现形"],
  "item_owners": [{"item": "匿名信", "owner": "林舟"}],
  "foreshadowing_status": [{"id": "foreshadow_0003", "status": "reinforced"}],
  "world_facts": []
}
```

## 要求
- 只记录**发生变化**的项，不重复已有状态。
- 信息变化需标注来源章节。
- 供 `update_state.py` 校验与写入，防止重复应用同一章节。
