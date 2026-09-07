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


def test_score_style_project_mode(built_project):
    out = os.path.join(built_project, "reviews", "style_metrics.json")
    rc, out_s, err = run_script(
        "score_style.py", "--project", built_project,
        "--baseline-index", "1", "--sample-rel", "chapters/original/0002.md",
        "--out", out,
    )
    assert rc == 0, err
    assert os.path.isfile(out)
