"""
聚合通知管理器

处理剧集和音乐的聚合发送：
- 剧集聚合：15秒内同一部电视剧的不同剧集入库，合并为一个通知
- 音乐聚合：15秒内所有入库的歌曲，合并为一个通知
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from app.services.config_manager import config_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SeriesAggregator:
    """
    剧集聚合发送管理器
    15秒内同一部电视剧的不同剧集入库，合并为一个通知
    标题格式：入库《剧集名》剧集。S01 E05-E08
    """

    def __init__(self):
        self._pending: Dict[str, Dict[str, Any]] = {}  # 待发送的剧集
        self._timers: Dict[str, asyncio.Task] = {}  # 定时器任务
        self._lock = asyncio.Lock()  # 并发锁

    def _get_series_key(self, series_name: str, season_number: int) -> str:
        """生成剧集的唯一标识键"""
        return f"{series_name}_S{season_number:02d}"

    async def add_episode(self, media: Dict[str, Any], send_callback: Callable, event_id: str = None) -> bool:
        """
        添加剧集到聚合队列

        Args:
            media: 剧集媒体数据
            send_callback: 发送通知的回调函数
            event_id: 事件记录ID

        Returns:
            True: 已加入聚合队列
            False: 非剧集类型，需要立即发送
        """
        series_name = media.get("series_name")
        season_number = media.get("season_number")
        episode_number = media.get("episode_number")
        media_type = media.get("type", "")

        # 只有 Episode 类型才聚合
        if media_type != "Episode":
            return False

        # 只有剧集类型才聚合
        if not series_name or season_number is None or episode_number is None:
            return False

        key = self._get_series_key(series_name, season_number)

        # 使用锁保护共享状态
        async with self._lock:
            # 取消之前的定时器（如果存在）
            if key in self._timers:
                self._timers[key].cancel()
                # 不等待定时器完成，避免_pending被清空

            # 添加到待发送列表
            if key not in self._pending:
                self._pending[key] = {
                    "series_name": series_name,
                    "season_number": season_number,
                    "episodes": [],
                    "first_added_time": time.time()
                }

            # 避免重复添加同一集
            episode_exists = any(
                ep["episode_number"] == episode_number
                for ep in self._pending[key]["episodes"]
            )

            if not episode_exists:
                self._pending[key]["episodes"].append({
                    "episode_number": episode_number,
                    "media": media,
                    "event_id": event_id
                })
                logger.debug(f"剧集 {series_name} S{season_number:02d}E{episode_number:02d} 加入聚合队列，当前队列: {[ep['episode_number'] for ep in self._pending[key]['episodes']]}")

            # 创建新的定时器
            self._timers[key] = asyncio.create_task(
                self._send_aggregated(key, send_callback)
            )

            return True

    async def _send_aggregated(self, key: str, send_callback: Callable):
        """延迟发送聚合后的通知"""
        try:
            # 从配置中获取延迟时间
            agg_config = config_manager.get_aggregation_config()
            delay = agg_config.delay_seconds
            await asyncio.sleep(delay)

            # 使用锁保护共享状态
            async with self._lock:
                if key not in self._pending:
                    return

                pending_data = self._pending.pop(key)
                self._timers.pop(key, None)

                episodes = pending_data["episodes"]
                if not episodes:
                    return

                # 按集数排序
                episodes.sort(key=lambda x: x["episode_number"])
                episode_numbers = [ep["episode_number"] for ep in episodes]

                # 构建集数范围字符串
                episode_range = self._format_episode_range(episode_numbers)

                # 使用第一集的媒体数据作为基础
                base_media = episodes[0]["media"].copy()

                # 更新聚合信息
                base_media["episode_range"] = episode_range
                base_media["episode_count"] = len(episodes)
                base_media["all_episodes"] = episode_numbers
                # 只有多集才标记为聚合
                base_media["is_aggregated"] = len(episodes) > 1
                base_media["timestamp"] = datetime.now().isoformat()

                if len(episodes) > 1:
                    logger.info(f"发送聚合通知: {pending_data['series_name']} S{pending_data['season_number']:02d} {episode_range}，共{len(episodes)}集")
                else:
                    logger.info(f"只有一集，发送单个通知: {pending_data['series_name']} S{pending_data['season_number']:02d}E{episodes[0]['episode_number']:02d}")

                # 调用发送回调
                await send_callback(base_media, episodes)

        except asyncio.CancelledError:
            # 被取消时不清理状态，让新的定时器处理
            pass
        except Exception as e:
            logger.error(f"聚合发送失败: {e}")

    def _format_episode_range(self, episodes: List[int]) -> str:
        """格式化集数范围：E05 或 E05-E08"""
        if len(episodes) == 1:
            return f"E{episodes[0]:02d}"

        # 检查是否是连续的
        if episodes == list(range(episodes[0], episodes[-1] + 1)):
            return f"E{episodes[0]:02d}-E{episodes[-1]:02d}"
        else:
            # 不连续，列出所有集数
            return ",".join(f"E{ep:02d}" for ep in episodes)


class MusicAggregator:
    """
    音乐聚合发送管理器
    15秒内所有入库的歌曲，合并为一个通知
    标题格式：入库 音乐。5首歌曲
    """

    def __init__(self):
        self._pending: Optional[Dict[str, Any]] = None  # 待发送的音乐
        self._timer: Optional[asyncio.Task] = None  # 定时器任务
        self._lock = asyncio.Lock()  # 并发锁

    async def add_song(self, media: Dict[str, Any], send_callback: Callable) -> bool:
        """
        添加歌曲到聚合队列

        Args:
            media: 歌曲媒体数据
            send_callback: 发送通知的回调函数

        Returns:
            True: 已加入聚合队列
            False: 非音乐类型，需要立即发送
        """
        media_type = media.get("type", "")

        # Audio 和 MusicAlbum 类型都聚合
        if media_type not in ("Audio", "MusicAlbum"):
            return False

        # 使用锁保护共享状态
        async with self._lock:
            # 取消之前的定时器（如果存在）
            if self._timer:
                self._timer.cancel()
                # 不等待定时器完成，避免_pending被清空

            # 添加到待发送列表
            if self._pending is None:
                self._pending = {
                    "songs": [],
                    "first_added_time": time.time()
                }

            # 避免重复添加同一首歌
            song_name = media.get("name", "")
            album = media.get("album", "")
            unique_key = f"{album}_{song_name}"
            song_exists = any(
                f"{s['media'].get('album', '')}_{s['name']}" == unique_key
                for s in self._pending["songs"]
            )

            if not song_exists:
                self._pending["songs"].append({
                    "name": song_name,
                    "album": album,
                    "media": media
                })
                logger.debug(f"歌曲 《{song_name}》 加入聚合队列，当前共 {len(self._pending['songs'])} 首")

            # 创建新的定时器
            self._timer = asyncio.create_task(
                self._send_aggregated(send_callback)
            )

            return True

    async def _send_aggregated(self, send_callback: Callable):
        """延迟发送聚合后的通知"""
        try:
            # 从配置中获取延迟时间
            agg_config = config_manager.get_aggregation_config()
            delay = agg_config.delay_seconds
            await asyncio.sleep(delay)

            # 使用锁保护共享状态
            async with self._lock:
                if self._pending is None:
                    return

                songs = self._pending["songs"]
                if not songs:
                    self._pending = None
                    self._timer = None
                    return

                # 按歌曲名排序
                songs.sort(key=lambda x: x["name"])
                song_names = [song["name"] for song in songs]

                # 使用第一首歌的媒体数据作为基础
                base_media = songs[0]["media"].copy()

                # 更新聚合信息
                base_media["song_count"] = len(songs)
                base_media["song_list"] = song_names
                # 只有多首歌曲才标记为聚合
                base_media["is_aggregated"] = len(songs) > 1
                base_media["timestamp"] = datetime.now().isoformat()

                if len(songs) > 1:
                    logger.info(f"发送聚合通知：共 {len(songs)} 首歌曲")
                else:
                    logger.info(f"只有一首歌曲，发送单个通知")

                # 调用发送回调
                await send_callback(base_media, songs)

                # 清空状态
                self._pending = None
                self._timer = None

        except asyncio.CancelledError:
            # 被取消时不清空状态，让新的定时器处理
            pass
        except Exception as e:
            logger.error(f"音乐聚合发送失败: {e}")
            # 使用锁保护清空状态
            async with self._lock:
                self._pending = None
                self._timer = None


# 全局聚合器实例
series_aggregator = SeriesAggregator()
music_aggregator = MusicAggregator()
