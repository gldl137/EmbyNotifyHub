"""
模板注册表
根据事件类型和媒体类型路由到对应的模板
"""
from typing import Dict, Any, Tuple
from app.templates.base import NotificationTemplate
from app.templates.movie import MovieTemplate


# 模板注册表
# key: (event_type, media_type) -> template_class
TEMPLATE_REGISTRY: Dict[Tuple[str, str], Any] = {
    # 电影事件 - 所有电影事件使用统一格式
    ("library.new", "Movie"): MovieTemplate,
    ("deep.delete", "Movie"): MovieTemplate,
    ("item.rate", "Movie"): MovieTemplate,
    ("playback.start", "Movie"): MovieTemplate,
    ("playback.stop", "Movie"): MovieTemplate,
    # 剧集事件 - 播放事件和入库事件使用统一格式
    ("library.new", "Episode"): MovieTemplate,
    ("playback.start", "Episode"): MovieTemplate,
    ("playback.stop", "Episode"): MovieTemplate,
}


def get_template(event_type: str, media_type: str) -> NotificationTemplate:
    """
    根据事件类型和媒体类型获取对应的模板
    
    Args:
        event_type: 事件类型，如 library.new, playback.start
        media_type: 媒体类型，如 Movie, Series, Episode, Audio
    
    Returns:
        对应的模板实例
    """
    key = (event_type, media_type)
    
    # 查找对应模板
    template_class = TEMPLATE_REGISTRY.get(key)
    
    if template_class:
        return template_class()
    
    # 没有找到对应模板，返回通用模板
    return GenericTemplate()


class GenericTemplate(NotificationTemplate):
    """通用模板 - 当没有匹配到特定模板时使用
    
    只使用标准化的 event_record 字段
    """
    
    def build_title(self, event_record: Dict[str, Any]) -> str:
        event_type = event_record.get("event_type", "")
        media_type = event_record.get("media_type", "")
        title = event_record.get("title", "")
        
        # 根据媒体类型添加标识
        type_name = ""
        if media_type == "Movie":
            type_name = "电影"
        elif media_type in ("Episode", "Series"):
            type_name = "剧集"
        elif media_type == "Audio":
            type_name = "音乐"
        
        if type_name:
            return f"📌 {event_type} {type_name} 《{title}》"
        return f"📌 {event_type} 《{title}》"
    
    def build_content(self, event_record: Dict[str, Any]) -> str:
        # 第一行：播放进度（如果是播放事件）
        line1 = ""
        event_type = event_record.get("event_type", "")
        if event_type.startswith("playback."):
            pos = event_record.get("play_position")
            dur = event_record.get("play_duration")
            if pos is not None and dur and dur > 0:
                from datetime import timedelta
                pos_sec = pos // 10000000
                dur_sec = dur // 10000000
                pos_str = str(timedelta(seconds=pos_sec))[2:7]
                dur_str = str(timedelta(seconds=dur_sec))[2:7]
                pct = int((pos_sec / dur_sec) * 100) if dur_sec > 0 else 0
                line1 = f"⏱️进度：{pos_str}/{dur_str} ({pct}%)"
        
        # 第二行：基础信息
        parts = []
        year = event_record.get("year")
        if year:
            parts.append(f"📅年份：{year}")
        
        server = event_record.get("server_name", "")
        user_name = event_record.get("user_name", "")
        if server:
            if user_name:
                parts.append(f"🖥️服务器：{server} | {user_name}")
            else:
                parts.append(f"🖥️服务器：{server}")
        line2 = "  ".join(parts) if parts else ""
        
        # 第三行：简介
        overview = event_record.get("overview", "")
        line3 = f"简介：{overview[:60]}..." if len(overview) > 60 else f"简介：{overview}" if overview else "简介：-"
        
        # 第四行：时间
        timestamp = event_record.get("timestamp", "")
        time_str = self.format_timestamp(timestamp)
        line4 = f"时间：{time_str}" if time_str else ""
        
        return "\n".join(filter(None, [line1, line2, line3, line4]))
