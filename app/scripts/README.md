# EmbyNotifyHub 运行脚本 (scripts/)

用于 unraid 环境（前端 Node + 后端 python:3.12-bookworm）启动本项目。脚本为 bash，请在 Linux/unraid shell 运行。

## 三个脚本

| 脚本 | 作用 |
|------|------|
| `build-frontend.sh` | 构建前端，输出到 `backend/static`（dist） |
| `start-backend.sh`  | 启动后端 Uvicorn（:7000），自动安装依赖，托管前端 + API |
| `start-frontend.sh` | 启动前端 Vite 开发服务器（:3000），自动 `npm install`，代理 `/api /webhook /health` 到 7000 |

## 依赖自动安装

- **前端**：`start-frontend.sh` 检测 `frontend/node_modules` 不存在时自动 `npm install`。
- **后端**：`start-backend.sh` 检测 `fastapi` 不可导入时自动安装到**应用专属目录**
  `PIP_TARGET_DIR`（不污染系统 site-packages）：
  - **本地测试**（项目不在 `/app`，如 `EmbyNotifyHub/app`）：`backend/pip-packages`（可见目录，不污染本机 Python）。
  - **构建镜像后运行**（项目在 `/app`）：`/app/pip-packages`。
  - 可用环境变量 `PIP_TARGET_DIR` 覆盖；设为 `""` 则退回 pip 默认系统路径。
  - 容器内可把 `/app/pip-packages` 映射到宿主机做依赖持久化（重启不重装）。

## 使用

```bash
cd /path/to/EmbyNotifyHub/app

# 生产模式 (单端口 7000) —— 依赖首次会自动安装
bash scripts/build-frontend.sh
bash scripts/start-backend.sh            # 前台; 加 -d 后台运行

# 或开发模式 (前端热更新, 访问 3000)
bash scripts/start-backend.sh -d        # 后端后台 (依赖自动装)
bash scripts/start-frontend.sh          # 前端前台 (依赖自动装)
```

## 环境变量

- `BACKEND_PORT` 默认 7000（后端）
- `FRONTEND_PORT` 默认 3000（前端）
- `DATA_DIR` 默认 `app/data`（配置/数据库，建议 unraid 映射到 appdata 盘）
- `PIP_TARGET_DIR` 本地默认 `backend/.pip`，容器内默认 `/app/pip-packages`（均可 `-v` 映射持久化）

## 构建 Docker 镜像（依赖不打包）

镜像基于 `python:3.12-bookworm`，**后端依赖在构建时就 `pip install` 打包进镜像**
（安装到应用专属目录 `/app/pip-packages`，不污染系统 site-packages）。构建一次后，
依赖永久在镜像内，之后**重启容器或删容器重建都不再重新 pip install**。
启动脚本 `start-backend.sh` 仍保留「检测→自动装」作为兜底（本地测试或镜像未含依赖时可用）。

```bash
# 镜像内目录:
#   /app/backend/     ← 后端代码
#   /app/scripts/     ← 启动脚本
#   /app/data         ← 运行时挂载的数据目录
#   /app/pip-packages ← 构建时已打包的依赖 (在镜像内, 不映射)

docker build -t embynotifyhub -f Dockerfile .
docker run -d -p 7000:7000 \
  -v /your/appdata/data:/app/data \
  embynotifyhub
```

> 注意：依赖随镜像走，升级 Python 大版本 (3.12→3.13) 或修改 `requirements.txt`
> 后必须重新 `docker build`。`/app/data` 仍建议映射到宿主机做数据持久化。

> 注意：`.dockerignore` 已忽略本地 `**/.pip/` 与 `.run/`，避免本地测试依赖目录被 COPY 进镜像。

## 访问地址

- 生产：http://localhost:7000 （前端由后端托管）
- 开发：http://localhost:3000 （API/Webhook 经 Vite 代理到 7000）
- Webhook：`/webhook/emby`　健康检查：`/health`　API 文档：`/docs`
