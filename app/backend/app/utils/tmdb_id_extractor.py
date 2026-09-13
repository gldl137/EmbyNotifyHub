"""
TMDB ID 提取器 - 从多种来源获取 TMDB ID

优先级：
1. 路径提取（最可靠）
2. ProviderIds 字段
3. Emby API 查询（备选）
"""
import re
from typing import Dict, Any, Optional
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_tmdb_id_from_path(path: str) -> Optional[str]:
    """
    从文件路径中提取 TMDB ID
    
    支持格式：
    - {tmdbid=272432}
    - [tmdbid-272432]
    - tmdbid_272432
    - TmdbId=272432
    - tmdb-272432
    - (tmdbid 272432)
    
    Args:
        path: 文件路径
        
    Returns:
        TMDB ID 字符串，未找到返回 None
    """
    if not path:
        return None
    
    # 匹配各种格式的 tmdbid
    patterns = [
        r'[tT][mM][dD][bB][iI][dD][\s]*[=\-_][\s]*(\d+)',  # tmdbid=272432, tmdbid-272432, tmdbid_272432
        r'[tT][mM][dD][bB][\s]*[=\-][\s]*(\d+)',           # tmdb-272432, tmdb=272432
        r'\{[\s]*[tT][mM][dD][bB][iI][dD][\s]*(\d+)[\s]*\}',  # {tmdbid 272432}
        r'\[[\s]*[tT][mM][dD][bB][iI][dD][\s]*(\d+)[\s]*\]',  # [tmdbid 272432]
    ]
    
    for pattern in patterns:
        match = re.search(pattern, path)
        if match:
            tmdb_id = match.group(1)
            logger.debug(f"从路径提取到 TMDB ID: {tmdb_id}")
            return tmdb_id
    
    return None


def extract_tmdb_id_from_provider_ids(item: Dict[str, Any]) -> Optional[str]:
    """
    从 ProviderIds 字段提取 TMDB ID
    
    Args:
        item: Emby Item 对象
        
    Returns:
        TMDB ID 字符串，未找到返回 None
    """
    provider_ids = item.get("ProviderIds", {})
    
    # 尝试各种可能的键名
    for key in ["Tmdb", "tmdb", "TMDb", "TmdbId", "tmdbId"]:
        if key in provider_ids and provider_ids[key]:
            return str(provider_ids[key])
    
    return None


def get_tmdb_id_from_emby_api(item_id: str, server_id: str = "", server_name: str = "") -> Optional[str]:
    """
    通过 Emby API 查询 TMDB ID
    支持多服务器配置，可根据 server_id 或 server_name 选择对应服务器

    Args:
        item_id: Emby 项目 ID
        server_id: 可选，指定 Emby ServerId
        server_name: 可选，指定 Emby 服务器名称

    Returns:
        TMDB ID 字符串，未找到返回 None
    """
    if not item_id:
        return None

    try:
        import requests

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
                        params = {"api_key": api_key, "fields": "ProviderIds"}
                        response = requests.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        data = response.json()

                        provider_ids = data.get("ProviderIds", {})
                        for key in ["Tmdb", "tmdb", "TMDb", "TmdbId", "tmdbId"]:
                            if key in provider_ids and provider_ids[key]:
                                tmdb_id = str(provider_ids[key])
                                logger.debug(f"从服务器 {matched_server.get('name')} API 获取到 TMDB ID: {tmdb_id}")
                                return tmdb_id
                        logger.debug(f"服务器 {matched_server.get('name')} 返回数据中未找到 TMDB ID")
                        return None
                    except Exception as e:
                        logger.warning(f"从服务器 {matched_server.get('name')} 查询 TMDB ID 失败: {e}")
                        return None
            else:
                logger.debug(f"ServerId {server_id} 未匹配到配置，尝试根据 server_name 匹配")

        # 如果提供了 server_name（或 server_id 没匹配到），根据名称匹配
        if server_name:
            server_name_lower = server_name.lower().strip()
            matched_server = None
            for server in servers:
                if not server.get("enabled", True):
                    continue
                config_name = server.get("name", "").lower().strip()
                if config_name == server_name_lower or server_name_lower in config_name or config_name in server_name_lower:
                    matched_server = server
                    break

            if matched_server:
                base_url = matched_server.get("base_url", "").rstrip("/")
                api_key = matched_server.get("api_key", "")
                if base_url and api_key:
                    try:
                        url = f"{base_url}/Items/{item_id}"
                        params = {"api_key": api_key, "fields": "ProviderIds"}
                        response = requests.get(url, params=params, timeout=10)
                        response.raise_for_status()
                        data = response.json()

                        provider_ids = data.get("ProviderIds", {})
                        for key in ["Tmdb", "tmdb", "TMDb", "TmdbId", "tmdbId"]:
                            if key in provider_ids and provider_ids[key]:
                                tmdb_id = str(provider_ids[key])
                                logger.debug(f"根据名称从服务器 {matched_server.get('name')} API 获取到 TMDB ID: {tmdb_id}")
                                return tmdb_id
                        logger.debug(f"服务器 {matched_server.get('name')} 返回数据中未找到 TMDB ID")
                        return None
                    except Exception as e:
                        logger.warning(f"从服务器 {matched_server.get('name')} 查询 TMDB ID 失败: {e}")
                        return None
            else:
                logger.warning(f"ServerName '{server_name}' 未匹配到任何服务器配置")

        # server_id 和 server_name 都没匹配到，记录警告
        if server_id or server_name:
            logger.warning(f"未找到匹配的服务器配置，跳过 TMDB ID 查询")
            logger.warning(f"请前往 Emby 服务器配置页面，点击'测试连接'按钮自动获取 ServerId")
            return None

        # 没有提供 server_id 和 server_name，遍历所有启用的服务器尝试获取
        for server in servers:
            if not server.get("enabled", True):
                continue
            base_url = server.get("base_url", "").rstrip("/")
            api_key = server.get("api_key", "")

            if not base_url or not api_key:
                continue

            try:
                url = f"{base_url}/Items/{item_id}"
                params = {"api_key": api_key, "fields": "ProviderIds"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                provider_ids = data.get("ProviderIds", {})
                for key in ["Tmdb", "tmdb", "TMDb", "TmdbId", "tmdbId"]:
                    if key in provider_ids and provider_ids[key]:
                        tmdb_id = str(provider_ids[key])
                        logger.debug(f"从服务器 {server.get('name')} API 获取到 TMDB ID: {tmdb_id}")
                        return tmdb_id

            except Exception as e:
                logger.debug(f"从服务器 {server.get('name')} 查询 TMDB ID 失败: {e}")
                continue

        # 兼容旧配置
        emby_config = config_manager.get("emby", {})
        base_url = emby_config.get("base_url", "").rstrip("/")
        api_key = emby_config.get("api_key", "")

        if base_url and api_key:
            try:
                url = f"{base_url}/Items/{item_id}"
                params = {"api_key": api_key, "fields": "ProviderIds"}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                provider_ids = data.get("ProviderIds", {})
                for key in ["Tmdb", "tmdb", "TMDb", "TmdbId", "tmdbId"]:
                    if key in provider_ids and provider_ids[key]:
                        tmdb_id = str(provider_ids[key])
                        logger.debug(f"从 Emby API 获取到 TMDB ID: {tmdb_id}")
                        return tmdb_id
            except Exception as e:
                logger.error(f"通过 Emby API 获取 TMDB ID 失败: {e}")

        logger.debug(f"未找到 TMDB ID: item_id={item_id}")
        return None

    except Exception as e:
        logger.error(f"通过 Emby API 获取 TMDB ID 失败: {e}")
        return None


def extract_tmdb_id(item: Dict[str, Any], server_id: str = "", server_name: str = "") -> Optional[str]:
    """
    从 Item 中提取 TMDB ID（按优先级）
    支持多服务器配置

    优先级：
    1. 路径提取（最可靠）
    2. ProviderIds 字段
    3. Emby API 查询（备选）

    Args:
        item: Emby Item 对象
        server_id: 可选，指定 Emby ServerId
        server_name: 可选，指定 Emby 服务器名称

    Returns:
        TMDB ID 字符串，未找到返回 None
    """
    # 音乐类型不需要查询 TMDB ID (Audio: 歌曲, MusicAlbum: 专辑, MusicArtist: 艺术家)
    item_type = item.get("Type", "")
    if item_type in ("Audio", "MusicAlbum", "MusicArtist"):
        logger.debug(f"音乐类型跳过 TMDB ID 查询: {item.get('Name', '')} (Type: {item_type})")
        return None

    # 方法1：优先从路径提取（最可靠）
    path = item.get("Path", "")
    if path:
        tmdb_id = extract_tmdb_id_from_path(path)
        if tmdb_id:
            logger.debug(f"从路径提取 TMDB ID: {tmdb_id}")
            return tmdb_id

    # 方法2：从 ProviderIds 提取
    tmdb_id = extract_tmdb_id_from_provider_ids(item)
    if tmdb_id:
        logger.debug(f"从 ProviderIds 提取 TMDB ID: {tmdb_id}")
        return tmdb_id

    # 方法3：通过 Emby API 查询（备选）
    item_id = item.get("Id", "")
    if item_id:
        logger.debug(f"尝试通过 Emby API 查询 TMDB ID: item_id={item_id}, server_id={server_id}, server_name={server_name}")
        tmdb_id = get_tmdb_id_from_emby_api(item_id, server_id=server_id, server_name=server_name)
        if tmdb_id:
            return tmdb_id
    
    logger.warning(f"无法提取 TMDB ID: item_id={item.get('Id')}, path={path}")
    return None
