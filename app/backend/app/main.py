"""
EmbyNotifyHub - Emby 媒体事件通知中心
接收 Emby Webhook，通过企业微信发送图文通知
"""
import logging
import sys
from contextlib import asynccontextmanager

# 首先配置日志（必须在导入其他模块之前）
from app.utils.logger import ColoredFormatter

_logging_configured = False

def setup_logging():
    """配置统一日志格式（只执行一次）"""
    global _logging_configured
    if _logging_configured:
        return

    formatter = ColoredFormatter()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 配置根日志器（捕获所有未被捕获的日志）
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.WARNING)

    # 配置 Uvicorn 日志器（避免使用 Uvicorn 默认格式）
    uvicorn_loggers = ["uvicorn", "uvicorn.access", "uvicorn.error"]
    for name in uvicorn_loggers:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False
        # access 日志改为 WARNING，其他保持 INFO
        if "access" in name:
            logger.setLevel(logging.WARNING)
        else:
            logger.setLevel(logging.INFO)

    # 配置 WatchFiles 日志器
    watchfiles_logger = logging.getLogger("watchfiles")
    watchfiles_logger.handlers.clear()
    watchfiles_logger.addHandler(handler)
    watchfiles_logger.propagate = False
    watchfiles_logger.setLevel(logging.WARNING)

    # 将 warnings 重定向到 logging
    import warnings
    logging.captureWarnings(True)
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.handlers.clear()
    warnings_logger.addHandler(handler)
    warnings_logger.propagate = False

    _logging_configured = True

setup_logging()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# API 路由导入
from app.api.webhook import router as webhook_router
from app.api.config import router as config_router
from app.api.events import router as events_router

from app.utils.logger import get_logger
from app.config import config
import os

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging()

    # 根据配置设置日志级别
    from app.services.config_manager import config_manager
    from app.utils.logger import set_global_log_level
    if config_manager.is_debug_logging_enabled():
        set_global_log_level("DEBUG")
        logger.debug("调试日志已启用")
    else:
        set_global_log_level("INFO")

    logger.info("=" * 50)
    logger.info("EmbyNotifyHub 启动中...")
    logger.info(f"版本: 1.01")
    logger.info(f"监听端口: {config.PORT}")
    logger.info("=" * 50)
    yield
    # 关闭时执行
    logger.info("EmbyNotifyHub 正在关闭...")


app = FastAPI(
    title="EmbyNotifyHub",
    description="Emby 媒体事件通知中心 - 接收 Emby Webhook，通过企业微信发送图文通知",
    version="1.01",
    lifespan=lifespan
)

# CORS 中间件 - 生产环境应该限制来源
allow_origins = ["*"]
if os.getenv("ENV") == "production":
    # 生产环境可以限制特定域名
    allow_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API路由 - 必须在静态文件之前注册
# Webhook 路由（根路径，无前缀）
app.include_router(webhook_router)

# 配置路由 (/api/config/*)
app.include_router(config_router)

# 事件路由 (/api/events/*)
app.include_router(events_router)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "EmbyNotifyHub", "version": "1.01"}


# 获取静态文件目录路径
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# 如果静态目录存在，托管前端文件
if os.path.exists(static_dir):
    # 先挂载静态文件目录到 /assets 路径
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 根路径返回 index.html
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    # 其他路径也返回 index.html (支持前端路由)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # API 路径不处理
        if full_path.startswith(("webhook", "health", "api/", "stream", "docs", "openapi")):
            return JSONResponse({"detail": "Not Found"}, status_code=404)

        # 尝试返回具体文件
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # 否则返回 index.html 让前端路由处理
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "service": "EmbyNotifyHub",
            "status": "running",
            "webhook_endpoint": "/webhook/emby",
            "api_endpoints": {
                "config": "/api/config",
                "events": "/api/events",
                "health": "/health"
            },
            "message": "前端未构建，请运行 npm run build"
        }
