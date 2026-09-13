"""
通知渠道配置 API

新架构：使用 get_event_info 获取统一的事件信息
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.services.config_manager import config_manager, DEFAULT_CHANNEL_EVENTS

from app.core.constants import get_event_info, EVENT_MAP, CATEGORY_NAME_MAP
from app.core.event_models import EVENT_CLASS_MAP
from app.utils.logger import get_logger

router = APIRouter(prefix="/notify", tags=["config-notify"])
logger = get_logger(__name__)


class WeComWebhookConfig(BaseModel):
    """企业微信群机器人配置"""
    enabled: bool = Field(False, description="是否启用")
    webhook_key: str = Field("", description="Webhook Key")
    bot_name: str = Field("Emby 通知助手", description="机器人名称")
    allowed_servers: List[str] = Field(default_factory=list, description="允许的 Emby 服务器列表（id），为空=全部")


class NotifyConfig(BaseModel):
    """通知配置模型"""
    wecom_webhook: Optional[WeComWebhookConfig] = Field(default_factory=WeComWebhookConfig)


class NotifyConfigResponse(BaseModel):
    """通知配置响应"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


class NotifyTestRequest(BaseModel):
    """通知测试请求"""
    channel: str = "wecom"
    webhook_key: str = ""
    bot_name: str = "测试机器人"


class NotifyTestResponse(BaseModel):
    """通知测试响应"""
    success: bool
    message: str


@router.get("", response_model=NotifyConfigResponse)
async def get_notify_config():
    """获取通知配置"""
    try:
        config = config_manager.get("notify", {})
        
        # 确保返回完整结构（包括 allowed_events）
        if "wecom_webhook" not in config:
            config["wecom_webhook"] = {
                "enabled": False,
                "webhook_key": "",
                "bot_name": "Emby 通知助手",
                "allowed_events": DEFAULT_CHANNEL_EVENTS.copy(),
                "allowed_servers": []
            }
        else:
            # 确保有 allowed_events 字段
            if "allowed_events" not in config["wecom_webhook"]:
                config["wecom_webhook"]["allowed_events"] = DEFAULT_CHANNEL_EVENTS.copy()
            # 确保有 allowed_servers 字段
            if "allowed_servers" not in config["wecom_webhook"]:
                config["wecom_webhook"]["allowed_servers"] = []
            
        return NotifyConfigResponse(
            success=True,
            data=config,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取通知配置失败: {e}")
        return NotifyConfigResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("", response_model=NotifyConfigResponse)
async def update_notify_config(config: dict):
    """更新通知配置"""
    try:
        logger.debug(f"收到保存请求: {config}")
        
        # 获取现有配置
        current_config = config_manager.get("notify", {})
        logger.debug(f"当前配置: {current_config}")
        
        # 合并新配置（支持部分更新）
        for key, value in config.items():
            if isinstance(value, dict):
                # 如果是字典，合并而不是替换
                if key not in current_config:
                    current_config[key] = {}
                current_config[key].update(value)
            else:
                current_config[key] = value
        
        logger.debug(f"合并后配置: {current_config}")
        config_manager.set("notify", current_config)
        
        # 验证保存结果
        saved_config = config_manager.get("notify", {})
        logger.debug(f"保存后的配置: {saved_config}")
        
        return NotifyConfigResponse(
            success=True,
            data=saved_config,
            message="保存成功"
        )
    except Exception as e:
        logger.error(f"保存通知配置失败: {e}")
        return NotifyConfigResponse(
            success=False,
            message=f"保存失败: {str(e)}"
        )


def is_test_allowed_for_channel(channel: str) -> tuple[bool, str]:
    """检查测试事件是否被允许发送到指定渠道
    返回: (是否允许, 消息)
    """
    notify_config = config_manager.get("notify", {})
    
    # 根据渠道类型获取配置
    if channel in ["wecom", "wecom_webhook"]:
        channel_config = notify_config.get("wecom_webhook", {})
        channel_name = "企业微信群机器人"
    else:
        return False, f"不支持的渠道: {channel}"
    
    # 获取允许的事件列表
    allowed_events = channel_config.get("allowed_events", DEFAULT_CHANNEL_EVENTS.copy())
    
    # 检查测试事件是否在允许列表中
    if "system.webhooktest" not in allowed_events:
        return False, "测试通知已被禁用，请在事件配置中勾选「系统测试」事件"
    
    return True, ""


@router.post("/test", response_model=NotifyTestResponse)
async def test_notify(req: NotifyTestRequest):
    """测试通知渠道"""
    try:
        # 检查测试事件是否被允许
        allowed, message = is_test_allowed_for_channel(req.channel)
        if not allowed:
            return NotifyTestResponse(
                success=False,
                message=message
            )
        
        if req.channel == "wecom" or req.channel == "wecom_webhook":
            if not req.webhook_key:
                return NotifyTestResponse(
                    success=False,
                    message="Webhook Key 不能为空"
                )
            
            # 构造测试消息
            test_msg = {
                "msgtype": "text",
                "text": {
                    "content": f"【测试】{req.bot_name}\n\n这是一条测试消息\n如果收到说明配置正确！"
                }
            }
            
            import requests
            response = requests.post(
                f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={req.webhook_key}",
                json=test_msg,
                timeout=10.0
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                return NotifyTestResponse(
                    success=True,
                    message="测试消息发送成功"
                )
            else:
                return NotifyTestResponse(
                    success=False,
                    message=f"发送失败: {result.get('errmsg', '未知错误')}"
                )
        else:
            return NotifyTestResponse(
                success=False,
                message=f"暂不支持 {req.channel} 渠道"
            )
    except Exception as e:
        logger.error(f"测试通知失败: {e}")
        return NotifyTestResponse(
            success=False,
            message=f"测试失败: {str(e)}"
        )


class EventTypeInfo(BaseModel):
    """事件类型信息"""
    event_type: str
    description: str
    emoji: str


class EventCategoryInfo(BaseModel):
    """事件分类信息"""
    category: str
    category_name: str
    events: List[EventTypeInfo]


class EventsListResponse(BaseModel):
    """事件列表响应"""
    success: bool
    data: List[EventCategoryInfo] = []
    message: str = ""


@router.get("/events", response_model=EventsListResponse)
async def get_available_events():
    """获取所有可用的事件类型列表
    
    新架构：
    1. 只返回已实现代码的事件（在 EVENT_CLASS_MAP 中）
    2. 按 Emby 官方分类分组
    3. 返回分类名称
    """
    try:
        # 按分类组织事件
        category_events = {}
        
        for event_type, event_def in EVENT_MAP.items():
            # 只返回已实现代码的事件
            if event_type not in EVENT_CLASS_MAP:
                continue
                
            category = event_def.get("category", "other")
            category_name = CATEGORY_NAME_MAP.get(category, category)
            
            if category not in category_events:
                category_events[category] = {
                    "category": category,
                    "category_name": category_name,
                    "events": []
                }
            
            category_events[category]["events"].append(EventTypeInfo(
                event_type=event_type,
                description=event_def.get("name", event_type),
                emoji=event_def.get("emoji", "📌")
            ))
        
        # 转换为列表并按分类顺序排列
        # 顺序：服务器 → 媒体库 → 播放 → 用户 → 设备 → 计划任务 → 插件 → 电视直播 → 外部 → 神医助手
        result = []
        category_order = [
            "server", "library", "playback", "user", "device",
            "task", "plugin", "livetv", "external", "assistant"
        ]
        
        for category in category_order:
            if category in category_events:
                result.append(EventCategoryInfo(
                    category=category_events[category]["category"],
                    category_name=category_events[category]["category_name"],
                    events=category_events[category]["events"]
                ))
        
        return EventsListResponse(
            success=True,
            data=result,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取事件类型失败: {e}")
        return EventsListResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


class ChannelEventsConfig(BaseModel):
    """渠道事件配置"""
    channel: str = Field(..., description="渠道名称: wecom_webhook")
    allowed_events: List[str] = Field(default_factory=list, description="允许的事件类型列表")


class ChannelEventsResponse(BaseModel):
    """渠道事件配置响应"""
    success: bool
    data: Optional[Dict] = None
    message: str = ""


@router.get("/events/{channel}", response_model=ChannelEventsResponse)
async def get_channel_events(channel: str):
    """获取指定渠道的事件过滤配置"""
    try:
        notify_config = config_manager.get("notify", {})
        channel_config = notify_config.get(channel, {})
        
        # 获取 allowed_events，如果不存在则使用默认值
        allowed_events = channel_config.get("allowed_events", DEFAULT_CHANNEL_EVENTS.copy())
        
        return ChannelEventsResponse(
            success=True,
            data={
                "channel": channel,
                "allowed_events": allowed_events,
                "all_events": list(EVENT_MAP.keys())  # 新架构：使用 EVENT_MAP
            },
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取渠道事件配置失败: {e}")
        return ChannelEventsResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("/events", response_model=ChannelEventsResponse)
async def update_channel_events(config: ChannelEventsConfig):
    """更新指定渠道的事件过滤配置"""
    try:
        if config.channel not in ["wecom_webhook"]:
            return ChannelEventsResponse(
                success=False,
                message=f"无效的渠道: {config.channel}"
            )
        
        # 获取当前配置
        notify_config = config_manager.get("notify", {})
        if config.channel not in notify_config:
            notify_config[config.channel] = {}
        
        # 更新 allowed_events
        notify_config[config.channel]["allowed_events"] = config.allowed_events
        config_manager.set("notify", notify_config)
        
        logger.debug(f"更新渠道 {config.channel} 的事件配置: {config.allowed_events}")
        
        return ChannelEventsResponse(
            success=True,
            data={
                "channel": config.channel,
                "allowed_events": config.allowed_events
            },
            message="保存成功"
        )
    except Exception as e:
        logger.error(f"保存渠道事件配置失败: {e}")
        return ChannelEventsResponse(
            success=False,
            message=f"保存失败: {str(e)}"
        )


@router.delete("", response_model=NotifyConfigResponse)
async def delete_notify_config():
    """删除通知配置"""
    try:
        config_manager.set("notify", {})
        return NotifyConfigResponse(
            success=True,
            message="配置已删除"
        )
    except Exception as e:
        logger.error(f"删除通知配置失败: {e}")
        return NotifyConfigResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )


# ==================== 辅助函数 ====================

async def send_wecom_app_test(
    corp_id: str,
    agent_id: str,
    secret: str,
    to_user: str,
    notify_name: str
) -> tuple[bool, str]:
    """
    使用临时配置发送企业微信应用测试消息
    返回: (success, message)
    """
    import requests
    from app.services.cache import cache
    
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
    
    try:
        # 获取 access token - 使用 corp_id + secret 组合作为 key，支持多应用配置
        cache_key = f"wecom_token_test:{corp_id}:{secret[:8]}"
        token = cache.get(cache_key)
        
        if not token:
            # 从企业微信获取 token
            url = f"{BASE_URL}/gettoken"
            params = {"corpid": corp_id, "corpsecret": secret}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("errcode") != 0:
                return False, f"获取 Access Token 失败: {data.get('errmsg', '未知错误')}"
            
            token = data.get("access_token")
            expires_in = data.get("expires_in", 7200)
            # 缓存 token（提前5分钟过期）
            cache.set(cache_key, token, ttl=expires_in - 300)
        
        # 发送文本测试消息
        url = f"{BASE_URL}/message/send"
        params = {"access_token": token}
        
        test_msg = {
            "touser": to_user,
            "agentid": agent_id,
            "msgtype": "text",
            "text": {
                "content": f"【测试】{notify_name}\n\n这是一条测试消息\n如果收到说明配置正确！"
            },
            "safe": 0
        }
        
        response = requests.post(url, params=params, json=test_msg, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            return True, "测试消息发送成功"
        else:
            return False, f"发送失败: {result.get('errmsg', '未知错误')}"
    
    except Exception as e:
        logger.error(f"发送企业微信应用测试消息失败: {e}")
        return False, f"发送失败: {str(e)}"


# ==================== 自定义通知 API ====================

class CustomNotifyConfigModel(BaseModel):
    """自定义通知配置模型"""
    id: Optional[str] = Field(None, description="通知ID，新增时自动生成")
    name: str = Field(..., description="通知名称")
    enabled: bool = Field(True, description="是否启用")
    channel_type: str = Field("wecom_app", description="渠道类型: wecom_webhook 或 wecom_app")
    # 企业微信应用配置
    corp_id: str = Field("", description="企业ID")
    agent_id: str = Field("", description="应用ID")
    secret: str = Field("", description="应用密钥")
    to_user: str = Field("@all", description="接收用户")
    # 群机器人配置
    webhook_key: str = Field("", description="Webhook Key")
    # 事件过滤
    allowed_events: List[str] = Field(default_factory=lambda: DEFAULT_CHANNEL_EVENTS.copy(), description="允许的事件类型列表")
    # 服务器过滤（存 Emby 服务器配置 id 列表，为空表示全部服务器）
    allowed_servers: List[str] = Field(default_factory=list, description="允许的 Emby 服务器列表（id），为空=全部")


class CustomNotifyResponse(BaseModel):
    """自定义通知响应"""
    success: bool
    data: Optional[Dict] = None
    message: str = ""


class CustomNotifyListResponse(BaseModel):
    """自定义通知列表响应"""
    success: bool
    data: List[Dict] = []
    message: str = ""


@router.get("/custom", response_model=CustomNotifyListResponse)
async def get_custom_notifies():
    """获取所有自定义通知配置"""
    try:
        notifies = config_manager.get_custom_notifies()
        return CustomNotifyListResponse(
            success=True,
            data=notifies,
            message="获取成功"
        )
    except Exception as e:
        logger.error(f"获取自定义通知失败: {e}")
        return CustomNotifyListResponse(
            success=False,
            message=f"获取失败: {str(e)}"
        )


@router.post("/custom", response_model=CustomNotifyResponse)
async def add_custom_notify(config: CustomNotifyConfigModel):
    """添加自定义通知配置"""
    try:
        notify_config = config.model_dump()
        result = config_manager.add_custom_notify(notify_config)
        return CustomNotifyResponse(
            success=True,
            data=result,
            message="添加成功"
        )
    except Exception as e:
        logger.error(f"添加自定义通知失败: {e}")
        return CustomNotifyResponse(
            success=False,
            message=f"添加失败: {str(e)}"
        )


@router.put("/custom/{notify_id}", response_model=CustomNotifyResponse)
async def update_custom_notify(notify_id: str, config: CustomNotifyConfigModel):
    """更新自定义通知配置"""
    try:
        updates = config.model_dump()
        # 如果传入的 id 和路径参数不一致，以路径参数为准
        updates['id'] = notify_id
        result = config_manager.update_custom_notify(notify_id, updates)
        return CustomNotifyResponse(
            success=True,
            data=result,
            message="更新成功"
        )
    except Exception as e:
        logger.error(f"更新自定义通知失败: {e}")
        return CustomNotifyResponse(
            success=False,
            message=f"更新失败: {str(e)}"
        )


@router.delete("/custom/{notify_id}", response_model=CustomNotifyResponse)
async def delete_custom_notify(notify_id: str):
    """删除自定义通知配置"""
    try:
        config_manager.delete_custom_notify(notify_id)
        return CustomNotifyResponse(
            success=True,
            message="删除成功"
        )
    except Exception as e:
        logger.error(f"删除自定义通知失败: {e}")
        return CustomNotifyResponse(
            success=False,
            message=f"删除失败: {str(e)}"
        )


@router.post("/custom/{notify_id}/test", response_model=NotifyTestResponse)
async def test_custom_notify(notify_id: str):
    """测试自定义通知配置"""
    try:
        # 获取通知配置
        notify = config_manager.get_custom_notify(notify_id)
        if not notify:
            return NotifyTestResponse(
                success=False,
                message="通知配置不存在"
            )
        
        # 检查测试事件是否被允许
        if "system.webhooktest" not in notify.get("allowed_events", []):
            return NotifyTestResponse(
                success=False,
                message="测试通知已被禁用，请在事件配置中勾选「系统测试」事件"
            )
        
        # 根据渠道类型发送测试消息
        if notify.get("channel_type") == "wecom_webhook":
            webhook_key = notify.get("webhook_key", "")
            if not webhook_key:
                return NotifyTestResponse(
                    success=False,
                    message="Webhook Key 不能为空"
                )
            
            test_msg = {
                "msgtype": "text",
                "text": {
                    "content": f"【测试】{notify.get('name', '通知助手')}\n\n这是一条测试消息\n如果收到说明配置正确！"
                }
            }
            
            import requests
            response = requests.post(
                f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}",
                json=test_msg,
                timeout=10.0
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                return NotifyTestResponse(
                    success=True,
                    message="测试消息发送成功"
                )
            else:
                return NotifyTestResponse(
                    success=False,
                    message=f"发送失败: {result.get('errmsg', '未知错误')}"
                )
        
        elif notify.get("channel_type") == "wecom_app":
            # 使用自定义配置发送测试消息
            corp_id = notify.get("corp_id", "")
            agent_id = notify.get("agent_id", "")
            secret = notify.get("secret", "")
            to_user = notify.get("to_user", "@all")
            
            if not corp_id or not agent_id or not secret:
                return NotifyTestResponse(
                    success=False,
                    message="企业微信应用配置不完整"
                )
            
            # 使用临时配置发送测试消息
            success, message = await send_wecom_app_test(
                corp_id=corp_id,
                agent_id=agent_id,
                secret=secret,
                to_user=to_user,
                notify_name=notify.get('name', '通知助手')
            )
            
            return NotifyTestResponse(
                success=success,
                message=message
            )
        
        else:
            return NotifyTestResponse(
                success=False,
                message=f"不支持的渠道类型: {notify.get('channel_type')}"
            )
    
    except Exception as e:
        logger.error(f"测试自定义通知失败: {e}")
        return NotifyTestResponse(
            success=False,
            message=f"测试失败: {str(e)}"
        )
