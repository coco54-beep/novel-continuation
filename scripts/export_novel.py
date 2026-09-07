#!/usr/bin/env python3
"""导出续写成书。

用法:
    python scripts/export_novel.py --project ./projects/my_novel --mode continuation
    python scripts/export_novel.py --project ./projects/my_novel --mode full
    python scripts/export_novel.py --project ./projects/my_novel \
        --mode full --format md --out-dir ./exports

mode: continuation(仅续写) | full(原文+续写)
format: txt | md
"""
import argparse
import json
import os
import sys
import zipfile


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_original(proj):
    """按顺序读原文章节。"""
    rows = []
    mf = os.path.join(proj, "indexes", "chapter_manifest.json")
    if os.path.exists(mf):
        manifest = load_json(mf)
        for m in sorted(manifest, key=lambda x: x["order"]):
            p = os.path.join(proj, m["path"])
            if os.path.exists(p):
                rows.append((m["order"], m.get("title", ""), open(p, encoding="utf-8").read()))
    return rows


def collect_generated(proj):
    """只收集 final.md。"""
    rows = []
    gen = os.path.join(proj, "chapters", "generated")
    if not os.path.isdir(gen):
        return rows
    for cid in sorted(os.listdir(gen)):
        final = os.path.join(gen, cid, "final.md")
        if os.path.exists(final):
            with open(final, encoding="utf-8") as f:
                text = f.read()
            # 取正文标题(去掉开头的 # )
            title = text.split("\n", 1)[0].lstrip("#").strip() if text else f"第{cid}章"
            rows.append((int(cid), title, text))
    return rows


def strip_leading_title(text, title):
    """若正文首行(非空)就是章节标题, 去掉它, 避免导出时标题重复。"""
    lines = text.split("\n")
    for idx, ln in enumerate(lines):
        if ln.strip() == "":
            continue
        norm = ln.strip().lstrip("#").strip()
        return "\n".join(lines[idx + 1:]).lstrip("\n") if norm == title.strip() else text
    return text


def main():
    ap = argparse.ArgumentParser(description="导出成书")
    ap.add_argument("--project", required=True)
    ap.add_argument("--mode", default="continuation", choices=["continuation", "full"])
    ap.add_argument("--format", default="txt", choices=["txt", "md"])
    ap.add_argument("--out-dir", default=None, help="输出目录(默认项目 exports/)")
    args = ap.parse_args()

    proj = args.project
    pj = load_json(os.path.join(proj, "project.json"))

    original = collect_original(proj)
    generated = collect_generated(proj)

    if args.mode == "continuation":
        body = generated
    else:
        body = original + generated

    header = f"# {pj['title']}\n\n> 本文档由 novel-continuation 技能辅助生成(AI 辅助创作结果)。\n\n"
    ext = "md" if args.format == "md" else "txt"

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = os.path.join(proj, "exports")
    os.makedirs(out_dir, exist_ok=True)

    out_name = f"{args.mode}_novel.{ext}" if ext == "md" else f"{args.mode}_novel.txt"
    out_path = os.path.join(out_dir, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        for order, title, text in body:
            body_text = strip_leading_title(text, title)
            if args.format == "md":
                f.write(f"\n## {title}\n\n{body_text}\n")
            else:
                f.write(f"\n{title}\n\n{body_text}\n")

    # 打包项目(排除 exports 输出目录与自身压缩包, 避免递归膨胀)
    zip_path = os.path.join(out_dir, "project_archive.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(proj):
            if os.path.basename(root) == "exports":
                dirs[:] = []
                continue
            for fn in files:
                if fn.endswith(".zip"):
                    continue
                full = os.path.join(root, fn)
                zf.write(full, os.path.relpath(full, proj))

    print(f"导出完成: {out_path}")
    print(f"  章节数   : 原文 {len(original)} / 续写 {len(generated)}")
    print(f"  压缩包   : {zip_path}")


if __name__ == "__main__":
    main()
