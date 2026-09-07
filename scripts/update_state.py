#!/usr/bin/env python3
"""更新故事状态 state/current_state.json, 并在更新前创建快照。

用法:
    python scripts/update_state.py --project ./projects/my_novel --chapter 0051
    python scripts/update_state.py --project ./projects/my_novel --chapter 0051 \
        --changes state/changes_0051.json

--changes 可选: 包含本次状态变化(遵循 story_state 的部分字段)。
若该章节快照已存在, 视为已应用, 拒绝重复更新(防止重复应用)。
"""
import argparse
import json
import os
import sys
import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "templates")


def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def empty_state(cid):
    return {
        "state_id": f"state_after_{cid}",
        "after_chapter": cid,
        "characters": [],
        "facts": [],
        "conflicts": [],
        "item_owners": [],
        "foreshadowing_status": [],
        "world_facts": [],
    }


def main():
    ap = argparse.ArgumentParser(description="更新故事状态")
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", required=True, help="已确认章节 ID, 如 0051")
    ap.add_argument("--changes", default=None, help="状态变化 JSON 文件(可选)")
    args = ap.parse_args()

    proj = args.project
    cid = args.chapter

    state_dir = os.path.join(proj, "state")
    snap_dir = os.path.join(state_dir, "snapshots")
    cur_path = os.path.join(state_dir, "current_state.json")
    snap_path = os.path.join(snap_dir, f"after_{cid}.json")

    if os.path.exists(snap_path):
        print(f"错误: 章节 {cid} 已更新过(快照已存在), 防止重复应用。", file=sys.stderr)
        sys.exit(1)

    current = load_json(cur_path, empty_state(cid))

    changes = load_json(args.changes, None) if args.changes else None
    if changes is None:
        # 无显式变化文件: 以现有状态为准(需人工/LLM 先提供 changes)
        print("提示: 未提供 --changes, 使用空变化。建议先用 extract_state_changes 提示词生成变化文件。")
        changes = {}

    # 合并变化
    for key in ("characters", "facts", "conflicts", "item_owners",
                "foreshadowing_status", "world_facts"):
        if isinstance(changes.get(key), list):
            current[key] = changes[key]

    # 快照前记录原状态
    os.makedirs(snap_dir, exist_ok=True)
    if os.path.exists(cur_path):
        shutil.copyfile(cur_path, snap_path)
        print(f"快照已创建: {snap_path}")
    else:
        save_json(snap_path, current)
        print(f"快照已创建(初始): {snap_path}")

    current["state_id"] = f"state_after_{cid}"
    current["after_chapter"] = cid
    current["_updated_at"] = datetime.now().isoformat()

    save_json(cur_path, current)
    print(f"状态已更新: {cur_path} (after_chapter = {cid})")


if __name__ == "__main__":
    main()
