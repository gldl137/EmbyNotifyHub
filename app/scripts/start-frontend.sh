#!/usr/bin/env bash
# =============================================================================
# 启动前端开发服务器 (Vite, 端口 5173, 代理 /api /webhook /health -> python-cs:7000)
# 用法:
#   bash scripts/start-frontend.sh         # 前台运行, Ctrl+C 退出
#   bash scripts/start-frontend.sh -d      # 后台守护运行
# 环境变量: FRONTEND_PORT (默认 5173)
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

DAEMON=0
[ "${1:-}" = "-d" ] && DAEMON=1

if ! have_cmd node; then
  err "未找到 node，无法启动前端。"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  warn "前端未安装依赖，正在 npm install ..."
  (cd "$FRONTEND_DIR" && npm install)
fi

if [ "$DAEMON" -eq 1 ]; then
  mkdir -p "$APP_DIR/.run"
  cd "$FRONTEND_DIR"
  npm run dev -- --port "$FRONTEND_PORT" --host 0.0.0.0 >>"$APP_DIR/.run/frontend.log" 2>&1 &
  echo $! >"$APP_DIR/.run/frontend.pid"
  log "前端已在后台启动 (PID $(cat "$APP_DIR/.run/frontend.pid")) -> http://localhost:$FRONTEND_PORT"
  log "日志: $APP_DIR/.run/frontend.log | 停止: kill \$(cat $APP_DIR/.run/frontend.pid)"
else
  cd "$FRONTEND_DIR"
  log "启动前端 -> http://localhost:$FRONTEND_PORT (Ctrl+C 退出)"
  exec npm run dev -- --port "$FRONTEND_PORT" --host 0.0.0.0
fi
