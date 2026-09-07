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


def _write_changes(proj, cid, data):
    p = os.path.join(proj, "state", f"changes_{cid}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p


def test_update_state_incremental_merge(built_project):
    """增量合并: 只更新变化人物, 不抹掉未变化人物/事实。"""
    p1 = _write_changes(built_project, "0001", {
        "characters": [
            {"name": "林舟", "location": "仓库", "current_goal": "追查失踪者"},
            {"name": "周岚", "location": "外围", "current_goal": "望风"},
        ],
        "facts": ["仓库附近发现脚印"],
    })
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0001",
                              "--changes", p1)
    assert rc == 0, err

    # 第 2 章只更新林舟: 周岚必须保留, 林舟的 current_goal 等未变字段也应保留
    p2 = _write_changes(built_project, "0002", {
        "characters": [{"name": "林舟", "location": "旧车站", "mental_state": "坚定"}],
        "conflicts": ["幕后势力尚未现形"],
    })
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0002",
                              "--changes", p2)
    assert rc == 0, err

    cur = json.load(open(_cur_path(built_project), encoding="utf-8"))
    names = [c["name"] for c in cur["characters"]]
    assert names == ["林舟", "周岚"], names
    lin = cur["characters"][0]
    assert lin["location"] == "旧车站"
    assert lin["current_goal"] == "追查失踪者"      # 未在变化中, 保留
    assert lin["mental_state"] == "坚定"
    assert "仓库附近发现脚印" in cur["facts"]        # 上一章事实保留
    assert "幕后势力尚未现形" in cur["conflicts"]
    assert cur["after_chapter"] == "0002"


def test_update_state_known_information_replace(built_project):
    """known_information 提供即整体覆盖(允许清空表达遗忘/澄清)。"""
    p1 = _write_changes(built_project, "0001", {
        "characters": [{"name": "林舟", "known_information": ["a", "b"]}],
    })
    run_script("update_state.py", "--project", built_project, "--chapter", "0001", "--changes", p1)
    p2 = _write_changes(built_project, "0002", {
        "characters": [{"name": "林舟", "known_information": ["a", "c"]}],
    })
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0002",
                              "--changes", p2)
    assert rc == 0, err
    cur = json.load(open(_cur_path(built_project), encoding="utf-8"))
    assert cur["characters"][0]["known_information"] == ["a", "c"]


def test_update_state_rollback(built_project):
    """回滚: --restore <id> 撤销该章的更新, 回到该章之前的状态。"""
    p1 = _write_changes(built_project, "0001", {
        "characters": [{"name": "林舟", "location": "仓库"}],
    })
    run_script("update_state.py", "--project", built_project, "--chapter", "0001", "--changes", p1)
    p2 = _write_changes(built_project, "0002", {
        "characters": [{"name": "林舟", "location": "旧车站"}],
    })
    run_script("update_state.py", "--project", built_project, "--chapter", "0002", "--changes", p2)
    assert json.load(open(_cur_path(built_project), encoding="utf-8"))["characters"][0]["location"] == "旧车站"

    # 撤销第 0002 章: 回到第 0001 章末
    rc, out, err = run_script("update_state.py", "--project", built_project, "--restore", "0002")
    assert rc == 0, err
    cur = json.load(open(_cur_path(built_project), encoding="utf-8"))
    assert cur["after_chapter"] == "0001"
    assert cur["characters"][0]["location"] == "仓库"

    # 快照缺失时应报错
    rc, out, err = run_script("update_state.py", "--project", built_project, "--restore", "9999")
    assert rc == 1


def test_update_state_rejects_unknown_changes_key(built_project):
    p = _write_changes(built_project, "0001", {"nonsense": []})
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0001",
                              "--changes", p)
    assert rc == 1
    assert "未知顶层键" in err
