# EmbyNotifyHub

Emby 媒体事件通知中心：接收 Emby Webhook 事件，经 TMDB 增强媒体信息（海报 / 评分 / 简介）后，推送企业微信图文通知。

前后端一体化，单端口部署，自带 Web 管理界面。

## 功能特性

- **事件覆盖全**：约 60 种 Emby 事件，含媒体库入库、播放、用户、插件、计划任务、电视直播等 10 大类
- **多服务器**：可接入多个 Emby，通知可按服务器分别过滤
- **多渠道通知**：企业微信群机器人 / 企业微信应用，每个渠道可独立配置「允许的事件」与「允许的服务器」
- **TMDB 增强**：自动补齐海报、评分、简介，支持 HTTP 代理
- **通知聚合**：剧集按「剧名 + 季」聚合（如 `E05-E08`），音乐按批次聚合，避免刷屏
- **实时与历史**：SSE 实时事件流 + 事件 / 通知历史查询
- **持久化**：SQLite 存事件与通知，JSON 存配置（旧版 JSON 数据自动迁移）

技术栈：Python 3.12 · FastAPI · Vue 3 · SQLite · Docker

## 安装

### 方式一：Docker（推荐）

`docker-compose.yml`：

```yaml
services:
  embynotifyhub:
    build:
      context: ./app
      dockerfile: Dockerfile
    image: embynotifyhub:latest
    container_name: embynotifyhub
    ports:
      - "7000:7000"              # 改左侧端口，如 "8080:7000"
    volumes:
      - ./app/data:/app/data     # 数据目录（配置 / 数据库 / 日志）
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
```

访问 `http://<服务器IP>:7000`（数据保存在 `./app/data`）。

### 方式二：启动脚本（Linux / unraid）

```bash
cd app

bash scripts/build-frontend.sh     # 构建前端 → backend/static（首次或前端改动后执行）
bash scripts/start-backend.sh      # 启动后端 :7000，首次会自动安装 Python 依赖
bash scripts/start-backend.sh -d   # 后台运行
```

依赖安装到项目专属目录，不污染系统 Python；`DATA_DIR`、`BACKEND_PORT` 等可用环境变量覆盖。

### 方式三：本地开发

```bash
# 后端
cd app/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload

# 前端（:5173 热更新，代理 /api、/webhook、/health 到后端）
cd app/frontend
npm install
VITE_PROXY_TARGET=http://localhost:7000 npm run dev
```

前端改动后需重新构建 `npm run build`（输出到 `app/backend/static`），后端才会托管新页面。

## 配置

### 1. 接入 Emby Webhook

Emby 后台 → `Plugins → Webhook → Add Webhook`：

| 配置项 | 值 |
|--------|-----|
| URL | `http://<EmbyNotifyHub地址>:7000/webhook/emby` |
| Content-Type | `application/json` |
| 事件 | 建议全选，具体推送哪些由本项目的通知渠道过滤 |

### 2. 在 Web 界面完成其余配置

- **媒体设置 → Emby 服务器**：填地址与 API Key，点「测试」
- **媒体设置 → TMDB**：填 API Key（需要媒体增强时；访问不通可配代理）
- **媒体设置 → 通知**：添加企业微信群机器人或企业微信应用，点「测试」确认能收到消息
- **系统设置**：聚合延迟、调试日志

配置保存在 `data/config.json`，优先级高于环境变量（模板见 `app/backend/.env.example`）。

## 访问地址

| 地址 | 说明 |
|------|------|
| `http://<IP>:7000` | Web 管理界面 |
| `http://<IP>:7000/webhook/emby` | Emby 事件入口 |
| `http://<IP>:7000/health` | 健康检查 |
| `http://<IP>:7000/docs` | API 文档（Swagger UI） |

## 安全提示

- 项目**未内置登录鉴权**，请勿直接暴露公网；如需外网访问请置于反向代理后并自行加认证
- `data/config.json` 明文保存 Emby / TMDB / 企业微信密钥，已通过 `.gitignore` 排除，切勿提交到仓库

## License

[MIT](LICENSE)
