import json
import os
import sys

from conftest import run_script


def test_init_project_creates_structure(tmp_path):
    proj = str(tmp_path / "nov")
    rc, out, err = run_script("init_project.py", "--name", "nov", "--output", proj)
    assert rc == 0, err
    assert os.path.exists(os.path.join(proj, "project.json"))
    pj = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    assert pj["status"] == "created"
    assert os.path.isdir(os.path.join(proj, "chapters", "generated"))


def test_init_project_rejects_invalid_name(tmp_path):
    rc, out, err = run_script("init_project.py", "--name", "bad-name!", "--output", str(tmp_path / "x"))
    assert rc == 1


def test_init_project_refuses_overwrite(tmp_path):
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    rc, out, err = run_script("init_project.py", "--name", "nov", "--output", proj)
    assert rc == 1


def test_import_novel_success(tmp_path, sample_novel):
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    rc, out, err = run_script("import_novel.py", "--input", sample_novel, "--project", proj)
    assert rc == 0, err
    assert os.path.exists(os.path.join(proj, "source", "original.txt"))
    assert os.path.exists(os.path.join(proj, "source", "import_info.json"))
    pj = json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    assert pj["status"] == "imported"


def test_import_novel_no_project(tmp_path, sample_novel):
    rc, out, err = run_script("import_novel.py", "--input", sample_novel, "--project", str(tmp_path / "nope"))
    assert rc == 1


def test_split_chapters(built_project):
    pj = json.load(open(os.path.join(built_project, "project.json"), encoding="utf-8"))
    assert pj["status"] == "split"
    assert pj["original_chapter_count"] == 3
    manifest = json.load(open(os.path.join(built_project, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    assert len(manifest) == 3
    for m in manifest:
        assert os.path.exists(os.path.join(built_project, m["path"]))
        assert m["title"].startswith("第")


def test_split_chapters_single_chapter_when_no_header(tmp_path):
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write("这里没有标题结构，只是一大段正文。")
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    assert "1 章" in out
    assert "全文" in out


def test_split_chapters_bracket_titles(tmp_path):
    """真实 txt 常见: 章节标题被方括号包裹([第一章] / [第1回 标题] / [序])。"""
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write("[序]\n写在书名之前的一段话。\n\n[第一章 风月无情]\n第一段正文字随着一句对话展开。\n\n[第二章 故人之子]\n第二段正文。")
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    assert len(manifest) == 3
    assert manifest[0]["title"] == "[序]"
    assert manifest[1]["title"] == "[第一章 风月无情]"
    assert manifest[2]["title"] == "[第二章 故人之子]"


def test_split_chapters_dedupes_adjacent_repeat_title(tmp_path):
    """[第一章] 与紧随其后的 '第一章' 重复行只应识别为一个标题。"""
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write("[第一章]\n第一章\n正文第一段。\n\n[第二章]\n第二章\n正文第二段。")
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    assert len(manifest) == 2


def test_split_chapters_weak_signal_not_used_when_strong_found(tmp_path):
    """存在方括号强信号标题时, 正文里的 '一、二、' 分点句不应被弱信号误判为章节。
    这正是某乡土史诗长篇类真实文本曾出现的 bug: 方括号标题 + 正文分点句导致切分碎片化。"""
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write(
            "[第一章]\n"
            "一段长正文开始。\n"
            "一、产业园劝。这里是一个分点段落。\n"
            "二、扶贫款灾。这里也是正文。\n"
            "正文接着往下写了很多内容。\n\n"
            "[第二章]\n"
            "第二段长正文。\n"
            "三、另起一个分点。\n"
            "正文继续。"
        )
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    # 只应识别两个方括号章节, 不应因 '一、' 而切出碎片
    assert len(manifest) == 2
    assert manifest[0]["title"] == "[第一章]"
    assert manifest[1]["title"] == "[第二章]"


def test_split_chapters_weak_signal_fallback_no_strong(tmp_path):
    """当全文找不到任何强信号标题时, 弱信号(中文数字顿号)应兜底识别出章节。"""
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as f:
        f.write("一、第一篇\n第一段内容。\n\n二、第二篇\n第二段内容。")
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    assert len(manifest) == 2
    assert "兜底" in out or "弱信号" in out


def test_split_chapters_body_line_starting_zhenghui_not_title(tmp_path):
    """章回体正文常以 '第四回中已将……' 这类长句开头, 不应被 '第X回' 强信号误判为标题。
    这正是某章回体书目切分失真的 bug: 正文一整段被当作下一个章节标题(曾造成 0 字章)。"""
    proj = str(tmp_path / "nov")
    run_script("init_project.py", "--name", "nov", "--output", proj)
    src = os.path.join(proj, "source", "original.txt")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    body = "第五回里已把那家母子寄居的事说罢，这一回可少写些了。眼下只说那户人家的女儿，自进得门来，老太太百般疼爱，姊妹们也都处处让她。" * 6
    with open(src, "w", encoding="utf-8") as f:
        f.write("[第1回 风月]\n" + body + "\n\n[第2回 故人]\n第二回正文。")
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    manifest = json.load(open(os.path.join(proj, "indexes", "chapter_manifest.json"), encoding="utf-8"))
    # 只应有两个方括号标题章节, 且第1章正文应包含那段"第五回里"开头的内容
    assert len(manifest) == 2
    assert manifest[0]["title"] == "[第1回 风月]"
    assert manifest[1]["title"] == "[第2回 故人]"
    assert manifest[0]["character_count"] > 0
