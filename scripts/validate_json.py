#!/usr/bin/env python3
"""根据 JSON Schema 校验 JSON 文件。

用法:
    python scripts/validate_json.py --schema schemas/chapter_analysis.schema.json \
        --input projects/my_novel/analysis/chapters/0001.json

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


def validate(schema_path, data_path, schema_dir=DEFAULT_SCHEMA_DIR):
    schema = load_json(schema_path)
    data = load_json(data_path)

    # 注册 schema 目录下所有 schema 文件, 以支持跨文件相对 $ref。
    resources = []
    for p in glob.glob(os.path.join(schema_dir, "*.json")):
        try:
            content = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        file_uri = "file:///" + os.path.abspath(p).replace("\\", "/")
        # 两种 URI 都注册: $id(相对文件名) 与 绝对 file:// 路径
        resources.append((file_uri, DRAFT7.create_resource(content)))
        if "$id" in content:
            resources.append((content["$id"], DRAFT7.create_resource(content)))

    abs_schema = "file:///" + os.path.abspath(schema_path).replace("\\", "/")
    registry = Registry(resources)
    if "$id" in schema:
        registry = registry.with_resource(schema["$id"], DRAFT7.create_resource(schema))
    registry = registry.with_resource(abs_schema, DRAFT7.create_resource(schema))

    validator = Draft7Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return errors


def main():
    ap = argparse.ArgumentParser(description="JSON Schema 校验")
    ap.add_argument("--schema", required=True, help="Schema 文件路径")
    ap.add_argument("--input", required=True, help="待校验的 JSON 文件路径")
    ap.add_argument("--schema-dir", default=DEFAULT_SCHEMA_DIR, help="schema 目录(用于解析相对引用)")
    args = ap.parse_args()

    if not os.path.exists(args.schema):
        print(f"错误: schema 不存在 {args.schema}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.input):
        print(f"错误: 输入不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        errors = validate(args.schema, args.input, args.schema_dir)
    except Exception as e:
        from referencing.exceptions import Unresolvable
        if isinstance(e, Unresolvable) or "RefResolutionError" in type(e).__name__ \
                or "Unresolvable" in type(e).__name__:
            print(f"错误: 无法解析 schema 引用: {e}", file=sys.stderr)
            sys.exit(1)
        raise

    if errors:
        print(f"校验失败 ({len(errors)} 个问题):")
        for e in errors[:30]:
            path = ".".join(str(p) for p in e.path) or "<root>"
            print(f"  - {path}: {e.message}")
        sys.exit(1)
    else:
        print("校验通过 [OK]")


if __name__ == "__main__":
    main()
