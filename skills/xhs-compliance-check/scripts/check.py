#!/usr/bin/env python3
"""
小红书文案合规自检 — 纯本地，不联网。

用法:
    python3 check.py "文案内容"
    python3 check.py --file draft.txt
    echo "文案" | python3 check.py -
    python3 check.py --file draft.txt --json
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(HERE, "words.json")

LEVEL_LABEL = {"high": "🔴 高危", "medium": "🟡 中危", "low": "🔵 低危"}
LEVEL_ORDER = {"high": 0, "medium": 1, "low": 2}

# 常见误报排除：命中的词如果落在这些上下文里，不算违规。
# 目的是压掉"第一次用""最大值""最后一页"这类纯叙述用法。
EXCLUDE_PATTERNS = {
    "第一": [r"第一次", r"第一步", r"第一天", r"第一周", r"第一个月", r"第一眼",
             r"第一印象", r"第一感觉", r"第一时间", r"第一瓶", r"第一支", r"第一件",
             r"第一年", r"第一次见", r"第一家", r"第一节", r"第一条", r"第一张"],
    "第二": [r"第二次", r"第二周", r"第二步"],
    "最新": [r"最新消息", r"最新一集", r"最新一期"],
    "最大": [r"最大值", r"最大音量", r"最大尺寸", r"最大光圈"],
    "最小": [r"最小值"],
    "最好": [r"最好的自己", r"最好的状态"],
    "绝对": [r"绝对值"],
    "首个": [r"首个尝试"],
    "私聊": [r"私聊我"],  # 私聊仍是导流，但比"微信"轻，单独保留提示
}


def load_dict(path=DICT_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_index(data):
    """词 -> (分类, 等级)。长词优先，避免"微信"抢了"微信号"的匹配。"""
    entries = []
    for cat, info in data["categories"].items():
        for w in info["words"]:
            entries.append((w, cat, info["level"], info["desc"]))
    entries.sort(key=lambda x: len(x[0]), reverse=True)
    return entries


def is_excluded(text, idx, word):
    """命中的词是否落在无害上下文里（如"第一次""最大值"）。"""
    patterns = EXCLUDE_PATTERNS.get(word)
    if not patterns:
        return False
    # 看词前 2 个字符到词尾后 6 个字符这一小段
    window = text[max(0, idx - 2): idx + len(word) + 6]
    for p in patterns:
        m = re.search(p, window)
        if m:
            # 排除短语必须覆盖命中词的起点
            abs_start = max(0, idx - 2) + m.start()
            if abs_start <= idx < abs_start + (m.end() - m.start()):
                return True
    return False


def detect(text, entries, replacements, ner=True):
    hits = []
    taken = [False] * len(text)

    for word, cat, level, desc in entries:
        start = 0
        while True:
            idx = text.find(word, start)
            if idx < 0:
                break
            # 已被更长的词占用则跳过
            if any(taken[idx:idx + len(word)]):
                start = idx + 1
                continue
            # 落在无害上下文里则跳过（"第一次""最大值"）
            if is_excluded(text, idx, word):
                start = idx + 1
                continue
            for i in range(idx, idx + len(word)):
                taken[i] = True
            hits.append({
                "word": word,
                "category": cat,
                "level": level,
                "position": idx,
                "context": text[max(0, idx - 8):idx + len(word) + 8],
                "suggestions": replacements.get(word, []),
            })
            start = idx + len(word)

    # 联系方式 / 外链检测
    if not ner or True:
        for m in re.finditer(r"1[3-9]\d{9}", text):
            hits.append({
                "word": m.group(), "category": "联系方式", "level": "high",
                "position": m.start(), "context": text[max(0, m.start() - 8):m.end() + 8],
                "suggestions": ["移除手机号"],
            })
        for m in re.finditer(r"https?://\S+", text):
            hits.append({
                "word": m.group()[:40], "category": "外链", "level": "high",
                "position": m.start(), "context": text[max(0, m.start() - 8):m.end() + 8],
                "suggestions": ["移除链接"],
            })

    hits.sort(key=lambda h: (LEVEL_ORDER.get(h["level"], 9), h["position"]))
    return hits


def render(text, hits):
    if not hits:
        return "✅ 未命中词库中的风险词。\n\n注意：词库只能兜底，发布前仍建议人工通读一遍。"

    counts = {"high": 0, "medium": 0, "low": 0}
    for h in hits:
        counts[h["level"]] = counts.get(h["level"], 0) + 1

    lines = [
        f"⚠️ 命中 {len(hits)} 处风险词："
        f"🔴 高危 {counts['high']} · 🟡 中危 {counts['medium']} · 🔵 低危 {counts['low']}",
        "",
    ]
    if counts["high"]:
        lines.append("🚨 存在高危词，直接发布可能限流或封号，务必先改。")
        lines.append("")

    current = None
    for h in hits:
        if h["level"] != current:
            current = h["level"]
            lines.append(f"{LEVEL_LABEL[current]}")
        ctx = h["context"].replace("\n", " ")
        lines.append(f"  · 「{h['word']}」 — {h['category']}｜位置 {h['position']}")
        lines.append(f"    上下文：…{ctx}…")
        if h["suggestions"]:
            lines.append(f"    可换：{' / '.join(h['suggestions'])}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="小红书文案合规自检（本地）")
    ap.add_argument("text", nargs="?", help="待检测文案；用 - 表示从 stdin 读")
    ap.add_argument("--file", help="从文件读取文案")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    elif args.text == "-" or (args.text is None and not sys.stdin.isatty()):
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        ap.error("请提供文案，或用 --file / - 从文件或 stdin 读取")

    data = load_dict()
    entries = build_index(data)
    hits = detect(text, entries, data.get("replacements", {}))

    if args.json:
        print(json.dumps({
            "length": len(text),
            "total": len(hits),
            "hits": hits,
        }, ensure_ascii=False, indent=2))
    else:
        print(render(text, hits))
        print(f"\n—— 共检测 {len(text)} 字")


if __name__ == "__main__":
    main()
