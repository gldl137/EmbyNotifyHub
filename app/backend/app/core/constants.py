"""
核心常量模块 - 事件定义和分类管理

架构设计：
- 一级分类：按照 Emby 官方分类
- 二级动作：细分具体动作（如 item.rate 细分为 favorite/unfavorite/rate）
- 统一事件定义：EVENT_MAP 集中管理所有事件属性

事件来源标记：
- source: "emby" | "external" - 事件来源
- plugin: "none" | "shenyi" - 是否来自第三方插件
"""


# ============================== 一级分类 ==============================

class EventCategory:
    """事件一级分类（官方分类）"""
    SERVER = "server"           # 服务器
    LIBRARY = "library"         # 媒体库
    PLAYBACK = "playback"       # 播放
    USER = "user"               # 用户
    DEVICE = "device"           # 设备
    TASK = "task"               # 计划任务
    PLUGIN = "plugin"           # 插件
    TV = "livetv"               # 电视直播
    EXTERNAL = "external"       # 外部
    ASSISTANT = "assistant"     # 神医助手


# 分类显示名称映射
CATEGORY_NAME_MAP = {
    EventCategory.SERVER: "服务器",
    EventCategory.LIBRARY: "媒体库",
    EventCategory.PLAYBACK: "播放",
    EventCategory.USER: "用户",
    EventCategory.DEVICE: "设备",
    EventCategory.TASK: "计划任务",
    EventCategory.PLUGIN: "插件",
    EventCategory.TV: "电视直播",
    EventCategory.EXTERNAL: "外部",
    EventCategory.ASSISTANT: "神医助手",
}


# ============================== 统一事件定义表 ==============================

EVENT_MAP = {
    # ========== 播放 ==========
    "playback.start": {
        "category": EventCategory.PLAYBACK,
        "name": "开始播放",
        "emoji": "▶️",
        "source": "emby",
        "plugin": "none",
    },
    "playback.pause": {
        "category": EventCategory.PLAYBACK,
        "name": "暂停播放",
        "emoji": "⏸️",
        "source": "emby",
        "plugin": "none",
    },
    "playback.unpause": {
        "category": EventCategory.PLAYBACK,
        "name": "继续播放",
        "emoji": "⏯️",
        "source": "emby",
        "plugin": "none",
    },
    "playback.stop": {
        "category": EventCategory.PLAYBACK,
        "name": "停止播放",
        "emoji": "⏹️",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 媒体库 ==========
    "library.new": {
        "category": EventCategory.LIBRARY,
        "name": "入库",
        "emoji": "🎬",
        "source": "emby",
        "plugin": "none",
    },
    "library.new.music": {
        "category": EventCategory.LIBRARY,
        "name": "音乐入库",
        "emoji": "🎵",
        "source": "emby",
        "plugin": "none",
    },
    "library.deleted": {
        "category": EventCategory.LIBRARY,
        "name": "删除媒体",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "none",
    },
    "media.deepdelete": {
        "category": EventCategory.LIBRARY,
        "name": "深度删除",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "none",
    },
    "media.metadataupdate": {
        "category": EventCategory.ASSISTANT,
        "name": "元数据更新",
        "emoji": "📝",
        "source": "emby",
        "plugin": "shenyi",
    },
    "media.imageupdate": {
        "category": EventCategory.ASSISTANT,
        "name": "图像更新",
        "emoji": "🖼️",
        "source": "emby",
        "plugin": "shenyi",
    },

    # ========== 用户 ==========
    "item.rate": {
        "category": EventCategory.USER,
        "name": "收藏/评分",
        "emoji": "⭐",
        "source": "emby",
        "plugin": "none",
        "needs_resolve": True,  # 需要二次解析动作
    },
    "item.markplayed": {
        "category": EventCategory.USER,
        "name": "标记已播放",
        "emoji": "✅",
        "source": "emby",
        "plugin": "none",
        "action": "played",  # 二级动作
    },
    "item.markunplayed": {
        "category": EventCategory.USER,
        "name": "标记未播放",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
        "action": "unplayed",  # 二级动作
    },
    "user.authenticated": {
        "category": EventCategory.USER,
        "name": "登录成功",
        "emoji": "🔓",
        "source": "emby",
        "plugin": "none",
        "action": "login_success",
    },
    "user.authenticationfailed": {
        "category": EventCategory.USER,
        "name": "登录失败",
        "emoji": "⚠️",
        "source": "emby",
        "plugin": "none",
        "action": "login_failed",
    },
    "user.locked": {
        "category": EventCategory.USER,
        "name": "用户已锁定",
        "emoji": "🔒",
        "source": "emby",
        "plugin": "none",
        "action": "locked",
    },
    "user.created": {
        "category": EventCategory.USER,
        "name": "用户已创建",
        "emoji": "👤",
        "source": "emby",
        "plugin": "none",
        "action": "created",
    },
    "user.deleted": {
        "category": EventCategory.USER,
        "name": "用户已删除",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "none",
        "action": "deleted",
    },
    "user.passwordchanged": {
        "category": EventCategory.USER,
        "name": "密码已更改",
        "emoji": "🔑",
        "source": "emby",
        "plugin": "none",
        "action": "password_changed",
    },
    "user.policyupdated": {
        "category": EventCategory.USER,
        "name": "用户政策已更新",
        "emoji": "📋",
        "source": "emby",
        "plugin": "none",
        "action": "policy_updated",
    },

    # ========== 服务器 ==========
    "system.serverstartup": {
        "category": EventCategory.SERVER,
        "name": "服务器启动",
        "emoji": "🚀",
        "source": "emby",
        "plugin": "none",
    },
    "system.servershutdown": {
        "category": EventCategory.SERVER,
        "name": "服务器关闭",
        "emoji": "🛑",
        "source": "emby",
        "plugin": "none",
    },
    "server.restart": {
        "category": EventCategory.SERVER,
        "name": "服务器重启",
        "emoji": "🔄",
        "source": "emby",
        "plugin": "none",
    },
    "server.restartrequired": {
        "category": EventCategory.SERVER,
        "name": "服务器需要重启",
        "emoji": "⚠️",
        "source": "emby",
        "plugin": "none",
    },
    "server.updateavailable": {
        "category": EventCategory.SERVER,
        "name": "有可用更新",
        "emoji": "📦",
        "source": "emby",
        "plugin": "none",
    },
    "server.updated": {
        "category": EventCategory.SERVER,
        "name": "服务器已更新",
        "emoji": "✅",
        "source": "emby",
        "plugin": "none",
    },
    "system.maintenancemode.enter": {
        "category": EventCategory.SERVER,
        "name": "进入维护模式",
        "emoji": "🔧",
        "source": "emby",
        "plugin": "none",
    },
    "system.maintenancemode.exit": {
        "category": EventCategory.SERVER,
        "name": "退出维护模式",
        "emoji": "🔓",
        "source": "emby",
        "plugin": "none",
    },
    "backup.completed": {
        "category": EventCategory.SERVER,
        "name": "备份已完成",
        "emoji": "💾",
        "source": "emby",
        "plugin": "none",
    },
    "backup.failed": {
        "category": EventCategory.SERVER,
        "name": "备份失败",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 计划任务 ==========
    "scheduledtasks.completed": {
        "category": EventCategory.TASK,
        "name": "计划任务完成",
        "emoji": "✅",
        "source": "emby",
        "plugin": "none",
    },
    "scheduledtasks.failed": {
        "category": EventCategory.TASK,
        "name": "计划任务失败",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 插件 ==========
    "plugin.installed": {
        "category": EventCategory.PLUGIN,
        "name": "插件已安装",
        "emoji": "📦",
        "source": "emby",
        "plugin": "none",
    },
    "plugin.installfailed": {
        "category": EventCategory.PLUGIN,
        "name": "插件安装失败",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
    },
    "plugin.uninstalled": {
        "category": EventCategory.PLUGIN,
        "name": "插件已卸载",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "none",
    },
    "plugin.updated": {
        "category": EventCategory.PLUGIN,
        "name": "插件已更新",
        "emoji": "⬆️",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 电视直播 ==========
    "livetv.recording.scheduled": {
        "category": EventCategory.TV,
        "name": "已计划录制",
        "emoji": "📅",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.cancelled": {
        "category": EventCategory.TV,
        "name": "已取消录制",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.series.scheduled": {
        "category": EventCategory.TV,
        "name": "已计划剧集录制",
        "emoji": "📺",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.series.cancelled": {
        "category": EventCategory.TV,
        "name": "已取消剧集录制",
        "emoji": "❌",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.started": {
        "category": EventCategory.TV,
        "name": "已开始录制",
        "emoji": "🔴",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.ended": {
        "category": EventCategory.TV,
        "name": "已结束录制",
        "emoji": "⏹️",
        "source": "emby",
        "plugin": "none",
    },
    "livetv.recording.error": {
        "category": EventCategory.TV,
        "name": "录制出错",
        "emoji": "⚠️",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 设备 ==========
    "device.cameraimageuploaded": {
        "category": EventCategory.DEVICE,
        "name": "相机图像已上传",
        "emoji": "📷",
        "source": "emby",
        "plugin": "none",
    },

    # ========== 外部 ==========
    "external.notification": {
        "category": EventCategory.EXTERNAL,
        "name": "外部通知",
        "emoji": "📨",
        "source": "external",
        "plugin": "none",
    },

    # ========== 神医助手 ==========
    "collection.items.added": {
        "category": EventCategory.ASSISTANT,
        "name": "合集项目已添加",
        "emoji": "📂",
        "source": "emby",
        "plugin": "shenyi",
    },
    "collection.items.removed": {
        "category": EventCategory.ASSISTANT,
        "name": "合集项目已移除",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "shenyi",
    },
    "assistant.favorite.updated": {
        "category": EventCategory.ASSISTANT,
        "name": "最爱有更新",
        "emoji": "⭐",
        "source": "emby",
        "plugin": "shenyi",
    },
    "assistant.intro.updated": {
        "category": EventCategory.ASSISTANT,
        "name": "片头片尾已更新",
        "emoji": "🎬",
        "source": "emby",
        "plugin": "shenyi",
    },
    "assistant.collection.added": {
        "category": EventCategory.ASSISTANT,
        "name": "合集项目已添加",
        "emoji": "📂",
        "source": "emby",
        "plugin": "shenyi",
    },
    "assistant.collection.removed": {
        "category": EventCategory.ASSISTANT,
        "name": "合集项目已移除",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "shenyi",
    },
    "deep.delete": {
        "category": EventCategory.ASSISTANT,
        "name": "媒体深度删除",
        "emoji": "🗑️",
        "source": "emby",
        "plugin": "shenyi",
        "action": "deep_delete",
    },

    # ========== IntroSkip 插件 ==========
    "introskip.update": {
        "category": EventCategory.PLUGIN,
        "name": "片头片尾标记更新",
        "emoji": "⏭️",
        "source": "emby",
        "plugin": "introskip",
    },

    # ========== 测试 ==========
    "system.webhooktest": {
        "category": None,  # 测试事件不归类
        "name": "Webhook 测试",
        "emoji": "🧪",
        "source": "emby",
        "plugin": "none",
    },
    "system.notificationtest": {
        "category": None,
        "name": "通知测试",
        "emoji": "🧪",
        "source": "emby",
        "plugin": "none",
    },
}


# ============================== 二级动作系统 ==============================

def resolve_action(event_type: str, data: dict) -> str:
    """
    解析二级动作

    某些事件（如 item.rate）需要根据数据细分具体动作
    支持原始数据结构（Item.UserData.IsFavorite）和已解析数据结构（is_favorite）

    Args:
        event_type: 事件类型
        data: 原始事件数据或已解析的事件数据

    Returns:
        动作标识符
    """
    if event_type == "item.rate":
        is_favorite = None

        # 优先检查已解析的 is_favorite 字段（兼容 event_models.py 的输出）
        if "is_favorite" in data:
            is_favorite = data.get("is_favorite")

        # 如果 is_favorite 为 None，尝试从原始数据结构提取
        if is_favorite is None:
            item = data.get("Item", {})
            user_data = item.get("UserData", {})
            if "IsFavorite" in user_data:
                is_favorite = user_data.get("IsFavorite")

        # item.rate 事件只有两种操作：添加收藏 或 取消收藏
        if is_favorite is True:
            return "favorite"  # 添加收藏
        else:
            return "unfavorite"  # 取消收藏（包括 IsFavorite: false 的情况）
    
    # 如果事件定义中有预定义的动作，直接返回
    event_def = EVENT_MAP.get(event_type, {})
    if "action" in event_def:
        return event_def["action"]
    
    # 默认返回事件类型
    return event_type


def get_event_info(event_type: str, data: dict = None) -> dict:
    """
    获取事件的完整信息

    Args:
        event_type: 事件类型
        data: 原始事件数据（用于解析二级动作）

    Returns:
        {
            "event": 原始事件名,
            "category": 一级分类,
            "action": 二级动作,
            "name": 显示名称,
            "emoji": Emoji,
            "source": 来源,
            "plugin": 插件,
        }
    """
    event_def = EVENT_MAP.get(event_type, {})

    # 解析二级动作（优先使用已解析的 action 字段）
    if data and "action" in data and data["action"]:
        action = data["action"]
    else:
        action = resolve_action(event_type, data or {}) if data else event_def.get("action", event_type)

    # 根据动作获取更精确的显示名称
    name = event_def.get("name", event_type)
    if event_type == "item.rate":
        if action == "favorite":
            name = "添加收藏"
        else:
            name = "取消收藏"

    return {
        "event": event_type,
        "category": event_def.get("category"),
        "action": action,
        "name": name,
        "emoji": event_def.get("emoji", "📌"),
        "source": event_def.get("source", "emby"),
        "plugin": event_def.get("plugin", "none"),
    }


# ============================== 辅助函数 ==============================

def get_events_by_category(category: str) -> list:
    """获取指定分类的所有事件类型"""
    return [event for event, info in EVENT_MAP.items() if info.get("category") == category]


def get_all_categories() -> list:
    """获取所有分类列表"""
    categories = set()
    for info in EVENT_MAP.values():
        cat = info.get("category")
        if cat:
            categories.add(cat)
    return sorted(list(categories))


# ============================== 计划任务名称翻译映射 ==============================

SCHEDULED_TASK_NAME_MAP = {
    # ==================== Application ====================
    "Emby Server Backup": "Emby 服务器备份",
    "Rotate log file": "轮换日志文件",
    # ==================== Chapter API ====================
    "Update Intro DB": "更新片头数据库",
    # ==================== Database ====================
    "Vacuum Database": "清理数据库",
    # ==================== Downloads & Conversions ====================
    "Convert media": "转换媒体",
    "Transfer media": "传输媒体",
    # ==================== Episode Refresh ====================
    "Refresh Recently Aired Episodes": "刷新最近播出剧集",
    # ==================== Library ====================
    "Detect Episode Intros": "检测剧集片头",
    "Download subtitles": "下载字幕",
    "Scan Metadata Folder": "扫描元数据文件夹",
    "Scan media library": "扫描媒体库",
    "Video preview thumbnail extraction": "视频预览缩略图提取",
    # ==================== Live TV ====================
    "Refresh Guide": "刷新节目指南",
    # ==================== 神医助手 💎 PRO ====================
    "Build Douban Cache": "构建豆瓣缓存",
    "Extract Intro Fingerprint": "提取片头声纹",
    "Extract MediaInfo": "提取媒体信息",
    "Extract Video Thumbnail": "提取视频缩略图",
    "Merge Multi Versions": "合并多版本",
    "Persist MediaInfo": "持久化媒体信息",
    "Refresh Chinese Actor": "刷新中文演员信息",
    "Refresh Episode": "刷新剧集",
    "Scan External Tracks": "扫描外部音轨",
    "Update Plugin": "更新插件",
    # ==================== 其他常用任务 ====================
    "Download OCR Data": "下载 OCR 数据",
    "Download Subtitles": "下载字幕",
    "Refresh Media Library": "刷新媒体库",
    "Scan Media Library": "扫描媒体库",
    "Clean Transcode Cache": "清理转码缓存",
    "Clean Log Directory": "清理日志目录",
    "Update Plugins": "更新插件",
    "Check for application updates": "检查应用更新",
}


# ============================== 计划任务功能描述映射 ==============================

SCHEDULED_TASK_DESC_MAP = {
    # ==================== Application ====================
    "Emby Server Backup": "执行 Emby Backup 插件的定时备份任务",
    "Rotate log file": "将日志写入新文件，帮助减小日志文件大小",
    # ==================== Chapter API ====================
    "Update Intro DB": "下载并重新加载最新的片头数据库",
    # ==================== Database ====================
    "Vacuum Database": "在下次服务器启动时执行数据库清理",
    # ==================== Downloads & Conversions ====================
    "Convert media": "执行使用媒体转换功能创建的转换任务，以及需要转换为兼容格式的下载任务",
    "Transfer media": "将已完成的转换传输到最终目标位置，供下载和转换功能使用",
    # ==================== Episode Refresh ====================
    "Refresh Recently Aired Episodes": "刷新最近播出的剧集，填补缺失或不完整的元数据",
    # ==================== Library ====================
    "Detect Episode Intros": "检测已启用剧集的片头开始和结束时间",
    "Download subtitles": "如果已在 Emby 媒体库设置中启用自动字幕下载，则在互联网上搜索缺失的字幕",
    "Scan Metadata Folder": "如果您直接修改了 Emby Server 内部元数据文件夹的内容，请运行此任务以便 Emby Server 发现更改",
    "Scan media library": "扫描媒体库以检查新的和已更新的文件",
    "Video preview thumbnail extraction": "为视频创建预览缩略图",
    # ==================== Live TV ====================
    "Refresh Guide": "从直播电视服务下载频道信息",
    # ==================== 神医助手 💎 PRO ====================
    "Build Douban Cache": "构建豆瓣元数据缓存，用于辅助刮削",
    "Extract Intro Fingerprint": "剧集片头声纹提取与片头检测",
    "Extract MediaInfo": "提取视频和音频的媒体信息，以及视频截图",
    "Extract Video Thumbnail": "提取视频预览缩略图和章节图",
    "Merge Multi Versions": "按偏好库内或跨库合并电影和电视节目，扫库后自动运行",
    "Persist MediaInfo": "导出媒体信息、章节片头片尾标记至 JSON 文件",
    "Refresh Chinese Actor": "刷新和修复演员信息，尽可能获取中文及头像",
    "Refresh Episode": "按偏好刷新剧集缺失的元数据和图片",
    "Scan External Tracks": "单独扫描视频的外挂字幕和音轨，更新至媒体信息",
    "Update Plugin": "更新本插件至最新版",
    # ==================== 其他常用任务 ====================
    "Download OCR Data": "下载 OCR 识别所需的数据文件",
    "Download Subtitles": "自动搜索并下载缺失的字幕文件",
    "Refresh Media Library": "刷新媒体库以获取最新元数据",
    "Scan Media Library": "扫描媒体库以检查新的和已更新的文件",
    "Clean Transcode Cache": "清理转码过程中产生的临时缓存文件",
    "Clean Log Directory": "清理旧的日志文件以释放磁盘空间",
    "Update Plugins": "检查并更新所有已安装的插件",
    "Check for application updates": "检查是否有新的 Emby Server 版本可用",
}


# ============================== 媒体类型映射 ==============================

MEDIA_TYPE_MAP = {
    "Movie": "电影",
    "Series": "剧集",
    "Episode": "单集",
    "Season": "季",
    "Audio": "音乐",
    "MusicAlbum": "专辑",
    "MusicArtist": "艺术家",
    "BoxSet": "合集",
    "Video": "视频",
    "Trailer": "预告片",
}


# ============================== 默认配置 ==============================

# 默认允许的事件类型
DEFAULT_ALLOW_EVENTS = [
    "library.new",
    "playback.start",
    "playback.stop",
    "system.webhooktest",
    "system.notificationtest",
]

# 默认允许的媒体类型
DEFAULT_ALLOW_MEDIA_TYPES = [
    "Movie",
    "Series",
    "Episode",
    "Audio",
]

# 按分类分组的默认允许事件
DEFAULT_ALLOW_EVENTS_BY_CATEGORY = {
    EventCategory.SERVER: [],
    EventCategory.LIBRARY: ["library.new"],
    EventCategory.PLAYBACK: ["playback.start", "playback.stop"],
    EventCategory.USER: [],
    EventCategory.DEVICE: [],
    EventCategory.TASK: [],
    EventCategory.PLUGIN: [],
    EventCategory.TV: [],
    EventCategory.EXTERNAL: [],
    EventCategory.ASSISTANT: [],
}


# ============================== 向后兼容 ==============================

# 为兼容旧代码，保留这些映射（但推荐使用 EVENT_MAP 和 get_event_info）

EVENT_EMOJI_MAP = {k: v.get("emoji", "📌") for k, v in EVENT_MAP.items()}
EVENT_DESC_MAP = {k: v.get("name", k) for k, v in EVENT_MAP.items()}
EVENT_CATEGORY_MAP = {k: v.get("category") for k, v in EVENT_MAP.items() if v.get("category")}
