#!/usr/bin/env python3
"""章节切分: 从标准化正文切分章节, 输出到 chapters/original/000N.md。

用法:
    python scripts/split_chapters.py --project ./projects/my_novel
    python scripts/split_chapters.py --project ./projects/my_novel --regex '^第[一二三...]章'

默认强信号章节标题规则(优先识别, 误伤正文概率低):
    ^\[[^\[\]]{1,80}\]$
    ^第[零一二三四五六七八九十百千万两0-9]+[章节卷回部].*$
    ^Chapter\s+\d+.*$
弱信号规则(仅在强信号完全未命中任何章节时兜底启用, 可用 --weak 强制、--no-weak 禁用):
    ^[一二三四五六七八九十]+、\s*\S+$
    ^\d{1,3}[、\.．]\s*\S+$
(--regex 可多次传入, 追加自定义正则并合并到强信号; 自动跳过页面说明行与去重相邻重复标题)
"""
import argparse
import hashlib
import json
import os
import re
import sys

# 强信号: 大概率是真正的章节标题, 默认优先识别。
#   注意: 这些模式本身很明确(方括号包裹 / 第X章回节卷部 / Chapter N), 误伤正文概率低。
STRONG_PATTERNS = [
    # 方括号单行标题(最常见, 如 [第一章] / [第1回 标题] / [序] / [第一章 · 一])
    r"^\[[^\[\]]{1,80}\]$",
    # 第X章/回/节/卷/部 [+ 标题]。要求"章/回"后跟空白或行尾, 避免误判 "第二回正文。" 这类正文句
    r"^第[零一二三四五六七八九十百千万两0-9]+[章节卷回部](\s.*)?$",
    r"^Chapter\s+\d+.*$",
]

# 弱信号: 仅在全文找不到任何强信号章节标题时才兜底启用。
#   这类模式(如 "一、二、" 或 "1、2、")容易把正文里的分点句误判为标题,
#   因此不默认使用, 只在强信号完全未命中时作为最后的线索。
WEAK_PATTERNS = [
    # 中文数字编号 + 顿号(如 一、二、)
    r"^[一二三四五六七八九十]+、\s*\S+$",
    # 阿拉伯数字编号 (如 1、 1.  1 )
    r"^\d{1,3}[、\.．]\s*\S+$",
]

# 明显不是标题、应跳过的行(页面说明/格式残留)
SKIP_TITLE_LINES = [
    r"^={2,}.*={2,}$",          # === 页面标题说明 ===
    r"^www\..*$",                # 网址
]

# 章节标题行最大长度(字符, 含标点)。过长因此极可能是正文句子而非标题。
#   eg. 章回体正文常以 "第四回中已将……" 开头, 会被 "第X回" 正则在强信号里误判为标题;
#       其实那是正文一整段, 长达数千字, 远超标题长度。设置上限可剔除这种误判。
#   方括号标题(如 [第1回 …])此时也会因超长被剔除, 属正常防御。
MAX_TITLE_LEN = 60


def is_title_line(line, patterns):
    """判断 line 是否是一条可信的章节标题行。"""
    s = line.strip()
    if not s:
        return False
    if any(re.match(sp, line) for sp in SKIP_TITLE_LINES):
        return False
    if len(s) > MAX_TITLE_LEN:
        return False
    return any(re.match(pat, line) for pat in patterns)


def detect_chapter_lines(lines, patterns):
    idxs = []
    for i, line in enumerate(lines):
        if is_title_line(line, patterns):
            idxs.append(i)
    return idxs


def resolve_patterns(extra_extras, allow_weak):
    """返回实际使用的模式列表。

    强信号优先: extra_extras(用户 --regex)与 STRONG_PATTERNS 合并, 若命中则只启用这些;
    弱信号仅当 allow_weak 为真且强信号在这篇文本里一条都没命中时才兜底加入。
    """
    strong = (extra_extras or []) + STRONG_PATTERNS
    if not allow_weak:
        return strong
    return strong + WEAK_PATTERNS


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def title_key(line):
    """规范化标题用于去重: 去方括号、去空白、去首尾标点。"""
    s = line.strip()
    s = re.sub(r"^\[|\]$", "", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[。．.、，,；;：:！!？?…·\-—_]+$", "", s)
    return s


def dedupe_idxs(idx_list, lines):
    """抑制相邻重复标题(如 [第一章] 与 第一章 紧邻), 保留首个。"""
    kept = []
    prev_key = None
    for i in idx_list:
        k = title_key(lines[i])
        if k and k != prev_key:
            kept.append(i)
            prev_key = k
    return kept


def split(text, patterns):
    """返回 [(title, body)]。若无标题结构则视为单章。"""
    lines = text.split("\n")
    idxs = detect_chapter_lines(lines, patterns)
    if not idxs:
        return [("全文", text.strip())]
    idxs = dedupe_idxs(idxs, lines)
    chapters = []
    for i, start in enumerate(idxs):
        end = idxs[i + 1] if i + 1 < len(idxs) else len(lines)
        title = re.sub(r"\s+", " ", lines[start].strip())
        body = "\n".join(lines[start + 1:end]).strip()
        chapters.append((title, body))
    return chapters


def main():
    ap = argparse.ArgumentParser(description="切分章节")
    ap.add_argument("--project", required=True)
    ap.add_argument("--regex", action="append", default=None, help="自定义章节标题正则(可多次, 与默认强信号合并)")
    ap.add_argument("--weak", action="store_true", default=False,
                    help="允许启用弱信号标题规则(中文数字顿号/阿拉伯数字编号)。默认仅在强信号未命中任何章节时自动兜底启用。")
    ap.add_argument("--no-weak", action="store_true", default=False,
                    help="禁用弱信号(即使强信号未命中也不使用弱信号)。")
    args = ap.parse_args()

    proj = args.project
    pj_path = os.path.join(proj, "project.json")
    if not os.path.exists(pj_path):
        print(f"错误: 项目不存在 {proj}", file=sys.stderr)
        sys.exit(1)

    with open(pj_path, encoding="utf-8") as f:
        project = json.load(f)

    src = os.path.join(proj, "source", "original.txt")
    if not os.path.exists(src):
        print(f"错误: 未找到 {src}, 请先导入小说", file=sys.stderr)
        sys.exit(1)

    with open(src, encoding="utf-8") as f:
        text = f.read()

    strong = (args.regex or []) + STRONG_PATTERNS
    # 先仅用强信号检测, 决定是否需要弱信号兜底
    patterns = strong
    if not args.no_weak:
        lines = text.split("\n")
        if not detect_chapter_lines(lines, strong):
            # 强信号完全未命中: 若允许弱信号(默认自动兜底, 或显式 --weak), 则加入弱信号
            if not args.weak:
                print("提示: 未命中强信号章节标题, 尝试用弱信号规则(中文数字/阿拉伯数字编号)兜底识别。")
            patterns = strong + WEAK_PATTERNS
    chapters = split(text, patterns)

    orig_dir = os.path.join(proj, "chapters", "original")
    os.makedirs(orig_dir, exist_ok=True)

    manifest = []
    for i, (title, body) in enumerate(chapters, start=1):
        chapter_id = f"{i:04d}"
        fpath = os.path.join(orig_dir, f"{chapter_id}.md")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
        manifest.append({
            "chapter_id": chapter_id,
            "order": i,
            "title": title,
            "path": os.path.relpath(fpath, proj),
            "character_count": len("".join(body.split())),
            "sha256": sha256(body),
        })

    idx_dir = os.path.join(proj, "indexes")
    os.makedirs(idx_dir, exist_ok=True)
    with open(os.path.join(idx_dir, "chapter_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    project["status"] = "split"
    project["original_chapter_count"] = len(manifest)
    import datetime
    project["updated_at"] = datetime.datetime.now().isoformat()
    with open(pj_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

    print(f"切分完成: {len(manifest)} 章")
    for m in manifest:
        print(f"  {m['chapter_id']} {m['title']} ({m['character_count']}字)")
    if not manifest:
        print("提示: 未识别到章节标题, 已作为单章处理。若切分不正确, 请检查标题或用 --regex 自定义。")


if __name__ == "__main__":
    main()
