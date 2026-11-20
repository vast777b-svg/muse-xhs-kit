---
name: xhs-card-render
description: 小红书 3:4 图文卡片渲染。当用户要把文案变成小红书图文组图、做封面、做多页轮播图、或要一张可以直接发的竖版图时使用。用本地 HTML+Playwright 截图，不调用任何生图 API，不联网，完全可控。
---

# 图文卡片渲染

把文字排成 1242×1660（小红书 3:4）的图。**纯本地渲染**，不用生图模型，所以文字绝不会糊、绝不会错字。

## 依赖检查

```bash
python3 -c "import playwright" || pip install playwright && playwright install chromium
```

Muse 上第一次跑要下载 chromium（约 150MB），之后就快了。

## 三步

### 1. 写 spec

```bash
python3 ~/.claude/skills/xhs-card-render/scripts/render.py --write-sample ~/xhs/output/spec.json
```

spec 长这样：

```json
{
  "theme": "editorial",
  "slug": "ai-habits",
  "cards": [
    {"type": "cover", "kicker": "TOOL REVIEW",
     "title": "被 AI 惊到了", "body": "用了三个月，我改了三个习惯"},
    {"type": "content", "title": "第一个改动",
     "body": "以前写周报要一小时。\n现在先口述五分钟，让它整理成结构。"},
    {"type": "end", "title": "就这样", "body": "有问题评论区聊"}
  ]
}
```

三种卡片类型：

| type | 用途 | 排版 |
|---|---|---|
| `cover` | 首图 | 大标题居中偏下，带 kicker |
| `content` | 内页 | 序号 + 标题 + 正文，左上对齐 |
| `end` | 尾页 | 居中，字少 |

`number: "off"` 可以关掉内页序号。

### 2. 渲染

```bash
python3 ~/.claude/skills/xhs-card-render/scripts/render.py \
  --spec ~/xhs/output/spec.json --out ~/xhs/output
```

输出 `slug-01.png` 到 `slug-NN.png`，尺寸 1242×1660。

### 3. 看一眼

渲染完**必须打开图看**。脚本会做密度检查，但排版问题只有眼睛能看出来。

## 三种主题

| 主题 | 视觉 | 适合 |
|---|---|---|
| `editorial` | 米白底 + 衬线标题 + 砖红烧线 | 叙事、生活方式、读书 |
| `swiss` | 纯白底 + 无衬线 + 电光蓝 | 产品、数据、方法论 |
| `dark` | 深色底 + 浅字 + 荧光绿 | 科技、AI、夜间场景 |

`swiss` 在中文下会回退到系统无衬线，视觉比 `editorial` 硬，适合干货类。

## 内容密度

脚本会提示两种情况：

- **少于 30 字**：渲染后大面积留白，补到 40-120 字
- **多于 200 字**：可能溢出，拆成两张

留白不是坏事，但**每张卡只讲一件事**才是关键。宁可多一页，不要一页塞满。

## 排版硬规则

- 标题 ≤ 16 字（超过会换行到 3 行以上，难看）
- 正文每段 ≤ 40 字
- 一张卡只放一个观点
- 首图必须能独立看懂（很多人只看首图）

## 边界

- **字体用系统字体**。Muse 环境可能没有设计字体，所以不下载外部字体，保证一定能跑。
- **不做图片合成**。这是纯文字排版工具，要放照片需要另做。
- **渲染完必须人眼看**。密度检查只能发现字数问题，发现不了溢出和错位。
- 生成的图在 `~/xhs/output/`，发布前仍要过 `xhs-compliance-check` 检查文案部分。
