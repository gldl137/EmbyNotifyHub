"""
配置管理模块 - 处理 config.json 的读写操作
只保留三个配置：Emby服务器、TMDB、通知渠道
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 配置文件路径 - 支持环境变量或自动检测项目根目录
if os.getenv("CONFIG_DIR"):
    CONFIG_DIR = Path(os.getenv("CONFIG_DIR"))
else:
    # 自动检测项目根目录 (backend/app/services/config_manager.py -> 项目根目录)
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    CONFIG_DIR = BASE_DIR / "data"

CONFIG_FILE = CONFIG_DIR / "config.json"

# 输出配置文件路径
logger.debug(f"配置文件路径: {CONFIG_FILE}")


class EmbyServerConfig(BaseModel):
    """单个 Emby 服务器配置"""
    id: str = ""  # 唯一标识
    name: str = ""  # 服务器名称
    base_url: str = ""  # 服务器地址（内网）
    external_url: str = ""  # 外网访问地址（用于封面图片）
    api_key: str = ""  # API Key
    enabled: bool = True  # 是否启用
    server_id: str = ""  # Emby ServerId (从 Emby 系统信息中获取)


class EmbyConfig(BaseModel):
    """Emby 服务器配置（支持多个服务器）"""
    servers: list = Field(default_factory=list)  # 服务器列表
    # 兼容旧配置
    base_url: str = ""
    api_key: str = ""


class TMDBConfig(BaseModel):
    """TMDB 配置"""
    api_key: str = ""
    # 代理设置（用于访问 TMDB）
    proxy_enabled: bool = False
    proxy_url: str = ""  # 例如: http://127.0.0.1:7890


# 默认允许的事件类型（用于通知渠道）
DEFAULT_CHANNEL_EVENTS = [
    "library.new",
    "library.new.music",
    "playback.start",
    "playback.stop",
    "item.rate",  # 评分/收藏事件
    "item.unrate",  # 取消评分事件
    "system.webhooktest",
    "system.notificationtest",
]


class WeComWebhookConfig(BaseModel):
    """企业微信群机器人配置"""
    enabled: bool = False
    webhook_key: str = ""
    bot_name: str = "Emby 通知助手"
    allowed_events: list = Field(default_factory=lambda: DEFAULT_CHANNEL_EVENTS.copy())
    allowed_servers: list = Field(default_factory=list)  # Emby 服务器 id 列表，为空=全部


class CustomNotifyConfig(BaseModel):
    """自定义通知配置（支持多个通知）"""
    id: str = ""  # 唯一标识
    name: str = ""  # 通知名称
    enabled: bool = True
    channel_type: str = "wecom_app"  # wecom_webhook 或 wecom_app
    # 企业微信应用配置
    corp_id: str = ""
    agent_id: str = ""
    secret: str = ""
    to_user: str = "@all"
    # 群机器人配置
    webhook_key: str = ""
    # 事件过滤
    allowed_events: list = Field(default_factory=lambda: DEFAULT_CHANNEL_EVENTS.copy())
    # 服务器过滤
    allowed_servers: list = Field(default_factory=list)  # Emby 服务器 id 列表，为空=全部


class NotifyConfig(BaseModel):
    """通知渠道总配置"""
    wecom_webhook: WeComWebhookConfig = Field(default_factory=WeComWebhookConfig)
    # 自定义通知列表（支持多个通知配置）
    custom_notifies: list = Field(default_factory=list)


class AggregationConfig(BaseModel):
    """聚合通知配置"""
    delay_seconds: int = 15  # 单集事件聚合时间（秒）


class SystemConfig(BaseModel):
    """系统配置"""
    debug_logging: bool = False  # 是否启用调试日志


class AppConfig(BaseModel):
    """应用总配置"""
    model_config = {"extra": "ignore"}  # 忽略额外字段，不保存到文件

    emby: EmbyConfig = Field(default_factory=EmbyConfig)
    tmdb: TMDBConfig = Field(default_factory=TMDBConfig)
    notify: NotifyConfig = Field(default_factory=NotifyConfig)
    aggregation: AggregationConfig = Field(default_factory=AggregationConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)


class ConfigManager:
    """配置管理器"""

    _instance: Optional['ConfigManager'] = None
    _config: Optional[AppConfig] = None

    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True)
            logger.debug(f"创建配置目录: {CONFIG_DIR}")

    def _load_config(self) -> AppConfig:
        """从文件加载配置"""
        self._ensure_config_dir()

        if not CONFIG_FILE.exists():
            # 创建默认配置
            self._config = AppConfig()
            self._save_config()
            logger.debug("创建默认配置")
        else:
            try:
                with CONFIG_FILE.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = AppConfig(**data)
                logger.debug("配置加载成功")
            except Exception as e:
                logger.error(f"加载配置失败: {e}，使用默认配置")
                self._config = AppConfig()

        return self._config

    def _save_config(self):
        """保存配置到文件（带板块分隔符）"""
        try:
            self._ensure_config_dir()

            config_data = self._config.model_dump()

            # 定义配置顺序和板块标题
            sections = [
                ("_comment_emby", "============================== Emby 服务器配置 =============================="),
                ("emby", config_data.get("emby", {})),
                ("_comment_tmdb", "============================== TMDB 设置 =============================="),
                ("tmdb", config_data.get("tmdb", {})),
                ("_comment_notify", "============================== 通知设置 =============================="),
                ("notify", config_data.get("notify", {})),
                ("_comment_aggregation", "============================== 聚合通知设置 =============================="),
                ("aggregation", config_data.get("aggregation", {})),
                ("_comment_system", "============================== 系统设置 =============================="),
                ("system", config_data.get("system", {})),
            ]

            # 手动构建带格式的 JSON
            lines = ['{']

            for i, (key, value) in enumerate(sections):
                is_last = (i == len(sections) - 1)
                comma = ',' if not is_last else ''

                if key.startswith('_comment'):
                    # 板块分隔符
                    lines.append(f'  "{key}": "{value}"{comma}')
                else:
                    # 配置项 - 格式化为多行
                    json_str = json.dumps(value, indent=2, ensure_ascii=False)
                    # 调整缩进
                    json_lines = json_str.split('\n')
                    if len(json_lines) == 1:
                        lines.append(f'  "{key}": {json_str}{comma}')
                    else:
                        lines.append(f'  "{key}": {json_lines[0]}')
                        for j, line in enumerate(json_lines[1:], 1):
                            if j == len(json_lines) - 1:
                                lines.append(f'  {line}{comma}')
                            else:
                                lines.append(f'  {line}')

            lines.append('}')

            with CONFIG_FILE.open('w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')

            logger.debug(f"配置保存成功: {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise

    def get_config(self) -> AppConfig:
        """获取当前配置"""
        return self._config

    def update_config(self, updates: Dict[str, Any]) -> AppConfig:
        """更新配置"""
        try:
            # 合并更新
            current_data = self._config.model_dump()
            self._deep_update(current_data, updates)
            self._config = AppConfig(**current_data)
            self._save_config()
            logger.debug("配置更新成功")
            return self._config
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            raise

    def _deep_update(self, base_dict: dict, update_dict: dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get_emby_config(self) -> EmbyConfig:
        """获取 Emby 配置"""
        return self._config.emby

    def get_tmdb_config(self) -> TMDBConfig:
        """获取 TMDB 配置"""
        return self._config.tmdb

    def get_notify_config(self) -> NotifyConfig:
        """获取通知配置"""
        return self._config.notify
    
    def get_aggregation_config(self) -> AggregationConfig:
        """获取聚合通知配置"""
        return self._config.aggregation
    
    # 兼容方法 - 返回固定配置值
    def get_webhook_config(self):
        """获取 Webhook 配置（固定值）"""
        class WebhookConfig:
            enabled_events = ["library.new", "playback.start", "playback.stop"]
            enabled_media_types = ["Movie", "Series", "Episode"]
            filter_rules = {"skip_duplicates": True, "min_file_size_mb": 0}
        return WebhookConfig()
    
    def get_cache_config(self):
        """获取缓存配置（固定值）"""
        class CacheConfig:
            tmdb_ttl = 86400
            token_ttl = 7200
        return CacheConfig()
    
    def get_notification_config(self):
        """获取通知格式配置（固定值）"""
        class NotificationConfig:
            enabled = True
            format = "news"
            include_overview = True
            include_rating = True
            include_year = True
        return NotificationConfig()
    
    @property
    def config(self):
        """兼容属性访问"""
        return self._config
    
    def reset(self):
        """重置配置为默认值"""
        self._config = AppConfig()
        self._save_config()

    def reload(self):
        """重新加载配置"""
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """获取指定配置项（支持点号路径）"""
        try:
            keys = key.split('.')
            value = self._config.model_dump()
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, default)
                else:
                    return default
            return value
        except Exception:
            return default

    def set(self, key: str, value: Any):
        """设置指定配置项"""
        try:
            keys = key.split('.')
            config_data = self._config.model_dump()
            target = config_data
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self._config = AppConfig(**config_data)
            self._save_config()
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
            raise

    # ========== 自定义通知管理方法 ==========
    def get_custom_notifies(self) -> list:
        """获取所有自定义通知配置"""
        return self._config.notify.custom_notifies or []

    def get_custom_notify(self, notify_id: str) -> dict:
        """获取指定自定义通知配置"""
        notifies = self.get_custom_notifies()
        for notify in notifies:
            if notify.get('id') == notify_id:
                return notify
        return None

    def add_custom_notify(self, notify_config: dict) -> dict:
        """添加自定义通知配置"""
        try:
            import uuid
            notify_config['id'] = notify_config.get('id') or str(uuid.uuid4())[:8]
            
            if not self._config.notify.custom_notifies:
                self._config.notify.custom_notifies = []
            
            self._config.notify.custom_notifies.append(notify_config)
            self._save_config()
            logger.debug(f"添加自定义通知: {notify_config.get('name')}")
            return notify_config
        except Exception as e:
            logger.error(f"添加自定义通知失败: {e}")
            raise

    def update_custom_notify(self, notify_id: str, updates: dict) -> dict:
        """更新自定义通知配置"""
        try:
            notifies = self._config.notify.custom_notifies or []
            for i, notify in enumerate(notifies):
                if notify.get('id') == notify_id:
                    notifies[i].update(updates)
                    self._save_config()
                    logger.debug(f"更新自定义通知: {notify_id}")
                    return notifies[i]
            raise ValueError(f"通知配置不存在: {notify_id}")
        except Exception as e:
            logger.error(f"更新自定义通知失败: {e}")
            raise

    def delete_custom_notify(self, notify_id: str):
        """删除自定义通知配置"""
        try:
            notifies = self._config.notify.custom_notifies or []
            self._config.notify.custom_notifies = [
                n for n in notifies if n.get('id') != notify_id
            ]
            self._save_config()
            logger.debug(f"删除自定义通知: {notify_id}")
        except Exception as e:
            logger.error(f"删除自定义通知失败: {e}")
            raise

    def get_all_notifies(self) -> list:
        """获取所有通知配置（包括未启用的）"""
        return self.get_custom_notifies()
    
    def get_all_enabled_notifies(self) -> list:
        """获取所有启用的通知配置（仅自定义通知）"""
        enabled_notifies = []
        
        # 只返回自定义通知配置
        for custom in self.get_custom_notifies():
            if custom.get('enabled', True):
                enabled_notifies.append(custom)
        
        return enabled_notifies

    # ========== Emby 服务器管理方法 ==========
    def get_emby_servers(self) -> list:
        """获取所有 Emby 服务器配置"""
        return self._config.emby.servers or []

    def get_emby_server(self, server_id: str) -> dict:
        """获取指定 Emby 服务器配置"""
        servers = self.get_emby_servers()
        for server in servers:
            if server.get('id') == server_id:
                return server
        return None

    def add_emby_server(self, server_config: dict) -> dict:
        """添加 Emby 服务器配置"""
        try:
            import uuid
            server_config['id'] = server_config.get('id') or str(uuid.uuid4())[:8]
            
            if not self._config.emby.servers:
                self._config.emby.servers = []
            
            self._config.emby.servers.append(server_config)
            self._save_config()
            logger.debug(f"添加 Emby 服务器: {server_config.get('name')}")
            return server_config
        except Exception as e:
            logger.error(f"添加 Emby 服务器失败: {e}")
            raise

    def update_emby_server(self, server_id: str, updates: dict) -> dict:
        """更新 Emby 服务器配置"""
        try:
            servers = self._config.emby.servers or []
            for i, server in enumerate(servers):
                if server.get('id') == server_id:
                    servers[i].update(updates)
                    self._save_config()
                    logger.debug(f"更新 Emby 服务器: {server_id}")
                    return servers[i]
            raise ValueError(f"服务器配置不存在: {server_id}")
        except Exception as e:
            logger.error(f"更新 Emby 服务器失败: {e}")
            raise

    def delete_emby_server(self, server_id: str):
        """删除 Emby 服务器配置"""
        try:
            servers = self._config.emby.servers or []
            self._config.emby.servers = [
                s for s in servers if s.get('id') != server_id
            ]
            self._save_config()
            logger.debug(f"删除 Emby 服务器: {server_id}")
        except Exception as e:
            logger.error(f"删除 Emby 服务器失败: {e}")
            raise

    def get_emby_config(self) -> EmbyConfig:
        """获取 Emby 配置（兼容旧版本）"""
        # 如果有旧配置，迁移到新格式
        if self._config.emby.base_url and not self._config.emby.servers:
            # 创建默认服务器配置
            default_server = {
                'id': 'default',
                'name': '默认服务器',
                'base_url': self._config.emby.base_url,
                'api_key': self._config.emby.api_key,
                'enabled': True
            }
            self._config.emby.servers = [default_server]
            self._save_config()
        return self._config.emby

    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        return self._config.system

    def update_system_config(self, updates: dict) -> SystemConfig:
        """更新系统配置"""
        try:
            current_data = self._config.system.model_dump()
            current_data.update(updates)
            self._config.system = SystemConfig(**current_data)
            self._save_config()
            logger.debug(f"系统配置已更新: {current_data}")
            return self._config.system
        except Exception as e:
            logger.error(f"更新系统配置失败: {e}")
            raise

    def is_debug_logging_enabled(self) -> bool:
        """检查是否启用了调试日志"""
        return self._config.system.debug_logging


# 全局配置管理器实例
config_manager = ConfigManager()
