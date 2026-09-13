import time
import threading
from typing import Any, Optional, Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SimpleCache:
    """
    简单的内存缓存实现
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        """
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None

            # 检查是否过期
            if item["expires"] > 0 and time.time() > item["expires"]:
                del self._cache[key]
                return None

            return item["value"]

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），0表示永不过期
        """
        with self._lock:
            expires = time.time() + ttl if ttl > 0 else 0
            self._cache[key] = {
                "value": value,
                "expires": expires,
            }
            logger.debug(f"缓存已设置: {key}")


# 全局缓存实例
cache = SimpleCache()
