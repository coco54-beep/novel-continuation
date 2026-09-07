#!/usr/bin/env python3
"""输出项目状态概览与下一步建议(相当于无页面的"进度条")。

用法:
    python scripts/project_status.py --project ./projects/my_novel
"""
import argparse
import json
import os
import sys

SUPPORTED_SCHEMA = "1.0"


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def count_files(path, ext=None):
    n = 0
    if not os.path.isdir(path):
        return 0
    for root, _, files in os.walk(path):
        for f in files:
            if ext and not f.endswith(ext):
                continue
            n += 1
    return n


def bible_names(proj):
    """story_bible 中的通行人物名集合, 用于与 current_state 对照。"""
    p = os.path.join(proj, "story_bible", "characters.json")
    arr = load_json(p, [])
    if not isinstance(arr, list):
        return set()
    names = set()
    for c in arr:
        if isinstance(c, dict) and c.get("name"):
            names.add(c["name"])
    return names


def suggest_next(status, analysis, generated, final, planning, has_state):
    """按状态机给出更细的下一步建议。"""
    if status == "created":
        return "运行 import_novel.py 导入小说"
    if status == "imported":
        return "运行 split_chapters.py 切分章节"
    if status == "split" or analysis == 0:
        return "执行逐章分析(analyze_chapter 提示词) -> analysis/chapters/*.json"
    if status == "analyzing" or status == "analyzed":
        if not planning:
            return "建立故事档案(story_bible) → 生成结局方案(propose_endings) 并等待用户选择"
        if not any("outline" in f or f.startswith("story_outline") for f in planning):
            return "用户选定结局后生成续写总纲/卷纲/章纲(planning/)"
    if status == "planning":
        return "生成续写大纲与下一章场景卡"
    if status == "planned":
        return "为下一章生成场景卡(scenes/) → 生成正文 draft_v1"
    if generated == 0:
        return "生成场景卡与目标章节正文(chapters/generated/*/draft_v1.md)"
    if final == 0:
        return "执行一致性检查(review_chapter) → 修订 → 复检通过后 promote_chapter.py 确认 final.md"
    if status == "writing":
        return "为刚生成的章节做一致性检查与修订"
    if status == "reviewing":
        return "修订后复检, 通过后 promote_chapter.py 生成 final.md"
    if status == "completed":
        return "可用 export_novel.py 导出(--mode full|continuation), 或完结本章节存档"
    return "继续生成下一章 / 导出成书"


def main():
    ap = argparse.ArgumentParser(description="项目状态")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    proj = args.project
    pj = load_json(os.path.join(proj, "project.json"))
    if pj is None:
        print(f"错误: 不是有效项目(缺少 project.json): {proj}", file=sys.stderr)
        sys.exit(1)

    if pj.get("schema_version") != SUPPORTED_SCHEMA:
        print(f"警告: project.json schema_version = {pj.get('schema_version')} != {SUPPORTED_SCHEMA}, "
              f"脚本行为可能不兼容, 请升级/迁移。", file=sys.stderr)

    analysis_count = count_files(os.path.join(proj, "analysis", "chapters"), ".json")
    generated = os.path.join(proj, "chapters", "generated")
    generated_count = count_files(generated, ".md")
    final_count = 0
    if os.path.isdir(generated):
        for cid in os.listdir(generated):
            if os.path.exists(os.path.join(generated, cid, "final.md")):
                final_count += 1
    review_count = count_files(os.path.join(proj, "reviews"), ".json")

    state = load_json(os.path.join(proj, "state", "current_state.json"))
    planning_dir = os.path.join(proj, "planning")
    planning_files = os.listdir(planning_dir) if os.path.isdir(planning_dir) else []

    print(f"项目: {pj.get('title', '')}")
    print(f"  项目 ID       : {pj.get('project_id')}")
    print(f"  状态          : {pj.get('status')}")
    print(f"  原文章节数    : {pj.get('original_chapter_count')}")
    print(f"  已分析章节数  : {analysis_count}")
    print(f"  规划文件      : {', '.join(planning_files) if planning_files else '无'}")
    print(f"  已生成章节数  : {generated_count}")
    print(f"  已确认章节数  : {final_count}")
    print(f"  审查报告数    : {review_count}")
    if state:
        print(f"  当前推进至    : 第{state.get('after_chapter')}章之后")
        names = {c.get("name") for c in state.get("characters", []) if c.get("name")}
        if names:
            missing = sorted(n for n in names if n not in bible_names(proj))
            if missing:
                print(f"  提示          : current_state 有 {len(missing)} 个人物名在 story_bible 未收录: "
                      f"{', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}")

    next_step = suggest_next(pj.get("status"), analysis_count, generated_count, final_count,
                             planning_files, state is not None)
    print(f"\n  下一步建议    : {next_step}")


if __name__ == "__main__":
    main()
