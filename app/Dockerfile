# ============================== EmbyNotifyHub 运行镜像 ==============================
# 注意：
#   - 前端编译产物已预构建到 backend/static，无需在镜像内编译前端。
#   - data 为运行时宿主机挂载目录，禁止 COPY 进镜像。
#   - 【后端 Python 依赖在构建时打包进镜像】，pip install 到应用专属目录
#     /app/pip-packages (PIP_TARGET_DIR)，不污染系统 site-packages。
#     构建一次依赖即在镜像内，之后重启/重建容器都不再重新 pip install。
# FROM python:3.12-slim-bookworm

FROM python:3.12-slim-bookworm

# 使用国内 apt 镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 使用国内 pip 镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 创建非 root 用户
RUN useradd -m -u 1000 appuser

WORKDIR /app

# 创建依赖目录 (构建时装依赖进去, 运行时由 appuser 读取)
RUN mkdir -p /app/pip-packages

# 复制依赖清单并【在构建时安装依赖进镜像】
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --target=/app/pip-packages -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

# 复制后端应用代码（含已预构建的前端静态文件 backend/static）
COPY backend /app/backend

# 镜像内启动脚本 (仅运行必需, 不含本地测试逻辑)
#   - 将构建时安装的依赖目录加入 PYTHONPATH
#   - 启动 uvicorn (端口/数据目录等由环境变量控制, 见 backend/app/config.py)
RUN printf '%s\n' \
    '#!/bin/bash' \
    'set -e' \
    'export PYTHONPATH=/app/pip-packages:${PYTHONPATH:-}' \
    'cd /app/backend' \
    'exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7000}"' \
    > /app/start.sh && chmod +x /app/start.sh

# 创建数据目录并设置权限（运行时挂载点，不随镜像打包）
#   /app/data 运行时数据 (挂载)
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data /app/pip-packages

# 环境变量
ENV DATA_DIR=/app/data

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 7000

# 健康检查 (依赖就绪、服务起来后才通)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7000/health || exit 1

# 启动：依赖已在镜像内 (/app/pip-packages)，直接设置 PYTHONPATH 跑 uvicorn
CMD ["bash", "/app/start.sh"]
