# novel-continuation

> 一个用于 **AI 辅助小说续写** 的 opencode 技能：读前文 → 提炼可复刻的叙事特征 → 续写后续章节 → 定量校验文风贴近度。只分析抽象叙事风格，**不复制、不冒充任何原作者**。

[![CI](https://github.com/coco54-beep/novel-continuation/actions/workflows/ci.yml/badge.svg)](https://github.com/coco54-beep/novel-continuation/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## 它能做什么

- **完整续写管线**：创建项目 → 导入小说 → 章节切分 → 自动探知篇幅与密度 → 逐章分析与建档 → 结局/章纲 → 场景卡 → 正文 → 一致性检查 → 修订。
- **轻量续写模式**：只需快速续写 1–2 章时，跳过全套档案，直接「读前文 → 抓风格 → 续写 → 快速自检」。
- **篇幅自动探知**：统计原文章节真实字数，作为续写目标字数，不靠人工拍脑袋。
- **密度自动探知**：归并全书叙事「密度档位」（密实 / 中等 / 疏朗），续写强制匹配，破解"续写比原著偏薄、被压成纲要式"。
- **风格定量评分**：把续写与原文基准做密度型指标比对，输出 0–100 的**风格贴近度**，让文风是否达标可复现。
- **分层贴合度体系**：贴近度按「结构(句法/段落/对白) / 语言(用词/方言/叠字/抒情) / 语义(情绪张力)」三层加权，输出总贴合度 + 分项雷达；自带**反动漫决**——检测 AI 腔/爽文套话密度并给出雷区提示。
- **文风分析半自动化**：半自动生成风格指纹脚手架，自动填充确定性指标，文本类细节留给模型提炼。
- **文风范式库**（已脱敏）：按叙事范式（史诗全景 / 章回说书 / 章回武侠 / 现实厚重 / 克制白描 / 诗意田园 / 悬疑盗墓 / 黑道纪实 / 暖心随笔 / 古风玄幻 / 半文白言情 / 古典雅致 / 硬科幻）归纳可复刻要点与高频踩坑点；每范式配一段**自创、无版权**的锚定正文（`references/style_samples.md`）用于直观落地。

## 目录结构

```
SKILL.md            技能入口与指挥中心
prompts/            提示词模板(标准流程 + 轻量模式)
references/         方法论文档(工作流/分析维度/一致性/文风/文风范式库/文风锚定样例/版权/上下文)
scripts/            确定性处理脚本(切分/校验/状态/搜索/导出/篇幅探知/密度探知/风格评分)
schemas/            JSON Schema 契约
templates/          JSON 模板
tests/              脚本层测试 + 合规 fixture(全部为自创样例)
.github/workflows/  GitHub Actions CI(自动跑测试)
```

> 开发与贡献规范见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 快速开始

```bash
# 初始化项目 + 导入 + 切分
python scripts/init_project.py --name my_novel --output ./projects/my_novel
python scripts/import_novel.py --input ./novel.txt --project ./projects/my_novel
python scripts/split_chapters.py --project ./projects/my_novel

# 自动探知篇幅与密度档位
python scripts/estimate_chapter_length.py --project ./projects/my_novel
python scripts/analyze_density.py --project ./projects/my_novel
```

然后按 `SKILL.md` 的标准流程继续（分析文风 → 生成场景卡 → 续写正文 → 一致性检查），或走 `prompts/light_continue.md` 的轻量模式。

## 运行测试

```bash
python -m pytest -q
```

## 版权与合规声明

- 本仓库**只包含工具与方法层**；不附带任何受版权保护的小说原文、续写或评价数据。
- `tests/fixtures/` 中的样例均为**自创、未发布**片段，仅用于演示不同叙事范式，无版权问题。
- 文风分析只针对**抽象叙事特征**（人称 / 视角 / 句长 / 对白占比 / 意象等），**不承诺、也不应被用作"完美复制某位在世作者"**。
- 使用前请确认待处理文本属于：用户原创 / 用户拥有版权 / 已获授权 / 公版领域 / 合法私人研究用途。

## 许可证

[MIT](./LICENSE)
