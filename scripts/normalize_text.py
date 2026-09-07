#!/usr/bin/env python3
"""文本标准化: 统一换行、清理无意义空格(保留段落结构)、计算字符数。

不修改原文语义, 仅做编码无关的一致性调整。
"""
import re


def normalize(text):
    """统一换行为 \n, 清理行尾空格与多余空白, 保留空行作为段落分隔。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        # 清理行内首尾空格(trim), 保留段首缩进(中文常用全角缩进)
        stripped = line.strip()
        # 全角空格缩进保留
        indent = re.match(r"^([\u3000 ]+)", line)
        indent_str = indent.group(1) if indent else ""
        lines.append(indent_str + stripped)
    # 合并连续空行为单个空行
    result = []
    prev_blank = False
    for ln in lines:
        if ln == "":
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(ln)
            prev_blank = False
    return "\n".join(result).strip() + "\n"


def count_characters(text):
    """统计不含空白与换行的字符数。"""
    return len(re.sub(r"\s+", "", text))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            print(normalize(f.read()))
