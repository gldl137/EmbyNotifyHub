"""
核心模块
包含事件解析、过滤、消息构建等核心功能
"""

# 导出常量
from app.core.constants import (
    # 分类系统
    EventCategory,
    CATEGORY_NAME_MAP,
    # 事件定义
    EVENT_MAP,
    # 动作解析
    resolve_action,
    get_event_info,
    get_events_by_category,
    get_all_categories,
    # 向后兼容的映射
    EVENT_EMOJI_MAP,
    EVENT_DESC_MAP,
    EVENT_CATEGORY_MAP,
    # 其他常量
    MEDIA_TYPE_MAP,
    DEFAULT_ALLOW_EVENTS,
    DEFAULT_ALLOW_MEDIA_TYPES,
    DEFAULT_ALLOW_EVENTS_BY_CATEGORY,
    SCHEDULED_TASK_NAME_MAP,
    SCHEDULED_TASK_DESC_MAP,
)

# 导出消息构建函数（新架构 - 发送时渲染）
from app.core.message_builder import (
    # 企业微信
    build_notification_message,
    build_wecom_news_message,
    # 工具函数
    get_message_article,
)

# 导出解析和过滤函数
from app.core.event_models import parse_emby_event
from app.core.filter import allow_event

__all__ = [
    # ===== 分类系统 =====
    "EventCategory",
    "CATEGORY_NAME_MAP",
    # ===== 事件定义 =====
    "EVENT_MAP",
    # ===== 动作解析 =====
    "resolve_action",
    "get_event_info",
    "get_events_by_category",
    "get_all_categories",
    # ===== 向后兼容 =====
    "EVENT_EMOJI_MAP",
    "EVENT_DESC_MAP",
    "EVENT_CATEGORY_MAP",
    # ===== 其他常量 =====
    "MEDIA_TYPE_MAP",
    "SCHEDULED_TASK_NAME_MAP",
    "SCHEDULED_TASK_DESC_MAP",
    "DEFAULT_ALLOW_EVENTS",
    "DEFAULT_ALLOW_MEDIA_TYPES",
    "DEFAULT_ALLOW_EVENTS_BY_CATEGORY",
    # ===== 消息构建（新架构 - 发送时渲染）=====
    "build_notification_message",
    "build_wecom_news_message",
    "get_message_article",
    # ===== 解析和过滤 =====
    "parse_emby_event",
    "allow_event",
]
