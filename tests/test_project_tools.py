import json
import os

from conftest import run_script, SKILL_DIR


def _w(proj, rel, data):
    p = os.path.join(proj, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2))
    return p


def test_init_creates_state_baseline(tmp_path):
    proj = str(tmp_path / "p")
    rc, out, err = run_script("init_project.py", "--name", "p", "--output", proj)
    assert rc == 0, err
    cur = json.load(open(os.path.join(proj, "state", "current_state.json"), encoding="utf-8"))
    assert cur["after_chapter"] == "0000"
    assert os.path.exists(os.path.join(proj, "state", "snapshots", ".gitkeep"))
    readme = open(os.path.join(proj, "README.md"), encoding="utf-8").read()
    assert "story_bible" in readme


def test_project_status_runs(built_project):
    rc, out, err = run_script("project_status.py", "--project", built_project)
    assert rc == 0, err
    assert "项目" in out
    assert "下一步" in out


def test_build_manifest_rebuilds(built_project):
    rc, out, err = run_script("build_manifest.py", "--project", built_project)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(built_project, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    originals = [f for f in os.listdir(os.path.join(built_project, "chapters", "original"))
                 if f.endswith(".md")]
    assert len(manifest) == len(originals)
    assert all("chapter_id" in m and "sha256" in m and "character_count" in m for m in manifest)


def test_compare_versions_reports_diff(built_project):
    _w(built_project, os.path.join("chapters", "generated", "0001", "draft_v1.md"),
       "第一段甲\n第二段甲\n第三段甲\n")
    _w(built_project, os.path.join("chapters", "generated", "0001", "revised_v2.md"),
       "第一段甲\n第二段乙\n第三段甲\n")
    rc, out, err = run_script("compare_versions.py", "--project", built_project, "--chapter", "0001")
    assert rc == 0, err
    assert "draft_v1" in out and "revised_v2" in out


def _mk_chapter(built_project, cid="0001"):
    _w(built_project, os.path.join("chapters", "generated", cid, "draft_v1.md"), "草稿正文。\n")
    _w(built_project, os.path.join("chapters", "generated", cid, "revised_v2.md"), "修订后正文。\n")
    return os.path.join(built_project, "chapters", "generated", cid)


def test_promote_gate_blocks_and_allows(built_project):
    cdir = _mk_chapter(built_project)
    _w(built_project, os.path.join("reviews", "0001_v1.json"),
       {"chapter_id": "0001", "version": "draft_v1", "overall_score": 60,
        "decision": "revision_required", "issues": []})
    # 最新报告非 approved -> 拒绝
    rc, out, err = run_script("promote_chapter.py", "--project", built_project, "--chapter", "0001")
    assert rc == 1
    assert not os.path.exists(os.path.join(cdir, "final.md"))
    # 复检通过(新报告 approved) -> 放行
    _w(built_project, os.path.join("reviews", "0001_v2.json"),
       {"chapter_id": "0001", "version": "revised_v2", "overall_score": 88,
        "decision": "approved", "issues": []})
    rc, out, err = run_script("promote_chapter.py", "--project", built_project, "--chapter", "0001")
    assert rc == 0, err
    assert os.path.exists(os.path.join(cdir, "final.md"))
    assert open(os.path.join(cdir, "final.md"), encoding="utf-8").read() == "修订后正文。\n"
    # final 已存在, 不 --force 则拒绝
    rc, out, err = run_script("promote_chapter.py", "--project", built_project, "--chapter", "0001")
    assert rc == 1
    # --force 覆盖
    rc, out, err = run_script("promote_chapter.py", "--project", built_project, "--chapter", "0001", "--force")
    assert rc == 0, err


def test_promote_requires_review(built_project):
    _mk_chapter(built_project)
    rc, out, err = run_script("promote_chapter.py", "--project", built_project, "--chapter", "0001")
    assert rc == 1
    assert "一致性报告" in err


def test_attach_style_score(built_project):
    _w(built_project, os.path.join("reviews", "0013_v1.json"),
       {"chapter_id": "0013", "version": "draft_v1", "overall_score": 80,
        "decision": "revision_required", "issues": []})
    metrics = {"style_similarity_score": 89.3, "mean_sentence_len": 28.2}
    _w(built_project, os.path.join("reviews", "style_metrics_0013.json"), metrics)
    rc, out, err = run_script("attach_style_score.py", "--project", built_project,
                              "--review", os.path.join("reviews", "0013_v1.json"),
                              "--metrics", os.path.join("reviews", "style_metrics_0013.json"))
    assert rc == 0, err
    review = json.load(open(os.path.join(built_project, "reviews", "0013_v1.json"), encoding="utf-8"))
    assert review["style_score"]["style_similarity_score"] == 89.3
    # 含 style_score 后仍符合 review_report schema
    rc2, out2, err2 = run_script(
        "validate_json.py",
        "--schema", os.path.join(SKILL_DIR, "schemas", "review_report.schema.json"),
        "--input", os.path.join(built_project, "reviews", "0013_v1.json"))
    assert rc2 == 0, f"{out2}\n{err2}"


def test_project_status_warns_state_vs_bible(built_project):
    # current_state 出现一个 story_bible 未收录的人物名 -> 状态页应给出提示
    changes = os.path.join(built_project, "state", "ch.json")
    with open(changes, "w", encoding="utf-8") as f:
        json.dump({"characters": [{"name": "路人甲", "location": "城门"}]}, f, ensure_ascii=False)
    rc, out, err = run_script("update_state.py", "--project", built_project, "--chapter", "0001",
                              "--changes", changes)
    assert rc == 0, err
    rc, out, err = run_script("project_status.py", "--project", built_project)
    assert rc == 0, err
    assert "未收录" in out
