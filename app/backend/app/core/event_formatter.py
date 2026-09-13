"""
事件格式化模块
定义通知事件的标题和内容格式

重要：本模块只使用标准化的 event_record 字段
不直接解析 webhook，不查询 TMDB
所有数据已在前面的流程中标准化
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.core.constants import get_event_info, SCHEDULED_TASK_DESC_MAP
from app.utils.logger import get_logger
from app.templates import get_template
from app.templates.registry import GenericTemplate
import re

logger = get_logger(__name__)


def _format_timestamp(timestamp: str) -> Optional[str]:
    """
    将 ISO 8601 格式的时间戳转换为北京时间字符串
    支持多种格式，包括带微秒的格式
    """
    if not timestamp:
        return None

    try:
        # 处理 Z 后缀
        ts = timestamp.replace('Z', '+00:00')

        # 尝试直接解析
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            # 处理带微秒的格式，如 2026-05-09T11:09:32.7549287+00:00
            # Python 的 fromisoformat 最多支持 6 位微秒
            match = re.match(r'(.+\.\d{6})\d*(\+\d{2}:\d{2}|\-\d{2}:\d{2}|Z)?$', ts)
            if match:
                ts = match.group(1) + (match.group(2) if match.group(2) else '')
                dt = datetime.fromisoformat(ts)
            else:
                # 尝试使用 strptime
                dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")

        # 转换为北京时间
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        beijing = timezone(timedelta(hours=8))
        return dt.astimezone(beijing).strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        logger.warning(f"时间格式化失败: {e}, timestamp: {timestamp}")
        return None


def build_event_title(event_record: dict) -> str:
    """
    构建通知事件标题（核心函数）
    
    依赖的标准化字段：
    - event_type: 事件类型
    - title: 媒体标题
    - media_type: 媒体类型
    - series_name: 剧集名称
    - season_number: 季号
    - episode_number: 集号
    - episode_range: 集数范围（聚合通知）
    - song_count: 歌曲数量（聚合音乐）
    - artists: 艺术家列表
    """
    event_type = event_record.get("event_type", "")
    title = event_record.get("title", "")
    media_type = event_record.get("media_type", "")
    series_name = event_record.get("series_name", "")
    season_number = event_record.get("season_number")
    episode_number = event_record.get("episode_number")

    logger.debug(f"build_event_title: series_name={series_name}, season_number={season_number}, episode_number={episode_number}, media_type={media_type}, title={title}")
    
    # 新架构：使用模板系统（优先处理已知模板）
    template = get_template(event_type, media_type)
    if not isinstance(template, GenericTemplate):
        return template.build_title(event_record)
    
    # 使用 get_event_info 获取事件信息
    event_info = get_event_info(event_type, event_record)
    event_desc = event_info["name"]
    emoji = event_info["emoji"]
    
    # 处理登录失败事件（特殊格式）
    if event_type == "user.authenticationfailed":
        # 从 Title 提取用户名（格式：服务器 上来自 用户名 的登录尝试失败）
        if title and "来自" in title and "的登录尝试失败" in title:
            import re
            match = re.search(r'来自\s+(.+?)\s+的登录尝试失败', title)
            if match:
                user = match.group(1)
                return f"{emoji} {event_desc}：用户 {user}"
        return f"{emoji} {event_desc}"

    # 处理计划任务事件 - 标题使用原始 title
    if event_type in ("scheduledtasks.completed", "scheduledtasks.failed"):
        raw_title = event_record.get("title", "")
        if raw_title:
            return f"{emoji} {raw_title}"
        return f"{emoji} {event_desc}"
    
    def get_type_name(mt):
        if mt == "Episode":
            return "单集"
        elif mt == "Series":
            return "剧集"
        elif mt in ("Audio", "MusicAlbum", "MusicArtist"):
            return "音乐"
        return ""
    
    # 构建标题
    # 处理 season_number 为 None 的情况
    effective_season = season_number
    if effective_season is None and (media_type in ("Episode", "Series") or series_name):
        effective_season = 1
        logger.debug(f"season_number 为 None，使用默认值 1")

    # 如果没有 series_name 但有 title，使用 title 作为剧集名称
    effective_series_name = series_name if series_name else (title if media_type in ("Episode", "Series") else "")

    result = ""
    
    if effective_series_name and effective_season is not None:
        type_name = get_type_name(media_type)
        # 检查是否有集数范围（聚合通知）
        episode_range = event_record.get("episode_range", "")
        if episode_range:
            # 聚合通知：使用集数范围
            type_name = "剧集"
            result = f"{event_desc} {type_name} 《{effective_series_name}》 S{effective_season:02d} {episode_range}"
        elif episode_number is not None:
            episode_title = f"S{effective_season:02d}E{episode_number:02d}"
            if title and title != effective_series_name:
                episode_title += f" {title}"
            result = f"{event_desc} {type_name} 《{effective_series_name}》 {episode_title}"
        else:
            result = f"{event_desc} {type_name} 《{effective_series_name}》 S{effective_season:02d}"
    elif media_type == "Series":
        type_name = get_type_name(media_type)
        effective_season_series = season_number if season_number is not None else 1
        effective_series_name_series = series_name if series_name else title
        episode_range = event_record.get("episode_range", "")
        if episode_range:
            result = f"{event_desc} {type_name} 《{effective_series_name_series}》 S{effective_season_series:02d} {episode_range}"
        else:
            result = f"{event_desc} {type_name} 《{effective_series_name_series}》 S{effective_season_series:02d}"
    elif media_type in ("Audio", "MusicAlbum", "MusicArtist"):
        if event_record.get("is_aggregated"):
            # 聚合音乐标题
            song_count = event_record.get("song_count", 1)
            result = f"{event_desc} 音乐 共{song_count}首歌曲"
        else:
            artists = event_record.get("artists", [])
            artist_str = ", ".join(artists) if artists else ""
            type_name = get_type_name(media_type)
            if artist_str:
                result = f"{event_desc} {type_name} 《{title}》- {artist_str}"
            else:
                result = f"{event_desc} {type_name} 《{title}》"
    else:
        # 默认情况：根据媒体类型添加标识
        type_name = ""
        if media_type == "Movie":
            type_name = "电影"
        elif media_type in ("Episode", "Series"):
            type_name = "剧集"
        elif media_type == "Audio":
            type_name = "音乐"
        
        if type_name:
            result = f"{event_desc} {type_name} 《{title}》"
        else:
            result = f"{event_desc}《{title}》"
    
    return f"{emoji} {result}"


def build_event_content(event_record: dict) -> str:
    """
    构建通知事件内容（核心函数）
    
    依赖的标准化字段：
    - event_type: 事件类型
    - media_type: 媒体类型
    - overview: 简介
    - timestamp: 时间戳
    - year: 年份
    - region_category: 地区分类
    - media_profile: 视频质量信息 {resolution, hdr}
    - tmdb_vote: TMDB 评分
    - total_episodes: 总集数
    - tv_status: 剧集状态
    - all_episodes: 所有集数列表
    - episode_number: 集号
    - unplayed_count: 未播放数量
    - is_aggregated: 是否聚合
    - song_list: 歌曲列表
    - artists: 艺术家
    - album: 专辑
    - play_position: 播放位置
    - play_duration: 播放时长
    - user_name: 用户名
    """
    event_type = event_record.get("event_type", "")
    media_type = event_record.get("media_type", "")
    overview = event_record.get("overview", "")
    timestamp = event_record.get("timestamp", "")
    
    # 新架构：使用模板系统（优先处理已知模板）
    template = get_template(event_type, media_type)
    if not isinstance(template, GenericTemplate):
        return template.build_content(event_record)
    
    is_playback = event_type.startswith("playback.")
    is_library_new = event_type == "library.new"
    lines = []
    parts = []
    
    # 处理登录失败事件
    if event_type == "user.authenticationfailed":
        # 从 overview 提取 IP 地址（第一行）
        ip = overview.split('\n')[0] if overview else ""
        if ip:
            lines.append(f"🌐IP：{ip}")
        # 时间
        if timestamp:
            time_str = _format_timestamp(timestamp)
            if time_str:
                lines.append(f"时间：{time_str}")
        return "\n".join(lines) if lines else "登录验证失败"

    # 处理计划任务事件
    if event_type in ("scheduledtasks.completed", "scheduledtasks.failed"):
        task_name = event_record.get("name", "")
        # 获取功能描述
        task_desc = ""
        if task_name:
            task_desc = SCHEDULED_TASK_DESC_MAP.get(task_name, "")
        # 处理运行时间
        duration_str = overview
        if duration_str and "运行时间：" in duration_str:
            duration_str = duration_str.replace("seconds", "秒")
            duration_str = duration_str.replace("minute", "分钟")
            duration_str = duration_str.replace("minutes", "分钟")
            duration_str = duration_str.replace("hour", "小时")
            duration_str = duration_str.replace("hours", "小时")
        # 构建内容
        # 第一行：简介
        desc_parts = []
        if task_desc:
            desc_parts.append(task_desc)
        if duration_str:
            desc_parts.append(duration_str)
        if desc_parts:
            lines.append("简介：" + "  ".join(desc_parts))
        # 第三行：时间
        if timestamp:
            time_str = _format_timestamp(timestamp)
            if time_str:
                lines.append(f"时间：{time_str}")
        return "\n".join(lines) if lines else event_type
    
    # 入库进度（剧集显示总集数和剩余集数）
    if is_library_new and media_type in ["Series", "Episode"]:
        # 支持 total_episodes 和 episode_count 两种字段名
        total_episodes = event_record.get("total_episodes") or event_record.get("episode_count")
        tv_status = event_record.get("tv_status", "")
        if total_episodes:
            status_cn = ""
            if tv_status == "Ended":
                status_cn = "【已完结】"
            elif tv_status == "Returning Series":
                status_cn = "【连载中】"
            elif tv_status == "Canceled":
                status_cn = "【已取消】"
            elif tv_status == "In Production":
                status_cn = "【制作中】"
            
            all_episodes = event_record.get("all_episodes", [])
            if all_episodes:
                max_episode = max(all_episodes)
                remaining = total_episodes - max_episode
                if remaining > 0:
                    lines.append(f"📊进度：{max_episode}/{total_episodes}集  还剩{remaining}集{status_cn}")
                else:
                    lines.append(f"📊进度：{max_episode}/{total_episodes}集  ✅已完结{status_cn}")
            else:
                episode_number = event_record.get("episode_number")
                if episode_number:
                    remaining = total_episodes - episode_number
                    if remaining > 0:
                        lines.append(f"📊进度：{episode_number}/{total_episodes}集  还剩{remaining}集{status_cn}")
                    else:
                        lines.append(f"📊进度：{episode_number}/{total_episodes}集  ✅已完结{status_cn}")
    
    # 年份和类别
    year = event_record.get("year")
    region_category = event_record.get("region_category", "")
    if year:
        if region_category:
            parts.append(f"📅年份：{year} ｜ {region_category}")
        else:
            parts.append(f"📅年份：{year}")
    
    # 视频质量（使用 media_profile）
    if media_type not in ("Audio", "MusicAlbum", "MusicArtist"):
        media_profile = event_record.get("media_profile", {})
        quality_parts = []

        if media_profile:
            resolution = media_profile.get("resolution", "")
            hdr = media_profile.get("hdr", "")

            if resolution:
                quality_parts.append(resolution)
            if hdr:
                quality_parts.append(hdr)

        if quality_parts:
            parts.append(f"🎬质量：{' | '.join(quality_parts)}")
    
    # 评分
    if media_type not in ("Audio", "MusicAlbum", "MusicArtist"):
        score = event_record.get("tmdb_vote")
        score_str = f"{score}" if score else "暂无"
        parts.append(f"⭐评分：{score_str}")
    
    # 未播放数量
    unplayed_count = event_record.get("unplayed_count")
    if unplayed_count is not None and unplayed_count > 0:
        parts.append(f"🆕未看：{unplayed_count}集")
    
    # 聚合音乐信息
    if media_type in ("Audio", "MusicAlbum", "MusicArtist") and event_record.get("is_aggregated"):
        song_list = event_record.get("song_list", [])
        if song_list:
            parts.append(f"🎵歌曲：{', '.join(song_list[:5])}")
            if len(song_list) > 5:
                parts.append(f"等共{len(song_list)}首")
    
    # 单音乐信息
    if media_type in ("Audio", "MusicAlbum", "MusicArtist") and not event_record.get("is_aggregated"):
        artists = event_record.get("artists", [])
        if artists:
            parts.append(f"🎤艺术家：{', '.join(artists)}")
        album = event_record.get("album", "")
        if album:
            parts.append(f"💿专辑：{album}")
    
    # 服务器和用户名
    server = event_record.get("server_name", "")
    user_name = event_record.get("user_name", "")
    if server:
        if user_name:
            parts.append(f"🖥️服务器：{server} | {user_name}")
        else:
            parts.append(f"🖥️服务器：{server}")

    if parts:
        lines.append("  ".join(parts))

    # 播放进度（插入到第一行）
    if is_playback:
        pos = event_record.get("play_position")
        dur = event_record.get("play_duration")
        if pos is not None and dur:
            pos_sec = pos // 10000000
            dur_sec = dur // 10000000
            pos_str = str(timedelta(seconds=pos_sec))[2:7]
            dur_str = str(timedelta(seconds=dur_sec))[2:7]
            pct = int((pos_sec / dur_sec) * 100) if dur_sec > 0 else 0
            # 插入到第一行
            lines.insert(0, f"⏱️进度：{pos_str}/{dur_str} ({pct}%)")

    # 简介
    if overview:
        short_overview = overview[:60] + "..." if len(overview) > 60 else overview
        lines.append(f"简介：{short_overview}")

    # 时间
    if timestamp:
        time_str = _format_timestamp(timestamp)
        if time_str:
            lines.append(f"时间：{time_str}")
    
    return "\n".join(lines) if lines else "暂无详细信息"
