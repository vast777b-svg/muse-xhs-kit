#!/usr/bin/env bash
# Muse 小红书工具包 — 安装脚本
# 用法：bash install.sh            （只装不碰账号的部分）
#       bash install.sh --with-publish  （额外装自动发布，风险自负）

set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
fail()  { echo -e "${RED}[X]${NC} $*"; }

WITH_PUBLISH=0
[ "${1:-}" = "--with-publish" ] && WITH_PUBLISH=1

echo "================================================"
echo " Muse 小红书工具包 安装"
echo "================================================"
echo

# ---------- 0. 环境检查 ----------
echo ">>> 检查环境"
command -v python3 >/dev/null || { fail "缺少 python3"; exit 1; }
PY_VER=$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python $PY_VER"
command -v git >/dev/null || { fail "缺少 git"; exit 1; }
info "git $(git --version | awk '{print $3}')"
echo

# ---------- 1. 装 skill ----------
echo ">>> 安装 skills"
SKILL_DIR="${HOME}/.claude/skills"
mkdir -p "$SKILL_DIR"

SKILLS="xhs-compliance-check xhs-title-optimizer xhs-viral-remix
xhs-knowledge-base xhs-topic-ideas xhs-account-audit
xhs-card-render xhs-multi-platform xhs-daily-digest"

for s in $SKILLS; do
  if [ -d "$SKILL_DIR/$s" ]; then
    rm -rf "$SKILL_DIR/$s"
  fi
  cp -R "skills/$s" "$SKILL_DIR/$s"
  info "$s"
done

# 用脚本路径验证能跑
if python3 "$SKILL_DIR/xhs-compliance-check/scripts/check.py" "测试第一名的效果" >/dev/null 2>&1; then
  info "检测脚本自检通过"
else
  fail "检测脚本跑不起来，请检查 python3"
  exit 1
fi
echo

# ---------- 2. 建工作目录 + 知识库 ----------
echo ">>> 建立工作目录与知识库"
python3 "$SKILL_DIR/xhs-knowledge-base/scripts/kb.py" init
echo

# ---------- 3. 可选：自动发布 ----------
if [ "$WITH_PUBLISH" -eq 1 ]; then
  echo ">>> 安装自动发布组件（xiaohongshu-mcp）"
  warn "这一步会操作你的真实账号，风险见 RISK-LEVELS.md"
  echo

  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64)  BIN_ARCH="amd64" ;;
    aarch64) fail "xiaohongshu-mcp 官方不支持 Linux ARM64"; exit 1 ;;
    *)       fail "未知架构：$ARCH"; exit 1 ;;
  esac

  MCP_DIR="${HOME}/xhs/xiaohongshu-mcp"
  mkdir -p "$MCP_DIR"
  cd "$MCP_DIR"

  if [ ! -f xiaohongshu-mcp ]; then
    echo "下载二进制（需要能访问 github.com）..."
    curl -fL -o xiaohongshu-mcp \
      "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-linux-amd64" \
      || { fail "下载失败，检查网络或代理"; exit 1; }
    curl -fL -o xiaohongshu-login \
      "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-linux-amd64" \
      || { fail "下载失败"; exit 1; }
    chmod +x xiaohongshu-mcp xiaohongshu-login
    info "二进制已下载"
  else
    info "二进制已存在，跳过下载"
  fi

  echo
  warn "=========================================="
  warn " 以下步骤必须你本人手动完成"
  warn "=========================================="
  echo " 1. 运行登录程序，它会输出二维码："
  echo "      cd $MCP_DIR && ./xiaohongshu-login"
  echo " 2. 用手机小红书 App 扫码"
  echo " 3. 如有短信/人机验证，手动完成"
  echo " 4. 登录成功后再运行 MCP 服务："
  echo "      cd $MCP_DIR && ./xiaohongshu-mcp"
  echo
  warn " 首次运行会下载约 150MB 的无头浏览器，耐心等"
  warn " 机房 IP 异地登录大概率触发验证，这是正常的"
  echo
fi

# ---------- 4. 完成 ----------
echo "================================================"
info "安装完成"
echo "================================================"
echo
echo "装了这些："
echo "  skills （在 ${SKILL_DIR}）:"
echo "    xhs-compliance-check   违规词检测"
echo "    xhs-title-optimizer    标题优化"
echo "    xhs-viral-remix        爆款拆解与仿写"
echo "    xhs-knowledge-base     本地知识库"
echo "    xhs-topic-ideas        选题生成与评分"
echo "    xhs-account-audit      账号体检与复盘"
echo "    xhs-card-render        3:4 图文卡片渲染"
echo "    xhs-multi-platform     多平台改写"
echo "    xhs-daily-digest       每日简报与定时"
echo
echo "  知识库: ~/xhs/"
echo "  下一步: 填 ~/xhs/persona.md（人设决定所有文案语气）"
echo
echo "马上试一下："
echo "  python3 $SKILL_DIR/xhs-compliance-check/scripts/check.py \"这款面膜全网第一，加微信领取\""
echo "  python3 $SKILL_DIR/xhs-daily-digest/scripts/digest.py"
echo
warn "xhs-card-render 需要 playwright："
warn "  pip install playwright && playwright install chromium"
echo
if [ "$WITH_PUBLISH" -eq 0 ]; then
  warn "自动发布未安装。需要的话：bash install.sh --with-publish"
fi
