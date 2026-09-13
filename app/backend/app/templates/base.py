"""
通知模板基础模块
定义所有通知模板的基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import re


class NotificationTemplate(ABC):
    """通知模板基类"""
    
    @abstractmethod
    def build_title(self, data: Dict[str, Any]) -> str:
        """构建通知标题"""
        pass
    
    @abstractmethod
    def build_content(self, data: Dict[str, Any]) -> str:
        """构建通知内容（三行格式）"""
        pass
    
    def format_timestamp(self, timestamp: str) -> Optional[str]:
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
