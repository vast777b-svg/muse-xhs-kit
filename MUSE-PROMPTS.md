# 直接转给 Muse 的安装指令

把下面**整段**复制粘贴到 Muse 对话框里发出去即可。Muse 可以联网、有 root，会自己装。

---

## 指令 A｜只装不碰账号的部分（推荐先这样）

```
帮我装一个小红书工作流工具包，包含三个 skill。按顺序做，每步做完告诉我结果。

1. 在 ~/.claude/skills/ 下创建这三个目录（如果目录不存在就先 mkdir -p）。

2. 写入以下文件：

文件 ~/.claude/skills/xhs-compliance-check/SKILL.md
---
name: xhs-compliance-check
description: 小红书文案发布前合规自检。检测站外导流、广告法极限词、医疗功效宣称、化妆品夸大、虚假紧迫、诱导互动、迷信用语等风险词，给出风险分级与替换建议。当用户要发小红书笔记、检查文案会不会被限流或封号、问"这段能不能发"时使用。纯本地运行，不联网。
---

# 小红书文案合规自检

纯本地运行，文案不出本机。

## 怎么跑

python3 <本skill目录>/scripts/check.py "文案"
python3 <本skill目录>/scripts/check.py --file draft.txt
echo "文案" | python3 <本skill目录>/scripts/check.py -

## 用法

1. 先看高危。有高危词就别发了，先改。
2. 替换建议不是唯一解，好的改法要结合语境重写整句。
3. 误报正常（"第一次用"里的"第一"）。判断标准是这个词有没有给产品背书或做绝对化承诺。
4. 改完再跑一遍，确认清零。

## 边界

- 词库会过时，只能兜底，替代不了人工通读。
- 通过检测不等于一定过审。图片违规、资质问题不在范围内。

3. 写入检测脚本到 ~/.claude/skills/xhs-compliance-check/scripts/ 下：
   - check.py（我会在下面给出完整代码）
   - words.json（我会在下面给出完整内容）

4. 写入 ~/.claude/skills/xhs-title-optimizer/SKILL.md
   （标题优化 skill，我会在下面给出完整内容）

5. 写入 ~/.claude/skills/xhs-viral-remix/SKILL.md
   （爆款拆解 skill，我会在下面给出完整内容）

6. 建工作目录：mkdir -p ~/xhs/{drafts,patterns,output}

7. 自检：运行
   python3 ~/.claude/skills/xhs-compliance-check/scripts/check.py "这款面膜全网第一，加微信领取"
   应该输出 2 个高危命中（「第一」「微信」）。把实际输出贴给我看。

全程不需要 API Key，不需要联网。
```

⚠️ 上面这段是**框架**。完整的 check.py 和 words.json 有 300 多行，直接粘贴会很长。**更省事的做法是用下面的指令 B。**

---

## 指令 B｜让 Muse 自己从 GitHub 拉（最省事，推荐）

```
帮我装一套小红书 skill。从我的 GitHub 仓库拉，装完自检。

1. 克隆：
   git clone https://github.com/vast777b-svg/muse-xhs-kit.git ~/muse-xhs-kit

2. 进目录跑安装脚本：
   cd ~/muse-xhs-kit && bash install.sh

3. 装完把输出的最后 20 行贴给我。

4. 然后跑一次自检，把结果贴给我：
   python3 ~/.claude/skills/xhs-compliance-check/scripts/check.py "这款面膜全网第一，加微信领取"

这个工具包纯本地，不需要 API Key，不碰我的小红书账号。
```

---

## 指令 C｜加上自动发布（风险自负）

⚠️ **只在你想让 Muse 真的发笔记时才用这个。** 装完仍要保留人工确认。

```
接着装自动发布组件。

1. 进工具包目录，带参数重装：
   cd ~/muse-xhs-kit && bash install.sh --with-publish

2. 装完先别登录。先确认这两件事并告诉我：
   a) 机器架构是 x86_64 还是 aarch64？（uname -m）
   b) 能不能访问 github.com 下载二进制？

3. 如果架构是 aarch64，停下来告诉我，官方不支持 ARM64。

4. 如果是 x86_64，继续：
   cd ~/xhs/xiaohongshu-mcp
   运行 ./xiaohongshu-login

5. 它会输出一张二维码。请把二维码保存成图片，然后告诉我文件的绝对路径，
   我要用手机扫码。不要自己尝试登录，不要伪造任何登录状态。

6. 等我扫码成功、你说登录完成之后，再告诉我下一步怎么做。
   在我明确说"可以发布"之前，不要调用任何发布接口。
```

---

## 指令 D｜只问不动手

```
先别装。告诉我：
1. 你的系统架构（uname -m）、Python 版本、有没有安装 playwright/chromium
2. ~/.claude/skills/ 目录现在有哪些东西
3. 能不能访问 github.com 和 pypi.org

我看完再决定装什么。
```

---

## Muse 上会遇到的三个坑（提前告诉它）

把这段也发过去：

```
提醒你几个这台机器上的已知问题：

1. 这是机房 IP，小红书首次登录大概率判异地触发验证。
   这是正常的，不要反复重试超过 3 次，也不要换各种偏方绕过。

2. 机器无 GPU，也没有图形界面。
   扫码登录必须把二维码导出成图片，我手动扫。不要在无头环境里瞎试。

3. 小红书明确禁止自动化操作。高频发布和批量互动最容易触发风控。
   一天最多发 3 篇，不要定时在凌晨跑。
```
