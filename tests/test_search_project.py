import json
import os

from conftest import run_script


def _add_story_bible(proj):
    """在 story_bible 写一个人物档作为搜索样本。"""
    d = os.path.join(proj, "story_bible")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "characters.json"), "w", encoding="utf-8") as f:
        json.dump({"characters": [{"name": "林舟", "alias": ["小舟", "林先生"]}]}, f, ensure_ascii=False)


def test_search_chapters(built_project):
    rc, out, err = run_script("search_project.py", "--project", built_project,
                              "--query", "仓库", "--scope", "chapters")
    assert rc == 0, err
    assert "匹配" in out


def test_search_characters_in_json(built_project):
    _add_story_bible(built_project)
    rc, out, err = run_script("search_project.py", "--project", built_project,
                              "--query", "林舟", "--scope", "characters")
    assert rc == 0, err
    assert "林舟" in out


def test_search_no_match(built_project):
    rc, out, err = run_script("search_project.py", "--project", built_project,
                              "--query", "不存在词xyz", "--scope", "all")
    assert rc == 0
    assert "无匹配" in out


def test_search_missing_project(tmp_path):
    rc, out, err = run_script("search_project.py", "--project", str(tmp_path / "nope"),
                              "--query", "x")
    assert rc == 1
