"""
事件 API 模块
聚合所有事件相关的子路由
"""
from fastapi import APIRouter
from app.api.events import query, manage, stream

router = APIRouter(prefix="/api/events", tags=["events"])

# 包含各子路由
router.include_router(query.router)
router.include_router(manage.router)
router.include_router(stream.router)

__all__ = ["router"]
