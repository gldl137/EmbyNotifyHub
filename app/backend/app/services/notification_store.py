"""
通知存储服务 - 每种通知类型独立文件存储

目录结构：
data/notifications/
  ├── desktop.json    # 桌面通知（前端展示格式）
  ├── wecom.json      # 企业微信通知（微信格式）
  └── ...             # 可扩展其他通知类型

每种文件保存对应通知渠道的完整格式数据
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.utils.logger import get_logger
from app.services.database import get_db, migrate_json_to_sqlite

logger = get_logger(__name__)

# 数据目录
if os.getenv("DATA_DIR"):
    DATA_DIR = Path(os.getenv("DATA_DIR"))
else:
    DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"

NOTIFICATIONS_DIR = DATA_DIR / "notifications"

# 通知类型配置文件映射（仅用于迁移定位旧 JSON）
NOTIFICATION_FILES = {
    "desktop": NOTIFICATIONS_DIR / "desktop.json",
    "wecom": NOTIFICATIONS_DIR / "wecom.json",
}


class NotificationStore:
    """
    通知存储管理器

    持久化于 database.sqlite 的 notifications 表（取代原 JSON 文件）
    """

    def __init__(self, max_notifications: int = 20):
        self._max_notifications = max_notifications  # 最大保留通知数，循环覆盖
        self._notifications: Dict[str, List[Dict[str, Any]]] = {}
        # 启动时将既有 notifications/*.json 迁移进 SQLite（幂等）
        try:
            migrate_json_to_sqlite()
        except Exception as e:
            logger.error(f"通知迁移失败: {e}")
        self._load_all()

    def _ensure_dir(self):
        """确保通知目录存在"""
        NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_all(self):
        """从 SQLite 加载所有通知到内存缓存"""
        for notify_type in NOTIFICATION_FILES.keys():
            self._notifications[notify_type] = get_db().get_notifications_by_type(notify_type)
    
    def add_notification(self, notify_type: str, event_id: str,
                        notification_data: Dict[str, Any],
                        meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        添加通知

        Args:
            notify_type: 通知类型 (desktop/wecom/...)
            event_id: 关联事件ID
            notification_data: 通知的完整格式数据（官方格式）
            meta: 扩展元信息（保存到 data 外部，在 type 之后）

        Returns:
            保存的通知记录
        """
        if notify_type not in NOTIFICATION_FILES:
            logger.warning(f"未知的通知类型: {notify_type}")
            return {}

        # 构建记录，meta 放在 type 之后
        record: Dict[str, Any] = {
            "id": f"{notify_type}_{event_id}",
            "event_id": event_id,
            "type": notify_type,
        }

        # 添加扩展元信息（如果有），放在 type 之后
        if meta:
            record.update(meta)

        # 添加 timestamp 和 data
        record["timestamp"] = datetime.now().isoformat()
        record["data"] = notification_data  # 官方格式数据

        if notify_type not in self._notifications:
            self._notifications[notify_type] = []

        # 检查是否已存在相同 event_id 的记录，避免重复
        existing_index = None
        for i, n in enumerate(self._notifications[notify_type]):
            if n.get("event_id") == event_id:
                existing_index = i
                break

        if existing_index is not None:
            # 更新现有记录（合并 meta 和 data）
            existing = self._notifications[notify_type][existing_index]
            if meta:
                # 合并 channels 和 channel_names
                if "channels" in meta and "channels" in existing:
                    existing["channels"] = list(set(existing["channels"] + meta["channels"]))
                    meta.pop("channels")
                if "channel_names" in meta and "channel_names" in existing:
                    existing["channel_names"].update(meta["channel_names"])
                    meta.pop("channel_names")
                existing.update(meta)
            existing["data"] = notification_data
            existing["timestamp"] = record["timestamp"]
            logger.debug(f"更新 {notify_type} 通知: {event_id}")
        else:
            # 添加新记录
            self._notifications[notify_type].append(record)
            logger.debug(f"添加 {notify_type} 通知: {event_id}")

        # 持久化到 SQLite
        self._persist_type(notify_type)
        return record

    def _persist_type(self, notify_type: str):
        """将某类型的内存通知全量写入 SQLite（含循环覆盖裁剪）"""
        notifications = self._notifications.get(notify_type, [])
        # 只保留最近的通知
        if len(notifications) > self._max_notifications:
            notifications = notifications[-self._max_notifications:]
            self._notifications[notify_type] = notifications
        db = get_db()
        for rec in notifications:
            record_id = rec.get("id")
            event_id = rec.get("event_id", "")
            timestamp = rec.get("timestamp", "")
            data = rec.get("data", {})
            meta = {
                k: v for k, v in rec.items()
                if k not in ("id", "event_id", "type", "timestamp", "data")
            }
            db.add_notification(record_id, event_id, notify_type, timestamp, meta, data)
        logger.debug(f"保存了 {len(notifications)} 条 {notify_type} 通知 (SQLite)")

    def get_notifications(self, notify_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指定类型的通知列表

        Args:
            notify_type: 通知类型
            limit: 返回数量

        Returns:
            通知列表
        """
        notifications = self._notifications.get(notify_type, [])
        return notifications[-limit:]

    def get_notification_by_event_id(self, event_id: str,
                                     notify_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        根据事件ID获取通知

        Args:
            event_id: 事件ID
            notify_type: 指定类型，None 则搜索所有类型

        Returns:
            通知记录或 None
        """
        return get_db().get_notification_by_event_id(event_id, notify_type)

    def get_all_by_event_id(self, event_id: str) -> Dict[str, Dict[str, Any]]:
        """
        获取一个事件的所有类型通知

        Returns:
            {type: record, ...}
        """
        return get_db().get_all_notifications_by_event_id(event_id)

    def delete_by_event_id(self, event_id: str):
        """根据事件ID删除所有相关通知"""
        get_db().delete_notifications_by_event_id(event_id)
        self._load_all()
        logger.debug(f"删除通知: {event_id}")

    def clear_all(self):
        """清空所有通知"""
        get_db().clear_notifications()
        for notify_type in list(self._notifications.keys()):
            self._notifications[notify_type] = []
        logger.info("清空所有通知")


# 全局实例
_notification_store: Optional[NotificationStore] = None


def get_notification_store() -> NotificationStore:
    """获取通知存储实例"""
    global _notification_store
    if _notification_store is None:
        _notification_store = NotificationStore()
    return _notification_store


# 便捷函数
def save_notification(notify_type: str, event_id: str, 
                     data: Dict[str, Any],
                     meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """保存通知"""
    return get_notification_store().add_notification(notify_type, event_id, data, meta)


def get_notifications(notify_type: str, limit: int = 100) -> List[Dict[str, Any]]:
    """获取指定类型通知"""
    return get_notification_store().get_notifications(notify_type, limit)


def get_notification_by_event_id(event_id: str, 
                                 notify_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """根据事件ID获取通知"""
    return get_notification_store().get_notification_by_event_id(event_id, notify_type)
