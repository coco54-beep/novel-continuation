#!/usr/bin/env python3
"""把修订稿提升为正式章节 final.md——一致性闭环的"确认门"。

原则: 只有 `final.md` 能进入正式故事状态(update_state/export 只认 final)。
此脚本强制: 该章至少有一份 review_report, 且"最新一份"的 decision 为 approved,
才允许生成 final.md(除非显式 --force 由用户强确认)。

用法:
    python scripts/promote_chapter.py --project ./projects/my_novel --chapter 0013
    python scripts/promote_chapter.py --project ./projects/my_novel --chapter 0013 --force

选择正文源: 优先 revised_v2.md → revised_v1.md → draft_v1.md → 其余非 final 版本。
"""
import argparse
import json
import os
import re
import shutil
import sys

SOURCE_PRIORITY = ["revised_v2.md", "revised_v1.md", "revised.md",
                   "draft_v2.md", "draft_v1.md", "draft.md"]


def pick_source(chapter_dir):
    candidates = [f for f in os.listdir(chapter_dir) if f.endswith(".md") and f != "final.md"]
    if not candidates:
        return None
    for name in SOURCE_PRIORITY:
        if name in candidates:
            return name
    return sorted(candidates)[0]


def latest_review(proj, cid):
    """返回 reviews/<cid>_v<N>.json 中版本号最大者, 无则 None。"""
    reviews_dir = os.path.join(proj, "reviews")
    if not os.path.isdir(reviews_dir):
        return None
    best = None
    best_v = -1
    for fn in os.listdir(reviews_dir):
        m = re.fullmatch(re.escape(cid) + r"_v(\d+)\.json", fn)
        if not m:
            continue
        v = int(m.group(1))
        if v > best_v:
            best_v = v
            best = os.path.join(reviews_dir, fn)
    return best


def review_decision(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("decision")


def main():
    ap = argparse.ArgumentParser(description="提升修订稿为 final.md")
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", required=True, help="章节 ID, 如 0013")
    ap.add_argument("--force", action="store_true", help="跳过复检门, 用户强确认")
    args = ap.parse_args()

    proj = args.project
    cid = args.chapter
    chapter_dir = os.path.join(proj, "chapters", "generated", cid)
    final_path = os.path.join(chapter_dir, "final.md")

    if not os.path.isdir(chapter_dir):
        print(f"错误: 章节目录不存在: {chapter_dir}", file=sys.stderr)
        sys.exit(1)

    source = pick_source(chapter_dir)
    if source is None:
        print(f"错误: 章节 {cid} 没有任何可提升的正文版本(draft/revised)。", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(final_path) and not args.force:
        print(f"错误: final.md 已存在: {final_path}。如需覆盖请加 --force。", file=sys.stderr)
        sys.exit(1)

    if not args.force:
        review = latest_review(proj, cid)
        if review is None:
            print(f"错误: 章节 {cid} 没有一致性报告(reviews/{cid}_v*.json)。"
                  f"请先 review_chapter → revise, 复检通过后再 promote。", file=sys.stderr)
            sys.exit(1)
        decision = review_decision(review)
        if decision != "approved":
            print(f"错误: 最新审查 {os.path.basename(review)} decision = {decision}, 非 approved。"
                  f"请先按报告修订并复检通过(或 --force 强确认)。", file=sys.stderr)
            sys.exit(1)
        print(f"复检门通过: {os.path.basename(review)} decision = approved")

    shutil.copyfile(os.path.join(chapter_dir, source), final_path)
    print(f"已生成 final.md: {final_path} (来源 {source})")
    print("提示: 确认无误后用 update_state.py 更新故事状态。")


if __name__ == "__main__":
    main()
