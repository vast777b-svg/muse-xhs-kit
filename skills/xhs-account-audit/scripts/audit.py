#!/usr/bin/env python3
"""
账号体检 — 把笔记数据粘进来，算诊断结论。

用「复制粘贴」而不是自动抓取。原因：
  自动抓取要登录、要浏览器、有封号风险。
  而用户自己的笔记数据本来就能在创作者中心看到，复制成本很低。

用法:
    python3 audit.py --file notes.csv
    python3 audit.py --file notes.json
    python3 audit.py --sample          # 看输入格式样例

CSV 表头（顺序不限，用英文名）:
    date,title,likes,collects,comments,views
    2026-11-01,我的第一个笔记,120,45,8,3000
"""

import argparse
import csv
import json
import os
import statistics
import sys


def load_csv(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({
                    "date": r.get("date", "").strip(),
                    "title": r.get("title", "").strip(),
                    "likes": int(float(r.get("likes") or 0)),
                    "collects": int(float(r.get("collects") or 0)),
                    "comments": int(float(r.get("comments") or 0)),
                    "views": int(float(r.get("views") or 0)),
                })
            except (ValueError, TypeError):
                continue
    return rows


def load_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "notes" in data:
        data = data["notes"]
    rows = []
    for r in data:
        rows.append({
            "date": str(r.get("date", "")),
            "title": str(r.get("title", "")),
            "likes": int(r.get("likes", 0) or 0),
            "collects": int(r.get("collects", 0) or 0),
            "comments": int(r.get("comments", 0) or 0),
            "views": int(r.get("views", 0) or 0),
        })
    return rows


def rate(a, b):
    return (a / b * 100) if b else 0.0


def analyze(rows):
    if not rows:
        return None

    for r in rows:
        r["interactions"] = r["likes"] + r["collects"] + r["comments"]
        r["ctr"] = rate(r["interactions"], r["views"]) if r["views"] else 0
        r["collect_rate"] = rate(r["collects"], r["interactions"]) if r["interactions"] else 0
        r["comment_rate"] = rate(r["comments"], r["interactions"]) if r["interactions"] else 0

    n = len(rows)
    views = [r["views"] for r in rows if r["views"] > 0]
    inter = [r["interactions"] for r in rows]

    med_views = statistics.median(views) if views else 0
    med_inter = statistics.median(inter) if inter else 0

    # 爆款判定：互动量超过中位数 2 倍
    hits = [r for r in rows if r["interactions"] >= max(med_inter * 2, 1)]
    lows = [r for r in rows if r["interactions"] < med_inter * 0.5]

    # 结构性指标
    total_collects = sum(r["collects"] for r in rows)
    total_inter = sum(r["interactions"] for r in rows)
    total_comments = sum(r["comments"] for r in rows)
    collect_ratio = rate(total_collects, total_inter)
    comment_ratio = rate(total_comments, total_inter)

    return {
        "count": n,
        "med_views": med_views,
        "med_inter": med_inter,
        "hits": hits,
        "lows": lows,
        "collect_ratio": collect_ratio,
        "comment_ratio": comment_ratio,
        "total_inter": total_inter,
    }


def diagnose(a):
    """把指标翻译成可执行结论。"""
    out = []

    # 收藏率高 → 信息密度够，适合做系列
    if a["collect_ratio"] >= 35:
        out.append(("✅ 收藏率健康（{:.0f}%）".format(a["collect_ratio"]),
                    "读者认为值得回看。说明信息密度够。这类内容适合做系列，"
                    "可以用 xhs-viral-remix 拆自己的爆款，复制结构。"))
    elif a["collect_ratio"] < 15:
        out.append(("⚠️ 收藏率偏低（{:.0f}%）".format(a["collect_ratio"]),
                    "读者看完了但没存。通常是信息太泛、缺具体数字和步骤。"
                    "下一篇试试每段至少塞一个具体信息（价格/参数/时间/步骤数）。"))

    # 评论率低 → 缺互动设计
    if a["comment_ratio"] < 3:
        out.append(("⚠️ 评论率偏低（{:.0f}%）".format(a["comment_ratio"]),
                    "结尾没有留钩子。加一个具体问题，或者故意留一个可争论的点。"
                    "注意：不要用「评论区告诉我」这种空话，要给具体的二选一。"))

    # 方差大 → 定位不稳
    if a["count"] >= 5:
        if a["med_inter"] > 0 and a["hits"]:
            ratio = max(r["interactions"] for r in a["hits"]) / a["med_inter"]
            if ratio >= 5:
                out.append((f"⚡ 数据断层（最高是中位数的 {ratio:.1f} 倍）",
                            "说明你的账号标签还不稳，平台在试探性推流。"
                            "**接下来 5-7 篇应统一风格和主题**，别换赛道，"
                            "让算法确认你是谁。这是最容易被忽视的关键期。"))

    # 低效笔记多 → 需要止损
    if len(a["lows"]) >= max(3, a["count"] // 2):
        out.append((f"🔻 {len(a['lows'])} 篇明显低于中位数",
                    "接近一半内容拖后腿。别删（删了影响账号权重判断），"
                    "但要复盘它们的共同点：是选题问题、标题问题，还是封面问题？"))

    if not out:
        out.append(("📊 数据没有明显异常", "继续按当前节奏输出，攒够 15 篇再看趋势。"))
    return out


def main():
    ap = argparse.ArgumentParser(description="小红书账号体检（本地，不联网）")
    ap.add_argument("--file", help="CSV 或 JSON 文件")
    ap.add_argument("--sample", action="store_true", help="输出输入格式样例")
    args = ap.parse_args()

    if args.sample:
        print("CSV 格式样例（第一行是表头）：\n")
        print("date,title,likes,collects,comments,views")
        print("2026-11-01,我的第一篇笔记,120,45,8,3000")
        print("2026-11-05,被 AI 惊到了,850,320,96,12000")
        print("\nJSON 格式样例：")
        print(json.dumps({"notes": [
            {"date": "2026-11-01", "title": "我的第一篇笔记",
             "likes": 120, "collects": 45, "comments": 8, "views": 3000}
        ]}, ensure_ascii=False, indent=2))
        return 0

    if not args.file:
        ap.error("需要 --file 或 --sample")

    ext = os.path.splitext(args.file)[1].lower()
    rows = load_json(args.file) if ext == ".json" else load_csv(args.file)

    if not rows:
        print("没读到数据。用 --sample 看格式。", file=sys.stderr)
        return 1

    a = analyze(rows)
    print(f"账号体检报告 — {a['count']} 篇笔记\n")
    print(f"  中位互动量  {a['med_inter']:.0f}")
    print(f"  中位浏览量  {a['med_views']:.0f}")
    print(f"  收藏占比    {a['collect_ratio']:.0f}%")
    print(f"  评论占比    {a['comment_ratio']:.0f}%")
    print()

    print("诊断：")
    for title, detail in diagnose(a):
        print(f"\n{title}")
        print(f"  {detail}")

    if a["hits"]:
        print("\n表现最好的笔记：")
        for r in sorted(a["hits"], key=lambda x: -x["interactions"])[:3]:
            print(f"  · {r['title']}  （互动 {r['interactions']}）")
        print("\n  → 用 xhs-viral-remix 拆这几篇，它们是已验证的骨架。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
