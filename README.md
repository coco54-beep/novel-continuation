# Novel Continuation Skill（长篇小说分析与续写技能）

面向未完成小说、原创小说和授权文本的长篇叙事分析与续写技能。无需部署服务器，用文件即可完成「分析前文 → 建立故事档案 → 规划结局 → 生成章纲 → 逐章续写 → 一致性检查 → 状态更新 → 导出成书」的完整闭环。

## 安装

1. 将本目录复制到对应技能目录：
   - opencode：`~/.config/opencode/skill(s)/novel-continuation/` 或项目 `.opencode/skill(s)/novel-continuation/`
   - 其它 Agent 工具：放入其技能加载路径。
2. 安装依赖（仅脚本需要）：

```bash
pip install -r requirements.txt
```

3. 重启对应 Agent 工具，以加载本技能。

## 使用

### 最简用法

```text
使用 novel-continuation 技能分析《我的小说.txt》，创建续写项目，并告诉我故事当前写到了什么阶段。
```

分析完成后：

```text
给我生成三个不同篇幅的完结方案。
```

选定方案后：

```text
采用标准完结方案，生成剩余章节大纲。
```

然后逐步生成场景卡、正文、审查修订：

```text
生成下一章的场景卡。
按照场景卡续写下一章（篇幅由技能自动探知作者单章字数，无需手动指定）。
检查这一章的人物、时间线、知识边界、伏笔和文风问题，修订后更新故事状态。
```

### 一句话完整流程

```text
分析 novel.txt，生成三个结局方案。我确认方案后，再生成章纲并逐章续写。每章生成后必须先做一致性检查，不要自动确认。
```

技能会执行到「等待用户选择结局方案」为止，不会跳过确认。

### 继续已有项目

```text
打开 projects/my_novel 项目，读取当前进度并继续生成下一章。
```

### 轻量模式（只快速续写一两章）

若你只想**接着某章快速续写 1–2 章看看下文**，且不需要长期跨章一致性、结局方案、章纲，可走轻量模式——跳过建档/结局/场景卡，只做「读前文 → 抓风格 → 续写 → 快速自检」。

```text
续写《我的小说》正文第 8 章之后的第 9、10 章，只要先续这两章看看，不用规划结局。
```

轻量模式会复用初始化/导入/切分/探知篇幅这几步机械脚本，然后精读续写起点章与开头章抓文体、对照 `references/style_library.md` 归范式，直接按剧情单元续写并快速自检。若你觉得方向对了、想长期续写，再升级到完整流程。触发判定与步骤见 `prompts/light_continue.md` 与 `references/workflow.md` 阶段十四。

### 篇幅自动探知

技能会在章节切分后自动统计原文章节真实字数，写入 `project.json#target_chapter_length`，作为所有续写章 / 场景卡的 `target_chars` 来源，**不要求用户手工指定字数**。手动重跑：

```bash
python scripts/estimate_chapter_length.py --project ./projects/my_novel
```

默认取篇章**中位数**（对超长/超短异常章节稳健），可用 `--stat mean` 改用均值。篇幅以「剧情单元完整 + 符合作者叙事节奏」为第一原则，字数是结果而非目标。

### 密度自动探知（破解"比原著偏薄"）

切分后运行 `scripts/analyze_density.py`，统计各原文章节的**密度指标**（句长 / 短句占比 / 对白占比 / 段长 / 方言 / 叠字），归并出全书主流**密度档位**（`密实` / `中等` / `疏朗`）写入 `project.json#density_tier`。续写正文会强制匹配该档位——密实档要短句多、段落碎、对白/方言/叠字密；疏朗档要句长舒展、抒情叙述多。这解决了续写普遍"比原著更工整干净、被压成纲要式"的问题。

```bash
python scripts/analyze_density.py --project ./projects/my_novel
```

### 风格贴近度量化评分

写作/审查后可用 `scripts/score_style.py` 把续写与基准原文章节做**密度型指标比对**，得到**风格贴近度**（0–100，越低越贴近原文），作为语言风格的量化佐证：

```bash
python scripts/score_style.py --project ./projects/my_novel \
  --baseline-index 8 --sample-rel "chapters/generated/0009_0010/draft_v1.md" \
  --out ./reviews/style_metrics.json
```

### 超长章节分段生成

古典章回体 / 史诗型小说（金庸、水浒、白鹿原等）的单回常在 5000 字以上，甚至可达数万字，一次生成会超时或被大幅收敛导致篇幅密度偏薄。这类超长章节**按剧情单元分多个「生成块」逐段生成、再拼接**成 `chapters/generated/{chapter_id}/draft_v1.md`：

- 每段以「该剧情单元饱满完成」为准，一般控制在约 2000–4000 字；
- 每段只装配与本段相关的最小上下文（本段场景卡、相关人物状态/知识边界、上一段结尾一句、风格指纹、必要伏笔），不重读整章整书；
- 段结尾留衔接钩子，各段按序拼接；决定文风的关键场景（辞赋铺陈、打斗工笔）宁可该段略长、不强行削短。

详细规则见 `references/workflow.md` 阶段十。

## 目录结构

```
novel-continuation/
├─ SKILL.md            技能入口
├─ plan.md             开发计划
├─ README.md           本文件
├─ LICENSE
├─ requirements.txt
├─ scripts/            确定性处理脚本
├─ references/         方法论文档
├─ schemas/            JSON Schema 契约
├─ templates/          JSON 模板
├─ prompts/            提示词模板
└─ tests/              自动化测试与 Fixtures
```

## 关键依赖

- `charset-normalizer`：编码检测
- `jsonschema`：JSON Schema 校验
- `python-docx`：DOCX 导入（后续扩展）
- `EbookLib`：EPUB 导入（后续扩展）
- `beautifulsoup4`：HTML 清洗（后续扩展）
- `pytest`：测试

> Skill 本身使用宿主 Agent 的语言模型，不强制安装独立 LLM SDK。

## 权限与版权

使用前请确认文本属于：用户原创 / 用户拥有版权 / 已获授权 / 公版领域 / 合法私人研究用途。详见 `references/copyright_rules.md`。

## 文档

- 工作流细节：`references/workflow.md`
- 文风范式库：`references/style_library.md`（多类型小说可复刻文风要点与高频踩坑点，续写/一致性检查时对照）
- 能力参照与复测基准：`tests/benchmark_novels.md`（21 部全类型小说的范式归类、得分与复测方法；含合规演示样本 `tests/fixtures/style_samples.txt`）
- 所有数据契约：`schemas/`
- 所有提示词：`prompts/`
