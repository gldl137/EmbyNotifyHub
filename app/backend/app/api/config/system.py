"""
系统配置 API
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.config_manager import config_manager
from app.services.event_store import event_store
from app.utils.logger import get_logger
import os
import time

router = APIRouter(prefix="/system", tags=["config-system"])
logger = get_logger(__name__)

# 启动时间
START_TIME = time.time()


class SystemConfig(BaseModel):
    """系统配置模型"""
    retention_days: int = Field(30, ge=1, le=365, description="事件保留天数")
    rate_limit: int = Field(5, ge=0, description="通知频率限制(秒)")
    debug_mode: bool = Field(False, description="调试模式")
    auto_start: bool = Field(True, description="开机自启")
    enable_cors: bool = Field(False, description="允许跨域")
    log_level: str = Field("info", description="日志级别")
    log_retention: int = Field(7, ge=1, le=90, description="日志保留天数")
    debug_logging: bool = Field(False, description="启用调试日志")


class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    success: bool
    data: dict
    message: str = ""


class ExportDataResponse(BaseModel):
    """导出数据响应"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


class AboutResponse(BaseModel):
    """关于页面响应"""
    success: bool
    data: dict
    message: str = ""


@router.get("", response_model=SystemConfigResponse)
async def get_system_config():
    """获取系统配置"""
    try:
        # 从 system 配置区域获取旧配置
        old_config = config_manager.get("system", {})
        # 从新的 system 模型获取配置
        system_config = config_manager.get_system_config()

        # 合并配置
        config = {
            "retention_days": old_config.get("retention_days", 30),
            "rate_limit": old_config.get("rate_limit", 5),
            "debug_mode": old_config.get("debug_mode", False),
            "auto_start": old_config.get("auto_start", True),
            "enable_cors": old_config.get("enable_cors", False),
            "log_level": old_config.get("log_level", "info"),
            "log_retention": old_config.get("log_retention", 7),
            "debug_logging": system_config.debug_logging
        }

        return SystemConfigResponse(
            success=True,
            data=config,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return SystemConfigResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("", response_model=SystemConfigResponse)
async def update_system_config(config: SystemConfig):
    """更新系统配置"""
    try:
        config_data = config.dict()

        # 保存旧配置字段到 system 区域
        old_config = {
            "retention_days": config_data.get("retention_days", 30),
            "rate_limit": config_data.get("rate_limit", 5),
            "debug_mode": config_data.get("debug_mode", False),
            "auto_start": config_data.get("auto_start", True),
            "enable_cors": config_data.get("enable_cors", False),
            "log_level": config_data.get("log_level", "info"),
            "log_retention": config_data.get("log_retention", 7)
        }
        config_manager.set("system", old_config)

        # 保存 debug_logging 到新的 system 模型
        config_manager.update_system_config({"debug_logging": config_data.get("debug_logging", False)})

        # 应用日志级别变更
        from app.utils.logger import set_global_log_level
        new_level = "DEBUG" if config_data.get("debug_logging") else "INFO"
        set_global_log_level(new_level)
        logger.debug(f"日志级别已切换为: {new_level}")

        return SystemConfigResponse(
            success=True,
            data=config_data,
            message="保存成功"
        )
    except Exception as e:
        logger.error(f"保存系统配置失败: {e}")
        return SystemConfigResponse(
            success=False,
            message=f"保存失败: {str(e)}"
        )


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息"""
    try:
        # 计算运行时间
        uptime_seconds = int(time.time() - START_TIME)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        # 获取事件统计
        all_events = event_store.get_events(limit=10000)
        
        # 获取最后通知时间
        last_event = event_store.get_last_event()
        last_notify = None
        if last_event:
            last_notify = last_event.get("notification_sent_at")
        
        data = {
            "version": "1.01",
            "uptime": f"{days} 天 {hours} 小时 {minutes} 分钟",
            "uptime_seconds": uptime_seconds,
            "event_count": len(all_events),
            "last_notify": last_notify,
            "data_dir": os.path.abspath("data")
        }
        
        return SystemInfoResponse(
            success=True,
            data=data,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return SystemInfoResponse(
            success=False,
            data={},
            message=f"获取失败: {str(e)}"
        )


@router.post("/export", response_model=ExportDataResponse)
async def export_data():
    """导出所有数据"""
    try:
        # 获取所有配置
        all_config = config_manager.config.dict()
        
        # 获取所有事件
        all_events = event_store.get_events(limit=10000)
        
        data = {
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": all_config,
            "events": all_events,
            "event_count": len(all_events)
        }
        
        return ExportDataResponse(
            success=True,
            data=data,
            message="导出成功"
        )
    except Exception as e:
        logger.error(f"导出数据失败: {e}")
        return ExportDataResponse(
            success=False,
            message=f"导出失败: {str(e)}"
        )


@router.post("/reset", response_model=SystemConfigResponse)
async def reset_all_config():
    """重置所有配置"""
    try:
        config_manager.reset()
        return SystemConfigResponse(
            success=True,
            message="配置已重置为默认值"
        )
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        return SystemConfigResponse(
            success=False,
            message=f"重置失败: {str(e)}"
        )


@router.get("/about", response_model=AboutResponse)
async def get_about_info():
    """获取关于页面信息"""
    try:
        # 项目信息
        about_data = {
            # 核心信息
            "project_name": "EmbyNotifyHub",
            "version": "1.01",
            "developer": "EmbyNotifyHub Contributors",
            "description": "Emby 媒体事件通知中心 - 接收 Emby Webhook，通过企业微信发送图文通知",
            
            # 详细信息
            "name": "EmbyNotifyHub",
            "repository": "",
            "license": "MIT",
            "homepage": "",
            
            # 功能特性
            "features": [
                "支持多种 Emby 事件（入库、播放、用户等）",
                "企业微信图文通知",
                "多服务器管理",
                "剧集聚合通知",
                "音乐入库通知",
                "TMDB 数据增强"
            ],
            
            # 技术栈
            "technologies": [
                "FastAPI",
                "Python 3.11+",
                "Pydantic",
                "企业微信 API"
            ],
            
            # 联系方式
            "contact": {
                "developer": "EmbyNotifyHub Contributors"
            }
        }
        
        return AboutResponse(
            success=True,
            data=about_data,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取关于信息失败: {e}")
        return AboutResponse(
            success=False,
            data={},
            message=f"获取失败: {str(e)}"
        )
