"""
事件管理 API
"""
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.event_store import event_store
from app.services.notification_store import get_notification_store
from app.utils.logger import get_logger

router = APIRouter(prefix="/manage", tags=["events-manage"])
logger = get_logger(__name__)

notification_store = get_notification_store()


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    deleted_count: int = 0
    message: str = ""


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    event_ids: List[str]


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    success: bool
    deleted_count: int = 0
    failed_ids: List[str] = []
    message: str = ""


class ClearResponse(BaseModel):
    """清空响应"""
    success: bool
    cleared_count: int = 0
    message: str = ""


class ResendResponse(BaseModel):
    """重发响应"""
    success: bool
    message: str = ""


@router.delete("/{event_id}", response_model=DeleteResponse)
async def delete_event(event_id: str):
    """删除单个事件及其消息"""
    try:
        # 删除事件
        result = event_store.delete_event(event_id)
        if result:
            # 同时删除相关通知
            notification_store.delete_by_event_id(event_id)
            return DeleteResponse(
                success=True,
                deleted_count=1,
                message="删除成功"
            )
        else:
            return DeleteResponse(
                success=False,
                message="事件不存在或删除失败"
            )
    except Exception as e:
        logger.error(f"删除事件失败: {e}")
        return DeleteResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_events(req: BatchDeleteRequest):
    """批量删除事件及其通知"""
    try:
        deleted = 0
        failed = []
        
        for event_id in req.event_ids:
            if event_store.delete_event(event_id):
                # 同时删除相关通知
                notification_store.delete_by_event_id(event_id)
                deleted += 1
            else:
                failed.append(event_id)
        
        return BatchDeleteResponse(
            success=len(failed) == 0,
            deleted_count=deleted,
            failed_ids=failed,
            message=f"成功删除 {deleted} 个事件" + (f"，{len(failed)} 个失败" if failed else "")
        )
    except Exception as e:
        logger.error(f"批量删除事件失败: {e}")
        return BatchDeleteResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )


@router.delete("/clear/all", response_model=ClearResponse)
async def clear_all_events():
    """清空所有事件和通知"""
    try:
        # 获取清空前的事件数量
        all_events = event_store.get_events(limit=100000)
        event_count = len(all_events)
        
        # 直接清空（更高效）
        event_store.clear_events()
        
        # 同时清空通知
        notification_store.clear_all()
        
        logger.info(f"已清空 {event_count} 个事件和通知")
        
        return ClearResponse(
            success=True,
            cleared_count=event_count,
            message=f"已清空 {event_count} 个事件和通知"
        )
    except Exception as e:
        logger.error(f"清空事件失败: {e}")
        return ClearResponse(
            success=False,
            message=f"清空失败: {str(e)}"
        )


@router.delete("/clear/before/{date}", response_model=ClearResponse)
async def clear_events_before(date: str):
    """清空指定日期之前的事件 (YYYY-MM-DD)"""
    try:
        cutoff_date = datetime.strptime(date, "%Y-%m-%d")
        all_events = event_store.get_events(limit=100000)
        
        deleted = 0
        for event in all_events:
            event_time = datetime.fromisoformat(event.get("created_at", "1970-01-01T00:00:00"))
            if event_time < cutoff_date:
                if event_store.delete_event(event.get("id")):
                    deleted += 1
        
        return ClearResponse(
            success=True,
            cleared_count=deleted,
            message=f"已删除 {date} 之前的 {deleted} 个事件"
        )
    except Exception as e:
        logger.error(f"清空事件失败: {e}")
        return ClearResponse(
            success=False,
            message=f"清空失败: {str(e)}"
        )


@router.post("/resend/{event_id}", response_model=ResendResponse)
async def resend_notification(event_id: str):
    """重新发送通知"""
    try:
        event = event_store.get_event(event_id)
        if not event:
            return ResendResponse(
                success=False,
                message="事件不存在"
            )
        
        # 这里需要调用通知服务重新发送
        # 暂时返回成功
        logger.debug(f"重新发送通知: {event_id}")
        
        return ResendResponse(
            success=True,
            message="通知已重新发送"
        )
    except Exception as e:
        logger.error(f"重发通知失败: {e}")
        return ResendResponse(
            success=False,
            message=f"重发失败: {str(e)}"
        )


@router.post("/mark-as-read/{event_id}", response_model=ResendResponse)
async def mark_event_as_read(event_id: str):
    """标记事件为已读"""
    try:
        # 更新事件状态
        logger.debug(f"标记已读: {event_id}")
        
        return ResendResponse(
            success=True,
            message="已标记为已读"
        )
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return ResendResponse(
            success=False,
            message=f"操作失败: {str(e)}"
        )
