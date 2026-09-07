#!/usr/bin/env python3
"""半自动生成全书文风指纹脚手架 `analysis/style_profile.json`(符合 style_profile.schema.json)。

用法:
    python scripts/build_style_profile.py --project ./projects/my_novel
    python scripts/build_style_profile.py --project ./projects/my_novel --out ./tmp/profile.json

脚本只负责**确定性**部分:
  - 读 project.json 的 target_chapter_length / density_tier;
  - 读 indexes/length_stats.json 与 indexes/density_stats.json 的可量化指标;
  - 组装成符合 style_profile.schema.json 的脚手架, 文本类/清单类字段(paradigm, voice,
    cultural_references, material_details, catchphrases, pitfalls 等)留空, 由智能体基于
    prompts/analyze_style.md 填充。

提示词 analyze_style.md 引用本脚本, 分析完用 validate_json.py 校验产物。
"""
import argparse
import json
import os
import re
import sys


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _mean_sentence_len_from_density(density_stats):
    """从密度统计取全书平均句长/段落指标(若有), 否则 None。"""
    chapters = density_stats.get("per_chapter", {})
    lens = [c.get("mean_sentence_len") for c in chapters.values() if c.get("mean_sentence_len") is not None]
    paras = [c.get("para_per_1k") for c in chapters.values() if c.get("para_per_1k") is not None]
    short = [c.get("short_sentence_ratio") for c in chapters.values() if c.get("short_sentence_ratio") is not None]
    dlg = [c.get("dialogue_ratio") for c in chapters.values() if c.get("dialogue_ratio") is not None]
    return {
        "mean_sentence_len": round(sum(lens) / len(lens), 2) if lens else None,
        "short_sentence_ratio": round(sum(short) / len(short), 4) if short else None,
        "dialogue_ratio_metric": round(sum(dlg) / len(dlg), 4) if dlg else None,
        "para_per_1k": round(sum(paras) / len(paras), 3) if paras else None,
    }


def main():
    ap = argparse.ArgumentParser(description="半自动生成文风指纹脚手架")
    ap.add_argument("--project", required=True, help="项目目录")
    ap.add_argument("--out", default=None, help="输出路径(默认 analysis/style_profile.json)")
    args = ap.parse_args()

    proj = args.project
    project_path = os.path.join(proj, "project.json")
    if not os.path.isfile(project_path):
        print(f"错误: 找不到 {project_path}, 请先运行 init_project.py", file=sys.stderr)
        sys.exit(1)

    project = _read_json(project_path)
    length_stats = {}
    if os.path.isfile(os.path.join(proj, "indexes", "length_stats.json")):
        length_stats = _read_json(os.path.join(proj, "indexes", "length_stats.json"))
    density_stats = {}
    if os.path.isfile(os.path.join(proj, "indexes", "density_stats.json")):
        density_stats = _read_json(os.path.join(proj, "indexes", "density_stats.json"))

    meta = _mean_sentence_len_from_density(density_stats)
    profile = {
        "schema_version": "1.0",
        "project_id": project.get("project_id", ""),
        "paradigm": "",
        "density_tier": project.get("density_tier", "中等"),
        "perspective": "",
        "voice": "",
        "sentence_rhythm": "",
        "emotion_presentation": "",
        "dialogue_ratio": "",
        "description_style": "",
        "cultural_references": [],
        "material_details": [],
        "catchphrases": [],
        "pitfalls": [],
        "style_metrics": {
            "target_chapter_length": project.get("target_chapter_length"),
            **meta,
        },
        "notes": "以下为半自动脚手架: 确定性字段(密度档/篇幅/指标)已由脚本读取 project.json 与 indexes/*.json 填充; 其余文本类/清单类字段待智能体基于 prompts/analyze_style.md 与 references/style_library.md 填充后, 用 validate_json.py 校验。",
    }

    out = args.out or os.path.join(proj, "analysis", "style_profile.json")
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print(f"文风指纹脚手架已生成: {out}")
    print(f"  密度档位: {profile['density_tier']}")
    print(f"  目标篇幅: {profile['style_metrics']['target_chapter_length']}")
    print("  (范式/声口/具体抓手/踩坑点待智能体填充)")


if __name__ == "__main__":
    main()
