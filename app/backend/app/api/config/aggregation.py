"""
聚合通知配置 API
用于配置入库通知的聚合时间（秒）
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

router = APIRouter(prefix="/aggregation", tags=["config-aggregation"])
logger = get_logger(__name__)


class AggregationConfig(BaseModel):
    """聚合通知配置模型"""
    delay_seconds: int = Field(15, description="单集事件聚合时间（秒）", ge=0, le=60)


class AggregationConfigResponse(BaseModel):
    """聚合配置响应"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


@router.get("", response_model=AggregationConfigResponse)
async def get_aggregation_config():
    """获取聚合通知配置"""
    try:
        config = config_manager.get("aggregation", {})
        
        # 确保返回完整结构
        if "delay_seconds" not in config:
            config["delay_seconds"] = 15
            
        return AggregationConfigResponse(
            success=True,
            data=config,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取聚合配置失败: {e}")
        return AggregationConfigResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("", response_model=AggregationConfigResponse)
async def update_aggregation_config(config: dict):
    """更新聚合通知配置"""
    try:
        logger.debug(f"收到聚合配置保存请求: {config}")
        
        # 获取现有配置
        current_config = config_manager.get("aggregation", {})
        
        # 更新聚合时间
        if "delay_seconds" in config:
            # 限制范围 0-60 秒
            delay = int(config["delay_seconds"])
            current_config["delay_seconds"] = max(0, min(60, delay))
        
        # 保存配置
        config_manager.update_config({"aggregation": current_config})
        
        logger.debug(f"聚合配置已保存: {current_config}")
        
        return AggregationConfigResponse(
            success=True,
            data=current_config,
            message="保存成功"
        )
    except Exception as e:
        logger.error(f"保存聚合配置失败: {e}")
        return AggregationConfigResponse(
            success=False,
            message=f"保存失败: {str(e)}"
        )
