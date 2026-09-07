#!/usr/bin/env python3
"""重建/校验章节清单 indexes/chapter_manifest.json。

用法:
    python scripts/build_manifest.py --project ./projects/my_novel

扫描 chapters/original/*.md, 重新生成章节清单(含字数与 SHA-256)。
"""
import argparse
import hashlib
import json
import os
import re
import sys


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_title(title):
    return re.sub(r"^\s*#+\s*", "", title).strip()


def main():
    ap = argparse.ArgumentParser(description="重建章节清单")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    proj = args.project
    orig_dir = os.path.join(proj, "chapters", "original")
    if not os.path.isdir(orig_dir):
        print(f"错误: 找不到 {orig_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(
        f for f in os.listdir(orig_dir)
        if re.fullmatch(r"\d{4}\.md", f)
    )

    manifest = []
    for fname in files:
        cid = fname[:4]
        with open(os.path.join(orig_dir, fname), encoding="utf-8") as f:
            content = f.read()
        # 去掉首行 # 标题
        lines = content.split("\n")
        if lines and lines[0].startswith("#"):
            title = strip_title(lines[0])
            body = "\n".join(lines[1:]).strip()
        else:
            title = ""
            body = content.strip()
        manifest.append({
            "chapter_id": cid,
            "order": len(manifest) + 1,
            "title": title,
            "path": os.path.relpath(os.path.join(orig_dir, fname), proj),
            "character_count": len("".join(body.split())),
            "sha256": sha256(body),
        })

    idx_dir = os.path.join(proj, "indexes")
    os.makedirs(idx_dir, exist_ok=True)
    with open(os.path.join(idx_dir, "chapter_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"章节清单重建完成: {len(manifest)} 章")


if __name__ == "__main__":
    main()
