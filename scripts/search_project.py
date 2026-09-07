#!/usr/bin/env python3
"""项目检索: 全文/人物/事件/伏笔搜索, 结果附文件位置。

用法:
    python scripts/search_project.py --project ./projects/my_novel --query "旧钥匙"
    python scripts/search_project.py --project ./projects/my_novel --query "林舟" --scope characters

scope: all | chapters | characters | events | foreshadowing
"""
import argparse
import json
import os
import sys
import glob


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def walk(path):
    """递归返回所有 json/md 文件。"""
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith((".json", ".md", ".txt")):
                yield os.path.join(root, f)


def search_in_text(q, text):
    return q.lower() in (text or "").lower()


def search_files(proj, q, scope):
    hits = []
    if scope in ("all", "chapters"):
        for p in walk(os.path.join(proj, "chapters")):
            if not p.endswith(".md"):
                continue
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if search_in_text(q, line):
                        hits.append({"file": p, "line": i, "snippet": line.strip()[:80]})
        # 也搜原文章节
        for p in walk(os.path.join(proj, "source")):
            if not p.endswith(".md") and not p.endswith(".txt"):
                continue
            if "import_info" in p:
                continue
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if search_in_text(q, line):
                        hits.append({"file": p, "line": i, "snippet": line.strip()[:80]})

    # 在 story_bible / planning / analysis 的 json 中搜索
    if scope in ("all", "characters", "events", "foreshadowing"):
        dirs = [os.path.join(proj, "story_bible"), os.path.join(proj, "planning"),
                os.path.join(proj, "analysis"), os.path.join(proj, "scenes")]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for p in walk(d):
                if not p.endswith(".json"):
                    continue
                try:
                    data = load_json(p)
                except Exception:
                    continue
                if isinstance(data, dict):
                    items = data.get("characters") or data.get("events") or \
                            data.get("foreshadowing") or ([data] if q in json.dumps(data, ensure_ascii=False) else [])
                    if search_in_text(q, json.dumps(data, ensure_ascii=False)):
                        hits.append({"file": p, "snippet": "匹配 JSON 内容"})
    return hits


def main():
    ap = argparse.ArgumentParser(description="项目检索")
    ap.add_argument("--project", required=True)
    ap.add_argument("--query", required=True, help="搜索关键词")
    ap.add_argument("--scope", default="all",
                    choices=["all", "chapters", "characters", "events", "foreshadowing"])
    args = ap.parse_args()

    if not os.path.isdir(args.project):
        print(f"错误: 项目不存在 {args.project}", file=sys.stderr)
        sys.exit(1)

    hits = search_files(args.project, args.query, args.scope)
    print(f"找到 {len(hits)} 处匹配「{args.query}」(scope={args.scope}):")
    for h in hits[:50]:
        loc = h.get("file", "")
        ln = f":{h['line']}" if h.get("line") else ""
        snip = h.get("snippet", "")
        print(f"  - {loc}{ln}  {snip}")
    if not hits:
        print("  无匹配。")


if __name__ == "__main__":
    main()
