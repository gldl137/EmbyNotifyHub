"""
Emby Webhook 接收处理
架构：Ingest → Process → Render → Send（四层解耦）

错误分类：
- 代码异常 → error log（logger.error）
- 业务失败 → status（状态记录）
"""
from fastapi import APIRouter, Request
from app.core.pipeline import process_webhook_pipeline
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhook/emby")
async def emby_webhook(req: Request):
    """
    接收 Emby Webhook 事件
    
    流程：
    1. Ingest - 解析 Webhook
    2. Process - 数据增强，构建 event_record
    3. Render - 渲染通知内容
    4. Send - 发送通知，记录业务状态
    """
    try:
        # 获取原始数据（JSON 格式）
        data = await req.json()
        
        # 记录原始事件
        event_type = data.get('Event', 'unknown')
        logger.info(f"[Webhook] 收到 Emby 事件: {event_type}")
        
        # 获取请求来源信息（用于匹配服务器配置）
        server_url = req.headers.get("X-Emby-Server", "")
        client_ip = req.client.host if req.client else ""
        
        # 将来源信息添加到数据中
        data["_webhook_source"] = {
            "server_url": server_url,
            "client_ip": client_ip,
            "headers": dict(req.headers)
        }
        
        # 调用管道处理
        result = await process_webhook_pipeline(data)
        
        return result

    except Exception as e:
        # Webhook 解析失败 → 代码异常 → 日志，不记录状态
        logger.error(f"[Webhook] 接收失败: {str(e)}")
        return {"ok": False, "error": str(e)}
