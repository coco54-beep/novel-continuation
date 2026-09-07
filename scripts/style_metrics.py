#!/usr/bin/env python3
"""可复用的中文文体指标计算模块。

被以下脚本共用:
  - score_style.py       (原文 vs 续写的定量文风比对)
  - analyze_density.py   (章节"密度档位"归并)

只输出【密度型】指标(比例/均值/每千字计数), 不输出绝对值, 便于跨篇幅比较。

指标见各 compute_* 函数文档; 统一入口为 compute_metrics(text) -> dict。
"""
import re
from collections import defaultdict

# 句末标点(中文)
SENT_END = "。！？…；"
# 成对引号(用于对白占比)
QUOTE_PAIRS = [("“", "”"), ("『", "』"), ("「", "」"), ("\"", "\""), ("《", "》"), ("（", "）")]

# 常见方言/市井口语词(覆盖关中/东北/湘西/山东/新疆/川渝/粤等多地), 命中计数
DIALECT_WORDS = [
    "甭", "啥", "咋", "咋呼", "墨迹", "整得", "恓惶", "犟", "营务", "言传", "这搭",
    "悖时", "砍脑壳", "砸锅", "撒", "勺子", "卖沟子", "嘎", "棒槌", "憋", "咯吱", "咔",
    "喽", "哩", "俺", "咱", "嘚瑟", "耍彪", "弄啥", "干哈", "娃子", "细伢", "鬼崽",
    "没得", "莫", "晓得", "劳什子", "孽障", "豁出去了",
]


def strip_space(text: str) -> str:
    """去空白得到"实际正文字符串"(不含换行/空格)。"""
    return re.sub(r"\s+", "", text)


def split_sentences(text: str) -> list:
    """按中英文句末标点切句, 返回非空句子列表。"""
    if not text:
        return []
    parts = re.split(r"[。！？…；]+", text)
    return [p for p in parts if p.strip()]


def compute_sentence_len(text: str) -> list:
    """返回各句长度(字符, 去空白后按句切)。"""
    body = strip_space(text)
    return [len(s) for s in split_sentences(body) if s]


def compute_dialogue_ratio(text: str) -> float:
    """对白占比 = 位于引号内的字符数 / 总字符数。"""
    body = strip_space(text)
    total = len(body)
    if total == 0:
        return 0.0
    quote_starts = set(s for s, _ in QUOTE_PAIRS)
    quote_ends = set(e for _, e in QUOTE_PAIRS)
    depth = 0
    in_quote = 0
    for c in body:
        if c in quote_starts:
            depth += 1
        elif c in quote_ends and depth > 0:
            depth -= 1
        if depth > 0:
            in_quote += 1
    return in_quote / total


def compute_dialect_hits(text: str) -> int:
    """方言/市井口语词命中次数。"""
    body = strip_space(text)
    return sum(body.count(w) for w in DIALECT_WORDS)


def compute_reduplication(text: str) -> int:
    """叠字(AA / AABB / ABB 型)出现次数, 用去重避免重复计数。"""
    body = strip_space(text)
    if not body:
        return 0
    count = 0
    # AA 型: 任意相邻重复汉字
    aa = set()
    for m in re.finditer(r"([\u4e00-\u9fff])\1", body):
        aa.add(m.start())
    count += len(aa)
    # AABB/ABB 型按字面计(可能包含部分AA, 但已按起点去重逻辑分离, 此处不作二次剔除)
    count += len(re.findall(r"([\u4e00-\u9fff])\1([\u4e00-\u9fff])\2", body))
    count += len(re.findall(r"([\u4e00-\u9fff])([\u4e00-\u9fff])\2", body))
    return count


def compute_overlap_bigram_ratio(text: str) -> float:
    """用词集中度代理: top-30 高频二元组字数 / 总字数。值越大表示用词越重复集中。"""
    han = re.sub(r"[^\u4e00-\u9fff]", "", strip_space(text))
    total = len(han)
    if total < 2:
        return 0.0
    counts = defaultdict(int)
    for i in range(len(han) - 1):
        counts[han[i] + han[i + 1]] += 1
    top = sorted(counts.values(), reverse=True)[:30]
    return sum(top) / total


def compute_para(text: str) -> tuple:
    """返回 (平均段落字数, 每千字段落数)。"""
    paras = [re.sub(r"\s+", "", p) for p in re.split(r"\n+", text) if p.strip()]
    if not paras:
        return 0.0, 0.0
    total = sum(len(p) for p in paras)
    avg = total / len(paras)
    per_1k = (len(paras) / total) * 1000 if total else 0
    return round(avg, 2), round(per_1k, 3)


def compute_metrics(text: str) -> dict:
    """统一入口: 计算一段中文文本的全部密度型文体指标。"""
    body = strip_space(text)
    total = len(body)
    if total == 0:
        return {"error": "没有可统计的正文"}

    sent_lens = compute_sentence_len(text)
    mean_sentence_len = sum(sent_lens) / len(sent_lens) if sent_lens else 0
    short_ratio = sum(1 for L in sent_lens if L <= 15) / len(sent_lens) if sent_lens else 0

    avg_para_len, para_per_1k = compute_para(text)

    return {
        "total_chars": total,
        "mean_sentence_len": round(mean_sentence_len, 2),
        "short_sentence_ratio": round(short_ratio, 4),
        "dialogue_ratio": round(compute_dialogue_ratio(text), 4),
        "overlap_bigram_ratio": round(compute_overlap_bigram_ratio(text), 4),
        "dialect_hits_per_1k": round(compute_dialect_hits(text) / total * 1000, 3),
        "reduplication_per_1k": round(compute_reduplication(text) / total * 1000, 3),
        "avg_para_len": avg_para_len,
        "para_per_1k": para_per_1k,
    }


def classify_density(metrics: dict) -> str:
    """根据指标归类"叙事密度档位"。

    密实档: 短句多、段落碎、对白/方言/叠字密, 画面颗粒感强(武侠/黑道/盗墓/克白描)。
    疏朗档: 句长偏长、段落少、抒情/白描舒展, 画面节奏放(诗意/史诗/暖心)。
    中等档: 介于两者之间(多数)。
    判定以 [短句占比, 段/千字, 对白占比] 三项加权为主, 其余为辅助。
    """
    short = metrics.get("short_sentence_ratio", 0)
    para = metrics.get("para_per_1k", 0)
    dlg = metrics.get("dialogue_ratio", 0)
    overlap = metrics.get("overlap_bigram_ratio", 0)
    s_len = metrics.get("mean_sentence_len", 0)

    score = 0.0
    score += short * 30            # 短句占比(0~1)
    score += min(para / 60, 1) * 30  # 段落碎度(每千字段落, 60+视为很碎)
    score += dlg * 20               # 对白占比
    score += min(overlap, 0.3) / 0.3 * 10  # 用词集中
    score += max(0, min(20 - s_len, 10)) / 10 * 10  # 句长短加分

    if score >= 55:
        return "密实"
    if score <= 38:
        return "疏朗"
    return "中等"
