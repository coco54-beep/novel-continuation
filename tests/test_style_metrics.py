"""对 style_metrics.py 公共文体指标模块做单元测试。"""
import os
import sys

import pytest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

from style_metrics import (
    classify_density,
    compute_cliche_hits,
    compute_dialogue_ratio,
    compute_metrics,
    compute_reduplication,
)


def test_compute_metrics_basic():
    text = "天黑了。他站在门口。\n{quotes}\n"
    cfg = "“你来了。”她说。"
    m = compute_metrics(text.format(quotes=cfg))
    assert "error" not in m
    assert m["total_chars"] > 0
    assert m["mean_sentence_len"] > 0
    assert 0 <= m["dialogue_ratio"] <= 1
    assert m["avg_para_len"] > 0


def test_dialogue_ratio_detects_quotes():
    no_quote = "天黑了。他站着。"
    with_quote = "“你来了。”她说。"
    assert compute_dialogue_ratio(with_quote) > compute_dialogue_ratio(no_quote)


def test_reduplication_counts():
    assert compute_reduplication("他她他她他她") == 0  # 非重复相邻
    assert compute_reduplication("看看") >= 1  # AA
    assert compute_reduplication("干干净净") >= 1  # AABB/AA


def test_classify_density_tiers():
    dense = compute_metrics("“走！”他吼。抄棍。砸门。萧正倒退三步。才喘口气。又冲上去。")
    sparse = compute_metrics("窗外的雨落了一夜，她静静坐着，看那盏灯，想起许多年以前。")
    d = classify_density(dense)
    assert d in ("密实", "中等", "疏朗")


def test_compute_metrics_empty():
    assert "error" in compute_metrics("   ")


def test_metrics_include_layered_and_cliche():
    plain = "他走进屋，坐下，端起碗喝了一口水。"
    ai = "那一刻，他目光深邃，嘴角勾起一抹笑意，仿佛命运的齿轮开始转动。"
    m_plain = compute_metrics(plain)
    m_ai = compute_metrics(ai)
    for key in ("emotion_markers_per_1k", "turnword_per_1k", "affective_adj_ratio",
                "cliche_per_1k", "cliche_hits"):
        assert key in m_plain
    # AI腔样本应命中更多套话雷区
    assert compute_cliche_hits(ai) > compute_cliche_hits(plain)
    assert m_ai["cliche_hits"] > m_plain["cliche_hits"]
