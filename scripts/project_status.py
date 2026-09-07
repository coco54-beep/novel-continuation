#!/usr/bin/env python3
"""输出项目状态概览与下一步建议。

用法:
    python scripts/project_status.py --project ./projects/my_novel
"""
import argparse
import json
import os
import sys


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


def main():
    ap = argparse.ArgumentParser(description="项目状态")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    proj = args.project
    pj = load_json(os.path.join(proj, "project.json"))
    if pj is None:
        print(f"错误: 不是有效项目(缺少 project.json): {proj}", file=sys.stderr)
        sys.exit(1)

    analysis_count = count_files(os.path.join(proj, "analysis", "chapters"), ".json")
    generated = os.path.join(proj, "chapters", "generated")
    generated_count = count_files(os.path.join(proj, "chapters", "generated"), ".md")
    final_count = 0
    if os.path.isdir(generated):
        for cid in os.listdir(generated):
            if os.path.exists(os.path.join(generated, cid, "final.md")):
                final_count += 1
    review_count = count_files(os.path.join(proj, "reviews"), ".json")

    state = load_json(os.path.join(proj, "state", "current_state.json"))
    pending = review_count  # 简化: 待处理问题数=审查报告数

    print(f"项目: {pj.get('title','')}")
    print(f"  项目 ID       : {pj.get('project_id')}")
    print(f"  状态          : {pj.get('status')}")
    print(f"  原文章节数    : {pj.get('original_chapter_count')}")
    print(f"  已分析章节数  : {analysis_count}")
    planning = os.path.join(proj, "planning")
    planning_files = os.listdir(planning) if os.path.isdir(planning) else []
    print(f"  规划文件      : {', '.join(planning_files) if planning_files else '无'}")
    print(f"  已生成章节数  : {generated_count}")
    print(f"  已确认章节数  : {final_count}")
    print(f"  待处理审查    : {pending}")
    if state:
        print(f"  当前推进至    : 第{state.get('after_chapter')}章之后")

    next_step = suggest_next(pj.get("status"), analysis_count, generated_count, final_count)
    print(f"\n  下一步建议    : {next_step}")


def suggest_next(status, analysis, generated, final):
    if status == "created":
        return "运行 import_novel.py 导入小说"
    if status == "imported":
        return "运行 split_chapters.py 切分章节"
    if status == "split":
        return "逐章分析(analyze_chapter 提示词)"
    if analysis == 0:
        return "执行章节分析"
    if status in ("analyzing", "analyzed"):
        return "生成结局方案并等待用户选择"
    if status == "planning":
        return "生成续写大纲"
    if generated == 0:
        return "生成场景卡与目标章节正文"
    if final == 0:
        return "确认已生成章节为正式版本"
    return "继续生成下一章 / 导出成书"


if __name__ == "__main__":
    main()
