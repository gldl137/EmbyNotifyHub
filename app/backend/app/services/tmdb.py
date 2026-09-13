import requests
from typing import Dict, Any, Optional
from app.services.config_manager import config_manager
from app.services.cache import cache
from app.utils.logger import get_logger

logger = get_logger(__name__)

# TMDB 基础配置
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def get_tmdb(media_type: str, tmdb_id: str) -> Dict[str, Any]:
    """
    从 TMDB 获取媒体信息

    Args:
        media_type: 媒体类型 (Movie, Series, Episode)
        tmdb_id: TMDB ID

    Returns:
        {
            "overview": "简介",
            "poster": "海报URL",
            "backdrop": "背景图URL",
            "title": "标题",
            "original_title": "原标题"
        }
    """
    if not tmdb_id:
        return {}

    # 检查缓存
    cache_key = f"tmdb:{media_type}:{tmdb_id}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"TMDB 缓存命中: {cache_key}")
        return cached

    # 从 config_manager 获取 API Key
    tmdb_config = config_manager.get_tmdb_config()
    api_key = tmdb_config.api_key
    
    if not api_key:
        logger.warning("TMDB API Key 未配置")
        return {}

    # 确定 API 路径
    type_path = "tv" if media_type in ["Series", "Episode"] else "movie"

    try:
        url = f"{TMDB_BASE_URL}/{type_path}/{tmdb_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
        }

        # 准备请求参数
        request_kwargs = {
            "params": params,
            "timeout": 10
        }
        
        # 如果启用了代理，添加代理设置
        if tmdb_config.proxy_enabled and tmdb_config.proxy_url:
            request_kwargs["proxies"] = {
                "http": tmdb_config.proxy_url,
                "https": tmdb_config.proxy_url
            }
            logger.debug(f"使用代理访问 TMDB: {tmdb_config.proxy_url}")

        logger.debug(f"请求 TMDB: {url}")
        response = requests.get(url, **request_kwargs)
        response.raise_for_status()
        data = response.json()

        poster_path = data.get("poster_path")
        backdrop_path = data.get("backdrop_path")

        # 获取国家和语言信息
        # TMDB 返回的 origin_country 可能是列表，统一处理为字符串
        origin_country = ""
        country_data = data.get("origin_country", [])
        if isinstance(country_data, list):
            origin_country = country_data[0] if country_data else ""
        else:
            origin_country = country_data or ""
        
        result = {
            "overview": data.get("overview", ""),
            "poster": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None,
            "backdrop": f"{TMDB_IMAGE_BASE_URL}{backdrop_path}" if backdrop_path else None,
            "title": data.get("name") if type_path == "tv" else data.get("title"),
            "original_title": data.get("original_name") if type_path == "tv" else data.get("original_title"),
            "vote_average": data.get("vote_average"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "original_language": data.get("original_language", ""),
            "origin_country": origin_country,
        }

        # 写入缓存
        cache_config = config_manager.get_cache_config()
        cache.set(cache_key, result, ttl=cache_config.tmdb_ttl)
        logger.debug(f"TMDB 数据已缓存: {cache_key}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"TMDB API 请求失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"TMDB 处理异常: {e}")
        return {}


def enrich_media(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用 TMDB 数据增强媒体信息

    优先级:
    1. TMDB poster
    2. Emby 图片
    3. 默认封面
    
    注意：当 TMDB 请求失败时，保留原有数据，不用 None 覆盖
    """
    media = event.copy()

    tmdb_id = event.get("tmdb_id")
    media_type = event.get("type", "")
    
    # Audio 类型跳过 TMDB 查询
    if media_type == "Audio":
        return media

    if tmdb_id:
        tmdb_data = get_tmdb(media_type, tmdb_id)

        # 只有获取到有效数据时才更新，避免用 None 覆盖原有数据
        if tmdb_data:
            # 使用 TMDB 数据补充（仅当原数据为空时）
            if tmdb_data.get("overview") and not media.get("overview"):
                media["overview"] = tmdb_data["overview"]

            # 优先使用 TMDB 海报
            if tmdb_data.get("poster"):
                media["poster"] = tmdb_data["poster"]
            elif tmdb_data.get("backdrop"):
                media["poster"] = tmdb_data["backdrop"]

            # 保存其他 TMDB 数据（仅当不为 None 时）
            if tmdb_data.get("title"):
                media["tmdb_title"] = tmdb_data["title"]
            if tmdb_data.get("vote_average") is not None:
                media["tmdb_vote"] = tmdb_data["vote_average"]
            if tmdb_data.get("genres"):
                media["tmdb_genres"] = tmdb_data["genres"]

        # 剧集类型：获取总集数信息
        if media_type in ["Series", "Episode"] and tmdb_id:
            tv_info = get_tv_episode_count(tmdb_id)
            if tv_info:
                if tv_info.get("total_episodes"):
                    media["total_episodes"] = tv_info["total_episodes"]
                if tv_info.get("total_seasons"):
                    media["total_seasons"] = tv_info["total_seasons"]
                if tv_info.get("status"):
                    media["tv_status"] = tv_info["status"]

    return media


def get_tv_episode_count(tmdb_id: str) -> Dict[str, Any]:
    """
    从 TMDB 获取剧集的总集数信息

    Args:
        tmdb_id: TMDB ID

    Returns:
        {
            "total_episodes": 总集数,
            "total_seasons": 总季数,
            "status": 剧集状态 (Ended, Returning Series, etc.)
        }
    """
    if not tmdb_id:
        return {}

    # 检查缓存
    cache_key = f"tmdb:tv:episodes:{tmdb_id}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"TMDB 剧集信息缓存命中: {cache_key}")
        return cached

    # 从 config_manager 获取 API Key
    tmdb_config = config_manager.get_tmdb_config()
    api_key = tmdb_config.api_key

    if not api_key:
        logger.warning("TMDB API Key 未配置")
        return {}

    try:
        url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"
        params = {
            "api_key": api_key,
            "language": "zh-CN",
        }

        request_kwargs = {
            "params": params,
            "timeout": 10
        }

        if tmdb_config.proxy_enabled and tmdb_config.proxy_url:
            request_kwargs["proxies"] = {
                "http": tmdb_config.proxy_url,
                "https": tmdb_config.proxy_url
            }

        logger.debug(f"请求 TMDB TV 信息: {url}")
        response = requests.get(url, **request_kwargs)
        response.raise_for_status()
        data = response.json()

        result = {
            "total_episodes": data.get("number_of_episodes"),
            "total_seasons": data.get("number_of_seasons"),
            "status": data.get("status"),  # "Ended", "Returning Series", "Canceled" etc.
            "in_production": data.get("in_production", False)
        }

        # 写入缓存（缓存时间更长，因为剧集信息变化不频繁）
        cache_config = config_manager.get_cache_config()
        cache.set(cache_key, result, ttl=cache_config.tmdb_ttl * 2)
        logger.debug(f"TMDB 剧集信息已缓存: {cache_key}, 总集数: {result['total_episodes']}")

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"TMDB TV 信息请求失败: {e}")
        return {}
    except Exception as e:
        logger.error(f"TMDB TV 信息处理异常: {e}")
        return {}
