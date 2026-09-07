#!/usr/bin/env python3
"""把 score_style.py 的定量指标并入一致性报告(review_report), 作"语言风格"一项的量化佐证。

用法:
    python scripts/attach_style_score.py --project ./projects/my_novel \
        --review reviews/0013_v1.json --metrics reviews/style_metrics_0013.json

流程中建议顺序:
    score_style.py --project ... --baseline-index 12 \
        --sample-rel chapters/generated/0013/draft_v1.md --out reviews/style_metrics_0013.json
    attach_style_score.py --project ... --review reviews/0013_v1.json \
        --metrics reviews/style_metrics_0013.json
    validate_json.py --schema schemas/review_report.schema.json --input reviews/0013_v1.json
"""
import argparse
import json
import os
import sys


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="并入风格定量分到一致性报告")
    ap.add_argument("--project", required=True)
    ap.add_argument("--review", required=True, help="review_report JSON(相对项目或绝对路径)")
    ap.add_argument("--metrics", required=True, help="score_style.py 输出的 metrics JSON")
    args = ap.parse_args()

    def resolve(p):
        return p if os.path.isabs(p) else os.path.join(args.project, p)

    review_path = resolve(args.review)
    metrics_path = resolve(args.metrics)
    if not os.path.exists(review_path):
        print(f"错误: 审查报告不存在: {review_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(metrics_path):
        print(f"错误: 指标文件不存在: {metrics_path}", file=sys.stderr)
        sys.exit(1)

    review = load_json(review_path)
    metrics = load_json(metrics_path)
    if not isinstance(metrics, dict):
        print("错误: metrics 不是 JSON 对象", file=sys.stderr)
        sys.exit(1)

    review["style_score"] = metrics
    with open(review_path, "w", encoding="utf-8") as f:
        json.dump(review, f, ensure_ascii=False, indent=2)

    keys = list(metrics.keys())
    print(f"已并入 style_score 到 {review_path} (字段: {', '.join(keys[:6])}{'…' if len(keys) > 6 else ''})")


if __name__ == "__main__":
    main()
