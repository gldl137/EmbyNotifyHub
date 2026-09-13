# EmbyNotifyHub

> Emby 媒体事件通知中心 —— 接收 Emby Webhook 事件，经 TMDB 媒体信息增强后，通过企业微信推送图文通知。

EmbyNotifyHub 把 Emby 的各种事件（媒体入库、播放、用户、插件、计划任务……）统一接收、解析、过滤、聚合，
再用 TMDB 补充海报 / 评分 / 简介，最后推送到企业微信群机器人或企业微信应用。
前后端一体化，单端口部署，自带可视化管理界面。

> 灵感来自各类 Emby 通知工具，目标是「配置简单、事件覆盖全、通知好看」。

---

## 功能特性

- **事件覆盖全面**：支持约 60 种 Emby 事件，归类为服务器 / 媒体库 / 播放 / 用户 / 设备 / 计划任务 / 插件 / 电视直播 / 外部 / 第三方插件等 10 大类。
- **多服务器管理**：可同时接入多个 Emby 服务器，自动匹配 `ServerId`，通知可按服务器分别过滤。
- **多渠道通知**：
  - 企业微信**群机器人**（Webhook）
  - 多个企业微信**应用**（CorpID / AgentId / Secret），每个渠道可独立配置「允许的事件」与「允许的服务器」。
- **TMDB 媒体增强**：自动补齐海报、评分、简介、发行信息；支持通过 HTTP 代理访问 TMDB。
- **通知聚合**：剧集入库按「剧名 + 季」聚合（如 `E05-E08`），音乐按批次聚合，避免刷屏（聚合窗口可配置）。
- **可视化 Web 界面**：事件流水、通知记录、Emby / TMDB / 通知 / 聚合 / 系统设置全部图形化。
- **实时推送**：内置 SSE（Server-Sent Events）通道，事件产生后界面即时刷新。
- **单端口一体化**：前端构建产物由 FastAPI 直接托管，只需暴露一个端口。
- **数据持久化**：SQLite 存储事件与通知记录，配置使用 JSON；支持旧版 JSON 数据自动迁移。
- **日志友好**：彩色控制台日志 + 滚动文件日志，支持运行中切换 DEBUG 级别。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · Uvicorn · Pydantic · Requests |
| 前端 | Vue 3 · Vue Router · Axios · Vite |
| 存储 | SQLite（事件 / 通知）+ JSON（配置） |
| 外部集成 | Emby API · TMDB API v3 · 企业微信（群机器人 + 应用消息） |
| 部署 | Docker / docker-compose（单端口 7000）或启动脚本 |

---

## 目录结构

```text
EmbyNotifyHub/
├── docker-compose.yml            # 一键部署（context=./app，单端口 7000，数据挂载 ./app/data）
├── LICENSE
├── README.md
└── app/
    ├── Dockerfile                # 运行镜像（依赖构建期装进镜像）
    ├── .dockerignore
    ├── build_push.sh             # 构建并推送镜像到 DockerHub
    ├── backend/
    │   ├── requirements.txt
    │   ├── .env.example          # 环境变量模板（Web 界面配置优先）
    │   ├── static/               # 前端构建产物（由 scripts/build-frontend.sh 生成）
    │   └── app/
    │       ├── main.py           # FastAPI 入口：路由注册 + 静态资源托管 + SPA 兜底
    │       ├── config.py         # 环境变量配置
    │       ├── api/
    │       │   ├── webhook.py    # POST /webhook/emby —— Emby 事件入口
    │       │   ├── config/       # /api/config/*  配置类接口
    │       │   └── events/       # /api/events/*  事件查询、管理、SSE
    │       ├── core/
    │       │   ├── event_models.py    # 事件数据模型与解析
    │       │   ├── constants.py       # 事件分类 / 媒体类型 / 计划任务映射
    │       │   ├── filter.py          # 事件过滤
    │       │   ├── aggregator.py      # 剧集 / 音乐聚合
    │       │   ├── message_builder.py # 通知标题与正文渲染
    │       │   └── pipeline.py        # 核心管道：接收 → 处理 → 渲染 → 发送
    │       ├── services/
    │       │   ├── emby.py            # Emby 详情 / 封面
    │       │   ├── tmdb.py            # TMDB 查询与缓存
    │       │   ├── wecom.py           # 企业微信发送
    │       │   ├── config_manager.py  # config.json 读写
    │       │   ├── database.py        # SQLite 封装与数据迁移
    │       │   ├── event_store.py     # 事件存储
    │       │   └── notification_store.py
    │       ├── templates/             # 通知模板（电影 / 通用）
    │       └── utils/                 # 日志、TMDB ID 提取
    ├── frontend/                 # Vue 3 源码（构建输出到 backend/static）
    │   ├── src/
    │   │   ├── views/            # 事件、媒体设置、系统设置、关于
    │   │   ├── api/              # Axios 封装
    │   │   └── router/
    │   ├── vite.config.js
    │   └── package.json
    ├── scripts/                  # Linux / unraid 启动脚本
    │   ├── build-frontend.sh     # 构建前端 → backend/static
    │   ├── start-backend.sh      # 启动后端（-d 后台）
    │   ├── start-frontend.sh     # 启动前端开发服务器（-d 后台）
    │   └── common.sh
    └── data/                     # 运行时数据（已 .gitignore）
        ├── config.json           # 配置（含密钥，勿提交）
        ├── database.sqlite       # 事件 / 通知数据库
        └── logs/                 # 运行日志
```

---

## 快速开始

### 方式一：Docker 部署（推荐）

#### 1）前置条件

| 项目 | 要求 |
|------|------|
| Docker Engine | 20.10+ |
| Docker Compose | **v2**（使用 `docker compose` 子命令，不是老的 `docker-compose`） |
| 磁盘空间 | 约 500 MB（基础镜像 + Python 依赖） |

安装 Docker（Linux 一键脚本，Debian / Ubuntu / CentOS / Fedora 通用）：

```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable --now docker

# 验证（两条都要能输出版本号）
docker --version
docker compose version
```

- **unraid**：系统自带 Docker，可在「Docker」页面操作，或 SSH 进终端执行本文命令（想用 compose 需装 Compose Manager 插件）。
- **Windows / macOS**：安装 Docker Desktop，确认已启用 Compose v2。
- **群晖 / 威联通**：用 Container Manager / Container Station，或 SSH 执行本文命令。

#### 2）获取代码

```bash
git clone https://github.com/gldl137/EmbyNotifyHub.git
cd EmbyNotifyHub
```

> 服务器无法直连 GitHub 时：可在本地下载 ZIP 上传解压，或用带代理的 git：
> `git -c http.proxy=http://<代理地址>:<端口> clone https://github.com/gldl137/EmbyNotifyHub.git`

#### 3）准备数据目录与权限（重要，别跳过）

```bash
mkdir -p ./app/data
sudo chown -R 1000:1000 ./app/data
```

容器内以非 root 用户 `appuser`（**uid 1000**）运行，`./app/data` 会挂载为容器内的 `/app/data`，
用于存放 `config.json`（配置）、`database.sqlite`（事件与通知）、`logs/`（日志）。
宿主机目录属主不是 1000 时，容器无法写库和写日志，表现为服务启动后 `/health` 异常或日志报 `Permission denied`。

#### 4）按需修改配置（可选）

仓库根目录的 `docker-compose.yml` 内容如下：

```yaml
services:
  embynotifyhub:
    build:
      context: ./app            # 构建上下文固定为 app/，不要改成根目录
      dockerfile: Dockerfile
    image: embynotifyhub:latest
    container_name: embynotifyhub
    ports:
      - "7000:7000"             # 左侧宿主机端口，右侧容器端口不可改
    volumes:
      - ./app/data:/app/data    # 数据持久化目录
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
```

| 想改什么 | 改哪一行 | 示例 |
|----------|----------|------|
| Web 访问端口 | `ports` 左侧 | `"8080:7000"` → 以后用 `http://IP:8080` 访问 |
| 数据存放位置 | `volumes` 左侧 | `/mnt/user/appdata/embynotifyhub:/app/data` |
| 时区 | `environment` | `TZ=Asia/Shanghai` |

#### 5）构建并启动

```bash
docker compose up -d --build
```

首次构建约 1~3 分钟：Python 依赖在**构建阶段**就装进镜像的 `/app/pip-packages`，
之后重启或重建容器都不会重复 `pip install`；前端产物已随仓库提供（`app/backend/static`），
**构建过程不需要 Node.js**。

#### 6）验证启动

```bash
docker compose ps                    # STATE 应为 Up (healthy)
docker compose logs -f --tail=50     # 跟随日志，Ctrl+C 退出
curl http://localhost:7000/health    # 期望 {"status":"healthy",...}
```

浏览器打开 `http://<服务器IP>:7000`，看到 Web 界面即部署成功。

#### 7）首次配置

1. 「媒体设置 → Webhook」：复制 Webhook 地址，填到 Emby 的 Webhook 插件（见下文）。
2. 「媒体设置 → Emby 服务器」：填地址与 API Key，点「测试」。
3. 「媒体设置 → TMDB」：填 API Key（需要媒体增强时；访问不通可在此配代理）。
4. 「媒体设置 → 通知」：添加企业微信群机器人 / 企业微信应用，点「测试」确认能收到消息。
5. 「系统设置」：按需调整聚合延迟与调试日志。

> 配置保存在 `./app/data/config.json`，重建容器不会丢失；后续调整规则无需改 `docker-compose.yml`。

#### 8）日常运维

| 操作 | 命令 |
|------|------|
| 查看状态 | `docker compose ps` |
| 查看日志 | `docker compose logs -f --tail=100` |
| 重启 | `docker compose restart` |
| 停止并删除容器（数据保留） | `docker compose down` |
| 升级到最新代码 | `git pull && docker compose up -d --build` |
| 进入容器排查 | `docker compose exec embynotifyhub bash` |
| 备份数据 | `tar czf embynotifyhub-backup-$(date +%F).tgz ./app/data` |
| 彻底卸载（含镜像） | `docker compose down --rmi all`，再按需删除 `./app/data` |

#### 9）不用 Compose 的等价命令

```bash
cd EmbyNotifyHub/app     # 必须在 app/ 目录构建：Dockerfile 内的 COPY backend/... 以 app/ 为上下文根
docker build -t embynotifyhub:latest .

mkdir -p data && sudo chown -R 1000:1000 data
docker run -d \
  --name embynotifyhub \
  -p 7000:7000 \
  -v "$(pwd)/data:/app/data" \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  embynotifyhub:latest
```

#### 10）Docker 常见问题

**Q：构建报 `COPY failed: file not found ... stat backend`？**
A：构建上下文错了。Dockerfile 在 `app/` 下，其 `COPY backend/...` 以 `app/` 为上下文根，
必须用仓库自带的 `docker-compose.yml`（`context: ./app`），或手动在 `app/` 目录里 `docker build`。

**Q：拉取 `python:3.12-slim-bookworm` 很慢或失败？**
A：给 Docker 配置镜像加速器（`/etc/docker/daemon.json` 的 `registry-mirrors`，填你所在网络可用的镜像站），
或在能联网的机器上 `docker pull` 后 `docker save` / `docker load` 导入。镜像内 apt 与 pip 已使用阿里云源。

**Q：容器 Up 但页面打不开？**
A：`docker compose logs --tail=100` 看报错；`docker compose ps` 确认端口映射；
确认仓库内 `app/backend/static/index.html` 存在（缺失通常是构建上下文不对导致前端产物没进镜像）。

**Q：日志报 `Permission denied: /app/data/...`？**
A：回到第 3 步执行 `sudo chown -R 1000:1000 ./app/data`。

**Q：改了 `app/frontend` 源码，Docker 部署没生效？**
A：镜像用的是仓库里的构建产物 `app/backend/static`。先本地构建
（`cd app/frontend && npm install && npm run build`），再 `docker compose up -d --build`。


### 方式二：启动脚本（Linux / unraid）

```bash
cd app

bash scripts/build-frontend.sh     # 首次：构建前端到 backend/static
bash scripts/start-backend.sh      # 启动后端（:7000），首次会自动安装 Python 依赖

# 后台运行
bash scripts/start-backend.sh -d
```

脚本会把 Python 依赖装到应用专属目录（`PIP_TARGET_DIR`），不污染系统 `site-packages`；
可用 `DATA_DIR`、`BACKEND_PORT`、`PIP_INDEX_URL` 等环境变量覆盖默认行为。

### 方式三：本地开发（前后端分离热更新）

```bash
# 1) 后端
cd app/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload

# 2) 前端
cd app/frontend
npm install
npm run dev          # 默认 http://localhost:5173
```

前端开发服务器会把 `/api`、`/webhook`、`/health` 代理到后端，代理目标默认
`http://python-cs:7000`（容器场景）。本地开发请显式指定：

```bash
# Windows PowerShell
$env:VITE_PROXY_TARGET="http://localhost:7000"; npm run dev
# Linux / macOS
VITE_PROXY_TARGET=http://localhost:7000 npm run dev
```

修改前端代码后需要重新构建，产物才会更新到后端托管的静态目录：

```bash
cd app/frontend && npm run build      # 输出到 app/backend/static
```

---

## 访问地址

| 地址 | 说明 |
|------|------|
| `http://<host>:7000/` | Web 管理界面（生产：由后端托管） |
| `http://<host>:5173/` | Web 管理界面（开发：Vite） |
| `http://<host>:7000/docs` | 交互式 API 文档（Swagger UI） |
| `http://<host>:7000/health` | 健康检查 |
| `http://<host>:7000/webhook/emby` | Emby Webhook 接收地址 |

---

## 配置 Emby Webhook

在 Emby 后台 `Dashboard → Plugins → Webhook → Add Webhook`：

| 配置项 | 值 |
|--------|-----|
| URL | `http://<EmbyNotifyHub地址>:7000/webhook/emby` |
| Content-Type | `application/json` |
| 事件 | 按需勾选，如 `library.new`、`playback.start`、`playback.stop`、`user.authenticated` 等 |

> 建议把 Emby 通知插件里的事件「全选」，具体要推送哪些事件交给 EmbyNotifyHub 的
> 「通知渠道 → 允许的事件」来过滤，这样调整规则不用改 Emby 端配置。

Webhook 地址也可以直接在界面的「媒体设置 → Webhook」标签页里复制。

---

## 配置说明

配置有两层，**Web 界面保存的配置优先级更高**（持久化在 `data/config.json`）：

1. **Web 界面**（推荐）：媒体设置（Webhook / Emby 服务器 / TMDB / 通知渠道）、系统设置（聚合延迟 / 调试日志）。
2. **环境变量**：可参考 `app/backend/.env.example`，通过进程环境变量传入（Docker 用 `environment:` / `env_file:`，脚本运行前 `export`），仅作为默认值兜底。

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `HOST` | `0.0.0.0` | 后端监听地址 |
| `PORT` | `7000` | 后端端口 |
| `DATA_DIR` | `app/data` | 数据目录（配置 / 数据库 / 日志） |
| `ENV` | `development` | 设为 `production` 时启用 `ALLOWED_ORIGINS` 白名单 |
| `ALLOWED_ORIGINS` | `*` | CORS 白名单，逗号分隔 |
| `TMDB_API_KEY` | 空 | TMDB Key（建议在界面填写） |
| `WECOM_CORPID` / `WECOM_AGENTID` / `WECOM_SECRET` | 空 | 企业微信应用凭据 |
| `BACKEND_PORT` | `7000` | 启动脚本使用的后端端口 |
| `FRONTEND_PORT` | `5173` | 启动脚本使用的前端端口 |
| `PIP_TARGET_DIR` | 自动 | Python 依赖安装目录 |
| `VITE_PROXY_TARGET` | `http://python-cs:7000` | 开发模式下前端代理的后端地址 |

---

## 主要 API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/webhook/emby` | 接收 Emby 事件 |
| GET | `/health` | 健康检查 |
| GET/POST/PUT/DELETE | `/api/config/emby/servers[/{id}]` | Emby 服务器增删改查 |
| POST | `/api/config/emby/servers/{id}/test` | 测试 Emby 连接 |
| GET/POST/DELETE | `/api/config/tmdb` | TMDB 配置 |
| POST | `/api/config/tmdb/test` | 测试 TMDB / 代理 |
| GET/POST/DELETE | `/api/config/notify` | 群机器人通知配置 |
| GET/POST/PUT/DELETE | `/api/config/notify/custom[/{id}]` | 自定义通知渠道 |
| POST | `/api/config/notify/custom/{id}/test` | 测试指定渠道 |
| GET/POST | `/api/config/notify/events` | 查询 / 更新渠道事件过滤 |
| GET/POST | `/api/config/aggregation` | 聚合延迟 |
| GET/POST | `/api/config/system` | 系统配置 |
| GET | `/api/config/system/info` | 运行信息（版本 / 运行时长 / 事件数） |
| GET | `/api/config/system/about` | 项目信息 |
| GET | `/api/events/query/list` | 事件列表（分页） |
| GET | `/api/events/events/{id}` | 事件详情 |
| POST | `/api/events/manage/batch-delete` | 批量删除事件 |
| DELETE | `/api/events/manage/clear/all` | 清空事件 |
| GET | `/api/events/stream` | SSE 实时事件流 |

完整接口请访问 `/docs` 查看。

---

## 工作原理

```
Emby Webhook
   │  POST /webhook/emby
   ▼
[Ingest]  解析事件（event_models / constants，约 60 种事件）
   ▼
[Process] 过滤（渠道允许的事件 / 服务器）
          └─ 信息增强：Emby 封面与详情 + TMDB 海报 / 评分 / 简介
          └─ 入库（SQLite）并广播 SSE
   ▼
[Render]  渲染通知标题与正文（模板 + 事件分类），剧集/音乐可聚合
   ▼
[Send]    分发到各通知渠道（企业微信群机器人 / 企业微信应用）
```

---

## 常见问题

**Q：修改了前端代码，界面没变化？**
A：需要重新构建：`cd app/frontend && npm run build`（输出到 `app/backend/static`），然后刷新浏览器。

**Q：只想跑 API，不要 Web 界面？**
A：删除 `app/backend/static` 目录，根路径会返回接口说明 JSON。

**Q：数据存在哪？怎么备份？**
A：全部在 `app/data`：`config.json`（配置）、`database.sqlite`（事件与通知）、`logs/`。备份该目录即可。

**Q：端口冲突怎么办？**
A：Docker 改 `docker-compose.yml` 的端口映射；脚本用 `BACKEND_PORT=xxxx`；代码内默认值见 `app/backend/app/config.py`。

**Q：TMDB 访问不了？**
A：在「媒体设置 → TMDB」里开启代理并填写代理地址，保存后可点「测试连接」验证。

**Q：企业微信通知收不到？**
A：在通知渠道页点「测试」，分别检查：CorpID / AgentId / Secret 是否正确、应用的可见范围是否包含接收人、事件过滤与服务器过滤是否把该事件排除了。

---

## 安全提示

- 本项目**未内置登录鉴权**，Web 界面与 API 均可直接访问；Webhook 入口同样无签名校验。
- 请**不要直接暴露到公网**。如需外网访问，请置于反向代理之后，并自行添加认证（如 Basic Auth、OAuth）与 HTTPS。
- `data/config.json` 会明文保存 Emby API Key、TMDB Key、企业微信 Secret，请妥善保管，**切勿提交到 Git 仓库**（仓库已通过 `.gitignore` 排除 `app/data/`）。

---

## 参与贡献

欢迎提交 Issue 与 Pull Request。

```bash
# 开发流程建议
1. Fork 并创建分支：git checkout -b feature/xxx
2. 后端：python -m uvicorn app.main:app --reload
3. 前端：cd app/frontend && npm run dev
4. 提交：git commit -m "feat: xxx"
5. 发起 Pull Request
```

---

## License

[MIT](LICENSE)
