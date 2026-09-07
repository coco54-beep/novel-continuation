#!/usr/bin/env python3
"""对「原文风格基准」与「续写章」做定量文风比对, 输出可复现的离差评分。

用法:
    python scripts/score_style.py --baseline ./orig_chapter.txt --sample ./draft_v1.md --out ./reviews/style_metrics.json
    python scripts/score_style.py --project ./projects/my_novel --baseline-index 8 --sample-rel "chapters/generated/0009_0010/draft_v1.md"

指标与计算公式见 style_metrics.py。本脚本负责: 读文本 → 算两侧指标 → 归一化离差 → 贴近度。
贴近度 = 100 - 平均归一化离差; 离差越小越接近原文风格。
"""
import argparse
import json
import os
import sys

from style_metrics import compute_metrics

# (指标key, 中文说明, 是否越大越好)
KEYS = [
    ("mean_sentence_len", "句长(字)", None),
    ("short_sentence_ratio", "短句占比", None),
    ("dialogue_ratio", "对白占比", None),
    ("overlap_bigram_ratio", "用词集中度", None),
    ("dialect_hits_per_1k", "方言/千字", None),
    ("reduplication_per_1k", "叠字/千字", None),
    ("avg_para_len", "段长(字)", None),
    ("para_per_1k", "段落/千字", None),
]

# 分层指标体系: 三层权重, 每层若干指标。用于输出「总贴近度 + 分项雷达」
# 结构层 = 叙事骨架(句长/段/对白/转折节奏); 语言层 = 用词质地(用词/方言/叠字/抒情);
# 语义层 = 情绪张力与氛围(情绪标点/情感形容/套话雷区)。套话(cliche)作为雷区标记而非直接加分。
LAYERS = [
    {
        "name": "structure",
        "label": "结构(句法/段落/对白)",
        "weight": 0.5,
        "keys": ["mean_sentence_len", "short_sentence_ratio", "dialogue_ratio",
                 "avg_para_len", "para_per_1k", "turnword_per_1k"],
    },
    {
        "name": "language",
        "label": "语言(用词/方言/叠字/抒情)",
        "weight": 0.3,
        "keys": ["overlap_bigram_ratio", "dialect_hits_per_1k",
                 "reduplication_per_1k", "affective_adj_ratio"],
    },
    {
        "name": "semantics",
        "label": "语义(情绪张力/氛围)",
        "weight": 0.2,
        "keys": ["emotion_markers_per_1k"],
    },
]

# 雷区: 套话命中越多, 越可能"AI腔/套路", 非原作文气
CLICHE_METRIC = "cliche_per_1k"


def normalize_diff(base, sample, key):
    """归一化离差: 基准为0时直接看样本(上限10); 否则看相对偏差(上限1)。"""
    b = base.get(key, 0) or 0
    s = sample.get(key, 0) or 0
    if b == 0:
        return min(abs(s), 10.0) / 10.0
    return min(abs(b - s) / max(b, 1), 1.0)


def compute_score(base: dict, sample: dict):
    """返回 (贴近度0~100, 每项离差dict, 每项归一化dict)。"""
    diffs = {}
    norms = {}
    for key, _label, _direction in KEYS:
        b = base.get(key, 0)
        s = sample.get(key, 0)
        diffs[key] = round(abs((b or 0) - (s or 0)), 4)
        norms[key] = round(normalize_diff(base, sample, key), 4)

    avg_norm = sum(norms.values()) / len(KEYS)
    score = max(0.0, round(100 - avg_norm * 100, 1))
    return score, diffs, norms


def compute_layered_score(base: dict, sample: dict):
    """分层贴近度: 返回 (overall 0~100, per_layer dict, per_metric_diff dict)。

    overall = Σ(层权重 × 层贴近度)。层贴近度 = 100 - 该层指标平均归一化离差。
    雷区(cliche)额外检测并作为标记输出, 不计入 overall(避免一刀切扣分)。
    """
    layer_scores = {}
    per_layer_diff = {}
    for layer in LAYERS:
        norms = [normalize_diff(base, sample, k) for k in layer["keys"]]
        avg_norm = sum(norms) / len(norms) if norms else 0.0
        layer_score = max(0.0, round(100 - avg_norm * 100, 1))
        layer_scores[layer["name"]] = {
            "label": layer["label"],
            "weight": layer["weight"],
            "score": layer_score,
            "keys": layer["keys"],
        }
    # 雷区: 套话命中
    base_cliche = base.get(CLICHE_METRIC, 0) or 0
    sample_cliche = sample.get(CLICHE_METRIC, 0) or 0
    spare_hits = sample.get("cliche_hits", 0) or 0
    flags = []
    if sample_cliche > base_cliche * 1.5 + 1.0:
        flags.append({
            "label": "AI/爽文套话偏多",
            "info": f"续写套话密度 {sample_cliche}/千字, 高于基准的 {base_cliche}/千字; 建议删减",
            "level": "warn",
        })
    if spare_hits >= 3:
        flags.append({
            "label": "雷区词命中",
            "info": f"检测到 {spare_hits} 处套路/套话用词(如'那一刻/眸子/嘴角勾起/宿命'), 请人工复核是否AI腔",
            "level": "info",
        })

    overall = 0.0
    for layer in LAYERS:
        overall += layer["weight"] * layer_scores[layer["name"]]["score"]
    overall = round(overall, 1)

    per_layer_diff = {layer["name"]: layer_scores[layer["name"]]["score"] for layer in LAYERS}
    return overall, layer_scores, flags, per_layer_diff


def main():
    ap = argparse.ArgumentParser(description="原文 vs 续写的定量文风比对")
    ap.add_argument("--baseline", help="原文风格基准文本(可多文件, 用 ; 分隔)")
    ap.add_argument("--sample", help="续写文本")
    ap.add_argument("--project", help="项目目录(结合 --baseline-index / --sample-rel)")
    ap.add_argument("--baseline-index", type=int, help="项目内用作基准的原文章节序号(1-based)")
    ap.add_argument("--sample-rel", help="项目内续写文件的相对路径(正斜杠分隔)")
    ap.add_argument("--out", help="输出的 metrics json 路径")
    args = ap.parse_args()

    def read(path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    if args.project:
        if args.baseline_index is None or not args.sample_rel:
            print("错误: --project 模式需同时给 --baseline-index 与 --sample-rel", file=sys.stderr)
            sys.exit(1)
        baseline_path = os.path.join(
            args.project, "chapters", "original",
            f"{args.baseline_index:04d}.md",
        )
        if not os.path.isfile(baseline_path):
            print(f"错误: 找不到基准章节 {baseline_path}", file=sys.stderr)
            sys.exit(1)
        baseline_text = read(baseline_path)
        sample_path = os.path.join(args.project, *args.sample_rel.split("/"))
        if not os.path.isfile(sample_path):
            print(f"错误: 找不到续写文件 {sample_path}", file=sys.stderr)
            sys.exit(1)
        sample_text = read(sample_path)
    else:
        if not args.baseline or not args.sample:
            print("错误: 需给出 --baseline 与 --sample, 或 --project+--baseline-index+--sample-rel", file=sys.stderr)
            sys.exit(1)
        baseline_text = "\n".join(read(p) for p in args.baseline.split(";"))
        sample_text = read(args.sample)

    base_metrics = compute_metrics(baseline_text)
    sample_metrics = compute_metrics(sample_text)
    if "error" in base_metrics or "error" in sample_metrics:
        print(base_metrics.get("error") or sample_metrics.get("error"), file=sys.stderr)
        sys.exit(1)

    score, diffs, norms = compute_score(base_metrics, sample_metrics)
    overall, layer_scores, flags, per_layer_score = compute_layered_score(base_metrics, sample_metrics)
    # 向后兼容: 原单一贴近度 = 分层加权总贴近度
    result = {
        "baseline_metrics": base_metrics,
        "sample_metrics": sample_metrics,
        "per_metric_deviation": diffs,
        "per_metric_normalized": norms,
        "style_similarity_score": overall,
        "legacy_average_score": score,
        "overall_similarity": overall,
        "layered_metrics": layer_scores,
        "replica_flags": flags,
    }

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"风格贴近度(分层加权): {overall} / 100")
    for name, info in layer_scores.items():
        print(f"  [{info['label']}] {info['score']} / 100 (权重 {info['weight']})")
    print("各项离差(越小越接近基准):")
    for key, label, _ in KEYS:
        print(f"  {label:<12} 基准={base_metrics.get(key)}  续写={sample_metrics.get(key)} |Δ|={diffs[key]}")
    if flags:
        print("反动漫决提示:")
        for fl in flags:
            print(f"  [{fl['level']}] {fl['label']}: {fl['info']}")


if __name__ == "__main__":
    main()
