---
name: xhs-knowledge-base
description: 小红书本地知识库。当用户要记住爆款拆解、沉淀账号人设、管理选题池、记录复盘、或问"我之前分析过什么""我的定位是什么"时使用。全部存在本地 Markdown，纯离线，不上传到任何地方。
---

# 本地知识库

这是所有其他小红书 skill 的地基。**越用越值钱**，因为它在积累你自己的判断，而不是通用知识。

## 目录结构

```
~/xhs/
├── persona.md    账号人设（所有文案的语气基准）
├── patterns/     爆款拆解记录
├── topics/       选题池（带状态）
├── reviews/      复盘记录
├── drafts/       文案草稿
└── output/       渲染出的图
```

## 命令

```bash
KB=~/.claude/skills/xhs-knowledge-base/scripts/kb.py

python3 $KB init              # 初始化（生成 persona 模板）
python3 $KB persona           # 看人设
python3 $KB stats             # 看知识库概况
python3 $KB list pattern      # 列爆款库
python3 $KB search 关键词      # 全库搜索
echo "内容" | python3 $KB add pattern --title "标题" --tags "ai,工具"
```

类型可选：`pattern`（爆款拆解）、`topic`（选题）、`review`（复盘）、`draft`（草稿）。

## 什么时候必须用它

| 场景 | 动作 |
|---|---|
| 用户第一次用小红书相关 skill | 先 `init`，再让用户填 persona |
| 拆解完一篇爆款 | `add pattern`，把结论存下来 |
| 生成一批选题 | `add topic`，标 `待写` |
| 写完一篇稿 | `add draft` |
| 发布 7 天后 | `add review`，记数据表现 |
| 用户要写任何文案前 | 先 `persona`，按人设的语气写 |

## persona.md 是核心

这份文件决定所有输出的语气。**空白模板下不要开始写文案**，先问用户这几个问题：

1. 你是谁（一句话身份）
2. 写给谁（人群 + 处境 + 最烦什么）
3. 说话风格（语气 + 句子长度 + 用词禁忌）
4. 三个真实细节（具体经历、具体数字、具体场景）
5. 内容支柱（哪几个主题，各占多少）

填得越具体，生成的东西越像人写的。填"真诚、专业、有温度"这种词等于没填。

## 状态流转

选题和草稿用 `--tags` 标记状态，配合 `search` 追踪：

```
待写 → 已写 → 已发 → 已复盘
```

改状态目前靠重新 `add` 覆盖，或直接编辑 Markdown 文件。文件都在 `~/xhs/` 下，用户随时可以手改。

## 边界

- **纯本地**。所有内容只在 `~/xhs/`，不上传、不同步。
- **不自动清理**。用户不删就一直留着，所以别乱塞垃圾进去。
- **人可以随时手改**。Markdown 就是给人看的，别把它当数据库锁死。
