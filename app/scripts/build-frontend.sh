#!/usr/bin/env bash
# =============================================================================
# 构建前端 -> 输出到 backend/static (dist)
# 用法: bash scripts/build-frontend.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

if ! have_cmd node; then
  err "未找到 node，无法构建前端。"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  warn "前端未安装依赖，正在 npm install ..."
  (cd "$FRONTEND_DIR" && npm install)
fi

log "构建前端 (npm run build -> backend/static) ..."
(cd "$FRONTEND_DIR" && npm run build)
log "前端构建完成 ✅ -> $BACKEND_DIR/static"
