#!/usr/bin/env python3
"""
每日选题简报 — 从知识库生成，不联网。

设计立场：**不做自动采集**。
自动刷小红书要登录、要浏览器、有封号风险，而且刷来的热点质量参差。
这个脚本只做一件事：把你自己积累的知识库，按优先级整理成今天的行动清单。

用法:
    python3 digest.py                    # 输出到终端
    python3 digest.py --out ~/xhs/output/daily.md
    python3 digest.py --cron             # 生成 crontab 行
"""

import argparse
import datetime
import os
import re
import sys

DEFAULT_ROOT = os.path.expanduser("~/xhs")


def read_frontmatter(path):
    text = open(path, encoding="utf-8").read()
    meta = {}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            meta["_body"] = parts[2].strip()
    else:
        meta["_body"] = text
    return meta


def collect(root, kind):
    d = os.path.join(root, kind)
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            m = read_frontmatter(os.path.join(d, f))
            m["_file"] = f
            out.append(m)
    return out


def days_since(iso):
    try:
        dt = datetime.datetime.fromisoformat(iso)
        return (datetime.datetime.now() - dt).days
    except Exception:
        return 999


def build_digest(root):
    today = datetime.date.today()
    lines = [
        f"# 今日选题简报 · {today.isoformat()}",
        "",
    ]

    # 人设状态
    persona_path = os.path.join(root, "persona.md")
    persona_ready = False
    if os.path.exists(persona_path):
        content = open(persona_path, encoding="utf-8").read()
        persona_ready = "例：" not in content

    if not persona_ready:
        lines += [
            "## ⚠️ 第一步：填人设",
            "",
            "`~/xhs/persona.md` 还是空模板。**在填完之前，其他分析的参考价值有限。**",
            "",
            f"  open {persona_path}",
            "",
        ]

    # 待写选题
    topics = collect(root, "topics")
    pending = [t for t in topics if "待写" in t.get("tags", "")]
    if pending:
        lines += [f"## 待写选题（{len(pending)} 个）", ""]
        for t in pending[:5]:
            title = t.get("title", t["_file"])
            age = days_since(t.get("created", ""))
            flag = " ⏰ 已久" if age > 14 else ""
            lines.append(f"- {title}{flag}（{age} 天前）")
        lines.append("")
    else:
        lines += ["## 待写选题", "", "空。用 `xhs-topic-ideas` 生成一批。", ""]

    # 爆款库
    patterns = collect(root, "patterns")
    if patterns:
        recent = sorted(patterns, key=lambda p: p.get("created", ""), reverse=True)[:3]
        lines += [f"## 爆款库（{len(patterns)} 条，最近 3 条）", ""]
        for p in recent:
            lines.append(f"- {p.get('title', p['_file'])}")
        lines.append("")
        lines += ["  → 缺选题时从这里找骨架迁移。", ""]

    # 复盘提醒
    reviews = collect(root, "reviews")
    last_review = max((days_since(r.get("created", "")) for r in reviews), default=999)
    if last_review > 30:
        lines += [
            "## 📊 该复盘了",
            "",
            f"上次复盘是 {last_review} 天前。" if last_review < 999 else "还没有复盘记录。",
            "用 `xhs-account-audit` 跑一次，粘贴近期笔记数据。",
            "",
        ]

    # 今日建议
    lines += ["## 今天做一件事", ""]
    if not persona_ready:
        lines.append("**填 persona.md**。这是所有后续工作的前提。")
    elif pending:
        lines.append(f"把「{pending[0].get('title', '待写选题')}」写出来。")
    elif patterns:
        lines.append("从爆款库挑一个骨架，做一次迁移仿写。")
    else:
        lines.append("用 `xhs-topic-ideas` 生成 5 个选题，存入知识库。")
    lines.append("")

    # 流程提醒
    lines += [
        "---",
        "",
        "发布前别忘：`xhs-compliance-check` 检测 → 人工通读 → 再发。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="每日选题简报")
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--out", help="写入文件")
    ap.add_argument("--cron", action="store_true", help="输出 crontab 配置")
    args = ap.parse_args()

    if args.cron:
        script = os.path.abspath(__file__)
        out = os.path.expanduser("~/xhs/output/daily.md")
        print("# 每天早 8 点生成简报，复制到 crontab -e")
        print(f"0 8 * * * /usr/bin/env python3 {script} --out {out}")
        print()
        print("# 只工作日：")
        print(f"0 8 * * 1-5 /usr/bin/env python3 {script} --out {out}")
        print()
        print("# 注意：cron 环境变量很少，如果 python3 找不到，用绝对路径")
        print(f"# {sys.executable}")
        return 0

    root = os.path.expanduser(args.root)
    if not os.path.isdir(root):
        print(f"知识库不存在：{root}，先跑 kb.py init", file=sys.stderr)
        return 1

    text = build_digest(root)

    if args.out:
        out = os.path.expanduser(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"简报已写入 {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
