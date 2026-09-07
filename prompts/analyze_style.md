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
```json
{
  "narrative_person": "第三人称",
  "point_of_view_scope": "限知(以主角视角)",
  "avg_sentence_length": "短句为主",
  "sentence_mix": "长短句约 3:1",
  "dialogue_ratio": 0.35,
  "mental_description_ratio": 0.2,
  "environment_description_ratio": 0.2,
  "action_density": 0.25,
  "metaphor_density": "较高",
  "sensory_preference": ["视听", "触感"],
  "high_frequency_imagery": ["雨", "旧物件", "霓虹"],
  "transition_style": "硬切为主，少量留白",
  "chapter_hook": "多以悬念句收尾",
  "pacing": "中速，张弛交替",
  "restraint": "克制",
  "poetic_degree": "中等",
  "colloquial_degree": "高",

  "cultural_reference_density": "极高",
  "cultural_references": [
    {"source": "游戏/动漫/电影", "items": ["星际争霸的母巢/大和炮/机枪兵", "Wall-E 的 Eve", "黑客帝国 Neo", "日漫白金之星"]}
  ],
  "material_details": [
    "高仿万宝龙表", "N96 手机", "红点(IBM 红帽)打星际", "泽太子绰号",
    "寂寞的贪吃蛇笔名", "采蒲公英付告白", "蹭报刊亭看杂志"
  ],
  "emotional_rhythm": "悲喜突变，几句话内从憋屈跳到爆发",
  "emotion_presentation": "用具体事件承载情绪(如被当字母'e'、递花被忽略)，不用形容词旁白；难堪时保留冷场不急着化解；文化梗是角色当下自然联想而非硬排比喻",
  "catchphrases": ["我有一个偶尔会发疯的人呐", "别是三年三年又三年", "啊呸呸呸"]
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
