"""
事件查询 API
提供事件列表、详情、统计等查询功能
"""
from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.event_store import event_store
from app.services.notification_store import get_notification_store
from app.core.event_formatter import build_event_title, build_event_content
from app.utils.logger import get_logger

notification_store = get_notification_store()

logger = get_logger(__name__)
router = APIRouter()


@router.get("/events")
async def get_events(
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取事件列表"""
    events = event_store.get_events(event_type=event_type, limit=limit, offset=offset)
    total = len(event_store._events)
    
    # 格式化每个事件
    formatted_events = [format_event_for_response(event) for event in events]
    
    return {
        "events": formatted_events,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/query/list")
async def get_events_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取事件列表（前端兼容格式）"""
    offset = (page - 1) * page_size
    events = event_store.get_events(limit=page_size, offset=offset)
    total = len(event_store._events)
    
    # 格式化每个事件
    formatted_events = [format_event_for_response(event) for event in events]
    
    return {
        "success": True,
        "data": formatted_events,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/events/{event_id}")
async def get_event_detail(event_id: str):
    """获取单个事件详情"""
    event = event_store.get_event(event_id)
    if not event:
        return {"error": "Event not found"}
    
    return format_event_for_response(event)


@router.delete("/events/{event_id}")
async def delete_event(event_id: str):
    """删除单个事件及其通知"""
    success = event_store.delete_event(event_id)
    if success:
        # 同时删除相关通知
        notification_store.delete_by_event_id(event_id)
    return {"success": success}


@router.delete("/events")
async def clear_events():
    """清空所有事件和通知"""
    event_store.clear_events()
    # 同时清空通知
    notification_store.clear_all()
    return {"success": True}


@router.get("/events/stats/overview")
async def get_event_stats(
    days: int = Query(7, ge=1, le=30)
):
    """获取事件统计概览"""
    events = event_store.get_events(limit=1000)
    
    # 时间过滤
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.isoformat()
    recent_events = [
        e for e in events 
        if e.get('core', {}).get('timestamp', '') > cutoff_str
    ]
    
    # 按类型统计
    type_counts: Dict[str, int] = {}
    media_type_counts: Dict[str, int] = {}
    
    for event in recent_events:
        core = event.get('core', {})
        et = core.get('event_type', 'unknown')
        mt = core.get('media_type', 'unknown')
        
        type_counts[et] = type_counts.get(et, 0) + 1
        media_type_counts[mt] = media_type_counts.get(mt, 0) + 1
    
    return {
        "total_events": len(recent_events),
        "period_days": days,
        "event_types": type_counts,
        "media_types": media_type_counts
    }


def format_event_for_response(event: dict) -> dict:
    """
    格式化事件为前端响应格式
    实时渲染 messageTitle 和 messageContent（不再从存储读取）
    
    支持新的分层结构：core, content, media, external, user, media_profile, music, region, source, series
    """
    # 获取核心数据
    core = event.get('core', {})
    content = event.get('content', {})
    media = event.get('media', {})
    external = event.get('external', {})
    user = event.get('user', {})
    music = event.get('music', {})
    region = event.get('region', {})
    media_profile = event.get('media_profile', {})
    source = event.get('source', {})
    series = event.get('series', {})
    
    # 向后兼容：如果旧数据是平铺结构，转换为分层结构
    if not core and event.get('id'):
        core = {
            'id': event.get('id'),
            'timestamp': event.get('timestamp'),
            'event_type': event.get('event_type'),
            'media_type': event.get('media_type'),
            'title': event.get('title')
        }
    if not content and event.get('overview') is not None:
        content = {
            'series_name': event.get('series_name'),
            'season_number': event.get('season_number'),
            'episode_number': event.get('episode_number'),
            'year': event.get('year'),
            'overview': event.get('overview')
        }
    if not media and event.get('poster_url') is not None:
        media = {
            'poster_url': event.get('poster_url'),
            'backdrop': event.get('backdrop'),
            'series_poster_url': event.get('series_poster_url', '')
        }
    if not external and event.get('tmdb_id') is not None:
        external = {
            'tmdb_id': event.get('tmdb_id'),
            'imdb_id': event.get('imdb_id'),
            'douban_id': event.get('douban_id'),
            'tmdb_vote': event.get('tmdb_vote')
        }
    if not user and event.get('user_name') is not None:
        user = {
            'user_name': event.get('user_name'),
            'play_position': event.get('play_position'),
            'play_duration': event.get('play_duration')
        }
    if not music and event.get('artists') is not None:
        music = {
            'artists': event.get('artists', []),
            'album': event.get('album', '')
        }
    if not region and event.get('region_category') is not None:
        region = {
            'category': event.get('region_category', '')
        }
    if not source and event.get('server_name') is not None:
        source = {
            'server_name': event.get('server_name', ''),
            'server_id': event.get('server_id', '')
        }
    if not series and (event.get('episode_count') is not None or event.get('total_episodes') is not None or event.get('all_episodes') or event.get('episode_range')):
        series = {
            'episode_count': event.get('episode_count') or event.get('total_episodes'),
            'episodes': event.get('all_episodes', []),
            'range': event.get('episode_range', '')
        }
    
    # 向后兼容：如果没有 media_profile，但有 width/height/display_title/video_range
    if not media_profile:
        from app.services.event_store import MediaProfile
        media_profile = MediaProfile.from_emby_data(
            width=event.get('width'),
            height=event.get('height'),
            display_title=event.get('display_title') or event.get('deisplay_titl', ''),
            video_range=event.get('video_range', '')
        ).model_dump()
    
    # 字段名映射（前端驼峰命名）
    is_aggregated = event.get('is_aggregated', False)
    if event.get('isAggregated') and not is_aggregated:
        is_aggregated = event['isAggregated']
    
    song_count = event.get('song_count')
    if event.get('songCount') is not None and song_count is None:
        song_count = event['songCount']
    
    song_list = event.get('song_list', [])
    if event.get('songList') and not song_list:
        song_list = event['songList']
    
    # 构建扁平化的事件数据用于渲染
    flat_event = {
        **core,
        **content,
        **media,
        **external,
        **user,
        **music,
        **source,
        'region_category': region.get('category', ''),
        'media_profile': media_profile,
        'is_aggregated': is_aggregated,
        'song_count': song_count,
        'song_list': song_list,
        'episode_count': series.get('episode_count'),
        'all_episodes': series.get('episodes', []),
        'episode_range': series.get('range', '')
    }
    
    # 从 desktop.json 读取消息内容
    event_id = core.get('id', '')
    desktop_record = notification_store.get_notification_by_event_id(event_id, 'desktop')
    
    if desktop_record:
        # 从 desktop.json 读取已渲染的内容
        desktop_data = desktop_record.get('data', {})
        message_title = desktop_data.get('title', '')
        message_content = desktop_data.get('content', '')
        links = desktop_data.get('links', {})
    else:
        # 如果没有找到消息记录，实时渲染作为后备
        message_title = build_event_title(flat_event)
        message_content = build_event_content(flat_event)
        # 从 events.json 获取跳转链接
        links = flat_event.get('links', {})
    
    # 从企业微信通知记录读取实际发送到的渠道（含通知名字），用于卡片展示
    # 注意：notification_store 把 meta 内容展开到记录顶层，故直接取 channels / channel_names
    status = 'success'
    channel_results = {}
    wecom_record = notification_store.get_notification_by_event_id(event_id, 'wecom')
    if wecom_record:
        wecom_channels = wecom_record.get('channels', []) or []
        wecom_names = wecom_record.get('channel_names', {}) or {}
        for ch in wecom_channels:
            channel_results[ch] = {
                "name": wecom_names.get(ch, ch.split(':', 1)[-1] if ':' in ch else ch),
                "success": True
            }
    
    return {
        # Core
        "id": core.get('id'),
        "timestamp": core.get('timestamp'),
        "eventType": core.get('event_type'),
        "mediaType": core.get('media_type'),
        "title": core.get('title'),
        
        # Content
        "seriesName": content.get('series_name'),
        "seasonNumber": content.get('season_number'),
        "episodeNumber": content.get('episode_number'),
        "year": content.get('year'),
        "overview": content.get('overview'),
        
        # Media
        "poster": media.get('poster_url') or "",
        "backdrop": media.get('backdrop') or "",
        "seriesPoster": media.get('series_poster_url') or "",
        
        # External
        "tmdbId": external.get('tmdb_id') or "",
        "imdbId": external.get('imdb_id') or "",
        "doubanId": external.get('douban_id') or "",
        "tmdbVote": external.get('tmdb_vote'),
        
        # User
        "userName": user.get('user_name'),
        "playPosition": user.get('play_position'),
        "playDuration": user.get('play_duration'),
        
        # Media Profile
        "mediaProfile": media_profile,
        
        # Music
        "artists": music.get('artists', []),
        "album": music.get('album', ''),
        
        # Region
        "regionCategory": region.get('category', ''),
        
        # Source
        "serverName": source.get('server_name', ''),
        "serverId": source.get('server_id', ''),
        
        # Series
        "episodeCount": series.get('episode_count'),
        "allEpisodes": series.get('episodes', []),
        "episodeRange": series.get('range', ''),
        
        # Status
        "status": status,
        "channelResults": channel_results,
        "isAggregated": is_aggregated,
        "songCount": song_count,
        "songList": song_list,
        
        # Rendered
        "messageTitle": message_title,
        "messageContent": message_content,
        
        # Links
        "links": links,
        "tmdbUrl": links.get('tmdb', ''),
        "doubanUrl": links.get('douban', ''),
        "imdbUrl": links.get('imdb', ''),
    }


def _get_badge_text(event_type: str) -> str:
    """获取事件类型标签文本"""
    badge_map = {
        "library.new": "入库",
        "playback.start": "播放",
        "playback.stop": "停止",
        "user.authenticated": "登录",
        "user.authenticationfailed": "登录失败",
    }
    return badge_map.get(event_type, "其他")


def _get_status_text(status: str) -> str:
    """获取状态文本"""
    status_map = {
        "pending": "待处理",
        "processing": "处理中",
        "success": "成功",
        "failed": "失败",
        "filtered": "已过滤",
        "aggregating": "聚合中",
        "skipped": "已跳过",
    }
    return status_map.get(status, status)
