"""
Emby 事件模型模块
定义各类事件的标准数据结构，确保类型安全和代码可维护性
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EmbyEvent:
    """Emby 事件基础类"""
    event: str
    timestamp: str
    server_name: str
    raw_data: Dict[str, Any]
    server_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "server_name": self.server_name,
            "server_id": self.server_id,
            "raw_data": self.raw_data,
        }


@dataclass
class MediaEvent(EmbyEvent):
    """媒体事件基类（包含 Item 的事件）"""
    item_id: str = ""
    item_name: str = ""
    item_type: str = ""  # Movie, Series, Episode, Audio
    tmdb_id: Optional[str] = None
    imdb_id: str = ""
    douban_id: str = ""
    year: Optional[int] = None
    overview: str = ""
    image_tag: Optional[str] = None
    
    # 播放状态
    is_played: Optional[bool] = None
    is_favorite: Optional[bool] = None
    play_count: int = 0
    unplayed_count: Optional[int] = None
    user_rating: Optional[float] = None
    
    # 视频信息
    width: Optional[int] = None
    height: Optional[int] = None
    video_range: str = ""  # SDR, HDR, Dolby Vision
    bit_depth: Optional[int] = None
    display_title: str = ""  # 4K HEVC
    frame_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "item_id": self.item_id,
            "name": self.item_name,
            "type": self.item_type,
            "tmdb_id": self.tmdb_id,
            "imdb_id": self.imdb_id,
            "douban_id": self.douban_id,
            "year": self.year,
            "overview": self.overview,
            "image_tag": self.image_tag,
            "is_played": self.is_played,
            "is_favorite": self.is_favorite,
            "play_count": self.play_count,
            "unplayed_count": self.unplayed_count,
            "user_rating": self.user_rating,
            "width": self.width,
            "height": self.height,
            "video_range": self.video_range,
            "bit_depth": self.bit_depth,
            "display_title": self.display_title,
            "frame_rate": self.frame_rate,
        })
        return base


@dataclass
class PlaybackEvent(MediaEvent):
    """播放事件（playback.start, playback.stop 等）"""
    user_name: str = ""
    client: str = ""  # Emby Web, Infuse
    device_name: str = ""  # Edge Windows, iPhone
    play_position: int = 0  # 当前播放位置（ticks）
    play_duration: int = 0  # 总时长（ticks）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "user_name": self.user_name,
            "client": self.client,
            "device_name": self.device_name,
            "play_position": self.play_position,
            "play_duration": self.play_duration,
        })
        return base


@dataclass
class LibraryEvent(MediaEvent):
    """入库事件（library.new, library.deleted 等）"""
    series_name: str = ""
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    series_id: str = ""
    series_image_tag: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "series_name": self.series_name,
            "season_number": self.season_number,
            "episode_number": self.episode_number,
            "series_id": self.series_id,
            "series_image_tag": self.series_image_tag,
        })
        return base


@dataclass
class RateEvent(MediaEvent):
    """评分/收藏事件（item.rate）"""
    user_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "user_name": self.user_name,
        })
        return base


@dataclass
class MarkPlayedEvent(MediaEvent):
    """标记播放状态事件（item.markplayed, item.markunplayed）"""
    user_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "user_name": self.user_name,
        })
        return base


@dataclass
class AuthEvent(EmbyEvent):
    """认证事件（user.authenticationfailed, user.logged_in 等）"""
    user_name: str = ""
    client: str = ""
    device_name: str = ""
    login_ip: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "user_name": self.user_name,
            "client": self.client,
            "device_name": self.device_name,
            "login_ip": self.login_ip,
            "type": "",  # 兼容现有代码
            "name": "",  # 兼容现有代码
            "item_id": "",  # 兼容现有代码
            "tmdb_id": None,  # 兼容现有代码
        })
        return base


@dataclass
class SystemEvent(EmbyEvent):
    """系统事件（server.restart, scheduledtasks.completed 等）"""
    title: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "title": self.title,
            "name": self.title,  # 兼容现有代码
            "overview": self.description,
            "type": "System",  # 兼容现有代码
            "item_id": "",  # 兼容现有代码
            "tmdb_id": None,  # 兼容现有代码
        })
        return base


@dataclass
class TestEvent(EmbyEvent):
    """测试事件（system.webhooktest, system.notificationtest）"""
    title: str = ""
    description: str = ""
    user_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容现有代码）"""
        base = super().to_dict()
        base.update({
            "title": self.title,
            "name": self.title,  # 兼容现有代码
            "overview": self.description,
            "user_name": self.user_name,
            "is_test": True,  # 兼容现有代码
            "type": "Test",  # 兼容现有代码
            "item_id": "",  # 兼容现有代码
            "tmdb_id": None,  # 兼容现有代码
        })
        return base


# 事件类型映射表
EVENT_CLASS_MAP = {
    # ========== 播放事件 ==========
    "playback.start": PlaybackEvent,
    "playback.stop": PlaybackEvent,
    "playback.pause": PlaybackEvent,
    "playback.unpause": PlaybackEvent,
    
    # ========== 入库事件 ==========
    "library.new": LibraryEvent,
    "library.new.music": LibraryEvent,
    "library.deleted": LibraryEvent,
    "media.metadataupdate": LibraryEvent,
    "media.imageupdate": LibraryEvent,
    
    # ========== 评分事件 ==========
    "item.rate": RateEvent,
    "item.unrate": RateEvent,
    
    # ========== 标记播放状态事件 ==========
    "item.markplayed": MarkPlayedEvent,
    "item.markunplayed": MarkPlayedEvent,
    
    # ========== 认证事件 ==========
    "user.authenticated": AuthEvent,
    "user.authenticationfailed": AuthEvent,
    "user.locked": AuthEvent,
    "user.created": AuthEvent,
    "user.deleted": AuthEvent,
    "user.passwordchanged": AuthEvent,
    "user.policyupdated": AuthEvent,
    "user.logged_in": AuthEvent,
    "user.logged_out": AuthEvent,
    
    # ========== 系统事件 ==========
    "system.serverstartup": SystemEvent,
    "system.servershutdown": SystemEvent,
    "system.maintenancemode.enter": SystemEvent,
    "system.maintenancemode.exit": SystemEvent,
    
    # ========== 服务器事件 ==========
    "server.restart": SystemEvent,
    "server.restartrequired": SystemEvent,
    "server.updateavailable": SystemEvent,
    "server.updated": SystemEvent,
    "backup.completed": SystemEvent,
    "backup.failed": SystemEvent,
    
    # ========== 计划任务事件 ==========
    "scheduledtasks.completed": SystemEvent,
    "scheduledtasks.failed": SystemEvent,
    
    # ========== 插件事件 ==========
    "plugin.installed": SystemEvent,
    "plugin.installfailed": SystemEvent,
    "plugin.uninstalled": SystemEvent,
    "plugin.updated": SystemEvent,
    
    # ========== 电视直播事件 ==========
    "livetv.recording.scheduled": SystemEvent,
    "livetv.recording.cancelled": SystemEvent,
    "livetv.recording.series.scheduled": SystemEvent,
    "livetv.recording.series.cancelled": SystemEvent,
    "livetv.recording.started": SystemEvent,
    "livetv.recording.ended": SystemEvent,
    "livetv.recording.error": SystemEvent,
    
    # ========== 设备事件 ==========
    "device.cameraimageuploaded": SystemEvent,
    
    # ========== 外部事件 ==========
    "external.notification": SystemEvent,
    
    # ========== 神医助手事件 ==========
    "collection.items.added": SystemEvent,
    "collection.items.removed": SystemEvent,
    "shenyi.favoriteupdate": SystemEvent,
    "shenyi.introupdate": SystemEvent,
    "shenyi.collection.added": SystemEvent,
    "shenyi.collection.removed": SystemEvent,
    "deep.delete": LibraryEvent,  # 神医助手深度删除事件

    # ========== IntroSkip 插件事件 ==========
    "introskip.update": LibraryEvent,  # 片头片尾标记更新
    
    # ========== 测试事件 ==========
    "system.webhooktest": TestEvent,
    "system.notificationtest": TestEvent,
}


def parse_emby_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 Emby Webhook 事件数据
    
    使用事件模型解析，返回统一的事件结构：
    {
        "event": 原始事件名,
        "category": 一级分类,
        "action": 二级动作,
        "name": 显示名称,
        "emoji": Emoji,
        "source": 来源,
        "plugin": 插件,
        # ... 其他事件特定字段
    }
    """
    import re
    from app.utils.logger import get_logger
    from app.utils.tmdb_id_extractor import extract_tmdb_id
    from app.core.constants import get_event_info
    
    logger = get_logger(__name__)
    
    event_type = data.get("Event", "")
    
    # 获取对应的事件类
    event_class = EVENT_CLASS_MAP.get(event_type, EmbyEvent)
    
    # 提取基础字段
    timestamp = data.get("Date", data.get("UtcTimestamp", ""))
    server = data.get("Server", {})
    server_name = server.get("Name", "")
    server_id = server.get("Id", "")

    # 备用：从 Session.ServerName 获取（播放事件）
    if not server_name:
        session = data.get("Session", {})
        server_name = session.get("ServerName", "")

    # 备用：从 Item.ServerName 获取
    if not server_name:
        item = data.get("Item", {})
        server_name = item.get("ServerName", "")

    # 备用：从 Item.ServerId 获取 Emby 实例 ID
    if not server_id:
        item = data.get("Item", {})
        server_id = item.get("ServerId", "")
    if not server_id:
        session = data.get("Session", {})
        server_id = session.get("ServerId", "")
    
    try:
        # 根据事件类型解析特定字段
        if event_class == PlaybackEvent:
            parsed = _parse_playback_event(data, event_type, timestamp, server_name)
        elif event_class == LibraryEvent:
            parsed = _parse_library_event(data, event_type, timestamp, server_name)
        elif event_class == RateEvent:
            parsed = _parse_rate_event(data, event_type, timestamp, server_name)
        elif event_class == MarkPlayedEvent:
            parsed = _parse_markplayed_event(data, event_type, timestamp, server_name)
        elif event_class == AuthEvent:
            parsed = _parse_auth_event(data, event_type, timestamp, server_name)
        elif event_class == SystemEvent:
            parsed = _parse_system_event(data, event_type, timestamp, server_name)
        elif event_class == TestEvent:
            parsed = _parse_test_event(data, event_type, timestamp, server_name)
        else:
            # 默认处理
            event = EmbyEvent(
                event=event_type,
                timestamp=timestamp,
                server_name=server_name,
                raw_data=data
            )
            parsed = event.to_dict()
        
        # 添加统一的事件信息（分类、动作、来源等）
        # 注意：不要覆盖 name 字段，它存储的是媒体项目名称
        # 对于 item.rate 事件，使用解析后的 parsed 数据（包含 is_favorite）
        event_info = get_event_info(event_type, parsed if event_type == "item.rate" else data)
        parsed.update({
            "category": event_info["category"],
            "action": event_info["action"],
            "event_name": event_info["name"],  # 事件显示名称（如"开始播放"）
            "emoji": event_info["emoji"],
            "source": event_info["source"],
            "plugin": event_info["plugin"],
            "server_id": server_id,
        })

        return parsed

    except Exception as e:
        logger.warning(f"解析 {event_type} 事件失败: {e}，使用基础解析")
        # 回退到基础解析
        event = EmbyEvent(
            event=event_type,
            timestamp=timestamp,
            server_name=server_name,
            raw_data=data
        )
        parsed = event.to_dict()

        # 仍然尝试添加事件信息
        try:
            event_info = get_event_info(event_type, data)
            parsed.update({
                "category": event_info["category"],
                "action": event_info["action"],
                "event_name": event_info["name"],  # 事件显示名称
                "emoji": event_info["emoji"],
                "source": event_info["source"],
                "plugin": event_info["plugin"],
            })
        except:
            pass

        return parsed


def _parse_media_fields(item: Dict[str, Any], parsed: Dict[str, Any]) -> None:
    """解析媒体通用字段"""
    from app.utils.tmdb_id_extractor import extract_tmdb_id
    
    # 基础字段
    parsed["item_id"] = item.get("Id", "")
    parsed["item_name"] = item.get("Name", "")
    parsed["name"] = item.get("Name", "")  # 兼容现有代码，name 字段存储媒体项目名称
    parsed["item_type"] = item.get("Type", "")
    parsed["type"] = item.get("Type", "")  # 兼容 event_formatter.py 使用的 type 字段
    parsed["year"] = item.get("ProductionYear")
    parsed["overview"] = item.get("Overview", "")
    
    # 剧集相关字段
    parsed["series_name"] = item.get("SeriesName", "")
    parsed["season_number"] = item.get("ParentIndexNumber")
    parsed["episode_number"] = item.get("IndexNumber")
    parsed["episode_title"] = item.get("Name", "") if item.get("Type") == "Episode" else ""
    parsed["series_id"] = item.get("SeriesId", "")
    parsed["series_image_tag"] = item.get("SeriesPrimaryImageTag", "")
    parsed["width"] = item.get("Width")
    parsed["height"] = item.get("Height")
    parsed["video_range"] = item.get("VideoRange", "")
    parsed["bit_depth"] = item.get("BitDepth")
    parsed["display_title"] = item.get("DisplayTitle", "")
    parsed["frame_rate"] = item.get("RealFrameRate")
    
    # 图片标签
    image_tags = item.get("ImageTags", {})
    if "Primary" in image_tags:
        parsed["image_tag"] = image_tags["Primary"]
    
    # ProviderIds
    provider_ids = item.get("ProviderIds", {})
    if provider_ids:
        parsed["imdb_id"] = provider_ids.get("Imdb") or provider_ids.get("imdb", "")
        parsed["douban_id"] = provider_ids.get("Douban") or provider_ids.get("douban", "")
    
    # TMDB ID
    server_id = item.get("ServerId", "")
    parsed["tmdb_id"] = extract_tmdb_id(item, server_id=server_id, server_name=parsed.get("server_name", ""))
    
    # UserData
    user_data = item.get("UserData", {})
    if user_data:
        parsed["is_favorite"] = user_data.get("IsFavorite")
        parsed["is_played"] = user_data.get("Played")
        parsed["play_count"] = user_data.get("PlayCount", 0)
        parsed["unplayed_count"] = user_data.get("UnplayedItemCount")
        parsed["user_rating"] = user_data.get("Rating")
    
    # 音乐相关字段
    artists = item.get("Artists", [])
    if artists:
        parsed["artists"] = artists
    parsed["album_artist"] = item.get("AlbumArtist", "")
    # 对于 MusicAlbum 类型，Name 就是专辑名；对于 Audio 类型，从 Album 字段获取
    if item.get("Type") == "MusicAlbum":
        parsed["album"] = item.get("Name", "")
    else:
        parsed["album"] = item.get("Album", "")
    
    # 视频流信息
    media_streams = item.get("MediaStreams", [])
    if media_streams and len(media_streams) > 0:
        video_stream = media_streams[0]
        if video_stream.get("Type") == "Video":
            parsed["video_range"] = video_stream.get("VideoRange", parsed["video_range"])
            parsed["bit_depth"] = video_stream.get("BitDepth", parsed["bit_depth"])
            parsed["display_title"] = video_stream.get("DisplayTitle", parsed["display_title"])
            parsed["frame_rate"] = video_stream.get("RealFrameRate", parsed["frame_rate"])


def _parse_playback_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析播放事件"""
    item = data.get("Item", {})
    session = data.get("Session", {})
    user = data.get("User", {})
    playback_info = data.get("PlaybackInfo", {})
    
    parsed = {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "user_name": user.get("Name", ""),
        "client": session.get("Client", ""),
        "device_name": session.get("DeviceName", ""),
        "play_position": playback_info.get("PositionTicks", 0),
        "play_duration": playback_info.get("RunTimeTicks", 0),
    }
    
    if not parsed["play_duration"] and "MediaSource" in playback_info:
        parsed["play_duration"] = playback_info["MediaSource"].get("RunTimeTicks", 0)
    
    _parse_media_fields(item, parsed)
    return parsed


def _parse_library_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析入库事件"""
    item = data.get("Item", {})

    # 从 Item 获取基本信息
    series_name = item.get("SeriesName", "")
    season_number = item.get("ParentIndexNumber")
    episode_number = item.get("IndexNumber")

    # 从 Description 提取集数信息（如果是 Series 类型多集入库）
    description = data.get("Description", "")
    episode_range = ""
    all_episodes = []
    if description and not series_name and item.get("Type") == "Series":
        # 解析格式：S01 E01-E04 或 S01 E05
        import re
        match = re.search(r'S(\d+)\s+E(\d+)(?:-E?(\d+))?', description)
        if match:
            season_number = int(match.group(1))
            start_ep = int(match.group(2))
            end_ep = match.group(3)
            if end_ep:
                episode_range = f"E{start_ep:02d}-E{int(end_ep):02d}"
                # 生成所有集数的列表 [1, 2, 3, 4]
                all_episodes = list(range(start_ep, int(end_ep) + 1))
            else:
                episode_range = f"E{start_ep:02d}"
                all_episodes = [start_ep]
            # 如果是多集，使用第一集作为 episode_number
            episode_number = start_ep

    parsed = {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "series_name": series_name,
        "season_number": season_number,
        "episode_number": episode_number,
        "series_id": item.get("SeriesId", ""),
        "series_image_tag": item.get("SeriesPrimaryImageTag", ""),
        "episode_range": episode_range,
        "all_episodes": all_episodes,
    }

    _parse_media_fields(item, parsed)
    return parsed


def _parse_rate_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析评分/收藏事件"""
    item = data.get("Item", {})
    user = data.get("User", {})
    
    parsed = {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "user_name": user.get("Name", ""),
    }
    
    _parse_media_fields(item, parsed)
    return parsed


def _parse_markplayed_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析标记播放状态事件"""
    item = data.get("Item", {})
    user = data.get("User", {})
    
    parsed = {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "user_name": user.get("Name", ""),
        "series_name": item.get("SeriesName", ""),
        "season_number": item.get("ParentIndexNumber"),
        "episode_number": item.get("IndexNumber"),
        "series_id": item.get("SeriesId", ""),
        "series_image_tag": item.get("SeriesPrimaryImageTag", ""),
    }
    
    _parse_media_fields(item, parsed)
    return parsed


def _parse_auth_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析认证事件"""
    import re
    
    device_info = data.get("DeviceInfo", {})
    title = data.get("Title", "")
    description = data.get("Description", "")
    
    # 从 Title 提取用户名
    user_name = ""
    if "来自" in title and "的登录尝试失败" in title:
        match = re.search(r'来自\s+(.+?)\s+的登录尝试失败', title)
        if match:
            user_name = match.group(1)
    
    # 从 Description 提取 IP
    login_ip = description.split('\n')[0] if description else ""
    
    return {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "user_name": user_name,
        "client": device_info.get("AppName", ""),
        "device_name": device_info.get("Name", ""),
        "login_ip": login_ip,
        "type": "",
        "name": "",
        "item_id": "",
        "tmdb_id": None,
    }


def _parse_system_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析系统事件"""
    title = data.get("Title", "")
    description = data.get("Description", "")
    
    # 对于合集事件，从 Item 获取名称
    item = data.get("Item", {})
    if event_type in ("collection.items.added", "collection.items.removed"):
        name = item.get("Name", "")
    elif event_type == "scheduledtasks.completed" and " 上 " in title and " 已完成" in title:
        # 提取计划任务名称
        import re
        match = re.search(r' 上 (.+?) 已完成', title)
        name = match.group(1) if match else title
    else:
        name = title
    
    return {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "title": title,
        "name": name,
        "overview": description,
        "type": "System",
        "item_id": item.get("Id", ""),
        "tmdb_id": None,
    }


def _parse_test_event(data: Dict[str, Any], event_type: str, timestamp: str, server_name: str) -> Dict[str, Any]:
    """解析测试事件"""
    title = data.get("Title", "测试通知")
    description = data.get("Description", "")
    user = data.get("User", {})
    
    return {
        "event": event_type,
        "timestamp": timestamp,
        "server_name": server_name,
        "raw_data": data,
        "title": title,
        "name": title,
        "overview": description,
        "user_name": user.get("Name", "") if user else "",
        "is_test": True,
        "type": "Test",
        "item_id": "",
        "tmdb_id": None,
    }
