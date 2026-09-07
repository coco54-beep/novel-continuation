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


_TITLE_RE = [
    re.compile(r"^\[[^\[\]]{1,80}\]$"),                       # [第一章] / [第1回 …]
    re.compile(r"^第[零一二三四五六七八九十百千万两0-9]+[章节卷回部].*$"),
    re.compile(r"^[一二三四五六七八九十]+、"),                  # 一、二、…
    re.compile(r"^\d{1,3}[、\.．]\s*\S+"),                     # 1、1. 1．
    re.compile(r"^Chapter\s+\d+.*$", re.IGNORECASE),
]


def looks_like_title(line):
    line = line.strip()
    if not line:
        return False
    if line.startswith("#"):
        return True
    return any(r.match(line) for r in _TITLE_RE)


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
        lines = content.split("\n")
        # 找首个非空行: 若是标题(含 # / 方括号 / 第X回 / 数字编号 / Chapter)则拆出, 否则视为无标题正文
        title = ""
        body = content.strip()
        for idx, ln in enumerate(lines):
            if not ln.strip():
                continue
            if looks_like_title(ln):
                title = strip_title(ln)
                body = "\n".join(lines[idx + 1:]).strip()
            break
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
