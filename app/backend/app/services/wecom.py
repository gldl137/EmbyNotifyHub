import requests
from typing import Dict, Any, Optional
from app.services.cache import cache
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WeComAPI:
    """企业微信 API 封装"""

    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, corp_id: str = "", agent_id: str = "", secret: str = "", to_user: str = "@all"):
        self.corpid = corp_id
        self.agentid = agent_id
        self.secret = secret
        self.touser = to_user

    def _get_access_token(self) -> Optional[str]:
        """
        获取企业微信 Access Token
        """
        if not all([self.corpid, self.secret]):
            logger.error("企业微信配置不完整: 缺少 corp_id 或 secret")
            return None

        # 检查缓存 - 使用 corp_id + secret 组合作为 key，支持多应用配置
        cache_key = f"wecom_token:{self.corpid}:{self.secret[:8]}"
        cached_token = cache.get(cache_key)
        if cached_token:
            logger.debug("使用缓存的 Access Token")
            return cached_token

        try:
            url = f"{self.BASE_URL}/gettoken"
            params = {
                "corpid": self.corpid,
                "corpsecret": self.secret,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                token = data.get("access_token")
                expires_in = data.get("expires_in", 7200)

                # 缓存 token（提前5分钟过期）
                cache.set(cache_key, token, ttl=expires_in - 300)
                logger.debug("企业微信 Access Token 获取成功")
                return token
            else:
                logger.error(f"获取 Access Token 失败: {data}")
                return None

        except Exception as e:
            logger.error(f"获取 Access Token 异常: {e}")
            return None

    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送企业微信消息
        """
        token = self._get_access_token()
        if not token:
            logger.error("无法获取 Access Token，消息发送失败")
            return False

        try:
            url = f"{self.BASE_URL}/message/send"
            params = {"access_token": token}

            # 添加接收人和应用ID
            payload = {
                "touser": self.touser,
                "agentid": self.agentid,
                **message,
            }

            response = requests.post(url, params=params, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                logger.debug("企业微信消息发送成功")
                return True
            else:
                logger.error(f"企业微信消息发送失败: {data}")
                return False

        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False


def send_wecom_webhook(webhook_key: str, message: Dict[str, Any]) -> bool:
    """
    发送企业微信群机器人消息
    """
    if not webhook_key:
        logger.error("Webhook Key 不能为空")
        return False

    try:
        # 检查并修复 URL 长度（企业微信限制 URL 长度）
        message = _fix_message_urls(message)

        # 调试：记录实际发送的消息内容
        logger.debug(f"群机器人消息内容: {message}")

        url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"
        response = requests.post(url, json=message, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("errcode") == 0:
            logger.info("群机器人消息发送成功")
            return True
        else:
            logger.error(f"群机器人消息发送失败: {data}")
            # 如果失败，记录更详细的错误信息
            if data.get("errcode") == 40039:
                articles = message.get("news", {}).get("articles", [])
                for i, article in enumerate(articles):
                    logger.error(f"文章 {i} - url长度: {len(article.get('url', ''))}, picurl长度: {len(article.get('picurl', ''))}")
                    logger.error(f"文章 {i} - url: {article.get('url', '')[:100]}...")
            return False
    except Exception as e:
        logger.error(f"发送群机器人消息异常: {e}")
        return False


def _fix_message_urls(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    修复消息中的 URL 长度问题
    企业微信对 URL 长度有限制（通常 512 字节）
    """
    import copy
    message = copy.deepcopy(message)

    MAX_URL_LENGTH = 512  # 企业微信 URL 长度限制（保守值）

    if message.get("msgtype") == "news" and "news" in message:
        articles = message["news"].get("articles", [])
        for i, article in enumerate(articles):
            # 确保字段存在且为字符串
            for field in ["title", "description", "url", "picurl"]:
                if field not in article or article[field] is None:
                    article[field] = ""
                else:
                    article[field] = str(article[field])

            # 检查并截断 picurl
            picurl = article.get("picurl", "")
            if picurl and len(picurl) > MAX_URL_LENGTH:
                logger.warning(f"文章 {i} 图片 URL 过长 ({len(picurl)} 字符)，已移除")
                article["picurl"] = ""

            # 检查并截断 url
            article_url = article.get("url", "")
            if article_url and len(article_url) > MAX_URL_LENGTH:
                logger.warning(f"文章 {i} 链接 URL 过长 ({len(article_url)} 字符)，已截断")
                article["url"] = article_url[:MAX_URL_LENGTH]

            # 确保必填字段不为空
            if not article.get("title"):
                article["title"] = "无标题"
            if not article.get("description"):
                article["description"] = " "

    return message


def send_wecom_news_with_config(
    msg: Dict[str, Any],
    corp_id: str,
    agent_id: str,
    secret: str,
    to_user: str = "@all"
) -> Dict[str, Any]:
    """
    使用指定配置发送企业微信图文消息（支持多个自定义应用）
    返回: {"success": bool, "error": str}
    """
    try:
        # 创建 API 实例使用传入的配置
        api = WeComAPI(corp_id=corp_id, agent_id=agent_id, secret=secret, to_user=to_user)

        # 获取 token
        token = api._get_access_token()
        if not token:
            return {"success": False, "error": "无法获取 Access Token"}

        # 直接发送消息
        url = f"{api.BASE_URL}/message/send"
        params = {"access_token": token}

        payload = {
            "touser": to_user,
            "agentid": agent_id,
            **msg,
        }

        response = requests.post(url, params=params, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("errcode") == 0:
            logger.debug(f"企业微信消息发送成功 (agent_id={agent_id})")
            return {"success": True, "error": ""}
        else:
            logger.error(f"企业微信消息发送失败: {data}")
            return {"success": False, "error": f"发送失败: {data.get('errmsg', '未知错误')}"}

    except Exception as e:
        logger.error(f"发送消息异常: {e}")
        return {"success": False, "error": str(e)}
