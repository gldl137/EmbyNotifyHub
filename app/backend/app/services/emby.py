from typing import Dict, Any, Optional
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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

    # 如果需要检查图片是否存在（后端自检，走内网 base_url，避免 external_url 外网/HTTPS 证书问题误判）
    if check_exists:
        try:
            internal_base = server.get("base_url", "").rstrip("/")
            check_url = f"{internal_base}/Items/{item_id}/Images/{image_type}"
            response = requests.head(check_url, params={"api_key": api_key}, timeout=5, verify=False)
            if response.status_code != 200:
                logger.debug(f"Emby 图片不存在: {check_url} (status: {response.status_code})")
                return None
        except Exception as e:
            logger.debug(f"检查 Emby 图片存在性失败: {e}")
            return None

    return full_url


_user_id_cache: Dict[tuple, str] = {}


def _get_user_id(base_url: str, api_key: str) -> str:
    """获取服务器上任意一个有权限的用户 ID（优先管理员）。

    部分 Emby 实例的详情接口仅接受 /Users/{userId}/Items/{itemId}，
    直接访问 /Items/{itemId} 会返回 404，因此需要先取一个用户 ID。
    结果按 (base_url, api_key) 缓存，避免重复请求。
    """
    cache_key = (base_url, api_key)
    if cache_key in _user_id_cache:
        return _user_id_cache[cache_key]
    uid = ""
    try:
        r = requests.get(f"{base_url}/Users", params={"api_key": api_key}, timeout=8)
        if r.status_code == 200:
            users = r.json() or []
            if users:
                admins = [u for u in users if (u.get("Policy") or {}).get("IsAdministrator")]
                uid = (admins[0] if admins else users[0]).get("Id", "")
    except Exception as e:
        logger.debug(f"获取用户列表失败: {e}")
    _user_id_cache[cache_key] = uid
    return uid


def get_emby_item_details(item_id: str, server_id: str = "") -> Optional[Dict[str, Any]]:
    """
    获取 Emby 项目详细信息
    支持多服务器配置，可根据 server_id 选择对应服务器

    注意：详情接口优先使用 /Users/{userId}/Items/{itemId}（部分 Emby 实例
    对 /Items/{itemId} 直接返回 404），并保留 /Items/{itemId} 作为回退。

    Args:
        item_id: Emby 项目 ID
        server_id: 可选，指定 Emby ServerId
    """
    servers = config_manager.get_emby_servers()

    # 确定目标服务器（优先 server_id 精确匹配，否则第一个启用的，最后兼容旧配置）
    target = None
    if server_id:
        for server in servers:
            if server.get("server_id") == server_id and server.get("enabled", True):
                target = server
                break
    if not target:
        for server in servers:
            if server.get("enabled", True):
                target = server
                break
    if not target:
        emby_config = get_emby_config()
        if emby_config.get("base_url") and emby_config.get("api_key"):
            target = {
                "base_url": emby_config.get("base_url", ""),
                "api_key": emby_config.get("api_key", ""),
            }

    if not target:
        logger.warning(f"无法获取项目 {item_id} 的详情：无可用服务器配置")
        return None

    base_url = target.get("base_url", "").rstrip("/")
    api_key = target.get("api_key", "")
    if not base_url or not api_key:
        return None

    uid = _get_user_id(base_url, api_key)
    params = {
        "api_key": api_key,
        "Fields": "MediaSources,CommunityRating,Width,Height,DisplayTitle,VideoRange,MediaStreams",
    }

    # 优先 /Users/{uid}/Items/{id}，失败回退 /Items/{id}
    urls = []
    if uid:
        urls.append(f"{base_url}/Users/{uid}/Items/{item_id}")
    urls.append(f"{base_url}/Items/{item_id}")

    last_err = ""
    for url in urls:
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            last_err = f"HTTP {response.status_code}"
            logger.debug(f"从 {url} 获取详情失败: {response.status_code}")
        except Exception as e:
            last_err = str(e)
            logger.debug(f"从 {url} 获取详情异常: {e}")

    logger.warning(f"无法获取项目 {item_id} 的详情（{last_err}）")
    return None


def get_emby_season_episode_count(series_id: str, season_number: int,
                                 server_id: str = "", server_name: str = "") -> Optional[int]:
    """
    查询 Emby 媒体库中某剧「指定季」实际已有的集数（反映真实库状态，非本次入库）

    Args:
        series_id: 剧集（Series）的 Emby ItemId
        season_number: 目标季号
        server_id / server_name: 用于选择对应 Emby 服务器

    Returns:
        该季实际拥有的 Episode 数量；查询失败/无配置时返回 None
    """
    if not series_id or not season_number:
        return None

    server = _find_server(server_id, server_name)
    if not server:
        return None

    base_url = server.get("base_url", "").rstrip("/")  # 回查季集数必须走内网，避免 external_url(外网/HTTPS) 不可达或证书问题
    api_key = server.get("api_key", "")
    if not base_url or not api_key:
        return None

    uid = _get_user_id(base_url, api_key)
    params = {
        "api_key": api_key,
        "ParentId": series_id,
        "IncludeItemTypes": "Episode",
        "Recursive": True,
        "Fields": "ParentIndexNumber,SeasonIndex",
        "Limit": 1000,
    }

    urls = []
    if uid:
        urls.append(f"{base_url}/Users/{uid}/Items")
    urls.append(f"{base_url}/Items")

    last_err = ""
    for url in urls:
        try:
            response = requests.get(url, params=params, timeout=12)
            if response.status_code == 200:
                data = response.json() or {}
                items = data.get("Items", []) or []
                count = sum(
                    1 for it in items
                    if (it.get("ParentIndexNumber") or it.get("SeasonIndex") or 0) == season_number
                )
                logger.debug(f"Emby 剧集 {series_id} 第{season_number}季实际已有集数: {count}")
                return count
            last_err = f"HTTP {response.status_code}"
            logger.debug(f"从 {url} 查询季集数失败: {response.status_code}")
        except Exception as e:
            last_err = str(e)
            logger.debug(f"从 {url} 查询季集数异常: {e}")

    logger.warning(f"无法查询剧集 {series_id} 第{season_number}季集数（{last_err}）")
    return None
