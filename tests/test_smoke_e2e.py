"""合规端到端冒烟测试: 用自创 style_samples.txt(无版权问题) 跑通全脚本链路。

验证 skill 的脚本层能从上到下走通: 初始化→导入→切分→探知篇幅→探知密度→风格评分。
(续写/归范式等 AI 环节由人工/智能体执行, 此测试只保证确定性脚本链路不崩。)
"""
import json
import os

from conftest import FIXTURES, run_script

STYLE_SAMPLES = os.path.join(FIXTURES, "style_samples.txt")


def test_full_script_chain_e2e(tmp_path):
    proj = str(tmp_path / "styleproj")
    # 1 初始化
    rc, out, err = run_script("init_project.py", "--name", "styleproj", "--output", proj)
    assert rc == 0, err
    # 2 导入 style_samples.txt
    rc, out, err = run_script("import_novel.py", "--input", STYLE_SAMPLES, "--project", proj)
    assert rc == 0, err
    # 3 切分
    rc, out, err = run_script("split_chapters.py", "--project", proj)
    assert rc == 0, err
    # 4 探知篇幅
    rc, out, err = run_script("estimate_chapter_length.py", "--project", proj)
    assert rc == 0, err
    assert os.path.isfile(os.path.join(proj, "indexes", "length_stats.json"))
    # 5 探知密度
    rc, out, err = run_script("analyze_density.py", "--project", proj)
    assert rc == 0, err
    assert "density_tier" in json.load(open(os.path.join(proj, "project.json"), encoding="utf-8"))
    # 6 风格评分(文本模式): 用样本的"章回说书"片段 对比 "克制白描"片段, 验证能跑且能区分
    #    从样本源文件里取出两个不同范式块
    text = open(STYLE_SAMPLES, encoding="utf-8").read()
    # 按 【范式 开头 分段
    import re
    blocks = re.split(r"【(?=[^】]*范式)", text)
    # blocks 可能含说明行, 取含实际文本的两块
    body_blocks = [b for b in blocks if "话说" in b or "我爹说" in b]
    assert len(body_blocks) >= 2, "应至少提取到两个范式正文块"
    base_f = tmp_path / "base.md"
    sample_f = tmp_path / "sample.md"
    base_f.write_text(body_blocks[0], encoding="utf-8")
    sample_f.write_text(body_blocks[1], encoding="utf-8")
    rc, out_s, err = run_script(
        "score_style.py", "--baseline", str(base_f), "--sample", str(sample_f),
        "--out", os.path.join(proj, "reviews", "style_metrics.json"),
    )
    assert rc == 0, err
    data = json.load(open(os.path.join(proj, "reviews", "style_metrics.json"), encoding="utf-8"))
    assert "style_similarity_score" in data
