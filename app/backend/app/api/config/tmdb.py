"""
TMDB 配置 API
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

router = APIRouter(prefix="/tmdb", tags=["config-tmdb"])
logger = get_logger(__name__)


class TMDBConfig(BaseModel):
    """TMDB 配置模型"""
    api_key: str = Field("", description="TMDB API Key")
    proxy_enabled: bool = Field(False, description="是否启用代理")
    proxy_url: str = Field("", description="代理服务器地址")


class TMDBConfigResponse(BaseModel):
    """TMDB 配置响应"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


class TMDBTestResponse(BaseModel):
    """TMDB 测试响应"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.get("", response_model=TMDBConfigResponse)
async def get_tmdb_config():
    """获取 TMDB 配置"""
    try:
        config = config_manager.get("tmdb", {})
        return TMDBConfigResponse(
            success=True,
            data=config,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取 TMDB 配置失败: {e}")
        return TMDBConfigResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("", response_model=TMDBConfigResponse)
async def update_tmdb_config(config: dict):
    """更新 TMDB 配置"""
    try:
        # 获取现有配置
        current_config = config_manager.get("tmdb", {})
        
        # 合并更新
        if "api_key" in config:
            current_config["api_key"] = config["api_key"]
        if "proxy_enabled" in config:
            current_config["proxy_enabled"] = bool(config["proxy_enabled"])
        if "proxy_url" in config:
            current_config["proxy_url"] = config["proxy_url"]
        
        config_manager.set("tmdb", current_config)
        return TMDBConfigResponse(
            success=True,
            data=current_config,
            message="保存成功"
        )
    except Exception as e:
        logger.error(f"保存 TMDB 配置失败: {e}")
        return TMDBConfigResponse(
            success=False,
            message=f"保存失败: {str(e)}"
        )


@router.post("/test", response_model=TMDBTestResponse)
async def test_tmdb_connection():
    """测试 TMDB 连接（包含代理测试）"""
    try:
        import requests
        config = config_manager.get("tmdb", {})
        api_key = config.get("api_key", "")
        proxy_enabled = config.get("proxy_enabled", False)
        proxy_url = config.get("proxy_url", "")
        
        if not api_key:
            return TMDBTestResponse(
                success=False,
                message="请先配置 API Key"
            )
        
        # 准备请求参数
        request_kwargs = {
            "params": {"api_key": api_key},
            "timeout": 10.0
        }
        
        # 如果启用了代理，添加代理设置
        if proxy_enabled and proxy_url:
            request_kwargs["proxies"] = {
                "http": proxy_url,
                "https": proxy_url
            }
            logger.debug(f"测试 TMDB 使用代理: {proxy_url}")
        
        try:
            response = requests.get(
                "https://api.themoviedb.org/3/configuration",
                **request_kwargs
            )
            
            if response.status_code == 200:
                if proxy_enabled:
                    return TMDBTestResponse(
                        success=True,
                        message="代理和 TMDB 连接都正常"
                    )
                else:
                    return TMDBTestResponse(
                        success=True,
                        message="TMDB API 连接成功"
                    )
            elif response.status_code == 401:
                return TMDBTestResponse(
                    success=False,
                    message="API Key 无效"
                )
            else:
                return TMDBTestResponse(
                    success=False,
                    message=f"连接失败: HTTP {response.status_code}"
                )
                
        except requests.exceptions.ProxyError as e:
            logger.error(f"代理连接错误: {e}")
            return TMDBTestResponse(
                success=False,
                message="代理服务器连接失败，请检查代理地址是否正确"
            )
        except requests.exceptions.Timeout:
            return TMDBTestResponse(
                success=False,
                message="连接超时，请检查网络或代理设置"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {e}")
            if proxy_enabled:
                return TMDBTestResponse(
                    success=False,
                    message="无法连接到 TMDB，代理可能无法访问外部网络"
                )
            else:
                return TMDBTestResponse(
                    success=False,
                    message="无法连接到 TMDB，请检查网络"
                )
        except Exception as e:
            logger.error(f"连接异常: {e}")
            return TMDBTestResponse(
                success=False,
                message=f"连接失败: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"测试 TMDB 连接失败: {e}")
        return TMDBTestResponse(
            success=False,
            message=f"测试失败: {str(e)}"
        )


@router.delete("", response_model=TMDBConfigResponse)
async def delete_tmdb_config():
    """删除 TMDB 配置"""
    try:
        config_manager.set("tmdb", {})
        return TMDBConfigResponse(
            success=True,
            message="配置已删除"
        )
    except Exception as e:
        logger.error(f"删除 TMDB 配置失败: {e}")
        return TMDBConfigResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )
