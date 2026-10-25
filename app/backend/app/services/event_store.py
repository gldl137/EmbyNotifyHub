"""
通知事件存储服务 - 将收到的 Emby 通知保存到本地
"""
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.logger import get_logger
from app.services.database import get_db, migrate_json_to_sqlite

logger = get_logger(__name__)

# 事件存储文件路径 - 支持环境变量或自动检测项目根目录
if os.getenv("DATA_DIR"):
    DATA_DIR = Path(os.getenv("DATA_DIR"))
else:
    # 自动检测项目根目录 (backend/app/services/event_store.py -> 项目根目录)
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR = BASE_DIR / "data"

EVENTS_FILE = DATA_DIR / "events.json"


class CoreInfo(BaseModel):
    """① Core（永远不变）- 核心信息层

    绝对稳定，所有系统都依赖
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = ""  # library.new, playback.start, playback.stop
    media_type: str = ""  # Movie, Series, Episode, Audio
    title: str = ""  # 电影/剧集/歌曲名称
    action: str = ""  # 二级动作（如 favorite/unfavorite/rate）


class SourceInfo(BaseModel):
    """⑨ Source（来源层）- 运行环境上下文
    
    服务器信息、来源标识等
    """
    server_name: str = ""  # Emby 服务器名称
    server_id: str = ""    # Emby 服务器 ID


class ContentInfo(BaseModel):
    """② Content（内容层）- 用于展示

    可为空，随媒体类型变化
    """
    series_name: str = ""  # 电视剧名称（剧集类型）
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: str = ""  # 单集标题（剧集类型）
    year: Optional[int] = None
    overview: str = ""


class MediaResources(BaseModel):
    """③ Media（媒体资源层）- 只管资源，不管逻辑

    图片、封面等资源信息
    """
    poster_url: str = ""  # 竖版海报（单集/电影）
    backdrop: str = ""  # 横版背景图
    series_poster_url: str = ""  # 剧集封面（仅 Episode 类型使用）


class ExternalIds(BaseModel):
    """④ External（外部关联）- 外部平台ID和评分
    
    评分优先级：豆瓣 > TMDB > Emby
    """
    tmdb_id: Optional[str] = None
    imdb_id: Optional[str] = None
    douban_id: Optional[str] = None
    tmdb_vote: Optional[float] = None
    douban_vote: Optional[float] = None
    emby_vote: Optional[float] = None
    rating: Optional[float] = None  # 综合评分（优先级：豆瓣 > TMDB > Emby）


class UserPlayback(BaseModel):
    """⑤ User & Playback（行为层）- 动态数据
    
    用户信息和播放进度
    """
    user_name: str = ""
    play_position: Optional[int] = None  # 播放位置（ticks）
    play_duration: Optional[int] = None  # 总时长（ticks）


class MediaProfile(BaseModel):
    """⑥ Media Profile（技术层）- 视频质量信息

    技术规格：分辨率、编码、HDR等
    """
    resolution: str = ""  # 4K/1080p/720p 等
    codec: str = Field(default="", exclude=True)  # HEVC/H.264/AV1 等（不保存到 JSON）
    hdr: str = ""         # HDR10/Dolby Vision/SDR
    
    @classmethod
    def from_emby_data(cls, width: Optional[int], height: Optional[int],
                       display_title: str = "", video_range: str = "",
                       path: str = "") -> "MediaProfile":
        """从 Emby 数据创建 MediaProfile

        HDR / 编解码器判定优先级：
        1) Emby 真实字段 video_range（最准，但 webhook 经常不携带，且 STRM 文件常缺失）
        2) 文件名 / 路径兜底（多数片源命名含 HDR10 / Dolby Vision / 4K 等标记）
        """
        profile = cls()

        # 分辨率（支持只有 width 或 height 的情况）
        w = width or 0
        h = height or 0

        if w >= 3840 or h >= 2160:
            profile.resolution = "4K"
        elif w >= 1920 or h >= 1080:
            profile.resolution = "1080p"
        elif w >= 1280 or h >= 720:
            profile.resolution = "720p"
        elif w > 0 and h > 0:
            profile.resolution = f"{w}x{h}"
        elif w > 0:
            profile.resolution = f"{w}p"
        elif h > 0:
            profile.resolution = f"{h}p"
        else:
            # 兜底：从标题/路径提取分辨率标记
            _tl = ((display_title or "") + " " + (path or "")).lower()
            if "4k" in _tl or "2160p" in _tl:
                profile.resolution = "4K"
            elif "1080p" in _tl or "1080i" in _tl:
                profile.resolution = "1080p"
            elif "720p" in _tl:
                profile.resolution = "720p"

        # 合并 display_title 与 path 作为关键词搜索源
        # webhook 的 Item 通常不带 VideoRange / MediaStreams（STRM 尤其），
        # 而 HDR 标记常写在文件名里（如 "...2160p HDR10 - 夸克网盘.strm"）
        search_text = (display_title or "") + " " + (path or "")
        dt_lower = search_text.lower()

        # Codec
        if "hevc" in dt_lower or "h265" in dt_lower or "h.265" in dt_lower:
            profile.codec = "HEVC"
        elif "av1" in dt_lower:
            profile.codec = "AV1"
        elif "h264" in dt_lower or "h.264" in dt_lower or "avc" in dt_lower:
            profile.codec = "H.264"

        # 动态范围（HDR）
        # Emby/Jellyfin 的 VideoRange 枚举值常见：SDR / HDR / HDR10 / HDR 10 / HDR10Plus / Dolby Vision / HLG
        # 注意：Dolby Vision、HLG 不含 "hdr" 子串，原逻辑会误判为 SDR，这里完整覆盖
        vr = (video_range or "").lower()
        if "dolby" in vr or "dolby vision" in dt_lower or "dovi" in dt_lower:
            profile.hdr = "Dolby Vision"
        elif "hdr10" in vr or "hdr 10" in vr or "hdr10" in dt_lower or "hdr 10" in dt_lower:
            profile.hdr = "HDR10"
        elif "hlg" in vr or "hlg" in dt_lower:
            profile.hdr = "HLG"
        elif "hdr" in vr or "hdr" in dt_lower:
            profile.hdr = "HDR"
        elif "sdr" in vr or "sdr" in dt_lower:
            # 仅在视频范围或文件名明确标注 SDR 时才显示，避免把"未知"误标为 SDR
            profile.hdr = "SDR"
        else:
            # 获取不到 HDR / SDR 时直接留空，不默认填充 SDR
            profile.hdr = ""

        return profile


class MusicInfo(BaseModel):
    """⑦ Music（仅音乐用）- 音乐专用字段
    
    Movie/TV 为空
    """
    artists: List[str] = Field(default_factory=list)
    album: str = ""


class RegionInfo(BaseModel):
    """⑧ Region（语义层）- 地区分类
    
    未来可扩展：language, country
    """
    category: str = ""  # 国产剧/日韩/欧美/华语/外语


class SeriesInfo(BaseModel):
    """⑩ Series（剧集聚合层）- 多集入库信息
    
    Movie 为空，仅 Series/Episode 使用
    """
    episode_count: Optional[int] = None  # 总集数
    episodes: List[int] = Field(default_factory=list)  # 所有集数列表
    range: str = ""  # 集数范围显示 (如: E12-E13)
    library_owned_episodes: Optional[int] = None  # 媒体库该季实际已有集数（查 Emby）
    season_total_episodes: Optional[int] = None  # 该季理论总集数（查 TMDB 按季）
    season_year: Optional[int] = None  # 该季实际首播年份（查 TMDB 按季，非整剧首播年）


class NotificationEvent(BaseModel):
    """
    通知事件模型 - 分层结构化数据
    
    注意：发送状态（status, status_text, channel_results 等）
    保存到 notification_status.json，不在 events.json 中
    
    分层结构：
    - core: 核心信息（永远不变）
    - content: 内容层（用于展示）
    - media: 媒体资源层
    - external: 外部关联
    - user: 用户行为层
    - media_profile: 技术层
    - music: 音乐专用
    - region: 语义层
    - source: 来源层（运行环境上下文）
    - series: 剧集聚合层（多集入库信息）
    """
    # ① Core（永远不变）
    core: CoreInfo = Field(default_factory=CoreInfo)
    
    # ② Content（内容层）
    content: ContentInfo = Field(default_factory=ContentInfo)
    
    # ③ Media（媒体资源层）
    media: MediaResources = Field(default_factory=MediaResources)
    
    # ④ External（外部关联）
    external: ExternalIds = Field(default_factory=ExternalIds)
    
    # ⑤ User & Playback（行为层）
    user: UserPlayback = Field(default_factory=UserPlayback)
    
    # ⑥ Media Profile（技术层）
    media_profile: MediaProfile = Field(default_factory=MediaProfile)
    
    # ⑦ Music（仅音乐用）
    music: MusicInfo = Field(default_factory=MusicInfo)
    
    # ⑧ Region（语义层）
    region: RegionInfo = Field(default_factory=RegionInfo)
    
    # ⑨ Source（来源层）- 运行环境上下文
    source: SourceInfo = Field(default_factory=SourceInfo)
    
    # ⑩ Series（剧集聚合层）- 多集入库信息
    series: SeriesInfo = Field(default_factory=SeriesInfo)
    
    # 向后兼容的快捷访问属性
    @property
    def id(self) -> str:
        return self.core.id
    
    @property
    def timestamp(self) -> str:
        return self.core.timestamp
    
    @property
    def event_type(self) -> str:
        return self.core.event_type
    
    @property
    def media_type(self) -> str:
        return self.core.media_type
    
    @property
    def title(self) -> str:
        return self.core.title
    
    @property
    def server_name(self) -> str:
        return self.source.server_name
    
    @property
    def series_name(self) -> str:
        return self.content.series_name
    
    @property
    def season_number(self) -> Optional[int]:
        return self.content.season_number
    
    @property
    def episode_number(self) -> Optional[int]:
        return self.content.episode_number

    @property
    def episode_title(self) -> str:
        return self.content.episode_title

    @property
    def year(self) -> Optional[int]:
        return self.content.year
    
    @property
    def overview(self) -> str:
        return self.content.overview
    
    @property
    def poster_url(self) -> str:
        return self.media.poster_url

    @property
    def backdrop(self) -> str:
        return self.media.backdrop

    @property
    def series_poster_url(self) -> str:
        return self.media.series_poster_url

    @property
    def tmdb_id(self) -> Optional[str]:
        return self.external.tmdb_id
    
    @property
    def imdb_id(self) -> Optional[str]:
        return self.external.imdb_id
    
    @property
    def douban_id(self) -> Optional[str]:
        return self.external.douban_id
    
    @property
    def tmdb_vote(self) -> Optional[float]:
        return self.external.tmdb_vote
    
    @property
    def douban_vote(self) -> Optional[float]:
        return self.external.douban_vote
    
    @property
    def emby_vote(self) -> Optional[float]:
        return self.external.emby_vote
    
    @property
    def rating(self) -> Optional[float]:
        return self.external.rating
    
    @property
    def user_name(self) -> str:
        return self.user.user_name
    
    @property
    def play_position(self) -> Optional[int]:
        return self.user.play_position
    
    @property
    def play_duration(self) -> Optional[int]:
        return self.user.play_duration
    
    @property
    def artists(self) -> List[str]:
        return self.music.artists
    
    @property
    def album(self) -> str:
        return self.music.album
    
    @property
    def region_category(self) -> str:
        return self.region.category


class EventStore:
    """事件存储管理器"""
    
    _instance: Optional['EventStore'] = None
    _events: List[Dict[str, Any]] = []
    _max_events: int = 20  # 最大保留事件数，循环覆盖
    
    def __new__(cls) -> 'EventStore':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._events:
            # 启动时将既有 events.json 迁移进 SQLite（幂等）
            try:
                migrate_json_to_sqlite()
            except Exception as e:
                logger.error(f"事件迁移失败: {e}")
            self._load_events()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = EVENTS_FILE.parent
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_events(self):
        """从 SQLite 加载事件到内存列表（保留最近 _max_events 条）"""
        all_events = get_db().get_all_events()
        self._events = all_events[-self._max_events:] if len(all_events) > self._max_events else all_events
        logger.debug(f"加载了 {len(self._events)} 条事件记录")

    def add_event(self, event: NotificationEvent) -> NotificationEvent:
        """添加新事件"""
        event_id = event.core.id
        created_at = event.core.timestamp
        get_db().add_event(event_id, event.model_dump(), created_at)
        # 循环覆盖：仅保留最近 _max_events 条
        get_db().trim_events(self._max_events)
        # 重建内存列表（保留最近 _max_events 条）
        self._load_events()
        logger.debug(f"添加新事件: {event.core.title} ({event.core.event_type})")
        # 广播新事件给 SSE 客户端（在事件循环内异步调度）
        try:
            from app.api.events.stream import notify_new_event
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(notify_new_event(event.model_dump()))
        except RuntimeError:
            # 没有运行中的事件循环（如离线脚本），忽略推送
            pass
        return event
    
    def delete_event(self, event_id: str) -> bool:
        """删除单个事件"""
        get_db().delete_event(event_id)
        self._load_events()
        logger.debug(f"删除事件: {event_id}")
        return True
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取事件列表"""
        events = get_db().get_all_events()
        if event_type:
            events = [e for e in events if e.get('core', {}).get('event_type') == event_type]
        
        # 按时间倒序
        events = sorted(events, key=lambda x: x.get('core', {}).get('timestamp', ''), reverse=True)
        
        return events[offset:offset + limit]
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """获取单个事件"""
        return get_db().get_event(event_id)
    
    def clear_events(self):
        """清空所有事件"""
        get_db().clear_events()
        self._events = []
        logger.info("清空所有事件记录")


# 全局实例
event_store = EventStore()
