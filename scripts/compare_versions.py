#!/usr/bin/env python3
"""对比章节正文的不同版本(draft/revised/final), 输出差异统计。

用法:
    python scripts/compare_versions.py --project ./projects/my_novel --chapter 0051
"""
import argparse
import difflib
import json
import os
import re
import sys


def load_versions(proj, cid):
    """返回 {version_label: (path, text)}。"""
    gen = os.path.join(proj, "chapters", "generated", cid)
    if not os.path.isdir(gen):
        return {}
    versions = {}
    for fname in sorted(os.listdir(gen)):
        if not fname.endswith(".md"):
            continue
        label = os.path.splitext(fname)[0]
        with open(os.path.join(gen, fname), encoding="utf-8") as f:
            text = f.read()
        versions[label] = (os.path.join(gen, fname), text)
    return versions


def main():
    ap = argparse.ArgumentParser(description="对比章节版本")
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", required=True, help="章节 ID")
    args = ap.parse_args()

    versions = load_versions(args.project, args.chapter)
    if len(versions) < 2:
        print(f"提示: 章节 {args.chapter} 只有 {len(versions)} 个版本, 无法对比。")
        # 列出已有版本
        for label, (path, _) in versions.items():
            print(f"  {label}: {path}")
        return

    labels = list(versions.keys())
    print(f"章节 {args.chapter} 版本对比 (共 {len(labels)} 版):")
    for i in range(len(labels) - 1):
        a_label, b_label = labels[i], labels[i + 1]
        a = versions[a_label][1].splitlines()
        b = versions[b_label][1].splitlines()
        sm = difflib.unified_diff(a, b, fromfile=a_label, tofile=b_label, lineterm="")
        diff_lines = [l for l in sm if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
        removed = sum(1 for l in diff_lines if l.startswith("-"))
        added = sum(1 for l in diff_lines if l.startswith("+"))
        print(f"\n  {a_label} -> {b_label}: 删 {removed} 行, 增 {added} 行")
        for l in diff_lines[:20]:
            print(f"    {l}")


if __name__ == "__main__":
    main()
