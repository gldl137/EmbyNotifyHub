"""
通知模板模块
统一导出所有模板类
"""
from app.templates.base import NotificationTemplate
from app.templates.movie import MovieTemplate
from app.templates.registry import get_template

__all__ = [
    "NotificationTemplate",
    "MovieTemplate",
    "get_template",
]
