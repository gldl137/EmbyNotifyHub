"""
四层事件处理管道（简化架构）

架构：
1. Ingest（接收层）- 只解析 Webhook，不处理业务逻辑
2. Process（处理层）- 数据增强，构建标准化 event_record
3. Render（渲染层）- 生成通知内容（title/content 只计算一次）
4. Send（发送层）- 只发送，不存储状态

原则：
- 所有状态通过日志追踪
- 不维护状态存储（不重试、不去重）
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.event_models import parse_emby_event
from app.core.filter import allow_event
from app.core.aggregator import series_aggregator, music_aggregator
from app.services.tmdb import get_tmdb, enrich_media
from app.services.event_store import (
    event_store, NotificationEvent, CoreInfo, ContentInfo, MediaResources,
    ExternalIds, UserPlayback, MediaProfile, MusicInfo, RegionInfo, SourceInfo, SeriesInfo
)
from app.services.config_manager import config_manager

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Layer 1: Ingest（接收层）
# ============================================================================

async def ingest_webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    接收层：只解析 Webhook 数据，不处理业务逻辑
    
    Returns:
        {
            "ok": True/False,
            "event": parsed_event,  # 解析后的事件数据
            "error": error_message  # 仅在 ok=False 时有
        }
    """
    try:
        logger.info("----------------")
        logger.info("[Ingest] 收到事件")
        # 记录原始数据（DEBUG级别，不换行）
        logger.debug(f"[原始数据] {json.dumps(data, ensure_ascii=False, default=str)}")

        # 解析事件
        event = parse_emby_event(data)

        logger.info(f"         event: {json.dumps({'type': event.get('event'), 'title': event.get('name')}, ensure_ascii=False)}")

        return {"ok": True, "event": event}
    
    except Exception as e:
        # 代码异常 → 日志，不记录状态
        logger.error(f"[Ingest] 解析失败: {str(e)}")
        return {"ok": False, "error": f"解析失败: {str(e)}"}


# ============================================================================
# Layer 2: Process（处理层）
# ============================================================================

async def process_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理层：数据增强，构建标准化 event_record
    
    不包含任何 IO 操作（发送通知等）
    只构建数据，不处理发送
    
    Returns:
        {
            "ok": True/False,
            "event_record": NotificationEvent,  # 仅在 ok=True 时有
            "filtered": True/False,             # 是否被过滤
            "error": error_message              # 仅在 ok=False 时有
        }
    """
    try:
        # 1. 过滤判断
        if not allow_event(event.get("event")):
            logger.debug(f"[Process] 事件被过滤: {event.get('event')}")
            
            # 创建被过滤的事件记录
            event_record = NotificationEvent(
                core=CoreInfo(
                    event_type=event.get("event", ""),
                    media_type=event.get("type", ""),
                    title=event.get("name", "")
                ),
                source=SourceInfo(
                    server_name=event.get("server_name", ""),
                    server_id=event.get("server_id", "")
                )
            )
            
            # 保存到事件存储
            event_record = event_store.add_event(event_record)
            
            return {
                "ok": True,
                "event_record": event_record,
                "filtered": True
            }
        
        # 2. 数据增强
        logger.info("----------------")
        logger.info("[Process] 数据增强")
        
        enriched_event = await _enrich_event_data(event)
        
        # 3. 构建标准化事件记录
        event_record = _build_event_record(enriched_event)
        
        # 4. 保存到事件存储
        event_record = event_store.add_event(event_record)
        
        logger.info(f"[Process] 事件已构建: {event_record.core.id}")
        
        return {
            "ok": True,
            "event_record": event_record,
            "filtered": False
        }
    
    except Exception as e:
        # 代码异常 → 日志，不记录状态
        logger.error(f"[Process] 处理失败: {str(e)}")
        return {"ok": False, "error": f"处理失败: {str(e)}"}


async def _enrich_event_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """增强事件数据（优先从 Emby 获取图片和评分，TMDB 作为备用）"""
    media = event.copy()

    event_type = event.get("event", "")
    media_type = event.get("type", "")
    is_audio = media_type in ("Audio", "MusicAlbum", "MusicArtist")
    is_image_update = event_type == "image.update"

    # 跳过的情况：图片更新事件
    if is_image_update:
        return media

    tmdb_id = event.get("tmdb_id")

    # 从 Emby 数据提取信息
    item = event.get("raw_data", {}).get("Item", {})
    image_tags = item.get("ImageTags", {})
    backdrop_tags = item.get("BackdropImageTags", [])
    server_id = item.get("ServerId", "")
    item_id = item.get("Id", "")
    server_name = event.get("server_name", "")

    # 检查 Emby 是否有图片（根据 ImageTags）
    has_primary_image = bool(image_tags.get("Primary"))
    has_backdrop_image = bool(backdrop_tags)

    # 优先从 Emby 获取图片 URL（使用服务函数）
    emby_poster_url = ""
    emby_backdrop_url = ""

    if item_id:
        from app.services.emby import get_emby_item_image, get_emby_item_details

        # 只有 Emby 有 Primary 图片时才获取 URL（检查外网是否可访问）
        if has_primary_image:
            emby_poster_url = get_emby_item_image(
                item_id=item_id,
                image_type="Primary",
                server_id=server_id,
                server_name=server_name,
                check_exists=True
            ) or ""

        # 只有 Emby 有 Backdrop 图片时才获取 URL（检查外网是否可访问）
        if has_backdrop_image:
            emby_backdrop_url = get_emby_item_image(
                item_id=item_id,
                image_type="Backdrop",
                server_id=server_id,
                server_name=server_name,
                check_exists=True
            ) or ""

        # 获取 Emby 项目详情（包含评分）
        try:
            emby_details = get_emby_item_details(item_id=item_id, server_id=server_id)
            if emby_details:
                # 获取 Emby 评分（CommunityRating 字段，范围通常是 0-10）
                community_rating = emby_details.get("CommunityRating")
                if community_rating:
                    media["emby_vote"] = float(community_rating)
                    logger.debug(f"[Process] 获取到 Emby 评分: {community_rating}")
        except Exception as e:
            logger.debug(f"[Process] 获取 Emby 详情失败: {e}")

    media["emby_poster_url"] = emby_poster_url
    media["emby_backdrop_url"] = emby_backdrop_url

    # 获取剧集封面（仅 Episode 类型）
    # 优先级：TMDB（外网可访问） > Emby（可能是内网地址）
    emby_series_poster_url = ""
    tmdb_series_poster_url = ""
    if media_type == "Episode":
        series_id = event.get("series_id", "")
        series_image_tag = event.get("series_image_tag", "")

        # 优先从 TMDB 获取剧集封面（外网可访问）
        if tmdb_id:
            try:
                series_tmdb_data = get_tmdb("Series", tmdb_id)
                if series_tmdb_data and series_tmdb_data.get("poster"):
                    tmdb_series_poster_url = series_tmdb_data.get("poster", "")
                    logger.debug(f"[Process] 从 TMDB 获取剧集封面成功")
            except Exception as e:
                logger.debug(f"[Process] 从 TMDB 获取剧集封面失败: {e}")

        # 如果 TMDB 没有，尝试从 Emby 获取
        if not tmdb_series_poster_url and series_id and series_image_tag:
            from app.services.emby import get_emby_item_image
            emby_series_poster_url = get_emby_item_image(
                item_id=series_id,
                image_type="Primary",
                server_id=server_id,
                server_name=server_name,
                check_exists=True
            ) or ""

        media["emby_series_poster_url"] = emby_series_poster_url
        media["tmdb_series_poster_url"] = tmdb_series_poster_url

    # TMDB 查询（获取图片、简介、评分、语言、地区等）
    # 优先级：TMDB（外网可访问） > Emby（可能是内网地址）
    tmdb_poster_url = ""
    tmdb_backdrop_url = ""

    # 判断是否需要从 TMDB 获取数据
    needs_tmdb_data = tmdb_id and not is_audio and media_type
    # 优先使用 TMDB 封面（外网可访问），无论 Emby 是否有封面
    needs_tmdb_poster = tmdb_id and not is_audio and media_type
    needs_tmdb_backdrop = tmdb_id and not is_audio and media_type

    if needs_tmdb_data:
        try:
            # 获取 TMDB 数据（包含封面、简介、评分、语言、地区等）
            tmdb_data = get_tmdb(media_type, tmdb_id)

            if tmdb_data:
                # 优先使用 TMDB 海报（外网可访问）
                if needs_tmdb_poster and tmdb_data.get("poster"):
                    tmdb_poster_url = tmdb_data.get("poster", "")

                # 优先使用 TMDB 背景图（外网可访问）
                if needs_tmdb_backdrop and tmdb_data.get("backdrop"):
                    tmdb_backdrop_url = tmdb_data.get("backdrop", "")

                # 获取简介（如果 Emby 没有）
                if tmdb_data.get("overview") and not media.get("overview"):
                    media["overview"] = tmdb_data["overview"]

                # 获取 TMDB 评分
                if tmdb_data.get("vote_average"):
                    media["tmdb_vote"] = tmdb_data["vote_average"]

                # 获取语言和地区（用于地区分类）
                if tmdb_data.get("original_language"):
                    media["language"] = tmdb_data["original_language"]
                if tmdb_data.get("origin_country"):
                    media["country"] = tmdb_data["origin_country"]

            # 获取总集数（电视剧）
            if media_type in ["Series", "Episode"]:
                from app.services.tmdb import get_tv_episode_count
                tv_info = get_tv_episode_count(tmdb_id)
                if tv_info:
                    if tv_info.get("total_episodes"):
                        media["total_episodes"] = tv_info["total_episodes"]
                        media["episode_count"] = tv_info["total_episodes"]
                    if tv_info.get("status"):
                        media["tv_status"] = tv_info["status"]

        except Exception as e:
            # TMDB 失败 → warning，不阻塞流程
            logger.warning(f"[Process] TMDB 查询失败: {e}")

    media["tmdb_poster_url"] = tmdb_poster_url
    media["tmdb_backdrop_url"] = tmdb_backdrop_url

    # 计算综合评分（优先级：豆瓣 > TMDB > Emby）
    media["rating"] = _calculate_rating(media)

    return media


def _calculate_rating(media: Dict[str, Any]) -> Optional[float]:
    """
    计算综合评分
    优先级：豆瓣 > TMDB > Emby
    """
    # 优先级1：豆瓣评分（如果有）
    douban_vote = media.get("douban_vote")
    if douban_vote:
        return float(douban_vote)

    # 优先级2：TMDB 评分
    tmdb_vote = media.get("tmdb_vote")
    if tmdb_vote:
        return float(tmdb_vote)

    # 优先级3：Emby 评分
    emby_vote = media.get("emby_vote")
    if emby_vote:
        return float(emby_vote)

    return None


def _build_event_record(event: Dict[str, Any]) -> NotificationEvent:
    """构建标准化事件记录"""

    # 确定使用哪个封面（优先级：Emby > TMDB）
    poster_url = event.get("emby_poster_url") or event.get("tmdb_poster_url") or ""
    backdrop_url = event.get("emby_backdrop_url") or event.get("tmdb_backdrop_url") or ""

    # 确定剧集封面（仅 Episode 类型，固定从 TMDB 获取）
    series_poster_url = ""
    if event.get("type") == "Episode":
        series_poster_url = event.get("tmdb_series_poster_url") or ""

    # 地区分类
    region_category = _get_region_category(
        event.get("type", ""),
        event.get("language", ""),
        event.get("country", "")
    )
    
    return NotificationEvent(
        core=CoreInfo(
            event_type=event.get("event", ""),
            media_type=event.get("type", ""),
            title=event.get("name", ""),
            action=event.get("action", "")
        ),
        content=ContentInfo(
            series_name=event.get("series_name", ""),
            season_number=event.get("season_number"),
            episode_number=event.get("episode_number"),
            episode_title=event.get("episode_title", ""),
            year=event.get("year"),
            overview=event.get("overview", "")
        ),
        media=MediaResources(
            poster_url=poster_url,
            backdrop=backdrop_url,
            series_poster_url=series_poster_url
        ),
        external=ExternalIds(
            tmdb_id=event.get("tmdb_id") or "",
            imdb_id=event.get("imdb_id") or "",
            douban_id=event.get("douban_id") or "",
            tmdb_vote=event.get("tmdb_vote"),
            douban_vote=event.get("douban_vote"),
            emby_vote=event.get("emby_vote"),
            rating=event.get("rating")
        ),
        user=UserPlayback(
            user_name=event.get("user_name", ""),
            play_position=event.get("play_position"),
            play_duration=event.get("play_duration")
        ),
        media_profile=MediaProfile.from_emby_data(
            width=event.get("width"),
            height=event.get("height"),
            display_title=event.get("display_title") or event.get("deisplay_titl", ""),
            video_range=event.get("video_range", "")
        ),
        music=MusicInfo(
            artists=event.get("artists", []),
            album=event.get("album", "")
        ),
        region=RegionInfo(
            category=region_category
        ),
        source=SourceInfo(
            server_name=event.get("server_name", ""),
            server_id=event.get("server_id", "")
        ),
        series=SeriesInfo(
            episode_count=event.get("episode_count") or event.get("total_episodes"),
            episodes=event.get("all_episodes", []),
            range=event.get("episode_range", "")
        )
    )


def _get_region_category(media_type: str, language: str, country: str) -> str:
    """根据语言和国家判断地区类别"""
    # 华语内容
    if language in ("zh", "cn", "zh-cn", "zh-hk", "zh-tw"):
        return "华语"
    
    # 日语
    if language in ("ja", "jp"):
        if country == "KR":
            return "韩剧"
        return "日剧"
    
    # 韩语
    if language in ("ko", "kr"):
        return "韩剧"
    
    # 英语
    if language in ("en", "us", "gb", "uk"):
        return "欧美"
    
    # 欧洲
    if country in ("FR", "DE", "IT", "ES", "NL", "BE", "SE", "NO", "DK", "FI", "PL", "CZ", "AT", "CH"):
        return "欧美"
    
    # 其他
    if language or country:
        return "外语"
    
    return ""


# ============================================================================
# Layer 3: Render（渲染层）
# ============================================================================

async def render_notification(event_record: NotificationEvent) -> Dict[str, Any]:
    """
    渲染层：生成通知内容
    
    原则：
    - events.json 作为唯一事实源
    - 返回渲染后的消息内容，由 Send 层保存并标记 platform
    
    Returns:
        {
            "ok": True/False,
            "title": "...",
            "content": "...",
            "flat_event": {...},
            "wecom_msg": {...},
            "error": error_message
        }
    """
    try:
        from app.core.event_formatter import build_event_title, build_event_content
        
        # 将分层模型转换为扁平化字典
        flat_event = _flatten_event_record(event_record)
        
        # 计算一次标题和内容（避免重复计算）
        title = build_event_title(flat_event)
        content = build_event_content(flat_event)
        
        logger.info("----------------")
        logger.info("[Render] 通知已渲染")
        logger.info(f"         title: {title}")
        
        return {
            "ok": True,
            "title": title,
            "content": content,
            "flat_event": flat_event
        }
    
    except Exception as e:
        import traceback
        logger.error(f"[Render] 渲染失败: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"ok": False, "error": f"渲染失败: {str(e)}"}


def _build_links(external, media_type: str) -> Dict[str, str]:
    """构建跳转链接（从 ExternalIds）"""
    links = {}
    if external.douban_id:
        links["douban"] = f"https://movie.douban.com/subject/{external.douban_id}/"
    if external.tmdb_id:
        # 剧集类型（Series 或 Episode）使用 tv 路径，电影使用 movie 路径
        tmdb_path = "tv" if media_type in ("Series", "Episode") else "movie"
        links["tmdb"] = f"https://www.themoviedb.org/{tmdb_path}/{external.tmdb_id}"
    if external.imdb_id:
        links["imdb"] = f"https://www.imdb.com/title/{external.imdb_id}/"
    return links


def _flatten_event_record(event_record: NotificationEvent) -> Dict[str, Any]:
    """
    将分层 NotificationEvent 转换为扁平化字典
    用于兼容渲染函数
    """
    core = event_record.core
    content = event_record.content
    media = event_record.media
    external = event_record.external
    user = event_record.user
    music = event_record.music
    region = event_record.region
    source = event_record.source
    series = event_record.series
    
    # 构建跳转链接
    links = _build_links(external, core.media_type)
    
    return {
        # Core
        "id": core.id,
        "timestamp": core.timestamp,
        "event_type": core.event_type,
        "media_type": core.media_type,
        "title": core.title,
        "action": core.action,

        # Content
        "series_name": content.series_name,
        "season_number": content.season_number,
        "episode_number": content.episode_number,
        "episode_title": content.episode_title,
        "year": content.year,
        "overview": content.overview,
        
        # Media
        "poster_url": media.poster_url,
        "backdrop": media.backdrop,
        "series_poster_url": media.series_poster_url,

        # External
        "tmdb_id": external.tmdb_id,
        "imdb_id": external.imdb_id,
        "douban_id": external.douban_id,
        "tmdb_vote": external.tmdb_vote,
        "douban_vote": external.douban_vote,
        "emby_vote": external.emby_vote,
        "rating": external.rating,

        # Links (跳转链接)
        "links": links,
        "tmdb_url": links.get("tmdb", ""),
        "douban_url": links.get("douban", ""),
        "imdb_url": links.get("imdb", ""),
        
        # User
        "user_name": user.user_name,
        "play_position": user.play_position,
        "play_duration": user.play_duration,
        
        # Media Profile
        "media_profile": {
            "resolution": event_record.media_profile.resolution,
            "codec": event_record.media_profile.codec,
            "hdr": event_record.media_profile.hdr
        } if event_record.media_profile else {},
        "width": None,  # 保留兼容性
        "height": None,
        
        # Music
        "artists": music.artists,
        "album": music.album,
        
        # Region
        "region_category": region.category,
        
        # Source
        "server_name": source.server_name,
        "server_id": source.server_id,
        
        # Series
        "episode_count": series.episode_count,
        "total_episodes": series.episode_count,  # 兼容性字段
        "all_episodes": series.episodes,
        "episode_range": series.range
    }


# ============================================================================
# Layer 4: Send（发送层）
# ============================================================================

def _get_attr(obj, key, default=None):
    """兼容 dict 和模型对象访问"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _server_allowed(allowed_servers: List[str], server_id: str) -> bool:
    """检查事件来源服务器是否被允许发送

    allowed_servers 存的是 Emby 服务器配置 id 列表。
    空列表表示全部服务器都允许。
    匹配方式：将配置 id 列表反查为 Emby 实例 ID（server_id），
    与事件的 server_id（Emby 自报的实例 ID）比对。
    """
    if not allowed_servers:
        return True
    try:
        servers = config_manager.get_emby_servers() or []
        allowed_ids = {
            s.get("server_id", "")
            for s in servers
            if s.get("id") in allowed_servers
        }
        return bool(server_id) and server_id in allowed_ids
    except Exception:
        return True


async def _send_to_wecom_channels(wecom_msg: Dict[str, Any], event_type: str, server_id: str = "") -> Dict[str, Any]:
    """
    发送消息到企业微信渠道
    
    Args:
        wecom_msg: 企业微信消息格式
        event_type: 事件类型
        server_id: 事件来源 Emby 实例 ID（用于服务器过滤）
    
    Returns:
        {
            "success": bool,
            "platforms": List[str],
            "results": Dict[str, Any]
        }
    """
    from app.services.wecom import send_wecom_webhook, send_wecom_news_with_config
    from app.services.config_manager import config_manager
    
    # 获取通知配置
    config = config_manager.get_notify_config()
    channels = []
    channel_names = {}
    
    # 检查企业微信机器人
    wecom_webhook = _get_attr(config, 'wecom_webhook', {})
    webhook_enabled = _get_attr(wecom_webhook, 'enabled', False)
    webhook_key = _get_attr(wecom_webhook, 'webhook_key', '')
    webhook_events = _get_attr(wecom_webhook, 'allowed_events', [])
    webhook_name = _get_attr(wecom_webhook, 'bot_name', '企业微信群机器人')
    webhook_servers = _get_attr(wecom_webhook, 'allowed_servers', [])
    
    if webhook_enabled and webhook_key and event_type in webhook_events and _server_allowed(webhook_servers, server_id):
        channels.append("wecom_webhook")
        channel_names["wecom_webhook"] = webhook_name
    
    # 检查自定义微信应用通知
    custom_notifies = _get_attr(config, 'custom_notifies', [])
    for custom in custom_notifies:
        custom_enabled = _get_attr(custom, 'enabled', False)
        custom_name = _get_attr(custom, 'name', '')
        custom_channel = _get_attr(custom, 'channel_type', 'wecom_app')
        custom_events = _get_attr(custom, 'allowed_events', [])
        custom_corp_id = _get_attr(custom, 'corp_id', '')
        custom_servers = _get_attr(custom, 'allowed_servers', [])
        
        if not custom_enabled or custom_channel != 'wecom_app' or not custom_corp_id:
            continue
        
        if event_type in custom_events and _server_allowed(custom_servers, server_id):
            channel_key = f"wecom_app:{custom_name}"
            channels.append(channel_key)
            channel_names[channel_key] = custom_name
    
    if not channels:
        return {"success": False, "platforms": [], "results": {}, "reason": "无匹配渠道"}
    
    results = {}
    success = False
    platforms = []
    
    # 发送群机器人消息
    if "wecom_webhook" in channels:
        try:
            webhook_result = send_wecom_webhook(webhook_key, wecom_msg)
            if webhook_result:
                results["wecom_webhook"] = {"success": True, "name": "企业微信群机器人"}
                success = True
                platforms.append("wecom_webhook")
            else:
                results["wecom_webhook"] = {"success": False, "name": "企业微信群机器人", "error": "发送失败"}
        except Exception as e:
            results["wecom_webhook"] = {"success": False, "name": "企业微信群机器人", "error": str(e)}
    
    # 发送自定义企业微信应用消息
    wecom_app_channels = [c for c in channels if c.startswith("wecom_app:")]
    for channel_key in wecom_app_channels:
        notify_name = channel_key.split(":", 1)[1]
        custom_config = None
        for custom in custom_notifies:
            if _get_attr(custom, 'name', '') == notify_name:
                custom_config = custom
                break
        
        if not custom_config:
            results[channel_key] = {"success": False, "name": notify_name, "error": "未找到配置"}
            continue
        
        try:
            custom_corp_id = _get_attr(custom_config, 'corp_id', '')
            custom_agent_id = _get_attr(custom_config, 'agent_id', '')
            custom_secret = _get_attr(custom_config, 'secret', '')
            
            app_result = send_wecom_news_with_config(
                wecom_msg,
                corp_id=custom_corp_id,
                agent_id=custom_agent_id,
                secret=custom_secret
            )
            if app_result.get("success"):
                results[channel_key] = {"success": True, "name": notify_name}
                success = True
                platforms.append(channel_key)
            else:
                results[channel_key] = {"success": False, "name": notify_name, "error": app_result.get("error")}
        except Exception as e:
            results[channel_key] = {"success": False, "name": notify_name, "error": str(e)}
    
    return {
        "success": success,
        "platforms": platforms,
        "results": results,
        "channel_names": channel_names
    }


async def send_notification(event_record: NotificationEvent, render_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送层：发送通知并保存到对应通知文件
    
    - desktop.json: 桌面通知格式
    - wecom.json: 企业微信格式
    """
    event_id = event_record.core.id
    
    try:
        from app.services.notification_store import save_notification
        
        # 获取渲染结果
        title = render_result.get("title", "")
        content = render_result.get("content", "")
        flat_event = render_result.get("flat_event", {})
        media_type = flat_event.get("media_type", "")
        links = flat_event.get("links", {})
        event_type = flat_event.get("event_type", "")
        
        # desktop.json：Episode/Series/Movie 使用 series_poster_url，音乐使用 poster_url
        if media_type in ("Episode", "Series", "Movie"):
            desktop_poster = flat_event.get("series_poster_url", "")
        else:
            desktop_poster = flat_event.get("poster_url", "")
        
        # 微信通知封面优先级：
        # - 单集：poster_url
        # - 其他：backdrop > poster_url
        if media_type == "Episode":
            wecom_poster = flat_event.get("poster_url", "")
        else:
            wecom_poster = flat_event.get("backdrop", "") or flat_event.get("poster_url", "")
        
        # platform 始终包含 desktop
        platforms = ["desktop"]
        
        # 保存桌面通知（固定使用 series_poster_url）
        desktop_data = {
            "title": title,
            "content": content,
            "poster": desktop_poster,
            "media_type": media_type,
            "event_type": event_type,
            "links": links
        }
        save_notification("desktop", event_id, desktop_data)
        
        # 构建企业微信消息格式
        url = links.get("douban", "") or links.get("tmdb", "") or links.get("imdb", "")
        wecom_msg = {
            "msgtype": "news",
            "news": {
                "articles": [{
                    "title": title,
                    "description": content,
                    "picurl": wecom_poster,
                    "url": url
                }]
            }
        }
        
        # 发送到企业微信渠道
        result = await _send_to_wecom_channels(wecom_msg, event_type, flat_event.get("server_id", ""))
        
        if result.get("reason") == "无匹配渠道":
            logger.info(f"[Send] 仅桌面通知 ({event_id}, 事件: {event_type}, 原因: 无匹配渠道)")
            return {"ok": True, "skipped": True, "reason": "通知未启用或事件类型不匹配", "platforms": platforms}
        
        # 合并平台列表
        platforms.extend(result.get("platforms", []))
        
        # 保存企业微信通知记录
        wecom_platforms = result.get("platforms", [])
        if wecom_platforms:
            wecom_meta = {
                "channels": wecom_platforms,
                "channel_names": {c: result.get("channel_names", {}).get(c, c) for c in wecom_platforms},
                "event_type": event_type
            }
            save_notification("wecom", event_id, wecom_msg, wecom_meta)
        
        # 记录结果到日志
        if result.get("success"):
            logger.info(f"[Send] 发送成功: {json.dumps({'event_id': event_id, 'platforms': platforms}, ensure_ascii=False)}")
        else:
            logger.error(f"[Send] 发送失败: {json.dumps({'event_id': event_id, 'error': '所有渠道发送失败', 'platforms': platforms}, ensure_ascii=False)}")
        
        return {
            "ok": True,
            "success": result.get("success", False),
            "results": result.get("results", {}),
            "platforms": platforms
        }
    
    except Exception as e:
        import traceback
        logger.error(f"[Send] 代码异常: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"ok": False, "error": f"发送异常: {str(e)}"}


# ============================================================================
# 聚合发送回调
# ============================================================================

async def _send_aggregated_notification(
    base_media: Dict[str, Any],
    episodes: List[Dict],
    original_event_record: NotificationEvent
) -> None:
    """
    发送聚合后的通知
    
    Args:
        base_media: 聚合后的基础媒体数据
        episodes: 聚合的剧集列表
        original_event_record: 原始事件记录（用于构建通知）
    """
    try:
        from app.core.event_formatter import build_event_title, build_event_content
        from app.services.notification_store import save_notification
        
        # 构建聚合事件数据
        flat_event = _flatten_event_record(original_event_record)

        # 更新为聚合信息
        flat_event["episode_range"] = base_media.get("episode_range", "")
        flat_event["episode_count"] = base_media.get("episode_count", len(episodes))
        flat_event["all_episodes"] = base_media.get("all_episodes", [])
        # 使用 base_media 中的 is_aggregated（只有多集才为 True）
        flat_event["is_aggregated"] = base_media.get("is_aggregated", len(episodes) > 1)

        # 获取总集数和状态（用于显示进度）
        # 从第一个剧集的媒体数据中获取
        first_episode_media = episodes[0].get("media", {})
        total_episodes = first_episode_media.get("total_episodes") or first_episode_media.get("episode_count")
        tv_status = first_episode_media.get("tv_status", "")
        if total_episodes:
            flat_event["total_episodes"] = total_episodes
        if tv_status:
            flat_event["tv_status"] = tv_status
        
        # 重新计算标题和内容（带聚合信息）
        title = build_event_title(flat_event)
        content = build_event_content(flat_event)
        
        logger.info("----------------")
        logger.info(f"[聚合] 生成聚合通知")
        logger.info(f"       title: {title}")
        
        media_type = flat_event.get("media_type", "")
        links = flat_event.get("links", {})
        event_type = flat_event.get("event_type", "")

        # desktop.json：Episode/Series/Movie 使用 series_poster_url，音乐使用 poster_url
        if media_type in ("Episode", "Series", "Movie"):
            desktop_poster = flat_event.get("series_poster_url", "")
        else:
            desktop_poster = flat_event.get("poster_url", "")

        # 微信通知封面优先级：
        # - 单集：poster_url
        # - 其他：backdrop > poster_url
        if media_type == "Episode":
            wecom_poster = flat_event.get("poster_url", "")
        else:
            wecom_poster = flat_event.get("backdrop", "") or flat_event.get("poster_url", "")

        # 构建企业微信消息
        url = links.get("douban", "") or links.get("tmdb", "") or links.get("imdb", "")
        wecom_msg = {
            "msgtype": "news",
            "news": {
                "articles": [{
                    "title": title,
                    "description": content,
                    "picurl": wecom_poster,
                    "url": url
                }]
            }
        }

        # 保存桌面通知
        desktop_data = {
            "title": title,
            "content": content,
            "poster": desktop_poster,
            "media_type": media_type,
            "event_type": event_type,
            "links": links
        }
        save_notification("desktop", original_event_record.core.id, desktop_data)

        # 发送到企业微信
        result = await _send_to_wecom_channels(wecom_msg, event_type, original_event_record.source.server_id)

        # 保存企业微信通知记录
        if result.get("platforms"):
            wecom_meta = {
                "channels": result["platforms"],
                "event_type": event_type
            }
            save_notification("wecom", original_event_record.core.id, wecom_msg, wecom_meta)
        
        if result.get("success"):
            logger.info(f"[聚合] 通知发送成功")
        else:
            logger.error(f"[聚合] 通知发送失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"[聚合] 发送聚合通知失败: {e}")


async def _send_music_aggregated_notification(
    base_media: Dict[str, Any],
    songs: List[Dict],
    original_event_record: NotificationEvent
) -> None:
    """
    发送音乐聚合后的通知
    
    Args:
        base_media: 聚合后的基础媒体数据
        songs: 聚合的歌曲列表
        original_event_record: 原始事件记录
    """
    try:
        from app.core.event_formatter import build_event_title, build_event_content
        from app.services.notification_store import save_notification
        
        # 构建聚合事件数据
        flat_event = _flatten_event_record(original_event_record)
        
        # 更新为聚合信息
        flat_event["song_count"] = base_media.get("song_count", len(songs))
        flat_event["song_list"] = base_media.get("song_list", [])
        # 使用 base_media 中的 is_aggregated（只有多首歌曲才为 True）
        flat_event["is_aggregated"] = base_media.get("is_aggregated", len(songs) > 1)
        
        # 重新计算标题和内容
        title = build_event_title(flat_event)
        content = build_event_content(flat_event)
        
        logger.info("----------------")
        logger.info(f"[音乐聚合] 生成聚合通知")
        logger.info(f"          title: {title}")
        
        media_type = flat_event.get("media_type", "")
        links = flat_event.get("links", {})
        event_type = flat_event.get("event_type", "")

        # desktop.json：音乐使用 poster_url
        desktop_poster = flat_event.get("poster_url", "")

        # 微信通知：音乐使用 poster_url
        wecom_poster = flat_event.get("poster_url", "")

        # 构建企业微信消息
        url = links.get("douban", "") or links.get("tmdb", "") or links.get("imdb", "")
        wecom_msg = {
            "msgtype": "news",
            "news": {
                "articles": [{
                    "title": title,
                    "description": content,
                    "picurl": wecom_poster,
                    "url": url
                }]
            }
        }

        # 保存桌面通知
        desktop_data = {
            "title": title,
            "content": content,
            "poster": desktop_poster,
            "media_type": media_type,
            "event_type": event_type,
            "links": links
        }
        save_notification("desktop", original_event_record.core.id, desktop_data)
        
        # 发送到企业微信
        result = await _send_to_wecom_channels(wecom_msg, event_type, original_event_record.source.server_id)
        
        # 保存企业微信通知记录
        if result.get("platforms"):
            wecom_meta = {
                "channels": result["platforms"],
                "event_type": event_type
            }
            save_notification("wecom", original_event_record.core.id, wecom_msg, wecom_meta)
        
        if result.get("success"):
            logger.info(f"[音乐聚合] 通知发送成功")
        else:
            logger.error(f"[音乐聚合] 通知发送失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"[音乐聚合] 发送聚合通知失败: {e}")


# ============================================================================
# 主流程入口
# ============================================================================

async def process_webhook_pipeline(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    完整处理管道
    
    1. Ingest → 2. Process → 3. Render → 4. Send
    """
    # Step 1: Ingest
    ingest_result = await ingest_webhook(data)
    if not ingest_result["ok"]:
        return ingest_result
    
    event = ingest_result["event"]
    event_type = event.get("event", "")
    media_type = event.get("type", "")
    
    # Step 2: Process
    process_result = await process_event(event)
    if not process_result["ok"]:
        return process_result
    
    event_record = process_result["event_record"]
    
    # 如果被过滤，直接返回
    if process_result.get("filtered"):
        return {
            "ok": True,
            "event_id": event_record.core.id,
            "filtered": True
        }
    
    # 检查是否需要聚合（只有入库事件才聚合）
    is_library_new = event_type in ("library.new", "library.new.music")
    
    if is_library_new:
        # 尝试剧集聚合
        if media_type == "Episode":
            # 使用 event_record 中的数据（包含 total_episodes 和 tv_status）
            flat_record = _flatten_event_record(event_record)
            media = {
                "series_name": flat_record.get("series_name"),
                "season_number": flat_record.get("season_number"),
                "episode_number": flat_record.get("episode_number"),
                "type": media_type,
                "total_episodes": flat_record.get("total_episodes"),
                "episode_count": flat_record.get("episode_count"),
                "tv_status": flat_record.get("tv_status"),
                **flat_record
            }

            async def series_callback(base_media, episodes):
                await _send_aggregated_notification(base_media, episodes, event_record)

            is_aggregated = await series_aggregator.add_episode(media, series_callback, event_record.core.id)
            
            if is_aggregated:
                from app.services.config_manager import config_manager
                agg_config = config_manager.get_aggregation_config()
                delay_seconds = agg_config.delay_seconds
                logger.info(f"剧集已加入聚合队列，将在 {delay_seconds} 秒后发送")
                return {
                    "ok": True,
                    "event_id": event_record.core.id,
                    "aggregated": True,
                    "message": f"剧集已加入聚合队列，{delay_seconds}秒后发送"
                }
        
        # 尝试音乐聚合 (Audio 和 MusicAlbum 类型)
        if media_type in ("Audio", "MusicAlbum"):
            # 使用 event_record 中的数据
            flat_record = _flatten_event_record(event_record)
            media = {
                "name": flat_record.get("title"),
                "album": flat_record.get("album"),
                "type": media_type,
                **flat_record
            }

            async def music_callback(base_media, songs):
                await _send_music_aggregated_notification(base_media, songs, event_record)

            is_music_aggregated = await music_aggregator.add_song(media, music_callback)
            
            if is_music_aggregated:
                from app.services.config_manager import config_manager
                agg_config = config_manager.get_aggregation_config()
                delay_seconds = agg_config.delay_seconds
                logger.info(f"音乐已加入聚合队列，将在 {delay_seconds} 秒后发送")
                return {
                    "ok": True,
                    "event_id": event_record.core.id,
                    "aggregated": True,
                    "message": f"音乐已加入聚合队列，{delay_seconds}秒后发送"
                }
    
    # 非入库事件或非聚合类型，立即发送
    # Step 3: Render
    render_result = await render_notification(event_record)
    if not render_result["ok"]:
        return render_result
    
    # Step 4: Send
    send_result = await send_notification(event_record, render_result)
    
    return {
        "ok": True,
        "event_id": event_record.core.id,
        "message_sent": send_result.get("success", False),
        "skipped": send_result.get("skipped", False),
        "platforms": send_result.get("platforms", ["desktop"])
    }
