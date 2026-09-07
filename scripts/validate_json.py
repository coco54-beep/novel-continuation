#!/usr/bin/env python3
"""根据 JSON Schema 校验 JSON 文件。

用法:
    python scripts/validate_json.py --schema schemas/chapter_analysis.schema.json \
        --input projects/my_novel/analysis/chapters/0001.json
    python scripts/validate_json.py --schema schemas/character.schema.json \
        --input projects/my_novel/story_bible/characters.json --items

--items: 当输入是"容器数组"文件(story_bible/*.json、ending_proposals.json、
         chapter_outlines.json、scenes/*.json 等)时, 逐元素按同一 schema 校验,
         并报告每个元素的错误位置。

支持内部 $ref 与同目录下的相对 $ref 文件。校验失败时显示具体错误路径。
"""
import argparse
import glob
import json
import os
import sys

try:
    import jsonschema
    from jsonschema import Draft7Validator
    from referencing import Registry
    from referencing.jsonschema import DRAFT7
except ImportError:
    print("错误: 需要 jsonschema/referencing 库, 请运行 pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCHEMA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "schemas")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_validator(schema_path, schema_dir=DEFAULT_SCHEMA_DIR):
    """加载 schema 及其目录下全部 schema, 返回 (schema, Draft7Validator)。"""
    schema = load_json(schema_path)

    resources = []
    for p in glob.glob(os.path.join(schema_dir, "*.json")):
        try:
            content = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        file_uri = "file:///" + os.path.abspath(p).replace("\\", "/")
        resources.append((file_uri, DRAFT7.create_resource(content)))
        if "$id" in content:
            resources.append((content["$id"], DRAFT7.create_resource(content)))

    abs_schema = "file:///" + os.path.abspath(schema_path).replace("\\", "/")
    registry = Registry(resources)
    if "$id" in schema:
        registry = registry.with_resource(schema["$id"], DRAFT7.create_resource(schema))
    registry = registry.with_resource(abs_schema, DRAFT7.create_resource(schema))
    return schema, Draft7Validator(schema, registry=registry)


def validate(schema_path, data_path, schema_dir=DEFAULT_SCHEMA_DIR):
    schema, validator = build_validator(schema_path, schema_dir)
    data = load_json(data_path)
    return sorted(validator.iter_errors(data), key=lambda e: list(e.path))


def validate_items(schema_path, data_path, schema_dir=DEFAULT_SCHEMA_DIR):
    """对数组容器的每个元素逐项校验, 返回 [(index, [errors])]"""
    schema, validator = build_validator(schema_path, schema_dir)
    data = load_json(data_path)
    if not isinstance(data, list):
        raise ValueError("--items 模式要求输入为数组, 当前不是 list")
    problems = []
    for i, item in enumerate(data):
        errs = sorted(validator.iter_errors(item), key=lambda e: list(e.path))
        if errs:
            problems.append((i, errs))
    return problems


def main():
    ap = argparse.ArgumentParser(description="JSON Schema 校验")
    ap.add_argument("--schema", required=True, help="Schema 文件路径")
    ap.add_argument("--input", required=True, help="待校验的 JSON 文件路径")
    ap.add_argument("--items", action="store_true",
                    help="输入为数组容器时, 逐元素按 schema 校验(默认按整体校验)")
    ap.add_argument("--schema-dir", default=DEFAULT_SCHEMA_DIR, help="schema 目录(用于解析相对引用)")
    args = ap.parse_args()

    if not os.path.exists(args.schema):
        print(f"错误: schema 不存在 {args.schema}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.input):
        print(f"错误: 输入不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.items:
            problems = validate_items(args.schema, args.input, args.schema_dir)
        else:
            problems = []
            for e in validate(args.schema, args.input, args.schema_dir):
                problems.append((None, [e]))
    except Exception as e:
        from referencing.exceptions import Unresolvable
        if isinstance(e, Unresolvable) or "RefResolutionError" in type(e).__name__ \
                or "Unresolvable" in type(e).__name__:
            print(f"错误: 无法解析 schema 引用: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    total = sum(len(errs) for _, errs in problems)
    if total:
        label = "数组逐元素校验" if args.items else "校验"
        print(f"{label}失败 ({total} 个问题):")
        shown = 0
        for idx, errs in problems:
            for e in errs:
                if shown >= 30:
                    break
                shown += 1
                where = f"<root>" if not list(e.path) else ".".join(str(p) for p in e.path)
                prefix = f"[{idx}] " if idx is not None else ""
                print(f"  - {prefix}{where}: {e.message}")
        sys.exit(1)
    else:
        mode = " (数组, 逐元素校验通过)" if args.items else ""
        print(f"校验通过 [OK]{mode}")


if __name__ == "__main__":
    main()
