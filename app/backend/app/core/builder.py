"""
消息构建模块 - 统一导出接口

新架构：使用 message_builder 替代旧的 client_templates 和 desktop_templates
所有消息构建都基于标准化的 event_record，在发送时渲染

数据流：
  events.json (标准化事件数据)
    ↓
  渲染函数（桌面端/企业微信等）
    ↓
  desktop.json / 发送
"""

# 从常量模块导入映射常量
from app.core.constants import (
    get_event_info,
    MEDIA_TYPE_MAP,
)

# 新消息构建模块（基于 event_record，发送时渲染）
from app.core.message_builder import (
    # 企业微信
    build_notification_message,
    build_wecom_news_message,
    # 桌面端
    render_desktop_message,
    # 工具函数
    get_message_article,
)

__all__ = [
    # 常量
    "get_event_info",
    "MEDIA_TYPE_MAP",
    # 企业微信
    "build_notification_message",
    "build_wecom_news_message",
    # 桌面端
    "render_desktop_message",
    # 工具函数
    "get_message_article",
]
