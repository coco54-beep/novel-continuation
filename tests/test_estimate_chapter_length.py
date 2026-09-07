import json
import os

from conftest import run_script


def test_estimate_sets_target_chapter_length(built_project):
    """split 之后运行 estimate_chapter_length, 应把 target_chapter_length 写回 project.json。"""
    proj = built_project
    project_path = os.path.join(proj, "project.json")
    with open(project_path, encoding="utf-8") as f:
        before = json.load(f)

    # 初始默认值应为模板里的 3500
    assert before["target_chapter_length"] == 3500

    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj)
    assert rc == 0, err

    with open(project_path, encoding="utf-8") as f:
        after = json.load(f)

    with open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    counts = sorted(e["character_count"] for e in manifest)
    import statistics
    expected = int(statistics.median(counts))

    assert after["target_chapter_length"] == expected
    assert after["target_chapter_length"] != 3500

    # 同时校验生成了篇幅统计
    with open(os.path.join(proj, "indexes", "length_stats.json"), encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["chapter_count"] == len(counts)
    assert stats["median"] == expected
    assert stats["min"] == counts[0]
    assert stats["max"] == counts[-1]


def test_estimate_mean_option(built_project):
    """--stat mean 应使用均值作为目标字数。"""
    proj = built_project
    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj, "--stat", "mean")
    assert rc == 0, err

    with open(os.path.join(proj, "project.json"), encoding="utf-8") as f:
        data = json.load(f)
    assert data["target_chapter_length"] > 0

    with open(os.path.join(proj, "indexes", "length_stats.json"), encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["stat"] == "mean"
    assert data["target_chapter_length"] == stats["mean"]


def _make_project(tmp_path, counts):
    """构造一个最小项目: 只需 project.json + indexes/chapter_manifest.json。"""
    proj = str(tmp_path / "proj")
    os.makedirs(os.path.join(proj, "indexes"), exist_ok=True)
    with open(os.path.join(proj, "project.json"), "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0", "project_id": "proj", "title": "proj",
            "source_type": "research", "status": "split", "original_chapter_count": len(counts),
            "latest_confirmed_chapter": 0, "target_chapter_length": 3500,
        }, f, ensure_ascii=False)
    manifest = []
    for i, c in enumerate(counts, 1):
        manifest.append({
            "chapter_id": f"{i:04d}", "order": i, "title": f"第{i}章",
            "path": f"chapters/original/{i:04d}.md", "character_count": c, "sha256": "x",
        })
    with open(os.path.join(proj, "indexes", "chapter_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    return proj


def test_estimate_missing_manifest_errors(tmp_path):
    """缺 manifest 时应报错退出。"""
    proj = str(tmp_path / "p")
    os.makedirs(proj, exist_ok=True)
    with open(os.path.join(proj, "project.json"), "w", encoding="utf-8") as f:
        json.dump({}, f)
    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj)
    assert rc != 0
    assert "manifest" in err.lower() or "分" in err


def test_estimate_no_valid_counts_errors(tmp_path):
    """清单里无有效字数(全为0/缺字段)应报错。"""
    proj = _make_project(tmp_path, [0, 0, 0])
    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj)
    assert rc != 0


def test_estimate_median_robust_to_outliers(tmp_path):
    """有超长异常章时, median(默认)不被拉偏, 而 mean 会被拉偏。"""
    proj = _make_project(tmp_path, [2000, 2100, 2200, 90000])
    # median = (2100+2200)/2 = 2150; mean 会被 90000 拉高
    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj)
    assert rc == 0, err
    with open(os.path.join(proj, "project.json"), encoding="utf-8") as f:
        data = json.load(f)
    assert data["target_chapter_length"] == 2150

    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj, "--stat", "mean")
    assert rc == 0, err
    with open(os.path.join(proj, "project.json"), encoding="utf-8") as f:
        data = json.load(f)
    assert data["target_chapter_length"] > 2150  # mean 被异常章拉高
