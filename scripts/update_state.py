#!/usr/bin/env python3
"""更新故事状态 state/current_state.json, 并在更新前创建快照; 支持按快照回滚。

用法:
    python scripts/update_state.py --project ./projects/my_novel --chapter 0051
    python scripts/update_state.py --project ./projects/my_novel --chapter 0051 \
        --changes state/changes_0051.json
    python scripts/update_state.py --project ./projects/my_novel --restore 0052   # 撤销第0052章的更新

--changes 可选: 状态变化文件, 请用 prompts/extract_state_changes.md 从已确认正文生成。
   merge 语义为"增量合并"(见下方), 不是整表替换:
   - characters    : 按 name 合并; 出现则覆盖变化字段, 未出现则追加
   - item_owners   : 按 item 合并(owner 覆盖)
   - foreshadowing_status : 按 id 合并(status 覆盖)
   - facts / conflicts / world_facts : 追加去重(不支持删除, v1)
   重复更新同一章节会被拒绝(以快照存在为准)。
--restore: 撤销某章的更新——用 state/snapshots/after_<cid>.json(该章更新前的状态)
           恢复 current_state.json, 回到该章之前(即上一章末)的时点。
"""
import argparse
import copy
import json
import os
import shutil
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "templates")

ALLOWED_KEYS = {"characters", "facts", "conflicts", "item_owners",
                "foreshadowing_status", "world_facts"}
CHAR_UPDATE_KEYS = {"location", "physical_condition", "mental_state",
                    "current_goal", "known_information", "misconceptions"}


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


def dedupe(items):
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out


def merge_characters(current, delta):
    """按 name 增量合并: 已存在则只覆盖变化字段, 不存在则追加。"""
    if not isinstance(delta, list):
        return current
    result = []
    index = {}
    for i, c in enumerate(current):
        if isinstance(c, dict) and c.get("name") is not None:
            index[c["name"]] = len(result)
            result.append(dict(c))
    for chg in delta:
        if not isinstance(chg, dict) or not chg.get("name"):
            continue
        name = chg["name"]
        if name in index:
            base = result[index[name]]
            for k, v in chg.items():
                if k in CHAR_UPDATE_KEYS:
                    if k in ("known_information", "misconceptions") and isinstance(v, list):
                        base[k] = dedupe(v)      # 提供则整体覆盖(允许清空表达移除/澄清)
                    else:
                        base[k] = v
        else:
            item = dict(chg)
            for k in ("known_information", "misconceptions"):
                if isinstance(item.get(k), list):
                    item[k] = dedupe(item[k])
            index[name] = len(result)
            result.append(item)
    return result


def merge_keyed(current, delta, key, update):
    """按某键合并: 出现则更新字段, 否则追加。update 为返回更新后字典的回调。"""
    if not isinstance(delta, list):
        return current
    result = []
    index = {}
    for i, it in enumerate(current):
        if isinstance(it, dict) and it.get(key) is not None:
            index[it[key]] = len(result)
            result.append(dict(it))
    for chg in delta:
        if not isinstance(chg, dict) or chg.get(key) is None:
            continue
        k = chg[key]
        if k in index:
            result[index[k]] = update(result[index[k]], chg)
        else:
            result.append(dict(chg))
    return result


def merge_strlist(current, delta):
    """字符串列表追加去重。"""
    if not isinstance(delta, list):
        return current
    return dedupe(list(current) + [x for x in delta if isinstance(x, str)])


def apply_changes(state, changes):
    state["characters"] = merge_characters(state.get("characters", []), changes.get("characters", []))
    state["facts"] = merge_strlist(state.get("facts", []), changes.get("facts", []))
    state["conflicts"] = merge_strlist(state.get("conflicts", []), changes.get("conflicts", []))
    state["world_facts"] = merge_strlist(state.get("world_facts", []), changes.get("world_facts", []))

    state["item_owners"] = merge_keyed(
        state.get("item_owners", []), changes.get("item_owners", []), "item",
        lambda old, chg: {**old, "owner": chg.get("owner", old.get("owner", ""))})

    state["foreshadowing_status"] = merge_keyed(
        state.get("foreshadowing_status", []), changes.get("foreshadowing_status", []), "id",
        lambda old, chg: {**old, "status": chg.get("status", old.get("status", ""))})
    return state


def check_changes_keys(changes):
    unknown = [k for k in changes if k not in ALLOWED_KEYS]
    if unknown:
        print(f"错误: changes 含未知顶层键: {unknown}, 允许: {sorted(ALLOWED_KEYS)}", file=sys.stderr)
        sys.exit(1)


def restore(proj, cid):
    state_dir = os.path.join(proj, "state")
    cur_path = os.path.join(state_dir, "current_state.json")
    snap_path = os.path.join(state_dir, "snapshots", f"after_{cid}.json")
    if not os.path.exists(snap_path):
        print(f"错误: 快照不存在: {snap_path}", file=sys.stderr)
        sys.exit(1)
    shutil.copyfile(snap_path, cur_path)
    print(f"已回滚: {cur_path} <- {snap_path}")
    return


def update(proj, cid, changes_path):
    state_dir = os.path.join(proj, "state")
    snap_dir = os.path.join(state_dir, "snapshots")
    cur_path = os.path.join(state_dir, "current_state.json")
    snap_path = os.path.join(snap_dir, f"after_{cid}.json")

    if os.path.exists(snap_path):
        print(f"错误: 章节 {cid} 已更新过(快照已存在), 防止重复应用。", file=sys.stderr)
        sys.exit(1)

    # 若无基线, 先建 after_chapter=0000 的空基线, 使首次快照可回滚到"空状态"
    if not os.path.exists(cur_path):
        baseline = empty_state("0000")
        baseline["_updated_at"] = datetime.now().isoformat()
        save_json(cur_path, baseline)

    changes = load_json(changes_path, None) if changes_path else None
    if changes is None:
        changes = {}
    check_changes_keys(changes)

    current = load_json(cur_path, empty_state(cid))

    # 快照 = 更新前状态(回滚点)
    os.makedirs(snap_dir, exist_ok=True)
    save_json(snap_path, current)
    print(f"快照已创建: {snap_path}")

    current = apply_changes(copy.deepcopy(current), changes)

    current["state_id"] = f"state_after_{cid}"
    current["after_chapter"] = cid
    current["_updated_at"] = datetime.now().isoformat()
    save_json(cur_path, current)
    print(f"状态已更新: {cur_path} (after_chapter = {cid})")


def main():
    ap = argparse.ArgumentParser(description="更新/回滚故事状态")
    ap.add_argument("--project", required=True)
    ap.add_argument("--chapter", default=None, help="已确认章节 ID, 如 0051")
    ap.add_argument("--changes", default=None, help="状态变化 JSON 文件(可选, 增量合并)")
    ap.add_argument("--restore", default=None, help="回滚到该快照时点, 如 0050")
    args = ap.parse_args()

    if not os.path.exists(os.path.join(args.project, "project.json")):
        print(f"错误: 项目不存在: {args.project}", file=sys.stderr)
        sys.exit(1)

    if args.restore:
        restore(args.project, args.restore)
        return
    if not args.chapter:
        print("错误: 需提供 --chapter(更新) 或 --restore <id>(回滚)", file=sys.stderr)
        sys.exit(1)
    update(args.project, args.chapter, args.changes)


if __name__ == "__main__":
    main()
