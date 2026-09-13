from typing import Dict, Any, Optional
import requests
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_emby_config():
    """获取 Emby 配置"""
    return config_manager.get("emby", {})


def _get_server_url(server: Dict[str, Any]) -> str:
    """
    获取服务器用于图片访问的 URL
    优先级：external_url（外网）> base_url（内网）
    """
    external_url = server.get("external_url", "").strip()
    base_url = server.get("base_url", "").strip()
    # 优先使用外网地址
    return external_url.rstrip("/") if external_url else base_url.rstrip("/")


def _find_server(server_id: str = "", server_name: str = "") -> Optional[Dict[str, Any]]:
    """
    根据 server_id 或 server_name 查找服务器配置
    """
    servers = config_manager.get_emby_servers()

    # 如果提供了 server_id，优先匹配
    if server_id:
        for server in servers:
            if server.get("server_id") == server_id and server.get("enabled", True):
                return server

    # 根据 server_name 匹配
    if server_name:
        server_name_lower = server_name.lower().strip()
        for server in servers:
            if not server.get("enabled", True):
                continue
            config_name = server.get("name", "").lower().strip()
            if config_name == server_name_lower or server_name_lower in config_name or config_name in server_name_lower:
                return server

    # 返回第一个启用的服务器
    for server in servers:
        if server.get("enabled", True):
            return server

    # 兼容旧配置
    emby_config = get_emby_config()
    if emby_config.get("base_url") and emby_config.get("api_key"):
        return {
            "base_url": emby_config.get("base_url", ""),
            "external_url": emby_config.get("external_url", ""),
            "api_key": emby_config.get("api_key", "")
        }

    return None


def get_emby_item_image(item_id: str, image_type: str = "Primary", server_id: str = "", server_name: str = "", check_exists: bool = False) -> Optional[str]:
    """
    获取 Emby 项目图片 URL
    支持多服务器配置，可根据 server_id 或 server_name 选择对应服务器

    Args:
        item_id: Emby 项目 ID
        image_type: 图片类型 (Primary, Backdrop, etc.)
        server_id: 可选，指定 Emby ServerId
        server_name: 可选，指定 Emby 服务器名称
        check_exists: 是否检查图片是否存在（默认 False）

    Returns:
        外网图片 URL（如果配置了 external_url），否则返回内网 URL
        如果 check_exists=True 且图片不存在，返回 None
        如果找不到服务器配置，返回 None
    """
    server = _find_server(server_id, server_name)

    if not server:
        logger.warning(f"无法找到匹配的服务器配置: server_id={server_id}, server_name={server_name}")
        return None

    base_url = _get_server_url(server)
    api_key = server.get("api_key", "")

    if not base_url or not api_key:
        logger.warning(f"服务器配置不完整: base_url={bool(base_url)}, api_key={bool(api_key)}")
        return None

    # 构造图片 URL
    url = f"{base_url}/Items/{item_id}/Images/{image_type}"
    full_url = f"{url}?api_key={api_key}"

    # 如果需要检查图片是否存在
    if check_exists:
        try:
            response = requests.head(url, params={"api_key": api_key}, timeout=5)
            if response.status_code != 200:
                logger.debug(f"Emby 图片不存在: {url} (status: {response.status_code})")
                return None
        except Exception as e:
            logger.debug(f"检查 Emby 图片存在性失败: {e}")
            return None

    return full_url


def get_emby_item_details(item_id: str, server_id: str = "") -> Optional[Dict[str, Any]]:
    """
    获取 Emby 项目详细信息
    支持多服务器配置，可根据 server_id 选择对应服务器

    Args:
        item_id: Emby 项目 ID
        server_id: 可选，指定 Emby ServerId
    """
    servers = config_manager.get_emby_servers()

    # 如果提供了 server_id，优先匹配对应的服务器
    if server_id:
        matched_server = None
        for server in servers:
            if server.get("server_id") == server_id and server.get("enabled", True):
                matched_server = server
                break

        if matched_server:
            base_url = matched_server.get("base_url", "").rstrip("/")
            api_key = matched_server.get("api_key", "")
            if base_url and api_key:
                try:
                    url = f"{base_url}/Items/{item_id}"
                    params = {"api_key": api_key}
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.warning(f"从服务器 {matched_server.get('name')} 获取详情失败: {e}")
            return None
        else:
            logger.debug(f"ServerId {server_id} 未匹配到配置，尝试遍历所有服务器")

    # 遍历所有启用的服务器尝试获取（用于没有 server_id 或匹配失败的情况）
    for server in servers:
        if not server.get("enabled", True):
            continue
        base_url = server.get("base_url", "").rstrip("/")
        api_key = server.get("api_key", "")

        if not base_url or not api_key:
            continue

        try:
            url = f"{base_url}/Items/{item_id}"
            params = {"api_key": api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.debug(f"从服务器 {server.get('name')} 获取详情失败: {e}")

    # 兼容旧配置
    emby_config = get_emby_config()
    base_url = emby_config.get("base_url", "")
    api_key = emby_config.get("api_key", "")

    if base_url and api_key:
        try:
            url = f"{base_url}/Items/{item_id}"
            params = {"api_key": api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取 Emby 详情失败: {e}")

    logger.warning(f"无法获取项目 {item_id} 的详情")
    return None
