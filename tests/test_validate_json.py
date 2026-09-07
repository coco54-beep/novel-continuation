import json
import os
import sys

from conftest import run_script, SKILL_DIR, SCRIPTS_DIR


def _schema(name):
    return os.path.join(SKILL_DIR, "schemas", name)


def test_validate_chapter_analysis(built_project):
    """chapter_analysis 的模板应能通过其自身 schema 校验。"""
    schema = _schema("chapter_analysis.schema.json")
    template = os.path.join(SKILL_DIR, "templates", "chapter_analysis.json")
    rc, out, err = run_script("validate_json.py", "--schema", schema, "--input", template)
    assert rc == 0, f"{out}\n{err}"


def test_validate_all_schemas_parse():
    """所有 schema 都是合法 JSON, 且多数模板能通过对应校验。"""
    q = json.dumps
    for fname in os.listdir(os.path.join(SKILL_DIR, "schemas")):
        if not fname.endswith(".json"):
            continue
        # 至少 schema 本身是合法 JSON
        json.load(open(os.path.join(SKILL_DIR, "schemas", fname), encoding="utf-8"))


def test_validate_rejects_bad_data(tmp_path):
    schema = _schema("chapter_analysis.schema.json")
    bad = os.path.join(str(tmp_path), "bad.json")
    with open(bad, "w", encoding="utf-8") as f:
        json.dump({"chapter_id": 123}, f)  # 缺少必需字段
    rc, out, err = run_script("validate_json.py", "--schema", schema, "--input", bad)
    assert rc == 1


def test_validate_missing_schema(tmp_path):
    rc, out, err = run_script("validate_json.py", "--schema", str(tmp_path / "nope.json"),
                              "--input", str(tmp_path / "x.json"))
    assert rc == 1


def test_validate_items_mode(tmp_path):
    """--items: 容器数组逐元素校验, 有一个坏元素即失败并指出其下标。"""
    schema = _schema("character.schema.json")
    good = {"character_id": "char_a", "name": "甲", "source_status": "confirmed",
            "identity": "x", "behavior_profile": {}, "speech_profile": {},
            "current_state": {}}
    bad = {"character_id": 123}  # 类型与必填都错
    arr = os.path.join(str(tmp_path), "chars.json")
    with open(arr, "w", encoding="utf-8") as f:
        json.dump([good, bad, good], f)

    rc, out, err = run_script("validate_json.py", "--schema", schema, "--input", arr, "--items")
    assert rc == 1
    assert "[1]" in out, out  # 出错下标指向第 2 个元素

    arr_ok = os.path.join(str(tmp_path), "chars_ok.json")
    with open(arr_ok, "w", encoding="utf-8") as f:
        json.dump([good, good], f)
    rc_ok, out_ok, err_ok = run_script(
        "validate_json.py", "--schema", schema, "--input", arr_ok, "--items")
    assert rc_ok == 0, f"{out_ok}\n{err_ok}"

