#!/usr/bin/env python3
"""初始化小说续写项目目录结构。

用法:
    python scripts/init_project.py --name my_novel --output ./projects/my_novel
    python scripts/init_project.py --name my_novel            # 默认输出到 <脚本目录>/../projects/my_novel

生成项目目录、project.json、初始状态与各子目录。防止覆盖已有项目。
"""
import argparse
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(SCRIPT_DIR)


def default_project_dir(name):
    return os.path.join(DEFAULT_ROOT, "projects", name)


def make_dirs(base):
    subdirs = [
        "source", "chapters/original", "chapters/generated",
        "analysis/chapters", "story_bible", "planning",
        "scenes", "reviews", "state/snapshots",
        "indexes", "exports",
    ]
    for s in subdirs:
        os.makedirs(os.path.join(base, s), exist_ok=True)


def project_json(project_id, title):
    now = datetime.now().isoformat()
    return {
        "schema_version": "1.0",
        "project_id": project_id,
        "title": title,
        "source_type": "user_owned",
        "status": "created",
        "original_chapter_count": 0,
        "latest_confirmed_chapter": 0,
        "target_chapter_length": 3500,
        "continuation_preferences": {
            "allow_new_characters": True,
            "allow_new_world_rules": False,
            "ending_tone": "由用户选择",
        },
        "created_at": now,
        "updated_at": now,
    }


def main():
    ap = argparse.ArgumentParser(description="初始化小说续写项目")
    ap.add_argument("--name", required=True, help="项目 ID (小写字母/数字/下划线)")
    ap.add_argument("--title", default=None, help="小说名称, 默认等于项目名")
    ap.add_argument("--output", default=None, help="项目输出目录")
    args = ap.parse_args()

    name = args.name
    if not name.replace("_", "").isalnum():
        print(f"错误: 项目名 '{name}' 只能是字母/数字/下划线", file=sys.stderr)
        sys.exit(1)

    out = args.output or default_project_dir(name)
    if os.path.exists(os.path.join(out, "project.json")):
        print(f"错误: 项目已存在: {out}", file=sys.stderr)
        sys.exit(1)

    make_dirs(out)
    data = project_json(name, args.title or name)
    with open(os.path.join(out, "project.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {data['title']}\n\n小说续写项目 `{name}`。\n")

    # 初始状态目录占位
    print(f"项目创建成功: {out}")
    print(f"  project_id : {name}")
    print(f"  title      : {data['title']}")
    print(f"  status     : created")


if __name__ == "__main__":
    main()
