# 工作流参考（workflow.md）

本文件详述 `novel-continuation` 各阶段的输入、动作与产物。作为 `SKILL.md` 中「标准工作流程」的落地细则。

## 用户项目目录

每部小说一个目录：`projects/<project_id>/`。核心结构见 `SKILL.md` 第 2.2 节。

---

## 阶段一：创建项目

**输入**：小说文件路径；项目名；文本权利类型；可选写作偏好。

**执行**：
```bash
python scripts/init_project.py --name my_novel --output ./projects/my_novel
```

**产物**：项目目录、`project.json`、初始状态、空故事档案、项目说明。

**状态机**：`created → imported → split → analyzing → analyzed → planning → planned → writing → reviewing → completed`。

**状态推进**：每完成一个阶段，用 `scripts/set_status.py --project ./projects/<id> --status <state>` 登记 `project.json#status`（不要手工改 JSON）。脚本推进到的中间状态：导入/切分/探知类脚本会自动置 `split`；其后的 analyze→`analyzed`、结局/大纲→`planning`/`planned`、正文→`writing`/`reviewing`、确认收尾→`completed` 由本脚本完成。

---

## 阶段二：导入小说

支持 TXT / Markdown（MVP）；DOCX / EPUB 后续扩展。

```bash
python scripts/import_novel.py --input ./novel.txt --project ./projects/my_novel
```

导入处理：检测编码 → 统一换行 → 清理无意义空格 → 保留原始文件 → 计算 SHA-256 → 保存导入信息。**不修改原文内容**。

---

## 阶段三：章节切分

```bash
python scripts/split_chapters.py --project ./projects/my_novel
```

默认标题规则（已覆盖真实 txt 常见格式，含方括号包裹）：

```
^\[[^\[\]]{1,80}\]$                                   # 方括号: [第一章] / [第1回 标题] / [序]
^第[零一二三四五六七八九十百千万两0-9]+[章节卷回部].*$
^[一二三四五六七八九十]+、\s*\S+$
^\d{1,3}[、\.．]\s*\S+$
^Chapter\s+\d+.*$
```

脚本会自动跳过页面说明行（`=== … ===`）、去重相邻重复标题（如 `[第一章]` 与紧随的 `第一章`），并可用 `--regex`（可多次）追加自定义正则。

产物：`chapters/original/000N.md` + `indexes/chapter_manifest.json`。章节清单记录 `chapter_id / order / title / path / character_count / sha256`。

若章节识别不确定，**让用户检查，不得擅自覆盖原文**。

---

## 阶段三点五：自动探知篇幅（切分完成后必做）

由脚本自动统计原文章节的**真实篇幅**，写入 `project.json` 的 `target_chapter_length`，作为后续所有章节/场景卡 `target_chars` 的唯一来源，**不依赖调用方手工拍字数**。

```bash
python scripts/estimate_chapter_length.py --project ./projects/my_novel
# 可选 --stat median|mean, 默认 median(对超长/超短异常章节更稳健)
```

统计口径：从 `indexes/chapter_manifest.json` 读取各章 `character_count`（去空白正文字数）。

**产物**：
- `indexes/length_stats.json`：`chapter_count / min / max / mean / median / target_chapter_length / per_chapter`。
- `project.json`：`target_chapter_length` 被改写为探知值。

**后续取用**：生成场景卡、章节大纲、正文时，`{target_chars}` / 场景卡 `target_chars`、章纲 `target_chars` 一律**取自该探知值**（中位数或其按剧情的合理拆分），不再手工填固定数。若单章按场景拆分，各场景 `target_chars` 之和应约等于章节目标字数，并可依剧情轻重做弹性分配（剧情单元饱满即止，不为凑数注水）。

---

## 阶段三点五·B：自动探知密度档位（切分完成后必做）

```bash
python scripts/analyze_density.py --project ./projects/my_novel
```

统计各原文章节的**密度指标**（句长/短句占比/对白占比/段长/方言/叠字/用词集中度），归并出全书主流**密度档位**（`密实`／`中等`／`疏朗`，见 `scripts/style_metrics.py` 的 `classify_density`）。

**产物**：
- `indexes/density_stats.json`：各章指标 + `overall_tier` + 档位分布。
- `project.json` 的 `density_tier`。

**后续取用**：续写正文（`write_scene.md` 步骤0b、`light_continue.md` 第3步）**强制匹配该档位**——密实档要短句多、段落碎、对白/方言/叠字密；疏朗档要句长舒展、抒情记叙多。这是破解"续写比原著偏薄、被压成纲要式"的量化约束。

---

## 阶段四：逐章分析

使用 `prompts/analyze_chapter.md`，对每章输出结构化分析：一句话摘要、详细梗概、叙事功能、时间地点、视角、出场人物(目标/心理/行为/状态变化)、核心事件(因果/即时结果/长期影响)、信息获取与误解、环境描写特征、章节语言特征、情绪曲线、节奏、章末钩子、原文证据、分析置信度。

产物：`analysis/chapters/{chapter_id}.json`（需符合 `schemas/chapter_analysis.schema.json`）。

---

## 阶段五：建立故事档案

所有章节分析完成后，按 `prompts/build_story_bible.md` 汇总生成 `story_bible/` 下的：characters / relationships / events / timeline / locations / factions / items / world_rules / knowledge / foreshadowing。

**键名铁律**：字段名一律以 `schemas/` 对应 schema 的 `properties` 为准，禁止为同一字段造别名键（如 `relation_id` 与 `relationship_id` 并存），否则数据会被污染（实测教训）。可选字段无内容就省略键，尤其 `foreshadowing.recommended_resolution_range` 回次未知时不要写 `[]`。

**必须处理人物别名**（如 林舟 / 小舟 / 林先生 / 队长），用 `prompts/merge_characters.md`。若不能确定是否为同一人物，保存为待确认候选，不得直接合并低置信度人物：

```json
{
  "candidate_entities": ["林舟", "林先生"],
  "suggested_same_entity": true,
  "confidence": 0.71,
  "status": "pending_user_confirmation"
}
```

**完成后校验**（`--items` 对数组逐元素校验，见 `scripts/validate_json.py`）：
```bash
python scripts/validate_json.py --schema schemas/character.schema.json --input projects/<id>/story_bible/characters.json --items
python scripts/validate_json.py --schema schemas/relationship.schema.json --input projects/<id>/story_bible/relationships.json --items
python scripts/validate_json.py --schema schemas/event.schema.json --input projects/<id>/story_bible/events.json --items
python scripts/validate_json.py --schema schemas/knowledge.schema.json --input projects/<id>/story_bible/knowledge.json --items
python scripts/validate_json.py --schema schemas/foreshadowing.schema.json --input projects/<id>/story_bible/foreshadowing.json --items
```
校验失败必须修正，不得跳过。

---

## 阶段六：分析故事阶段

依据主线/支线完成度、核心矛盾、已揭示与未揭示秘密、未完成人物弧、未回收伏笔、推进速度、类型、已有篇幅、冲突强度，判断当前阶段：

```
opening | development | midpoint | escalation | pre_climax | climax | resolution | unknown
```

产物：`analysis/current_stage.json` + `analysis/story_summary.md`。**结果必须给出判断依据**，不能只给结论。

---

## 阶段七：生成结局方案

默认三套：**快速收束 / 标准完结 / 长篇展开**。每套含：方案名、建议剩余章节、预计剩余字数、结局概述、最终冲突、主角结局、主要人物结局、主线解决方式、支线处理、伏笔回收计划、新增设定、原文支撑、推断部分、风险、与前文匹配度。

产物：`planning/ending_proposals.json`。**生成后必须暂停，等待用户选择**。

---

## 阶段八：生成续写大纲

用户选定结局后，生成：

- **续写总纲** `planning/story_outline.json`：核心主题、最终结局、剩余主线、人物弧线、最终冲突、伏笔回收顺序、关键转折点。
- **分卷大纲** `planning/volume_outlines.json`：卷名、起止章节、阶段目标、核心冲突、关键转折、人物变化、卷末状态。
- **章节大纲** `planning/chapter_outlines.json`：章节编号、名称、目标、出场人物、时间地点、核心事件、事件因果、人物心理变化、人物关系变化、信息增量、伏笔操作、环境特征、语言与节奏、章末钩子、目标字数。

---

## 批量产物落盘纪律（阶段八/九 适用）

一旦单次要产出大批量 JSON（如一次规划 10+ 章章纲、给某卷逐章出场景卡），**不要先在上下文里排完整套再一次性落盘**：

1. 分成若干小批，各写临时文件（如 `planning/_chapters_a.json`），主进程再合并成正式文件；
2. 长产物「先写盘、再汇报」，写完一批立即确认落盘，避免上下文超限导致整批静默丢失（实测：一次性产出 10 章章纲的子智能体多次空返回且零落盘）；
3. 阶段十「按剧情单元分段生成再拼接」的超长正文策略，与章纲/场景卡遵循同一逻辑。

---

## 阶段八点五：分析文风（写正文前必做）

使用 `prompts/analyze_style.md`，提取全书风格指纹 `analysis/style_profile.json`。

**前置**：先 `python scripts/build_style_profile.py --project ./projects/my_novel` 生成脚手架（自动填充确定性字段：密度档位/目标篇幅/量化指标）。
**填充**：把提炼的抽象特征与具体抓手填入脚手架的文本类/清单类字段。
**校验**：`python scripts/validate_json.py --schema schemas/style_profile.schema.json --input analysis/style_profile.json`。

**必须**覆盖两类特征：
- **抽象特征**：句长、对话/心理/环境比例、比喻密度、节奏、视角等。
- **具体抓手特征**（决定「像不像」的关键）：文化符号清单（游戏/动漫/电影梗）、生活细节质感（品牌/绰号/道具/习惯）、悲喜突变节奏、角色口头禅。

续写正文时**必须先读取并对照该风格指纹**，沿用其中的具体符号与细节，而非自创通用比喻。详见 `references/style_rules.md`。

---

## 阶段九：生成场景卡

正式写正文前，为目标章节生成场景卡。产物：`scenes/{chapter_id}.json`。

每场景含：场景序号、时间、地点、视角人物、出场人物、场景目标、每个人物目标、已知信息、未知信息、误解、冲突、行动、情绪变化、场景结果、需推进伏笔、与下一场景衔接、目标字数。

**目标字数（`target_chars`）** 取自阶段三点五的自动探知值 `project.json/target_chapter_length`，按剧情单元拆分到各场景；剧情单元完整饱满即为准，**可依剧情安排弹性分配**，不为凑数注水、也不被固定字数压扁节奏。

---

## 阶段十：生成章节正文

**上下文装配顺序**（见 `context_selection.md`）：

1. 本章大纲 → 2. 本章场景卡 → 3. 上一章正文或摘要 → 4. 相关人物当前状态 → 5. 相关人物知识边界 → 6. 相关人物语言风格 → 7. 当前地点 → 8. 相关世界规则 → 9. 本章涉及伏笔 → 10. 相关原文章节证据 → 11. 全书风格指纹 → 12. 用户写作要求。

长章节**按场景生成**，不建议一次生成整章。产物：`chapters/generated/{chapter_id}/draft_v1.md`。**生成后不能立即标记为正式章节**。

**篇幅控制**：本章目标字数取自 `project.json/target_chapter_length`（自动探知值），各场景 `target_chars` 之和约等于该值。写作时以**剧情单元完整 + 符合作者叙事节奏与程式**为第一原则，字数是结果而非目标：剧情饱满即止，避免为凑数注水或强行削短。

### 超长章节：按剧情单元分段生成

当单章目标字数（`target_chapter_length`，或某章的实际规划长度）**明显超过模型合理单次输出的上限**（如古典章回体/史诗型小说的单回常在 5000 字以上，金庸、水浒、白鹿原甚至可达一万至数万字）时，**不要一次生成整章**，而应按剧情单元拆分、逐段生成、最后拼接。这是经 21 部全类型测试后沉淀的硬性策略（《射雕》《神雕》《天龙》《水浒》《白鹿原》等超长回目若一次生成，要么超时、要么被迫大幅收敛，导致篇幅与密度普遍偏薄，成为该类作品最主要的失分点）。

**分段规则**：
1. **切分依据**：按场景卡的自然剧情单元切，而非机械按字数均摊。一个"生成块"应是一段完整的情节（如一场打斗、一次夜谈、一段回忆、一个地点转移），有清晰的起承转合与可衔接的边界。
2. **每段目标字数**：以"该剧情单元饱满完成为准"，一般控制在约 2000–4000 字/段（或按输出预算折半），各段之和约等于章节目标字数即可。
3. **逐段生成**：每段复用 `prompts/write_scene.md`，上下文只装配与该段相关的最小集（本段场景卡 + 相关人物状态/知识边界 + 上一段结尾一句 + 风格指纹 + 必要伏笔），**不要每次重读整章、整部小说**，避免上下文膨胀与超时。
4. **段间衔接**：每段结尾落在本段结果上，留好与下一段的钩子；下一段开头自然承接上一段结尾的人物状态与场景。
5. **拼接成章**：按顺序把各段正文写入 `chapters/generated/{chapter_id}/draft_v1.md`。**生成后不能立即标记为正式章节**，仍需走一致性检查与修订。
6. **保留余地**：若某段是对原作风格有决定性影响的关键场景（如《水浒》的辞赋铺陈、《金庸》的打斗工笔），宁可让该段略长、不强行削短，以保住文风与密度——篇幅是结果而非目标。

---

## 阶段十一：一致性检查

使用 `prompts/review_chapter.md`，检查六类：人物一致性、知识边界、时间空间、世界规则、情节伏笔、语言风格。详见 `consistency_rules.md`。

**可附加定量文风评分**：用 `scripts/score_style.py` 把续写与基准原文章节做密度型指标比对，得到**风格贴近度**（0–100，越低越贴近原文），并写入 `reviews/style_metrics.json` 作为语言风格一项的**量化佐证**：

```bash
python scripts/score_style.py --project ./projects/my_novel \
  --baseline-index 8 --sample-rel "chapters/generated/0009_0010/draft_v1.md" \
  --out ./reviews/style_metrics.json
```

贴近度过低(<60)时，重点查句长/段落碎度/对白占比是否偏离 `density_tier`，或在 `style_library.md` 对应范式的踩坑点上修正。

产物：`reviews/{chapter_id}_v1.json`。

---

## 阶段十二：修订与确认

根据审查报告创建 `chapters/generated/{chapter_id}/revised_v2.md`。修订要求：优先局部修改；不随意重写没问题的段落；不改变用户锁定内容；不引入新设定冲突；记录主要改动；严重问题再次检查。

用户确认后保存 `final.md`。**只有 `final.md` 可以进入正式故事状态**。

---

## 阶段十三：更新故事状态

```bash
python scripts/update_state.py --project ./projects/my_novel --chapter 0051
```

更新：人物位置、身体/心理状态、当前目标、掌握信息、误解、关系、道具持有者、势力状态、事件结果、未解决冲突、伏笔状态、世界新增事实。

**更新前创建快照** `state/snapshots/after_0051.json`，再更新 `state/current_state.json`。

---

## 从已有项目继续

先读取：`project.json`、`state/current_state.json`、`outlines/chapter_outlines.json`、最近一个正式章节、最近一个一致性报告，然后决定下一步。

---

## 阶段十四：轻量续写模式（可选分支）

> 当用户**只要快速续写 1–2 章**、且无需长期跨章一致性时，走此分支；完整流程（阶段四至十三的建档/结局/章纲/场景卡/一致性）可跳过。详见 `prompts/light_continue.md`。

**触发条件**（全部满足才走轻量模式）：
- 续写目标仅 1–2 章；
- 人物/伏笔/时间线简单，不需要长期维护一致性；
- 用户不要结局方案、多章规划。

**否则用完整流程**（多章长线、需跨章一致性、需结局/章纲时）。

**5 步**：
1. 初始化 + 导入 + 切分 + 探知篇幅（脚本不变）：`init_project.py → import_novel.py → split_chapters.py → estimate_chapter_length.py`。
2. 确定续写起点：精读续写起点章的**结尾**（人物状态与未完成线索）+ 开头章抓文体，其余用 grep/关键词取关键段，**不逐字通读整部**。
3. 抓轻量风格指纹：对照 `references/style_library.md` 归类范式，提炼视角/声口/方言市井味/情感呈现/意象抓手/章末钩子，并列出该范式的高频踩坑点作为续写红线（不必建完整 `style_profile.json`）。
4. 续写正文：按 `write_scene.md` 思路但**不生成场景卡**——直接按剧情单元写成章节；单章目标字数超输出上限时**按剧情单元分段生成再拼接**（见阶段十）。产物 `chapters/generated/{chapter_id}/draft_v1.md`。
5. 快速自检：按 `style_library.md` 通用自查清单反查（视角漂移/声口混同/具体抓手/事件承载情绪/文风毛边俗味糙感/篇幅密度），对照该范式踩坑点修正一次；有重大偏差时再走 `review_chapter.md`。

**定位**：轻量模式是**快速试写**，若用户认可并想长期续写，再升级到完整流程以保长线一致性。
