"""
Emby 服务器配置 API - 支持多服务器管理
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

router = APIRouter(prefix="/emby", tags=["config-emby"])
logger = get_logger(__name__)


class EmbyServerConfig(BaseModel):
    """Emby 服务器配置模型"""
    id: Optional[str] = Field(None, description="服务器ID，新增时自动生成")
    name: str = Field(..., description="服务器名称")
    base_url: str = Field(..., description="Emby 服务器地址（内网）")
    external_url: str = Field("", description="外网访问地址（用于封面图片）")
    api_key: str = Field(..., description="API Key")
    enabled: bool = Field(True, description="是否启用")
    server_id: str = Field("", description="Emby ServerId (自动获取，用于多服务器识别)")


class EmbyServerResponse(BaseModel):
    """Emby 服务器响应"""
    success: bool
    data: Optional[Dict] = None
    message: str = ""


class EmbyServerListResponse(BaseModel):
    """Emby 服务器列表响应"""
    success: bool
    data: List[Dict] = []
    message: str = ""


class ConnectionTestRequest(BaseModel):
    """连接测试请求"""
    base_url: str
    api_key: str
    server_config_id: Optional[str] = Field(None, description="服务器配置ID，用于更新现有配置")


class ConnectionTestResponse(BaseModel):
    """连接测试响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== 服务器管理 API ====================

@router.get("/servers", response_model=EmbyServerListResponse)
async def get_emby_servers():
    """获取所有 Emby 服务器配置"""
    try:
        servers = config_manager.get_emby_servers()
        return EmbyServerListResponse(
            success=True,
            data=servers,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取 Emby 服务器列表失败: {e}")
        return EmbyServerListResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("/servers", response_model=EmbyServerResponse)
async def add_emby_server(config: EmbyServerConfig):
    """添加 Emby 服务器配置"""
    try:
        server_config = config.model_dump()
        result = config_manager.add_emby_server(server_config)
        return EmbyServerResponse(
            success=True,
            data=result,
            message="添加成功"
        )
    except Exception as e:
        logger.error(f"添加 Emby 服务器失败: {e}")
        return EmbyServerResponse(
            success=False,
            message=f"添加失败: {str(e)}"
        )


@router.put("/servers/{server_id}", response_model=EmbyServerResponse)
async def update_emby_server(server_id: str, config: EmbyServerConfig):
    """更新 Emby 服务器配置"""
    try:
        updates = config.model_dump()
        updates['id'] = server_id
        result = config_manager.update_emby_server(server_id, updates)
        return EmbyServerResponse(
            success=True,
            data=result,
            message="更新成功"
        )
    except Exception as e:
        logger.error(f"更新 Emby 服务器失败: {e}")
        return EmbyServerResponse(
            success=False,
            message=f"更新失败: {str(e)}"
        )


@router.delete("/servers/{server_id}", response_model=EmbyServerResponse)
async def delete_emby_server(server_id: str):
    """删除 Emby 服务器配置"""
    try:
        config_manager.delete_emby_server(server_id)
        return EmbyServerResponse(
            success=True,
            message="删除成功"
        )
    except Exception as e:
        logger.error(f"删除 Emby 服务器失败: {e}")
        return EmbyServerResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )


@router.post("/servers/{server_id}/test", response_model=ConnectionTestResponse)
async def test_emby_server(server_id: str):
    """测试指定 Emby 服务器连接"""
    try:
        server = config_manager.get_emby_server(server_id)
        if not server:
            return ConnectionTestResponse(
                success=False,
                message="服务器配置不存在"
            )

        import requests
        response = requests.get(
            f"{server['base_url']}/emby/System/Info",
            headers={"X-Emby-Token": server['api_key']},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            emby_server_id = data.get("Id", "")

            # 自动更新服务器配置中的 ServerId
            if emby_server_id and not server.get("server_id"):
                config_manager.update_emby_server(server_id, {"server_id": emby_server_id})
                logger.debug(f"自动更新服务器 {server.get('name')} 的 ServerId: {emby_server_id}")

            return ConnectionTestResponse(
                success=True,
                message="连接成功",
                data={
                    "server_name": data.get("ServerName"),
                    "version": data.get("Version"),
                    "server_id": emby_server_id
                }
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message=f"连接失败: HTTP {response.status_code}"
            )
    except Exception as e:
        logger.error(f"测试 Emby 连接失败: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"连接失败: {str(e)}"
        )


# ==================== 兼容旧 API ====================

@router.post("/test", response_model=ConnectionTestResponse)
async def test_emby_connection(req: ConnectionTestRequest):
    """测试 Emby 连接（兼容旧接口）
    
    连接成功后会自动获取服务器名称和 ServerId
    如果提供了 server_config_id，会自动更新对应的服务器配置
    """
    try:
        import requests
        response = requests.get(
            f"{req.base_url}/emby/System/Info",
            headers={"X-Emby-Token": req.api_key},
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            server_name = data.get("ServerName", "")
            emby_server_id = data.get("Id", "")
            version = data.get("Version", "")
            
            result_data = {
                "server_name": server_name,
                "version": version,
                "server_id": emby_server_id
            }
            
            # 如果提供了服务器配置ID，自动更新服务器信息
            if req.server_config_id:
                try:
                    updates = {
                        "name": server_name,
                        "server_id": emby_server_id
                    }
                    config_manager.update_emby_server(req.server_config_id, updates)
                    logger.debug(f"自动更新服务器配置 {req.server_config_id}: 名称={server_name}, ServerId={emby_server_id}")
                    result_data["auto_updated"] = True
                except Exception as e:
                    logger.warning(f"自动更新服务器配置失败: {e}")
                    result_data["auto_updated"] = False
            
            return ConnectionTestResponse(
                success=True,
                message=f"连接成功 - {server_name}",
                data=result_data
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message=f"连接失败: HTTP {response.status_code}"
            )
    except Exception as e:
        logger.error(f"测试 Emby 连接失败: {e}")
        return ConnectionTestResponse(
            success=False,
            message=f"连接失败: {str(e)}"
        )
