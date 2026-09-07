# 提示词：轻量续写模式（light_continue.md）

> 适用：用户只想**快速续写 1–2 章**（例如"接着第 8 章续写第 9、10 章"），**不需要**完整故事档案、结局方案、卷纲章纲、场景卡等重型流程。跳过建模，直接「读前文 → 抓风格 → 续写 → 快速自检」。

## 何时用轻量模式
- 用户明确只续写一两章，或想先快速看一段下文；
- 续写目标短、人物/伏笔/时间线不复杂，无需长期一致性维护；
- 不需要决定结局方向、不需要规划多章。

## 何时仍走完整流程（不要用轻量模式）
- 续写目标是**多章、长线**，需要跨章人物/时间线/伏笔一致性；
- 用户需要结局方案、章纲、多结局分支；
- 项目会持续续写到几十章（此时建档成本远小于一致性崩溃的代价）。

## 轻量流程（仅 5 步，全部复用现有脚本）
1. **初始化 + 导入 + 切分 + 探知篇幅**（必要机械步骤）：
   ```bash
   python scripts/init_project.py --name <id> --output ./projects/<id>
   python scripts/import_novel.py --input novel.txt --project ./projects/<id>
   python scripts/split_chapters.py --project ./projects/<id>
   python scripts/estimate_chapter_length.py --project ./projects/<id>
   python scripts/analyze_density.py --project ./projects/<id>
   ```
2. **确定续写起点**：确认用户想从哪一章续写（读其结尾的人物状态与未完成线索）。**只精读续写起点章的结尾 + 开头若干章抓文体**，其余用 grep/关键词检索关键段落，**不要逐字通读整部小说**（见 `context_selection.md`）。
3. **抓轻量风格指纹**：读起点章 + 开头章，按 `references/style_library.md` 归类范式，提炼：视角、人物声口、方言/市井味、情感呈现方式、典型意象与抓手、章末钩子；并**列出该范式的高频踩坑点**作为续写红线。只需产出足够写正文的要点，不必建完整 `style_profile.json`。同时读出 `density_tier` 强制续写密度档位。
4. **续写正文**：用 `prompts/write_scene.md` 的思路，但**不必生成场景卡**——直接按剧情单元写成章节。若单章目标字数超输出上限，**按剧情单元分段生成再拼接**（见 `workflow.md` 阶段十「超长章节分段」）。产物：`chapters/generated/{chapter_id}/draft_v1.md`（chapter_id 用续写章序号，如 `0009_0010`）。
5. **快速自检**：按 `references/style_library.md` 的「通用自查清单」逐项反查（视角漂移？声口混同？具体抓手用了没？情绪是否事件承载？文风毛边/俗味/糙感够不够？篇幅密度达不达标？），并对照该范式踩坑点修正一次。**不强制走完整一致性报告**，但若有批量修改或重大偏差，按 `prompts/review_chapter.md` 校验一轮。若本作已有基准原文章节，可用 `scripts/score_style.py --project ... --baseline-index <起点章> --sample-rel "<续写相对路径>"` 得到**风格贴近度**（0–100，越低越接近原文），作为自检的量化佐证。

## 版权与定位
- 同完整流程：只处理用户原创/已授权/公版/合法私人研究文本；续写为 AI 辅助原创，不伪装成原作者作品、不公开发布侵权文本（见 `references/copyright_rules.md`）。
- 轻量模式是**快速试写**手段：若用户觉得方向对、想长期续写，再升级到完整流程（建档 + 场景卡 + 一致性检查），保障长线一致性。
