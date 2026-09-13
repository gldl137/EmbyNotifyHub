"""
服务模块
包含各种业务逻辑服务
"""

from app.services.cache import cache
from app.services.config_manager import config_manager, ConfigManager
from app.services.emby import get_emby_config, get_emby_item_image, get_emby_item_details
from app.services.event_store import event_store, EventStore, NotificationEvent
from app.services.tmdb import get_tmdb, enrich_media
from app.services.wecom import (
    WeComAPI,
    send_wecom_webhook,
    send_wecom_news_with_config,
)

__all__ = [
    # 缓存
    "cache",
    # 配置管理
    "config_manager",
    "ConfigManager",
    # Emby
    "get_emby_config",
    "get_emby_item_image",
    "get_emby_item_details",
    # 事件存储
    "event_store",
    "EventStore",
    "NotificationEvent",
    # TMDB
    "get_tmdb",
    "enrich_media",
    # 企业微信
    "WeComAPI",
    "send_wecom_webhook",
    "send_wecom_news_with_config",
]
