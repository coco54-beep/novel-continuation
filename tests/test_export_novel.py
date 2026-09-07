import json
import os
import zipfile

from conftest import run_script


def _make_final(proj, cid):
    """手工创建一个 final.md 作为续写章节。"""
    d = os.path.join(proj, "chapters", "generated", cid)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "final.md"), "w", encoding="utf-8") as f:
        f.write(f"# 续写章节 {cid}\n\n这是第{cid}章的续写正文。\n")


def test_export_continuation(built_project):
    _make_final(built_project, "0004")
    _make_final(built_project, "0005")
    rc, out, err = run_script("export_novel.py", "--project", built_project, "--mode", "continuation")
    assert rc == 0, err
    out_file = os.path.join(built_project, "exports", "continuation_novel.txt")
    assert os.path.exists(out_file)
    text = open(out_file, encoding="utf-8").read()
    assert "AI 辅助创作" in text
    assert "续写章节 0004" in text
    assert "第一章" not in text  # 仅续写, 不含原文


def test_export_full(built_project):
    _make_final(built_project, "0004")
    rc, out, err = run_script("export_novel.py", "--project", built_project, "--mode", "full")
    assert rc == 0, err
    out_file = os.path.join(built_project, "exports", "full_novel.txt")
    text = open(out_file, encoding="utf-8").read()
    assert "第一章" in text
    assert "续写" in text


def test_export_md_and_zip(built_project):
    _make_final(built_project, "0004")
    rc, out, err = run_script("export_novel.py", "--project", built_project, "--mode", "continuation",
                              "--format", "md")
    assert rc == 0, err
    out_file = os.path.join(built_project, "exports", "continuation_novel.md")
    assert os.path.exists(out_file)
    zip_path = os.path.join(built_project, "exports", "project_archive.zip")
    assert os.path.exists(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert any(n.endswith("project.json") for n in names)


def test_export_zip_does_not_rebundle_itself(built_project):
    """重复 export 时, 不得把上次生成的 project_archive.zip/exports 产物打包进去(避免递归膨胀)。"""
    _make_final(built_project, "0004")
    rc, out, err = run_script("export_novel.py", "--project", built_project,
                              "--mode", "continuation", "--format", "md")
    assert rc == 0, err
    rc, out, err = run_script("export_novel.py", "--project", built_project,
                              "--mode", "continuation", "--format", "md")
    assert rc == 0, err
    zip_path = os.path.join(built_project, "exports", "project_archive.zip")
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert not any(n.endswith(".zip") for n in names)
        assert not any(n.startswith("exports/") for n in names)
