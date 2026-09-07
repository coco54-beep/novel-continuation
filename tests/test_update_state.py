import json
import os

import pytest

from conftest import run_script


def _cur_path(proj):
    return os.path.join(proj, "state", "current_state.json")


def test_update_state_first_time(built_project):
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0001")
    assert rc == 0, err
    cur = json.load(open(_cur_path(built_project), encoding="utf-8"))
    assert cur["after_chapter"] == "0001"
    # 快照存在
    snap = os.path.join(built_project, "state", "snapshots", "after_0001.json")
    assert os.path.exists(snap)


def test_update_state_with_changes(built_project):
    changes = {
        "characters": [{"name": "林舟", "location": "旧车站仓库", "current_goal": "追查失踪者"}],
        "facts": ["仓库编号为17"],
    }
    ch_path = os.path.join(built_project, "state", "changes_0002.json")
    with open(ch_path, "w", encoding="utf-8") as f:
        json.dump(changes, f, ensure_ascii=False)
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0002",
                              "--changes", ch_path)
    assert rc == 0, err
    cur = json.load(open(_cur_path(built_project), encoding="utf-8"))
    assert cur["after_chapter"] == "0002"
    assert cur["characters"][0]["name"] == "林舟"


def test_update_state_prevents_repeat(built_project):
    run_script("update_state.py", "--project", built_project, "--chapter", "0001")
    # 第二次应被拒绝
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0001")
    assert rc == 1
    assert "重复" in err
