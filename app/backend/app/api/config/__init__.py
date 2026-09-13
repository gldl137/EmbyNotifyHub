"""
配置 API 模块
聚合所有配置相关的子路由
"""
from fastapi import APIRouter
from app.api.config import emby, tmdb, notify, system, aggregation

router = APIRouter(prefix="/api/config", tags=["config"])

# 包含各子路由
router.include_router(emby.router)
router.include_router(tmdb.router)
router.include_router(notify.router)
router.include_router(system.router)
router.include_router(aggregation.router)

__all__ = ["router"]
