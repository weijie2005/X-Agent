"""
日志配置模块

本模块负责配置整个应用的日志系统，包括：
- 控制台日志输出
- 文件日志输出
- 日志轮转
- 日志格式化
- 不同级别的日志文件分离

日志文件位置：
- logs/app.log: 所有日志（INFO及以上）
- logs/error.log: 错误日志（ERROR及以上）
- logs/debug.log: 调试日志（DEBUG及以上）

日志轮转策略：
- 按大小轮转：单个文件最大 10MB
- 按时间轮转：每天午夜轮转
- 保留数量：最近 30 天的日志文件

使用方式：
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("This is a log message")
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.config import get_settings


class CustomFormatter(logging.Formatter):
    """
    自定义日志格式化器
    
    日志格式：
    [时间] [级别] [模块名] [进程ID] [线程ID] - 消息
    
    示例：
    [2026-08-07 16:30:45,123] [INFO] [app.main] [12345] [MainThread] - Application started
    """
    
    def format(self, record):
        """
        格式化日志记录
        
        Args:
            record: 日志记录对象
        
        Returns:
            str: 格式化后的日志字符串
        """
        # 添加额外的字段
        record.asctime = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        
        # 构建日志格式
        log_format = (
            f"[{record.asctime}] "
            f"[{record.levelname}] "
            f"[{record.name}] "
            f"[{record.process}] "
            f"[{record.threadName}] "
            f"- {record.getMessage()}"
        )
        
        # 如果有异常信息，添加堆栈信息
        if record.exc_info:
            log_format += f"\n{self.formatException(record.exc_info)}"
        
        return log_format


class RequestFormatter(logging.Formatter):
    """
    请求日志格式化器
    
    用于记录 HTTP 请求的详细信息，包括：
    - 请求方法
    - 请求路径
    - 请求参数
    - 响应状态码
    - 处理时间
    - 客户端IP
    """
    
    def format(self, record):
        """
        格式化请求日志
        
        Args:
            record: 日志记录对象
        
        Returns:
            str: 格式化后的日志字符串
        """
        # 基础格式
        log_format = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]}] "
        log_format += f"[{record.levelname}] "
        log_format += f"[{record.name}] "
        
        # 添加请求信息（如果有）
        if hasattr(record, 'method'):
            log_format += f"[{record.method}] "
        if hasattr(record, 'path'):
            log_format += f"[{record.path}] "
        if hasattr(record, 'status_code'):
            log_format += f"[{record.status_code}] "
        if hasattr(record, 'process_time'):
            log_format += f"[{record.process_time:.3f}s] "
        if hasattr(record, 'client_ip'):
            log_format += f"[{record.client_ip}] "
        
        log_format += f"- {record.getMessage()}"
        
        return log_format


def setup_logging():
    """
    设置日志系统
    
    配置内容：
    1. 创建日志目录
    2. 配置根日志记录器
    3. 添加控制台处理器
    4. 添加文件处理器（轮转）
    5. 配置不同级别的日志文件
    
    日志文件：
    - logs/app.log: 所有日志（INFO及以上）
    - logs/error.log: 错误日志（ERROR及以上）
    - logs/debug.log: 调试日志（DEBUG及以上）
    - logs/request.log: 请求日志（INFO）
    
    轮转策略：
    - 按大小轮转：10MB
    - 保留文件：30个
    - 编码：UTF-8
    """
    settings = get_settings()
    
    # 创建日志目录
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置最低级别
    
    # 清除现有的处理器
    root_logger.handlers.clear()
    
    # ==================== 控制台处理器 ====================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)
    
    # ==================== 所有日志文件处理器 ====================
    app_log_file = log_dir / "app.log"
    app_handler = logging.handlers.RotatingFileHandler(
        filename=app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(app_handler)
    
    # ==================== 错误日志文件处理器 ====================
    error_log_file = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(error_handler)
    
    # ==================== 调试日志文件处理器 ====================
    if settings.DEBUG:
        debug_log_file = log_dir / "debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            filename=debug_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=30,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(CustomFormatter())
        root_logger.addHandler(debug_handler)
    
    # ==================== 请求日志文件处理器 ====================
    request_log_file = log_dir / "request.log"
    request_handler = logging.handlers.RotatingFileHandler(
        filename=request_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    request_handler.setLevel(logging.INFO)
    request_handler.setFormatter(RequestFormatter())
    
    # 创建专门的请求日志记录器
    request_logger = logging.getLogger('request')
    request_logger.setLevel(logging.INFO)
    request_logger.addHandler(request_handler)
    request_logger.propagate = False  # 不传播到根日志记录器
    
    # ==================== 数据库日志文件处理器 ====================
    db_log_file = log_dir / "database.log"
    db_handler = logging.handlers.RotatingFileHandler(
        filename=db_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    db_handler.setLevel(logging.INFO)
    db_handler.setFormatter(CustomFormatter())
    
    # 创建专门的数据库日志记录器
    db_logger = logging.getLogger('database')
    db_logger.setLevel(logging.INFO)
    db_logger.addHandler(db_handler)
    db_logger.propagate = False
    
    # ==================== Agent日志文件处理器 ====================
    agent_log_file = log_dir / "agent.log"
    agent_handler = logging.handlers.RotatingFileHandler(
        filename=agent_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    agent_handler.setLevel(logging.INFO)
    agent_handler.setFormatter(CustomFormatter())
    
    # 创建专门的Agent日志记录器
    agent_logger = logging.getLogger('agent')
    agent_logger.setLevel(logging.INFO)
    agent_logger.addHandler(agent_handler)
    agent_logger.propagate = False
    
    # 设置第三方库的日志级别（减少噪音）
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str, logger_type: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
        logger_type: 日志记录器类型
            - None: 默认日志记录器
            - 'request': 请求日志记录器
            - 'database': 数据库日志记录器
            - 'agent': Agent日志记录器
    
    Returns:
        logging.Logger: 日志记录器实例
    
    使用示例：
        >>> # 默认日志记录器
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        
        >>> # 请求日志记录器
        >>> request_logger = get_logger('request', 'request')
        >>> request_logger.info("Request received", extra={
        ...     'method': 'POST',
        ...     'path': '/api/v1/chat',
        ...     'client_ip': '127.0.0.1'
        ... })
        
        >>> # 数据库日志记录器
        >>> db_logger = get_logger('database', 'database')
        >>> db_logger.info("Database query executed", extra={
        ...     'query': 'SELECT * FROM sessions',
        ...     'duration': 0.123
        ... })
    """
    if logger_type:
        return logging.getLogger(logger_type)
    return logging.getLogger(name)


# 初始化日志系统
setup_logging()