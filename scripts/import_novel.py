#!/usr/bin/env python3
"""导入小说文件到项目 source/ 目录。

用法:
    python scripts/import_novel.py --input ./novel.txt --project ./projects/my_novel

支持 TXT / Markdown(检测编码)。保留原始文件, 计算 SHA-256, 保存导入信息, 不修改原文内容。
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

try:
    from charset_normalizer import from_bytes
except ImportError:
    from_bytes = None


def read_text(path):
    """读取文件, 优先使用 charset-normalizer 检测编码, 失败则尝试常用编码。"""
    with open(path, "rb") as f:
        raw = f.read()
    if from_bytes is not None:
        guess = from_bytes(raw).best()
        if guess is not None:
            return str(guess)
    for enc in ("utf-8", "gbk", "gb18030", "big5"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(f"无法识别文件编码: {path}")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="导入小说文件")
    ap.add_argument("--input", required=True, help="源小说文件路径")
    ap.add_argument("--project", required=True, help="项目目录")
    args = ap.parse_args()

    proj = args.project
    pj_path = os.path.join(proj, "project.json")
    if not os.path.exists(pj_path):
        print(f"错误: 项目不存在 {proj}, 请先运行 init_project.py", file=sys.stderr)
        sys.exit(1)

    with open(pj_path, encoding="utf-8") as f:
        project = json.load(f)

    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在 {args.input}", file=sys.stderr)
        sys.exit(1)

    text = read_text(args.input)
    raw = open(args.input, "rb").read()
    original_dir = os.path.join(proj, "source")
    os.makedirs(original_dir, exist_ok=True)

    src_name = os.path.basename(args.input)
    # 保存标准化的正文(作为 chapters 切分源)
    from normalize_text import normalize
    norm_path = os.path.join(original_dir, "original.txt")
    with open(norm_path, "w", encoding="utf-8") as f:
        f.write(normalize(text))

    # 保留原始副本
    raw_path = os.path.join(original_dir, "raw_" + src_name)
    with open(raw_path, "wb") as f:
        f.write(raw)

    import_info = {
        "source_file": os.path.abspath(args.input),
        "raw_copy": raw_path,
        "normalized_copy": norm_path,
        "encoding": "detected",
        "original_sha256": sha256_bytes(raw),
        "imported_at": datetime.now().isoformat(),
        "characters": len("".join(text.split())),
    }
    with open(os.path.join(original_dir, "import_info.json"), "w", encoding="utf-8") as f:
        json.dump(import_info, f, ensure_ascii=False, indent=2)

    project["status"] = "imported"
    project["updated_at"] = datetime.now().isoformat()
    with open(pj_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    print(f"导入成功: {args.input}")
    print(f"  字符数   : {import_info['characters']}")
    print(f"  SHA-256  : {import_info['original_sha256'][:16]}...")
    print(f"  状态     : imported")


if __name__ == "__main__":
    main()
