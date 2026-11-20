#!/usr/bin/env python3
"""
小红书知识库 — 本地 Markdown 沉淀。

用知识库记住三类东西：
  patterns/  爆款拆解、可复用骨架
  persona.md 账号人设与语气
  topics/    选题池与状态
  reviews/   复盘记录

用法:
    python3 kb.py init                              # 初始化
    python3 kb.py add pattern --title "..." --body -   # 加爆款拆解
    python3 kb.py add topic --title "..." --body -
    python3 kb.py list pattern
    python3 kb.py search 关键词
    python3 kb.py persona                            # 查看人设
    python3 kb.py stats
"""

import argparse
import datetime
import json
import os
import re
import sys

DEFAULT_ROOT = os.path.expanduser("~/xhs")

DIRS = {
    "pattern": "patterns",
    "topic": "topics",
    "review": "reviews",
    "draft": "drafts",
}

PERSONA_TEMPLATE = """# 账号人设

> 这个文件决定所有对外文案的语气。写给模型看的，要具体，不要形容词堆砌。

## 我是谁

- 身份：<一句话，例：在互联网公司做了 6 年产品的女生>
- 领域：<例：职场成长 / 护肤 / 家居改造>
- 不做什么：<例：不带货，不接软广>

## 写给谁

- 人群：<例：25-32 岁一线城市白领女性>
- 他们的处境：<例：工作三年遇到瓶颈，想转行但不敢>
- 他们最烦什么：<例：鸡汤、假大空、成功学>

## 说话风格

- 语气：<例：像朋友聊天，不端着，偶尔自嘲>
- 句子长度：<例：短句为主，一句一个意思>
- 用词禁忌：<例：不用"姐妹们""宝子们"这类称呼>

## 三个真实细节（写稿时会用到）

1. <具体经历>
2. <具体数字>
3. <具体场景>

## 内容支柱

| 支柱 | 占比 | 说明 |
|---|---|---|
| <主题 A> | 50% | |
| <主题 B> | 30% | |
| <主题 C> | 20% | |
"""


def ensure_dirs(root):
    for d in list(DIRS.values()) + ["output"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)
    persona = os.path.join(root, "persona.md")
    if not os.path.exists(persona):
        with open(persona, "w", encoding="utf-8") as f:
            f.write(PERSONA_TEMPLATE)
        return True
    return False


def slugify(text, maxlen=40):
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.strip())[:maxlen].strip("-")
    return s or "untitled"


def cmd_init(root):
    created = ensure_dirs(root)
    print(f"知识库根目录: {root}")
    for d in DIRS.values():
        print(f"  {d}/")
    if created:
        print("\n已生成 persona.md 模板 —— 先把人设填了，后面所有文案都会参考它。")
    else:
        print("\npersona.md 已存在，未覆盖。")
    return 0


def cmd_add(root, kind, title, body, tags):
    ensure_dirs(root)
    if kind not in DIRS:
        print(f"未知类型: {kind}，可选: {', '.join(DIRS)}", file=sys.stderr)
        return 1

    now = datetime.datetime.now()
    stamp = now.strftime("%Y-%m-%d")
    fname = f"{stamp}-{slugify(title)}.md"
    path = os.path.join(root, DIRS[kind], fname)

    front = [
        "---",
        f"title: {title}",
        f"type: {kind}",
        f"created: {now.isoformat(timespec='seconds')}",
    ]
    if tags:
        front.append(f"tags: [{', '.join(tags)}]")
    front.append("---")
    front.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(front) + "\n" + body.strip() + "\n")

    print(f"已保存: {path}")
    return 0


def parse_frontmatter(text):
    meta = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    return meta


def cmd_list(root, kind):
    ensure_dirs(root)
    d = os.path.join(root, DIRS.get(kind, kind))
    if not os.path.isdir(d):
        print(f"没有这个分类: {kind}")
        return 1
    files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    if not files:
        print(f"{kind} 下还没有内容。")
        return 0
    print(f"{kind}（{len(files)} 条）:")
    for f in files:
        p = os.path.join(d, f)
        meta = parse_frontmatter(open(p, encoding="utf-8").read())
        title = meta.get("title", f)
        print(f"  · {f[:10]}  {title}")
    return 0


def cmd_search(root, keyword):
    ensure_dirs(root)
    hits = []
    for kind, sub in DIRS.items():
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".md"):
                continue
            p = os.path.join(d, f)
            text = open(p, encoding="utf-8").read()
            if keyword in text:
                meta = parse_frontmatter(text)
                # 找上下文
                idx = text.find(keyword)
                ctx = text[max(0, idx - 40):idx + 60].replace("\n", " ")
                hits.append((kind, meta.get("title", f), ctx))
    if not hits:
        print(f"没找到「{keyword}」")
        return 0
    print(f"命中 {len(hits)} 条：")
    for kind, title, ctx in hits:
        print(f"\n  [{kind}] {title}")
        print(f"    …{ctx}…")
    return 0


def cmd_persona(root):
    ensure_dirs(root)
    p = os.path.join(root, "persona.md")
    print(open(p, encoding="utf-8").read())
    return 0


def cmd_stats(root):
    ensure_dirs(root)
    total = 0
    print(f"知识库: {root}\n")
    for kind, sub in DIRS.items():
        d = os.path.join(root, sub)
        n = len([f for f in os.listdir(d) if f.endswith(".md")]) if os.path.isdir(d) else 0
        total += n
        print(f"  {sub:<10} {n:>3} 条")
    persona_len = 0
    p = os.path.join(root, "persona.md")
    if os.path.exists(p):
        persona_len = len(open(p, encoding="utf-8").read())
    print(f"\n  persona.md  {persona_len} 字符" + ("（还是模板，待填写）" if "例：" in open(p, encoding='utf-8').read() else "（已填写）"))
    print(f"\n  合计 {total} 条")
    return 0


def main():
    ap = argparse.ArgumentParser(description="小红书本地知识库")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="知识库根目录")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    p_add = sub.add_parser("add")
    p_add.add_argument("kind", choices=list(DIRS.keys()))
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--body", default="-", help="内容，- 表示从 stdin 读")
    p_add.add_argument("--tags", default="", help="逗号分隔")

    p_list = sub.add_parser("list")
    p_list.add_argument("kind", choices=list(DIRS.keys()))

    p_search = sub.add_parser("search")
    p_search.add_argument("keyword")

    sub.add_parser("persona")
    sub.add_parser("stats")

    args = ap.parse_args()
    root = os.path.expanduser(args.root)

    if args.cmd == "init":
        return cmd_init(root)
    if args.cmd == "add":
        body = sys.stdin.read() if args.body == "-" else args.body
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        return cmd_add(root, args.kind, args.title, body, tags)
    if args.cmd == "list":
        return cmd_list(root, args.kind)
    if args.cmd == "search":
        return cmd_search(root, args.keyword)
    if args.cmd == "persona":
        return cmd_persona(root)
    if args.cmd == "stats":
        return cmd_stats(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
