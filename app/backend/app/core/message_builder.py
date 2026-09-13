"""
消息构建模块 - 新版本

从标准化的 event_record 渲染各渠道消息
每个渠道可以有自己的渲染方式

数据流：
  events.json (标准化事件数据)
    ↓
  渲染函数（桌面端/移动端/企业微信等）
    ↓
  desktop.json / wecom.json / 发送
"""
from typing import Dict, Any, Optional
from app.core.event_formatter import build_event_title, build_event_content


def build_wecom_news_message(event_record: Dict[str, Any], 
                             title: Optional[str] = None,
                             content: Optional[str] = None) -> Dict[str, Any]:
    """
    构建企业微信图文消息 (news 类型)
    
    从 event_record 渲染标题和内容
    
    Args:
        event_record: 标准化的事件记录
        title: 可选，预计算的标题（避免重复计算）
        content: 可选，预计算的内容（避免重复计算）
    
    Returns:
        企业微信 news 格式消息
    """
    # 如果提供了预计算的值，直接使用；否则重新计算
    if title is None:
        title = build_event_title(event_record)
    if content is None:
        content = build_event_content(event_record)
    
    # 获取封面图（微信通知优先级：）
    # - 电影/剧集：backdrop > poster_url
    # - 单集：poster_url
    media_type = event_record.get("media_type", "")
    if media_type == "Episode":
        poster = event_record.get("poster_url", "")
    else:
        poster = event_record.get("backdrop", "") or event_record.get("poster_url", "")
    
    # 构建跳转链接（优先级：豆瓣 > TMDB > IMDB）
    url = ""
    tmdb_id = event_record.get("tmdb_id", "")
    imdb_id = event_record.get("imdb_id", "")
    douban_id = event_record.get("douban_id", "")
    
    if douban_id:
        url = f"https://movie.douban.com/subject/{douban_id}/"
    elif tmdb_id:
        media_type_path = "tv" if media_type == "Series" else "movie"
        url = f"https://www.themoviedb.org/{media_type_path}/{tmdb_id}"
    elif imdb_id:
        url = f"https://www.imdb.com/title/{imdb_id}/"
    
    return {
        "msgtype": "news",
        "news": {
            "articles": [{
                "title": title,
                "description": content,
                "picurl": poster,
                "url": url
            }]
        }
    }


def build_wecom_markdown_message(event_record: Dict[str, Any],
                                  title: Optional[str] = None,
                                  content: Optional[str] = None) -> Dict[str, Any]:
    """
    构建企业微信 Markdown 消息
    
    适用于测试通知等简单场景
    
    Args:
        event_record: 标准化的事件记录
        title: 可选，预计算的标题（避免重复计算）
        content: 可选，预计算的内容（避免重复计算）
    
    Returns:
        企业微信 markdown 格式消息
    """
    # 如果提供了预计算的值，直接使用；否则重新计算
    if title is None:
        title = build_event_title(event_record)
    if content is None:
        content = build_event_content(event_record)
    
    # 构建 Markdown 内容
    markdown_content = f"## {title}\n\n{content}"
    
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content
        }
    }


def build_notification_message(event_record: Dict[str, Any], 
                               msg_type: str = "news",
                               title: Optional[str] = None,
                               content: Optional[str] = None) -> Dict[str, Any]:
    """
    构建通知消息的通用接口
    
    Args:
        event_record: 标准化的事件记录
        msg_type: 消息类型，news 或 markdown
        title: 可选，预计算的标题（避免重复计算）
        content: 可选，预计算的内容（避免重复计算）
    
    Returns:
        对应格式的消息字典
    """
    if msg_type == "markdown":
        return build_wecom_markdown_message(event_record, title=title, content=content)
    
    # 默认使用 news 格式
    return build_wecom_news_message(event_record, title=title, content=content)


def get_message_article(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    从消息中提取文章/内容信息
    
    用于获取标题和描述，更新事件记录
    """
    msg_type = msg.get("msgtype", "news")
    
    if msg_type == "markdown":
        markdown_content = msg.get("markdown", {}).get("content", "")
        lines = markdown_content.split('\n')
        title = lines[0] if lines else ""
        title = title.replace('## ', '').replace('**', '').strip()
        return {
            "title": title,
            "description": markdown_content,
            "url": "",
            "picurl": ""
        }
    
    # news 类型
    articles = msg.get("news", {}).get("articles", [{}])
    return articles[0] if articles else {}


# ==================== 桌面端和移动端渲染 ====================

def render_desktop_message(event_record: Dict[str, Any], save: bool = True) -> Dict[str, Any]:
    """
    渲染桌面端通知消息
    
    桌面端特点：
    - 内容可以更详细
    - 可以显示更多信息
    
    Args:
        event_record: 标准化的事件记录
        save: 是否保存到文件（保留参数兼容旧代码，实际不再使用）
    
    Returns:
        桌面端消息格式
    """
    title = build_event_title(event_record)
    content = build_event_content(event_record)

    # 桌面端固定使用剧集封面（series_poster_url）
    poster = event_record.get("series_poster_url", "")

    message = {
        "title": title,
        "content": content,
        "poster": poster,
        "backdrop": event_record.get("backdrop", ""),
        "event_type": event_record.get("event_type", ""),
        "media_type": event_record.get("media_type", ""),
        "platform": "desktop",
        "tmdb_url": event_record.get("tmdb_url", ""),
        "year": event_record.get("year"),
        "overview": event_record.get("overview", ""),
    }
    
    return message
