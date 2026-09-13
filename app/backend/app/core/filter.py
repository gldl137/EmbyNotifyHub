"""
事件过滤模块 - 根据配置决定是否处理事件
"""
from app.utils.logger import get_logger

logger = get_logger(__name__)


def allow_event(event: str) -> bool:
    """
    判断事件是否被允许处理
    所有非空事件都允许处理
    """
    if not event:
        logger.debug("事件为空，跳过")
        return False
    
    # 允许所有事件类型
    return True
