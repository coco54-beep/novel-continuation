"""对 build_style_profile.py 做集成测试: 生成脚手架并符合 style_profile.schema.json。"""
import json
import os

from conftest import run_script

SCHEMA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "schemas", "style_profile.schema.json")


def test_build_style_profile_generates_and_validates(built_project):
    # 先探知篇幅与密度(供给确定性指标)
    rc, out, err = run_script("analyze_density.py", "--project", built_project)
    assert rc == 0, err
    rc, out, err = run_script("build_style_profile.py", "--project", built_project)
    assert rc == 0, err
    out_path = os.path.join(built_project, "analysis", "style_profile.json")
    assert os.path.isfile(out_path)
    profile = json.load(open(out_path, encoding="utf-8"))
    assert profile["schema_version"] == "1.0"
    assert profile["project_id"] == "testnovel"
    assert profile["density_tier"] in ("密实", "中等", "疏朗")
    # 空脚本生成的脚手架应通过 schema 校验
    rc, out, err = run_script("validate_json.py", "--schema", SCHEMA, "--input", out_path)
    assert rc == 0, err


def test_build_style_profile_missing_project_errors(tmp_path):
    rc, out, err = run_script("build_style_profile.py", "--project", str(tmp_path / "nonexistent"))
    assert rc != 0
    assert "错误" in err
