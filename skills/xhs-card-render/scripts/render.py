#!/usr/bin/env python3
"""
小红书 3:4 图文卡片渲染 — 纯 HTML/CSS，用浏览器截图。

依赖：playwright（首次要装 chromium）
    pip install playwright && playwright install chromium

用法:
    python3 render.py --spec cards.json --out ~/xhs/output
    python3 render.py --sample            # 看 spec 格式

设计原则：字体用系统字体，不下载外部字体（Muse 环境无外网字体也能跑）。
"""

import argparse
import json
import os
import sys

CARD_W, CARD_H = 1242, 1660  # 小红书 3:4

THEMES = {
    "editorial": {
        "bg": "#faf8f5", "fg": "#1a1a1a", "accent": "#c8553d",
        "serif": "'Songti SC','Noto Serif CJK SC',serif",
        "sans": "'PingFang SC','Noto Sans CJK SC',sans-serif",
    },
    "swiss": {
        "bg": "#ffffff", "fg": "#111111", "accent": "#0047ff",
        "serif": "'Helvetica Neue',Arial,sans-serif",
        "sans": "'Helvetica Neue',Arial,sans-serif",
    },
    "dark": {
        "bg": "#111418", "fg": "#f0f0f0", "accent": "#4ade80",
        "serif": "'PingFang SC','Noto Sans CJK SC',sans-serif",
        "sans": "'PingFang SC','Noto Sans CJK SC',sans-serif",
    },
}


def check_density(spec):
    """卡片内容太少会显得空，太多会溢出。给出提示。"""
    warns = []
    for i, c in enumerate(spec.get("cards", []), 1):
        body = c.get("body", "")
        title = c.get("title", "")
        total = len(body) + len(title)
        kind = c.get("type", "content")
        if kind == "cover":
            continue
        if total < 30:
            warns.append(f"第 {i} 张内容偏少（{total} 字），"
                         f"渲染后会大面积留白，建议补到 40-120 字")
        elif total > 200:
            warns.append(f"第 {i} 张内容偏多（{total} 字），"
                         f"可能溢出，建议拆成两张")
    return warns


def build_html(spec):
    theme_name = spec.get("theme", "editorial")
    t = THEMES.get(theme_name, THEMES["editorial"])
    cards = spec.get("cards", [])
    if not cards:
        raise ValueError("cards 为空")

    pages = []
    for i, c in enumerate(cards):
        kind = c.get("type", "content")
        title = c.get("title", "")
        body = c.get("body", "")
        kicker = c.get("kicker", "")
        num = c.get("number", "")

        if kind == "cover":
            inner = f"""
              <div class="kicker">{kicker}</div>
              <h1 class="cover-title">{title}</h1>
              <div class="cover-sub">{body}</div>
            """
            extra = "card cover"
        elif kind == "end":
            inner = f"""
              <div class="end-title">{title}</div>
              <div class="end-body">{body}</div>
            """
            extra = "card end"
        else:
            numhtml = f'<div class="num">{num or i:02d}</div>' if num != "off" else ""
            inner = f"""
              {numhtml}
              <h2 class="h2">{title}</h2>
              <div class="body">{body}</div>
            """
            extra = "card"

        pages.append(f'<section class="{extra}">{inner}</section>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#888; display:flex; flex-direction:column; align-items:center; gap:20px; padding:20px; }}
  .card {{
    width:{CARD_W}px; height:{CARD_H}px; background:{t['bg']}; color:{t['fg']};
    padding:110px 96px; display:flex; flex-direction:column; position:relative;
    font-family:{t['sans']}; overflow:hidden;
  }}
  .kicker {{
    font-size:30px; letter-spacing:.18em; text-transform:uppercase;
    color:{t['accent']}; margin-bottom:44px; font-weight:600;
  }}
  .num {{
    font-size:28px; color:{t['accent']}; font-weight:700;
    letter-spacing:.1em; margin-bottom:32px;
  }}
  .cover {{
    justify-content:center;
    background:linear-gradient(160deg, {t['bg']} 0%, {t['bg']} 60%, {t['accent']}11 100%);
  }}
  .cover-title {{
    font-family:{t['serif']}; font-size:96px; line-height:1.12;
    font-weight:700; letter-spacing:-.02em;
  }}  .cover-sub {{
    margin-top:40px; font-size:34px; line-height:1.55; opacity:.72;
  }}
  .h2 {{
    font-family:{t['serif']}; font-size:66px; line-height:1.2;
    font-weight:700; margin-bottom:40px; letter-spacing:-.01em;
  }}
  .body {{
    font-size:38px; line-height:1.72; white-space:pre-wrap;
  }}
  .end {{ justify-content:center; align-items:center; text-align:center; }}
  .end-title {{ font-family:{t['serif']}; font-size:80px; font-weight:700; }}
  .end-body {{ margin-top:36px; font-size:34px; opacity:.7; line-height:1.6; }}
  .bar {{ position:absolute; left:0; bottom:0; width:100%; height:10px; background:{t['accent']}; }}
</style></head>
<body>
{''.join(pages)}
<script>
  document.querySelectorAll('.card').forEach(c => {{
    const bar = document.createElement('div'); bar.className='bar'; c.appendChild(bar);
  }});
</script>
</body></html>"""


SAMPLE = {
    "theme": "editorial",
    "cards": [
        {"type": "cover", "kicker": "TOOL REVIEW", "title": "被 AI 惊到了",
         "body": "用了三个月，我改了三个习惯"},
        {"type": "content", "title": "第一个改动", "body": "以前写周报要一小时。\n现在先口述五分钟，让它整理成结构，再自己改二十秒。"},
        {"type": "content", "title": "第二个改动", "body": "查资料不再从头读。\n先问它这篇讲了什么，判断值不值得读，再决定。"},
        {"type": "end", "title": "就这样", "body": "有问题评论区聊"},
    ],
}


def render(spec_path, outdir):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("需要 playwright：pip install playwright && playwright install chromium",
              file=sys.stderr)
        return 1

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    os.makedirs(outdir, exist_ok=True)
    for w in check_density(spec):
        print(f"[提示] {w}")
    html = build_html(spec)
    html_path = os.path.join(outdir, "_preview.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    slug = spec.get("slug", "card")
    outputs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": CARD_W + 80, "height": CARD_H + 80})
        page.goto("file://" + os.path.abspath(html_path))
        page.wait_for_timeout(400)

        cards = page.query_selector_all(".card")
        for i, el in enumerate(cards, 1):
            path = os.path.join(outdir, f"{slug}-{i:02d}.png")
            el.screenshot(path=path)
            outputs.append(path)
        browser.close()

    print(f"渲染完成，共 {len(outputs)} 张：")
    for p_ in outputs:
        print(f"  {p_}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="小红书 3:4 图文卡片渲染")
    ap.add_argument("--spec", help="JSON 规格文件")
    ap.add_argument("--out", default=os.path.expanduser("~/xhs/output"))
    ap.add_argument("--sample", action="store_true", help="输出示例 spec")
    ap.add_argument("--write-sample", help="把示例 spec 写到指定路径")
    args = ap.parse_args()

    if args.sample or args.write_sample:
        s = json.dumps(SAMPLE, ensure_ascii=False, indent=2)
        if args.write_sample:
            with open(args.write_sample, "w", encoding="utf-8") as f:
                f.write(s)
            print(f"示例 spec 已写到 {args.write_sample}")
        else:
            print(s)
        return 0

    if not args.spec:
        ap.error("需要 --spec 或 --sample")
    return render(args.spec, os.path.expanduser(args.out))


if __name__ == "__main__":
    sys.exit(main())
