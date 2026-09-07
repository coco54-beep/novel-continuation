# 输出规范（output_conventions.md）

本文件规定所有产物（正文、分析、报告、导出）的命名、格式与流转约定。

## 正文版本流转

```
chapters/generated/{chapter_id}/draft_v1.md     初稿
chapters/generated/{chapter_id}/revised_v2.md   修订稿
chapters/generated/{chapter_id}/final.md        用户确认的正式版
```

- 正文默认先存 `draft_v1`，**不直接作为正式章节**。
- 只有用户确认的 `final.md` 才进入正式故事状态。
- 修订优先局部修改；不随意重写无问题段落；不改变用户锁定内容；不引入新设定冲突。

## JSON 输出

- 所有结构化数据（分析、人物、事件、伏笔、规划、报告、状态）以 JSON 保存。
- 必须符合 `schemas/` 对应契约，并用 `scripts/validate_json.py` 校验。
- 校验失败拒绝保存损坏结果。

## 命名约定

- 章节 ID：`0001`（四位数）。
- 人物 ID：`char_<slug>`。
- 事件 ID：`evt_<slug>`；事实 ID：`fact_<n>`；伏笔 ID：`foreshadow_<n>`。
- 关系 ID：`rel_<n>`；方案 ID：`prop_<n>`；场景 ID：`scene_<chapter>_<n>`。
- 状态 ID：`state_after_<chapter>`。

## Markdown 正文格式

- 正文另存为 `.md` 文件。
- 首行可用 `# 章节标题`，正文放在其后。
- 不写 `[剧情推进]`、`（此处应……）` 等杂注。

## 导出

- 合并导出：`exports/continuation_novel.txt` 或 `.md`；`full_novel.txt` / `.md`。
- 导出文件头注明：**本作品由 AI 辅助创作**。
- 可选择仅续写（continuation）或原文+续写（full）。
- 生成项目压缩包 `exports/project_archive.zip`，便于迁移（不依赖绝对路径）。

## 文件编码

所有文件 `utf-8`（JSON 用 `ensure_ascii=False`）。
