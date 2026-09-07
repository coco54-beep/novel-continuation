"""对 analyze_density.py 做集成测试: 在已切分项目上运行并写回 density_tier。"""
import json
import os

from conftest import run_script


def test_density_writes_tier(built_project):
    rc, out, err = run_script("analyze_density.py", "--project", built_project)
    assert rc == 0, err
    with open(os.path.join(built_project, "indexes", "density_stats.json"), encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["overall_tier"] in ("密实", "中等", "疏朗")
    assert stats["chapter_count"] >= 1
    with open(os.path.join(built_project, "project.json"), encoding="utf-8") as f:
        proj = json.load(f)
    assert proj["density_tier"] == stats["overall_tier"]


def test_density_missing_manifest_errors():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run_script("analyze_density.py", "--project", d)
        assert rc != 0
        assert "错误" in err
