---
name: novel-continuation
description: |
  长篇小说分析与续写技能：分析小说并建立故事档案，提取章节剧情、人物、事件、时间线、知识边界、伏笔与语言风格；生成结局方案、续写大纲、场景卡和章节正文，并执行一致性检查与状态更新。
  当用户需要分析小说、生成章节梗概、整理人物档案、规划结局、推测剩余章数、续写章节、检查人物一致性、整理伏笔，或继续一个已有小说项目时使用。
  不用于：孤立短文、单句修改、普通语法纠错、无前文的完全独立创作、无授权侵权发布、高度模仿特定在世作者。
---

# Novel Continuation Skill（长篇小说分析与续写技能）

本技能把「小说分析 → 故事建模 → 大纲规划 → 一致性检查 → 逐章续写」封装成一套开箱即用的工作流。用户只需提供小说并调用本技能，即可在**不部署任何服务器**的前提下完成续写闭环。

**核心原则：先分析，再规划，最后续写。禁止在没有故事档案和章纲的情况下直接生成长篇续写。**

完整开发计划见同目录 `plan.md`。本文件是**技能入口与指挥中心**，具体规范分散在 `references/`（方法论文档）、`prompts/`（提示词）、`schemas/`（数据契约）、`scripts/`（确定性脚本）中。

---

## 1. 何时使用 / 何时不使用

### 应触发

- 分析一部小说；
- 为小说生成章节梗概；
- 整理人物档案、人物语言风格；
- 整理故事时间线、知识边界、伏笔账本；
- 推测小说还需多少章完结；
- 生成小说结局方案；
- 生成续写总纲 / 卷纲 / 章纲；
- 生成下一章场景卡或正文；
- 检查续写是否偏离人物设定、人物是否知道不该知道的信息；
- 继续已有的小说续写项目；
- 导出小说续写结果。

### 不应触发

- 只要求写一段孤立短文；
- 只要求修改单句 / 普通语法纠错；
- 没有前文却要求完全独立创作；
- 要求高度模仿某位**在世**作者；
- 要求处理无权使用的文本并用于侵权发布。

---

## 2. 项目文件约定

本技能使用**文件代替复杂应用**。所有数据保存在用户项目中，不使用数据库或服务器。

### 2.1 Skill 自身结构

```
novel-continuation/
├─ SKILL.md          技能入口(本文件)
├─ plan.md           开发计划
├─ README.md         安装与使用说明
├─ LICENSE
├─ requirements.txt
├─ scripts/          确定性处理脚本 (初始化/导入/切分/校验/状态/搜索/导出/篇幅探知/密度探知/风格评分)
├─ references/       方法论文档 (工作流/分析维度/状态规则/上下文/一致性/文风/文风范式库/版权/输出规范)
├─ schemas/          13 个 JSON Schema 契约
├─ templates/        9 个 JSON 模板
├─ prompts/          提示词模板 (标准流程 + 轻量模式，见 prompts/)
└─ tests/            自动化测试与 Fixtures
```

### 2.2 用户小说项目结构

每部小说一个独立目录，位于 `projects/<project_id>/`。详见 `references/workflow.md`。核心子目录：

```
projects/<project_id>/
├─ project.json          项目元数据与状态
├─ source/               原始小说与导入信息
├─ chapters/
│  ├─ original/          切分后的原文章节
│  └─ generated/         续写章节 (draft/revised/final 版本)
├─ analysis/             逐章分析 / 故事摘要 / 当前阶段 / 风格指纹
├─ story_bible/          人物/关系/事件/时间线/地点/势力/道具/规则/知识/伏笔
├─ planning/             结局方案/选定时/总纲/卷纲/章纲
├─ scenes/               场景卡
├─ reviews/              一致性检查报告
├─ state/                当前状态 + 历史快照
├─ indexes/              章节清单/关键词索引/实体索引
└─ exports/              导出的成书
```

**项目状态机**：`created → imported → split → analyzing → analyzed → planning → planned → writing → reviewing → completed`。

---

## 3. 标准工作流程

> 必须先读 `references/workflow.md` 获取每一步的细节。流程为：```text
导入小说
→ 切分章节
→ 自动探知篇幅
→ 分析章节
→ 汇总故事档案
→ 生成结局方案
→ 【用户确认方案】
→ 生成续写大纲
→ 分析文风（写正文前必做，产出风格指纹）
→ 生成章节场景卡
→ 生成章节正文
→ 一致性检查
→ 修订与确认
→ 更新故事状态
```

> **两种模式**：本技能提供**完整模式**（上图全套流程，适用长线/多章/多人物，需跨章一致性）与**轻量模式**（跳过建档/结局/章纲/场景卡，只读前文→抓风格→续写 1–2 章→快速自检，适用"就想快速续两章看看"或简单场景）。触发分支见 `prompts/light_continue.md` 的"何时用/何时不用"。默认为完整流程；若用户只要续一两章且无需长期一致性，走轻量模式。

> **篇幅由脚本自动探知、不由调用方手工决定。** 切分后运行 `scripts/estimate_chapter_length.py`，它统计原文章节真实字数并写入 `project.json#target_chapter_length`；后续所有场景卡/章纲/正文的 `target_chars` 均取自该值。写作以「剧情单元完整 + 符合作者叙事节奏」为第一原则，字数是结果而非目标。

> **密度档位同样由脚本自动探知。** 切分后运行 `scripts/analyze_density.py`，归并出全书主流密度档位（密实/中等/疏朗）写入 `project.json#density_tier`；续写正文必须匹配该档位的句长/段长/对白占比，否则易被压成"纲要式"偏薄（见 `references/style_library.md`）。
> **超长章节按剧情单元分段生成**：若单章目标字数明显超过单次合理输出上限（古典章回体/史诗型小说尤甚，单回可达数万字），把本章拆成多个约 2000–4000 字的"生成块"逐段生成、再拼接成 `draft_v1.md`，不要一次生成整章，否则易超时且篇幅密度偏薄。详见 `references/workflow.md` 阶段十。

> **文风分析是写正文前的必要步骤。** 跳过它会导致续写「形似神不似」：虽然人物、情节正确，却丢了原文的文化梗、生活细节与悲喜节奏。详见 `references/style_rules.md`。

各阶段的**输入、要执行脚本、生成文件、字段**详见 `references/workflow.md` 与对应 `prompts/*.md`。此处只给提纲：

| 阶段 | 执行 | 产物 |
|---|---|---|
| 创建项目 | `scripts/init_project.py` | 项目目录 + `project.json` |
| 导入小说 | `scripts/import_novel.py` | `source/original.txt` + 导入信息 |
| 章节切分 | `scripts/split_chapters.py` | `chapters/original/*.md` + `indexes/chapter_manifest.json` |
| 自动探知篇幅 | `scripts/estimate_chapter_length.py` | `indexes/length_stats.json` + `project.json#target_chapter_length` |
| 自动探知密度 | `scripts/analyze_density.py` | `indexes/density_stats.json` + `project.json#density_tier` |
| 逐章分析 | `prompts/analyze_chapter.md` | `analysis/chapters/*.json` |
| 建立故事档案 | `prompts/merge_characters.md` 等 | `story_bible/*.json` |
| 分析故事阶段 | `prompts/build_story_summary.md` | `analysis/current_stage.json` |
| 生成结局方案 | `prompts/propose_endings.md` | `planning/ending_proposals.json` |
| 生成续写大纲 | `prompts/generate_*.md` | `planning/story_outline.json` 等 |
| 分析文风 | `scripts/build_style_profile.py` + `prompts/analyze_style.md` | `analysis/style_profile.json` |
| 生成场景卡 | `prompts/generate_scene_cards.md` | `scenes/<id>.json` |
| 生成正文 | `prompts/write_scene.md` | `chapters/generated/<id>/draft_v1.md` |
| 一致性检查 | `prompts/review_chapter.md` | `reviews/<id>_v1.json` |
| 修订确认 | `prompts/revise_chapter.md` | `revised_v2.md` / `final.md` |
| 更新状态 | `scripts/update_state.py` | `state/current_state.json` + 快照 |

---

## 4. 用户确认节点

以下节点**必须暂停并询问用户**，禁止未经确认继续推进或覆盖项目状态：

1. **章节切分结果**——标题识别置信度低或有异常章节时；
2. **疑似重复人物**——无法可靠判断两个名称是否同一人物时（不得直接合并低置信度人物）；
3. **结局选择**——生成结局方案后等待用户选择/修改；
4. **大纲确认**——存在重大新增设定、角色死亡或关系改变时；
5. **正文确认**——正文经过审查修订后，由用户决定是否进入正式状态。

不允许未经用户确认连续生成整部小说并覆盖项目状态。

---

## 5. 原文事实等级

所有重要信息必须标记来源。见 `references/analysis_dimensions.md`。

```text
confirmed        原文明确确认
strong_implied   原文强烈暗示
inferred         根据原文推断
creative         续写新增
user_confirmed   用户确认
rejected         用户否定
```

**不得将模型推断伪装成原文事实。**

---

## 6. 上下文选择规则

生成下一章时**不得每次读取整部小说**。见 `references/context_selection.md`。

优先读取（按重要性）：

1. 目标章纲；2. 场景卡；3. 当前故事状态；4. 相关人物档案；5. 人物知识边界；
6. 相关世界规则；7. 相关伏笔；8. 上一章；9. 语义/关键词相关历史章节；10. 风格摘要。

**必须读取**：当前章纲、场景卡、视角人物状态、关键人物知识边界、本章必须处理的伏笔、相关硬性世界规则、用户锁定要求。

**可优先压缩**：很早以前的非相关章节、次要人物完整档案、无关地点、已完成的低影响事件、低重要度伏笔。

---

## 7. 结构化输出要求

所有结构化数据必须符合 `schemas/` 中的 JSON Schema 契约，并用 `scripts/validate_json.py` 校验。核心数据模型：

- **人物档案**（人物身份/价值观/欲望/恐惧/优缺点/行为/语言/当前状态）—— `schemas/character.schema.json`
- **人物知识**（事实 + 谁知晓/谁不知晓/谁误解）—— `schemas/knowledge.schema.json`
- **伏笔记录**（状态：planted/reinforced/partially_revealed/misdirected/resolved/abandoned）—— `schemas/foreshadowing.schema.json`
- **一致性报告**（问题类型/严重度/位置/证据/建议/状态）—— `schemas/review_report.schema.json`
- 其余（事件/关系/结局方案/大纲/场景卡/故事状态）各自对应 schema。

重构或生成数据后，**必须**用 `scripts/validate_json.py` 验证，拒绝损坏的结构化结果。

---

## 8. 一致性检查流程

每章生成后必须检查，见 `references/consistency_rules.md`：

1. **人物一致性**——性格漂移、行动动机、语言契合、情绪铺垫、能力超限、是否做出明确不会做的事；
2. **知识边界**——是否知道不该知道的信息、是否遗忘已知信息、秘密是否无理由传播、误解是否被当事实；
3. **时间与空间**——时间顺序、能否及时到达、是否同时在多地、昼夜日期合理性；
4. **世界规则**——能力规则、道具归属、社会/科技/魔法规则、新设定铺垫；
5. **情节与伏笔**——事件因果、巧合依赖、偏离章纲、伏笔错误回收、遗漏必须推进的伏笔；
6. **语言与风格**——视角漂移、对话风格、句式偏离、环境描写匹配、重复模板化表达。

报告保存到 `reviews/<chapter_id>_v1.json`。

---

## 9. 版权与安全要求

使用本技能前，要求用户确认文本属于以下至少一种：用户原创 / 用户拥有版权 / 已获授权 / 公版领域 / 合法私人研究。

技能必须：保留原文来源信息；默认在本地项目处理；不主动公开或发布文本；不把模型推断伪装成原作者计划；不声称续写代表原作者；避免不必要地复制大段原文；导出时提示为 AI 辅助创作结果。

详见 `references/copyright_rules.md`。

**文风**只分析抽象叙事特征（人称、视角、句长、对话/心理/环境比例、比喻密度、意象、节奏、克制/诗性/口语化程度），**不承诺** 100% 复制某位在世作者文风。见 `references/style_rules.md`。

---

## 10. 输出规范

续写正文、分析报告、导出文件遵循统一约定，见 `references/output_conventions.md`：

- 正文默认先存 `draft_v1`，不直接作为正式章节；
- 只有用户确认的 `final.md` 进入正式故事状态；
- 导出需提示为 AI 辅助创作结果。

---

## 11. 角色分工

```text
Skill 负责组织工作流；
Python 脚本负责确定性处理(切分/校验/状态/检索/导出)；
语言模型负责语义分析与创作。
```

若要初始化某个小说项目并从零开始走流程，先从 `scripts/init_project.py` 开始；若要继续已有项目，先读 `state/current_state.json` 与最近一个正式章节再决定下一步。
