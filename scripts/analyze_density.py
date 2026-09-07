#!/usr/bin/env python3
"""自动探知全书"叙事密度档位", 供续写时强制该档位密度, 破解"比原著偏薄/被压成纲要式"问题。

用法:
    python scripts/analyze_density.py --project ./projects/my_novel

从 indexes/chapter_manifest.json 读取各章路径, 读正文字数统计各章密度指标,
归并出全书主流密度档位(密实/中等/疏朗), 写入:
  - indexes/density_stats.json   各章指标 + 全书档位
  - project.json 的 density_tier  供 write_scene.md / light_continue.md 强制档位

密度定义见 style_metrics.classify_density():
  密实 = 短句多、段落碎、对白/方言/叠字密(武侠/黑道/盗墓/克制白描)
  疏朗 = 句长偏长、段落少、抒情舒展(诗意/史诗/暖心)
  中等 = 介于两者之间
建议在 estimate_chapter_length.py 之后运行。
"""
import argparse
import json
import os
import sys
from collections import Counter

from style_metrics import compute_metrics, classify_density


def main():
    ap = argparse.ArgumentParser(description="自动探知全书叙事密度档位")
    ap.add_argument("--project", required=True, help="项目目录")
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

    per_chapter = {}
    tier_counts = Counter()
    for entry in manifest:
        cid = entry.get("chapter_id")
        path = entry.get("path")
        if cid is None or not path:
            continue
        abs_path = os.path.join(proj, path)
        if not os.path.isfile(abs_path):
            continue
        try:
            with open(abs_path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        metrics = compute_metrics(text)
        if "error" in metrics:
            continue
        tier = classify_density(metrics)
        per_chapter[cid] = {"tier": tier, **metrics}
        tier_counts[tier] += 1

    if not per_chapter:
        print("错误: 无有效章节可统计", file=sys.stderr)
        sys.exit(1)

    # 全书档位 = 出现最多的单章档; 若并列, 取"中等"优先(保守)
    tier = tier_counts.most_common(1)[0][0] if tier_counts else "中等"

    density_stats = {
        "chapter_count": len(per_chapter),
        "overall_tier": tier,
        "tier_distribution": dict(tier_counts),
        "per_chapter": per_chapter,
    }

    with open(os.path.join(proj, "indexes", "density_stats.json"), "w", encoding="utf-8") as f:
        json.dump(density_stats, f, ensure_ascii=False, indent=2)

    from datetime import datetime

    with open(project_path, encoding="utf-8") as f:
        project = json.load(f)
    project["density_tier"] = tier
    project["updated_at"] = datetime.now().isoformat()
    with open(project_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    print(f"密度探知完成: 共 {len(per_chapter)} 章")
    print(f"  单章档位分布: {dict(tier_counts)}")
    print(f"  全书主流档位: {tier}   -> 已写入 density_tier")


if __name__ == "__main__":
    main()
