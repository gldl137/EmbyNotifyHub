#!/bin/bash
#clearLog=true
#noParity=true
#argumentDescription=请输入要构建推送的版本号
#argumentDefault=1.0.1

# ====================== 配置部分 ======================
# 以下配置均支持环境变量覆盖, 避免把个人信息硬编码进仓库
HUB_USER="${DOCKERHUB_USER:-your-dockerhub-username}"   # DockerHub 用户名 (需先 docker login)
APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"  # 项目根目录(含 Dockerfile), 默认取脚本所在目录
IMAGE_NAME="${IMAGE_NAME:-embynotifyhub}"
VERSION="${1:-1.0.0}"                            # 版本号: 脚本参数优先, 缺省用默认

# ====================== 校验 ======================
echo "[$(date +"%Y-%m-%d %H:%M:%S")] === 构建推送开始: 版本 $VERSION ==="
echo "[$(date +"%Y-%m-%d %H:%M:%S")] 项目目录: $APP_DIR"

if [ ! -d "$APP_DIR" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [ERROR] 项目目录不存在: $APP_DIR，退出"
    exit 1
fi
if [ ! -f "$APP_DIR/Dockerfile" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [ERROR] $APP_DIR/Dockerfile 不存在，退出"
    exit 1
fi

# 检查是否已登录 DockerHub
if [ ! -f "/root/.docker/config.json" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [ERROR] 尚未登录 DockerHub，请先运行 docker_login 脚本，退出"
    exit 1
fi

# 检查前端产物
if [ ! -f "$APP_DIR/backend/static/index.html" ]; then
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] [WARN] 前端产物 backend/static/index.html 不存在，镜像将不含前端页面"
fi

# ====================== 执行 ======================
cd "$APP_DIR" || { echo "[ERROR] 无法进入 $APP_DIR"; exit 1; }

echo "[$(date +"%Y-%m-%d %H:%M:%S")] 【1】docker build -> $HUB_USER/$IMAGE_NAME:$VERSION"
docker build -t "$HUB_USER/$IMAGE_NAME:$VERSION" . || { echo "[ERROR] 构建失败"; exit 1; }

echo "[$(date +"%Y-%m-%d %H:%M:%S")] 【2】docker push -> $HUB_USER/$IMAGE_NAME:$VERSION"
docker push "$HUB_USER/$IMAGE_NAME:$VERSION" || { echo "[ERROR] 推送失败"; exit 1; }

echo ""
echo "[$(date +"%Y-%m-%d %H:%M:%S")] ✅ 完成: $HUB_USER/$IMAGE_NAME:$VERSION"
docker images "$HUB_USER/$IMAGE_NAME"
