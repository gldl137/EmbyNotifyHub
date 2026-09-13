import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# 日志目录配置 - 项目根目录下的 data/logs
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # 项目根目录
LOG_DIR = BASE_DIR / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志滚动配置：单个文件最大 10MB，不保留备份（满 10MB 后截断当前文件）
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 0

# 全局日志级别
_global_log_level = logging.INFO

# 已创建的日志记录器列表（用于动态更新级别）
_loggers = []


def set_global_log_level(level: str):
    """
    设置全局日志级别

    Args:
        level: 日志级别字符串 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _global_log_level
    new_level = getattr(logging, level.upper(), logging.INFO)
    _global_log_level = new_level

    # 更新所有已创建的日志记录器
    for logger in _loggers:
        logger.setLevel(new_level)
        # 同时更新所有处理器的级别
        for handler in logger.handlers:
            handler.setLevel(new_level)


def get_global_log_level() -> str:
    """获取当前全局日志级别"""
    return logging.getLevelName(_global_log_level)


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def formatTime(self, record, datefmt=None):
        """自定义时间格式，只返回时分秒"""
        import time
        return time.strftime("%H:%M:%S", time.localtime(record.created))
    
    def format(self, record):
        # 获取级别颜色
        level_color = self.COLORS.get(record.levelname, self.RESET)
        
        # 格式化时间（只取时分秒）
        time_str = self.formatTime(record)
        
        # 格式化级别（加上方括号）
        level_str = f"{level_color}[{record.levelname}]{self.RESET}"
        
        # 组合日志行（间隔紧凑，只保留时间、级别、消息）
        return f"{time_str} {level_str} {record.getMessage()}"


class FileFormatter(logging.Formatter):
    """文件日志格式化器（无颜色）"""
    
    def formatTime(self, record, datefmt=None):
        """自定义时间格式"""
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
    
    def format(self, record):
        # 格式化时间
        time_str = self.formatTime(record)
        # 组合日志行：时间 | 级别 | 模块 | 消息
        return f"{time_str} | {record.levelname:8} | {record.name:20} | {record.getMessage()}"


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 使用全局日志级别或传入的级别
    log_level = level or get_global_log_level()
    logger.setLevel(getattr(logging, log_level.upper()))

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # 设置日志格式（对齐格式，只显示时间）
    formatter = ColoredFormatter(
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # 创建文件处理器 - 按大小滚动（单文件 10MB，最多保留 5 个备份）
    log_file = LOG_DIR / "app.log"

    file_handler = RotatingFileHandler(
        log_file,
        mode='a',                 # 追加模式
        maxBytes=LOG_MAX_BYTES,   # 单文件最大 10MB
        backupCount=LOG_BACKUP_COUNT,  # 保留 5 个备份
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # 设置文件日志格式
    file_formatter = FileFormatter()
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    # 禁用传播，避免日志被根日志器重复处理
    logger.propagate = False

    # 记录到全局列表（用于动态更新级别）
    _loggers.append(logger)

    return logger
