# 提示词：分析全书风格指纹（analyze_style.md）

## 用途
分析整部小说的抽象叙事风格，产出 `analysis/style_profile.json`（全书风格指纹），供续写时还原。

## 输入
- 若干代表性章节原文：{sample_chapters}
- 章节分析（可选）：{chapter_analyses}

## 任务
提炼全书可复刻的叙事特征，**只分析抽象特征，不涉及作者身份**。

**前置**：先运行 `scripts/build_style_profile.py --project ./projects/<id>` 生成脚手架 `analysis/style_profile.json`（已自动填充确定性字段：密度档位/目标篇幅/量化指标）。
**分析后**：把提炼出的抽象特征与具体抓手填入脚手架的文本类/清单类字段，最后用 `scripts/validate_json.py --schema schemas/style_profile.schema.json --input analysis/style_profile.json` 校验。

分析时先**归类叙事范式**：对照 `references/style_library.md`（文风示例库）的总览表与本作特征，判断本作属于史诗全景/章回说书/章回武侠/现实厚重/克制白描/诗意抒情/悬疑第一人称/黑道纪实/暖心随笔/古风玄幻/半文白言情/古典雅致/硬科幻 中的一类或多类，并把该范式的「可复刻要点」「具体抓手」「高频踩坑点」写入 `style_profile.json` 的对应字段（尤其 `emotional_rhythm` / `emotion_presentation` / `catchphrases` 要与踩坑点联动），供续写时规避。

## 输出

落盘文件 `style_profile.json` 的键名**严格以 `schemas/style_profile.schema.json` 的 properties 与脚手架 `scripts/build_style_profile.py` 生成的结构为准**（即 `schema_version/project_id/paradigm/density_tier/perspective/voice/sentence_rhythm/emotion_presentation/dialogue_ratio/description_style/cultural_references/material_details/catchphrases/pitfalls/style_metrics/notes`）。下面的 JSON 只是便于阅读的示意，不是键名依据；填脚手架时不要另造键（如不要写 `narrative_person/point_of_view_scope/avg_sentence_length` 等旧示例键）。

```json
{
  "paradigm": "古典雅致 / 家族兴衰(可叠章回说书、半文白)",
  "perspective": "第三人称全知为主，叙述者在话本评点腔与人物限知间滑移",
  "voice": "半文半白的雅白话，评点式叙述、市井口吻与诗性书面语杂糅",
  "sentence_rhythm": "疏朗长句为骨，长短离合，情绪处可转短句急收",
  "emotion_presentation": "用事件/物件/诗句承载情绪，写到垂泪低头即收，不直说不补金句",
  "dialogue_ratio": "对白偏多且言语有机锋，口吻随身份等级分层",
  "description_style": "白描为主，服饰器物、岁时节令细节可考，兼用诗词判词式写景",
  "cultural_references": ["女娲补天神话(出处)", "太虚幻境判词判曲(出处)", "僧道谶语(出处)"],
  "material_details": ["通灵玉铭文(出处)", "冷香丸海上仙方(出处)", "某器物风波(出处)"],
  "catchphrases": ["某角色口头禅(出处)"],
  "pitfalls": ["用现代白话破坏语感", "把古白话对白写成文言", "句子平均化缺少跌宕", "形容词直说情绪而非借物呈现"],
  "notes": "范式归类依据与可复刻要点；不承诺复制某位作者"
}
```

## 要求
1. **必须**提取以上「具体抓手」类字段（`cultural_references` / `material_details` / `emotional_rhythm` / `emotion_presentation` / `catchphrases`），不得只给抽象概括。
2. 续写时必须沿用这些具体符号与细节，而不是自创通用比喻。
3. 形象化字段给出**原文中出现过的具体例子**，而非编造。
4. `emotion_presentation` 应写明本作如何呈现悲感/衰感（事件 vs 形容词、是否保留冷场、梗如何咬合角色思维），续写时据此落地。

## 边界
- 不得承诺复制具体某位**在世**作者；表述为「按用户文本可观察到的抽象叙事特征续写」。
- 不将模型推断伪装成作者意图。
