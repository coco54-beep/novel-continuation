"""对 score_style.py 做单元测试: 文本对与项目模式。"""
import json
import os
import tempfile

from conftest import run_script


def test_score_style_text_mode(tmp_path):
    baseline = tmp_path / "base.md"
    sample = tmp_path / "sample.md"
    out = tmp_path / "out.json"
    baseline.write_text("天黑了。他冷冷地说：“走吧。”然后摔门而出。", encoding="utf-8")
    sample.write_text("天黑了。他冷冷地说：“走吧。”然后摔门而出。", encoding="utf-8")
    rc, out_s, err = run_script(
        "score_style.py", "--baseline", str(baseline), "--sample", str(sample), "--out", str(out)
    )
    assert rc == 0, err
    with open(out, encoding="utf-8") as f:
        data = json.load(f)
    assert "style_similarity_score" in data
    assert "baseline_metrics" in data and "sample_metrics" in data
    # 同一文本比对应得到高贴近度(接近100)
    assert data["style_similarity_score"] >= 95


def test_score_style_identical_text_scores_high():
    base = "“走！”他吼。抄起棍子砸向那张桌子，凳子应声而倒。"
    same = base
    import sys, os
    SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
    from score_style import compute_score
    from style_metrics import compute_metrics
    m1 = compute_metrics(base)
    m2 = compute_metrics(same)
    score, _, _ = compute_score(m1, m2)
    assert score >= 95


def test_layered_score_and_flags():
    import sys, os
    SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
    from score_style import compute_layered_score
    from style_metrics import compute_metrics
    base = "天黑了。他冷冷地说：“走吧。”然后摔门而出。"
    sample = "天黑了。他冷冷地说：“走吧。”然后摔门而出。"
    overall, layers, flags, per_layer = compute_layered_score(
        compute_metrics(base), compute_metrics(sample)
    )
    assert 0 <= overall <= 100
    # 相同文本应得到高总贴合度
    assert overall >= 95
    # 三层均应存在且为0~100
    for name, info in layers.items():
        assert 0 <= info["score"] <= 100
        assert info["weight"] > 0
    # 相同文本不应触发套话雷区
    assert flags == []


def test_layered_score_flags_cliche():
    import sys, os
    SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
    from score_style import compute_layered_score
    from style_metrics import compute_metrics
    base = "他坐下，喝水，看窗外。"
    ai = "那一刻，他目光深邃，嘴角勾起一抹笑，仿佛命运的齿轮开始转动，愿世间一切如约而至。"
    overall, layers, flags, _ = compute_layered_score(
        compute_metrics(base), compute_metrics(ai)
    )
    # 明显的AI腔样本应触发雷区提示
    assert any(f["label"].find("套话") >= 0 or f["label"].find("雷区") >= 0 for f in flags)


def test_score_style_project_mode(built_project):
    out = os.path.join(built_project, "reviews", "style_metrics.json")
    rc, out_s, err = run_script(
        "score_style.py", "--project", built_project,
        "--baseline-index", "1", "--sample-rel", "chapters/original/0002.md",
        "--out", out,
    )
    assert rc == 0, err
    assert os.path.isfile(out)
