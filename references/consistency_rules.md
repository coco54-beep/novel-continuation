# 一致性检查规则（consistency_rules.md）

每章正文生成后必须检查以下六类问题。报告遵循 `schemas/review_report.schema.json`。

---

## 1. 人物一致性

- 性格是否漂移
- 行动是否有动机
- 语言是否符合人物（说话风格、用词、称呼）
- 情绪变化是否有铺垫
- 能力是否超出设定
- 是否做出明确不会做的事情（`behavior_profile.will_not_do`）
- **称呼/辈分是否符合 `relationships.json` 的关系档案**：核对人物间的亲属/尊卑关系，杜绝辈分颠倒——反例：贾珍（玉字辈）称同辈弟媳凤姐为「婶子」；秦氏（草字辈，贾蓉之妻）称族叔宝玉为「侄儿」。这类错误单靠人物档案查不出，必须把 `relationships.json` 一并作为审查输入。

## 2. 知识边界

- 人物是否知道不应知道的信息
- 人物是否忘记已经知道的信息
- 秘密是否被无理由传播
- 人物误解是否被错误当成事实

## 3. 时间与空间

- 时间顺序是否冲突
- 人物能否及时到达地点
- 人物是否同时出现在不同地点
- 昼夜和日期是否合理

## 4. 世界规则

- 能力规则是否被违反
- 道具归属是否正确
- 社会、科技或魔法规则是否一致
- 新设定是否缺少铺垫

## 5. 情节与伏笔

- 事件是否有因果
- 是否依赖过多巧合
- 是否偏离章纲
- 伏笔是否错误回收
- 是否遗漏本章必须推进的伏笔

## 6. 语言与风格

- 视角是否漂移
- 对话风格是否异常
- 句式是否明显偏离
- 环境描写是否匹配
- 是否存在重复和模板化表达

---

## 问题记录字段

| 字段 | 内容 |
|---|---|
| `type` | character_consistency / knowledge_boundary / time_space / world_rules / plot_foreshadowing / language_style |
| `severity` | low / medium / high / critical |
| `location` | 大致位置（如「第14段」） |
| `description` | 问题描述 |
| `evidence` | 相关事实/伏笔/档案引用（如 `fact_0012`） |
| `suggestion` | 修复建议 |
| `status` | open / fixed / wont_fix |

---

## 报告与决策

- `overall_score`：0–100
- `decision`：approved / revision_required / major_revision_required / rejected

**严重问题（critical）必须修复后再次检查。**
