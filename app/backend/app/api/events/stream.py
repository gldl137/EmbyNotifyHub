"""
事件实时推送 API (Server-Sent Events)
用于向前端推送新事件通知
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import List
import asyncio
import json
from app.utils.logger import get_logger

router = APIRouter(prefix="/stream", tags=["events-stream"])
logger = get_logger(__name__)


class EventStreamManager:
    """事件流管理器"""
    
    _instance = None
    _clients: List[asyncio.Queue] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_clients'):
            self._clients = []
    
    def add_client(self, queue: asyncio.Queue):
        """添加客户端连接"""
        self._clients.append(queue)
        logger.debug(f"SSE 客户端连接，当前连接数: {len(self._clients)}")
    
    def remove_client(self, queue: asyncio.Queue):
        """移除客户端连接"""
        if queue in self._clients:
            self._clients.remove(queue)
            logger.debug(f"SSE 客户端断开，当前连接数: {len(self._clients)}")
    
    async def broadcast(self, data: dict):
        """广播消息给所有客户端"""
        disconnected = []
        for client in self._clients:
            try:
                await client.put(data)
            except Exception:
                disconnected.append(client)
        
        # 清理断开的连接
        for client in disconnected:
            self.remove_client(client)


# 全局事件流管理器实例
stream_manager = EventStreamManager()


async def event_generator(queue: asyncio.Queue):
    """生成 SSE 事件流"""
    try:
        while True:
            # 等待新消息（带超时保持连接）
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30.0)
                # 格式化 SSE 消息
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                yield ": heartbeat\n\n"
    except asyncio.CancelledError:
        logger.debug("SSE 连接取消")
        raise
    except Exception as e:
        logger.error(f"SSE 生成器错误: {e}")
        raise


@router.get("", response_class=StreamingResponse)
async def event_stream():
    """
    事件实时推送端点 (SSE)
    前端使用 EventSource 连接此端点接收新事件通知
    """
    queue = asyncio.Queue()
    stream_manager.add_client(queue)
    
    try:
        return StreamingResponse(
            event_generator(queue),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    finally:
        # 确保连接断开时清理
        stream_manager.remove_client(queue)


async def notify_new_event(event_data: dict):
    """
    通知所有客户端有新事件
    在 webhook.py 中添加新事件后调用
    """
    await stream_manager.broadcast({
        "type": "new_event",
        "data": event_data
    })
    logger.debug(f"广播: {event_data.get('title', '')}")
