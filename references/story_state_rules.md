# 故事状态规则（story_state_rules.md）

本文件规定如何记录、更新、回滚故事状态，以及续写时必须对齐的「当前状态」。

## 状态文件

- **当前状态**：`state/current_state.json`（唯一权威的「现在」）
- **历史快照**：`state/snapshots/after_XXXX.json`（每章更新前快照，用于回滚）

## 当前状态应包含

- 人物当前位置
- 人物身体状态
- 人物心理状态
- 人物当前目标
- 人物掌握的信息
- 人物误解
- 人物关系
- 道具持有者
- 势力状态
- 事件结果
- 未解决冲突
- 伏笔状态
- 世界新增事实

## 更新规则

1. 每个**已确认章节**（`final.md`）才能触发状态更新。
2. 更新前必须先创建 `state/snapshots/after_XXXX.json` 快照（复制当前状态）。
3. 更新 `state/current_state.json`。
4. **防止重复应用同一章节**：若该章节快照已存在，拒绝再次更新。
5. 状态更新可回滚：用上一快照覆盖当前状态。

## 快照命名

`after_<chapter_id>.json`，如 `after_0051.json`。`after_0000.json` 可为初始状态。

## 续写前对齐

每次生成下一章正文前，**必须**读取 `state/current_state.json` 作为上下文，确保：

- 人物位置、目标、心理从上一章结束处延续
- 人物掌握的信息与知识边界一致
- 道具归属正确
- 未解决冲突与伏笔状态准确

---

## 状态变化提取

由 `prompts/extract_state_changes.md` 从确认正文提取状态变化，保存为结构化的 `changes` 文件（遵循 `schemas/story_state.schema.json`），再交给 `scripts/update_state.py` 应用。
