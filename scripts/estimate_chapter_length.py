#!/usr/bin/env python3
"""自动探知作者单章篇幅习惯并写回项目, 供续写章节设置目标字数。

用法:
    python scripts/estimate_chapter_length.py --project ./projects/my_novel
    python scripts/estimate_chapter_length.py --project ./projects/my_novel --stat mean

从 indexes/chapter_manifest.json 读取各章 character_count(去空白字数),
计算中位数(默认, 对异常值稳健)或均值, 写入 project.json 的
target_chapter_length, 并将篇幅统计保存到 indexes/length_stats.json,
供 write_scene.md 的 {target_chars} 与 scene_card 的 target_chars 自动取值。

建议在章节切分(split)完成后运行。
"""
import argparse
import json
import os
import statistics
import sys


def main():
    ap = argparse.ArgumentParser(description="自动探知作者单章篇幅")
    ap.add_argument("--project", required=True, help="项目目录")
    ap.add_argument(
        "--stat",
        choices=["median", "mean"],
        default="median",
        help="统计口径, 默认 median(中位数), 对超长/超短异常章节更稳健",
    )
    args = ap.parse_args()

    proj = args.project
    manifest_path = os.path.join(proj, "indexes", "chapter_manifest.json")
    project_path = os.path.join(proj, "project.json")

    if not os.path.isfile(manifest_path):
        print(f"错误: 找不到 {manifest_path}, 请先运行 split_chapters.py", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(project_path):
        print(f"错误: 找不到 {project_path}, 请先运行 init_project.py", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    counts = {}
    for entry in manifest:
        cid = entry.get("chapter_id")
        cnt = entry.get("character_count")
        if cid is None or not isinstance(cnt, int) or cnt <= 0:
            continue
        counts[cid] = cnt

    if not counts:
        print("错误: 章节清单中无有效字数数据", file=sys.stderr)
        sys.exit(1)

    values = sorted(counts.values())
    if args.stat == "mean":
        estimate = int(round(statistics.mean(values)))
    else:
        estimate = int(statistics.median(values))

    length_stats = {
        "stat": args.stat,
        "chapter_count": len(values),
        "min": values[0],
        "max": values[-1],
        "mean": int(round(statistics.mean(values))),
        "median": int(statistics.median(values)),
        "target_chapter_length": estimate,
        "per_chapter": {k: counts[k] for k in sorted(counts)},
    }

    with open(os.path.join(proj, "indexes", "length_stats.json"), "w", encoding="utf-8") as f:
        json.dump(length_stats, f, ensure_ascii=False, indent=2)

    from datetime import datetime

    with open(project_path, encoding="utf-8") as f:
        project = json.load(f)
    project["target_chapter_length"] = estimate
    project["updated_at"] = datetime.now().isoformat()
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    print(f"篇幅探知完成: 共 {len(values)} 章")
    print(f"  中位数 {length_stats['median']} / 均值 {length_stats['mean']} / "
          f"范围 {values[0]}~{values[-1]}")
    print(f"  已写入 target_chapter_length = {estimate} ({args.stat})")


if __name__ == "__main__":
    main()
