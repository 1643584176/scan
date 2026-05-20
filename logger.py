#!/usr/bin/env python3
"""
统一日志模块 - 类似 logback 的日志系统
用法:
    from logger import get_logger
    logger = get_logger(__name__)
    logger.info("信息消息")
    logger.warning("警告消息")
    logger.error("错误消息")
    logger.debug("调试消息")
"""

import logging
import sys
from datetime import datetime


class ColorFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 保存原始级别名称
        levelname = record.levelname
        color = self.COLORS.get(levelname, '')
        
        # 添加颜色
        record.levelname = f"{color}{levelname}{self.RESET}"
        
        # 格式化
        result = super().format(record)
        
        # 恢复原始级别名称
        record.levelname = levelname
        
        return result


def setup_logger(name=None, level=logging.INFO, log_file=None):
    """
    配置并返回logger
    
    Args:
        name: logger名称,通常为 __name__
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 可选的日志文件路径
    
    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name or 'scan')
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式化器 - 类似 logback 格式: [时间] [级别] [模块] 消息
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器(带颜色)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Windows 下使用彩色格式化器
    if sys.platform == 'win32':
        try:
            # 尝试启用 ANSI 颜色支持
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
        console_handler.setFormatter(ColorFormatter(
            fmt='[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    else:
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # 文件处理器(如果指定了日志文件)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 便捷函数
def get_logger(name=None):
    """获取logger实例(快捷方式)"""
    return setup_logger(name)


def info(message, *args, **kwargs):
    """INFO 级别日志"""
    logger = setup_logger()
    logger.info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    """WARNING 级别日志"""
    logger = setup_logger()
    logger.warning(message, *args, **kwargs)


def error(message, *args, **kwargs):
    """ERROR 级别日志"""
    logger = setup_logger()
    logger.error(message, *args, **kwargs)


def debug(message, *args, **kwargs):
    """DEBUG 级别日志"""
    logger = setup_logger()
    logger.debug(message, *args, **kwargs)


def critical(message, *args, **kwargs):
    """CRITICAL 级别日志"""
    logger = setup_logger()
    logger.critical(message, *args, **kwargs)
