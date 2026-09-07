#!/usr/bin/env python3
"""推进项目状态机, 更新 project.json 的 status 与 updated_at。

用法:
    python scripts/set_status.py --project ./projects/my_novel --status analyzed
    python scripts/set_status.py --project ./projects/my_novel --status writing

状态机: created | imported | split | analyzing | analyzed | planning |
        planned | writing | reviewing | completed

说明: init/import/split/estimate/density 等脚本会各自把状态推进到 split,
其余阶段(逐章分析→analyzed、结局/大纲→planning/planned、正文→writing/reviewing、
导出→completed)此前没有脚本推进, 需调用本脚本在阶段完成处登记状态。
"""
import argparse
import json
import os
import sys
from datetime import datetime

VALID = {"created", "imported", "split", "analyzing", "analyzed", "planning",
         "planned", "writing", "reviewing", "completed"}


def main():
    ap = argparse.ArgumentParser(description="更新 project.json 状态")
    ap.add_argument("--project", required=True, help="项目目录")
    ap.add_argument("--status", required=True, help=f"目标状态, 可选: {'/'.join(sorted(VALID))}")
    args = ap.parse_args()

    if args.status not in VALID:
        print(f"错误: 未知状态 '{args.status}', 可选: {'/'.join(sorted(VALID))}", file=sys.stderr)
        sys.exit(1)

    path = os.path.join(args.project, "project.json")
    if not os.path.exists(path):
        print(f"错误: 项目不存在: {args.project}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["status"] = args.status
    data["updated_at"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"状态已更新: {data['project_id']} -> {args.status}")


if __name__ == "__main__":
    main()
