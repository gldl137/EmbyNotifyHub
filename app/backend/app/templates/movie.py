"""
电影通知模板
所有电影相关事件使用统一的正文格式

重要：本模板只使用标准化的 event_record 字段
不直接解析 webhook，不查询 TMDB
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import re


class MovieTemplate:
    """电影模板 - 所有电影事件通用（入库/删除/评分/播放）
    
    依赖的标准化字段（来自 event_record）：
    - event_type: 事件类型 (library.new, playback.start 等)
    - title: 电影标题
    - year: 年份
    - region_category: 地区分类 (欧美/华语/日韩等)
    - display_title: 视频格式 (4K HEVC 等)
    - video_range: 视频范围 (HDR/SDR)
    - tmdb_vote: TMDB 评分
    - server_name: 服务器名称
    - overview: 简介
    - timestamp: 时间戳
    """
    
    # 事件类型对应的 emoji 和名称
    EVENT_META = {
        "library.new": ("🎬", "入库"),
        "deep.delete": ("🗑️", "媒体深度删除"),
        "item.rate": ("⭐", "用户评分"),
        "playback.start": ("▶️", "开始播放"),
        "playback.stop": ("⏹️", "停止播放"),
    }
    
    def build_title(self, event_record: Dict[str, Any]) -> str:
        """构建电影通知标题

        Args:
            event_record: 标准化的事件记录，包含 event_type, title 等字段
        """
        event_type = event_record.get("event_type", "")
        media_type = event_record.get("media_type", "")
        emoji, action = self._get_event_meta(event_type)
        title = event_record.get("title", "")

        # 剧集类型特殊处理：显示剧集名 + 集数 + 单集标题
        if media_type in ("Episode", "Season", "Series"):
            series_name = event_record.get("series_name", "")
            season_number = event_record.get("season_number")
            episode_number = event_record.get("episode_number")

            # 确保有季号，默认为1
            if season_number is None:
                season_number = 1

            # 构建集数标识：整季只显示季号；整剧优先用 Description 解析的集范围；
            # 其余（单集/聚合）有入库集数则显示集号或范围
            all_episodes = event_record.get("all_episodes") or []
            episode_range = event_record.get("episode_range", "")
            if media_type == "Season":
                episode_info = f" 第{season_number}季"
            elif media_type == "Series" and episode_range:
                # Description 解析出的带季号集范围，如 S02E01-E19, E21-E22
                episode_info = episode_range
            elif len(all_episodes) > 1:
                # 多集（聚合）：显示集范围，如 S01E01-E08
                nums = sorted(all_episodes)
                lo, hi = nums[0], nums[-1]
                episode_info = f"S{season_number:02d}E{lo:02d}-E{hi:02d}"
            elif episode_number is not None:
                episode_info = f"S{season_number:02d}E{episode_number:02d}"
            else:
                episode_info = ""

            # 优先使用剧集名，如果没有则使用标题
            display_name = series_name if series_name else title

            # 单集标题与剧集名不同时，追加单集标题（整季/多集不追加）
            if media_type == "Episode" and len(all_episodes) <= 1 and title and title != series_name:
                return f"{emoji} {action} 剧集 《{display_name}》{episode_info} {title}"
            else:
                return f"{emoji} {action} 剧集 《{display_name}》{episode_info}"
        
        # 电影类型
        return f"{emoji} {action} 电影 《{title}》"
    
    def build_content(self, event_record: Dict[str, Any]) -> str:
        """构建电影通知内容

        Args:
            event_record: 标准化的事件记录，包含完整的电影信息
        """
        event_type = event_record.get("event_type", "")

        # 第一行：播放进度（播放事件）或入库进度（入库事件）
        if event_type.startswith("playback."):
            line1 = self._build_playback_progress(event_record)
        elif event_type == "library.new":
            line1 = self._build_library_progress(event_record)
        else:
            line1 = ""

        # 第二行：关键属性（年份、质量、评分、服务器）
        line2 = self._build_line1(event_record)

        # 第三行：简介
        line3 = self._build_line2(event_record)

        # 第四行：时间
        line4 = self._build_line3(event_record)

        return "\n".join(filter(None, [line1, line2, line3, line4]))
    
    def _get_event_meta(self, event_type: str) -> tuple:
        """获取事件的 emoji 和名称"""
        return self.EVENT_META.get(event_type, ("📌", "通知"))
    
    def _build_line1(self, event_record: Dict[str, Any]) -> str:
        """构建第一行：年份、质量、评分、服务器"""
        parts = []
        
        # 年份和地区：剧集优先用该季实际首播年份（而非整剧首播年）
        year = event_record.get("season_year") or event_record.get("year")
        region = event_record.get("region_category", "")
        if year and region:
            parts.append(f"📅年份：{year} ｜ {region}")
        elif year:
            parts.append(f"📅年份：{year}")
        
        # 质量
        quality = self._build_quality(event_record)
        if quality:
            parts.append(f"🎬质量：{quality}")
        
        # 评分（使用 tmdb_vote 字段）
        score = event_record.get("tmdb_vote")
        if score:
            parts.append(f"⭐评分：{score}")
        
        # 服务器和用户名
        server = event_record.get("server_name", "")
        user_name = event_record.get("user_name", "")
        if server:
            if user_name:
                parts.append(f"🖥️服务器：{server} | {user_name}")
            else:
                parts.append(f"🖥️服务器：{server}")

        return "  ".join(filter(None, parts))
    
    def _build_quality(self, event_record: Dict[str, Any]) -> str:
        """构建质量信息（使用 media_profile）"""
        media_profile = event_record.get("media_profile", {})

        quality_parts = []
        if media_profile:
            resolution = media_profile.get("resolution", "")
            hdr = media_profile.get("hdr", "")

            if resolution:
                quality_parts.append(resolution)
            if hdr:
                quality_parts.append(hdr)

        return " | ".join(quality_parts) if quality_parts else ""
    
    def _build_playback_progress(self, event_record: Dict[str, Any]) -> str:
        """构建播放进度行（仅播放事件）"""
        event_type = event_record.get("event_type", "")

        # 只有播放事件才显示进度
        if not event_type.startswith("playback."):
            return ""

        pos = event_record.get("play_position")
        dur = event_record.get("play_duration")

        if pos is not None and dur and dur > 0:
            from datetime import timedelta
            pos_sec = pos // 10000000
            dur_sec = dur // 10000000
            pos_str = str(timedelta(seconds=pos_sec))[2:7]
            dur_str = str(timedelta(seconds=dur_sec))[2:7]
            pct = int((pos_sec / dur_sec) * 100) if dur_sec > 0 else 0
            return f"⏱️进度：{pos_str}/{dur_str} ({pct}%)"
        return ""

    def _build_library_progress(self, event_record: Dict[str, Any]) -> str:
        """构建入库进度行（仅入库事件且为剧集类型）

        进度分母统一使用「该季总集数」，绝不回退到整剧总集数，
        避免标题是 S02 却显示整剧 53 集这种错位。
        """
        media_type = event_record.get("media_type", "")

        # 只有剧集类型才显示进度
        if media_type not in ("Series", "Episode"):
            return ""

        # 支持 total_episodes 和 episode_count 两种字段名（整剧，仅最后兜底用）
        total_episodes = event_record.get("total_episodes") or event_record.get("episode_count")
        tv_status = event_record.get("tv_status", "")

        status_cn = ""
        if tv_status == "Ended":
            status_cn = "【已完结】"
        elif tv_status == "Returning Series":
            status_cn = "【连载中】"
        elif tv_status == "Canceled":
            status_cn = "【已取消】"
        elif tv_status == "In Production":
            status_cn = "【制作中】"

        # 该季理论总集数（来自 TMDB 按季查询）；整剧总集数仅作最后兜底
        season_total = event_record.get("season_total_episodes")
        # 本次入库的集数信息
        all_episodes = event_record.get("all_episodes", []) or []
        episode_number = event_record.get("episode_number")
        # 媒体库真实已有集数（来自 Emby 查询）
        owned = event_record.get("library_owned_episodes")

        def _fmt(cur: int, total: int) -> str:
            remaining = total - cur
            if remaining > 0:
                return f"📊进度：已入库{cur}/{total}集  还剩{remaining}集{status_cn}"
            return f"📊进度：已入库{cur}/{total}集  ✅已完结"

        # 1) 媒体库真实已有 / 该季总（最佳，分子分母都精准）
        if owned is not None and season_total:
            return _fmt(owned, season_total)

        # 2) 有该季总，但 Emby 查询失败（无 owned）→ 用本次入库集数作为分子
        if season_total:
            if all_episodes:
                cur = len(all_episodes) if len(all_episodes) > 1 else all_episodes[0]
                return _fmt(cur, season_total)
            if episode_number:
                return _fmt(episode_number, season_total)

        # 3) 连该季总都没有（TMDB 按季失败）→ 回退整剧总集数兜底
        if not total_episodes:
            if media_type == "Episode" and episode_number:
                return f"📺第 {episode_number} 集"
            return ""

        if all_episodes:
            cur = len(all_episodes) if len(all_episodes) > 1 else all_episodes[0]
            return _fmt(cur, total_episodes)
        if episode_number:
            return _fmt(episode_number, total_episodes)
        return ""
    
    def _build_line2(self, event_record: Dict[str, Any]) -> str:
        """构建第二行：简介"""
        overview = event_record.get("overview", "")
        if overview:
            short = overview[:60] + "..." if len(overview) > 60 else overview
            return f"简介：{short}"
        return "简介：-"
    
    def _build_line3(self, event_record: Dict[str, Any]) -> str:
        """构建第三行：时间"""
        timestamp = event_record.get("timestamp", "")
        time_str = self._format_timestamp(timestamp)
        if time_str:
            return f"时间：{time_str}"
        return ""
    
    def _format_timestamp(self, timestamp: str) -> Optional[str]:
        """将 ISO 8601 格式的时间戳转换为北京时间字符串"""
        if not timestamp:
            return None
        
        try:
            ts = timestamp.replace('Z', '+00:00')
            
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                match = re.match(r'(.+\.\d{6})\d*(\+\d{2}:\d{2}|\-\d{2}:\d{2}|Z)?$', ts)
                if match:
                    ts = match.group(1) + (match.group(2) if match.group(2) else '')
                    dt = datetime.fromisoformat(ts)
                else:
                    dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            beijing = timezone(timedelta(hours=8))
            return dt.astimezone(beijing).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
