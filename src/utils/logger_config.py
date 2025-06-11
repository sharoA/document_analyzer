#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一日志配置模块
用于整个智能分析系统的日志初始化和管理
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """按日期轮转的文件处理器，支持按月份创建子目录"""
    
    def __init__(self, base_dir, filename_prefix, when='midnight', interval=1, backupCount=30, encoding='utf-8'):
        self.base_dir = Path(base_dir)
        self.filename_prefix = filename_prefix
        
        # 确保基础目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建当前月份目录和日志文件路径
        current_month = datetime.now().strftime('%Y-%m')
        self.current_month_dir = self.base_dir / current_month
        self.current_month_dir.mkdir(exist_ok=True)
        
        # 生成完整的日志文件路径
        log_filename = self.current_month_dir / f"{filename_prefix}.log"
        
        super().__init__(
            str(log_filename),
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding
        )
        
        # 设置日志文件后缀格式
        self.suffix = '%Y-%m-%d'
    
    def doRollover(self):
        """执行日志轮转，如果需要则创建新的月份目录"""
        # 检查是否需要创建新的月份目录
        current_month = datetime.now().strftime('%Y-%m')
        new_month_dir = self.base_dir / current_month
        
        if new_month_dir != self.current_month_dir:
            # 需要创建新的月份目录
            new_month_dir.mkdir(exist_ok=True)
            self.current_month_dir = new_month_dir
            
            # 更新文件路径
            new_log_filename = self.current_month_dir / f"{self.filename_prefix}.log"
            
            # 关闭当前文件
            if self.stream:
                self.stream.close()
                self.stream = None
            
            # 更新基础文件名
            self.baseFilename = str(new_log_filename)
        
        # 执行标准轮转
        super().doRollover()

class LoggerManager:
    """日志管理器"""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def initialize(cls, config: Dict[str, Any] = None):
        """
        初始化日志系统
        
        Args:
            config: 日志配置字典，如果为None则使用默认配置
        """
        if cls._initialized:
            return
        
        # 获取配置
        if config is None:
            config = cls._get_default_config()
        
        # 确保日志目录存在
        log_dir = Path(config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        # 创建按日期分组的子目录
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m')
        monthly_dir = log_dir / today
        monthly_dir.mkdir(exist_ok=True)
        
        # 移除现有的根日志处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置根日志级别
        log_level = getattr(logging, config.get('level', 'INFO').upper())
        root_logger.setLevel(log_level)
        
        # 创建格式器
        formatter = logging.Formatter(
            config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 2. 文件处理器 - 主应用日志（按日期轮转，按月分目录）
        file_handler = DailyRotatingFileHandler(
            base_dir=log_dir,
            filename_prefix='app',
            when='midnight',
            interval=1,
            backupCount=config.get('backup_count', 30)
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 3. API服务器专用日志（按日期轮转，按月分目录）
        api_handler = DailyRotatingFileHandler(
            base_dir=log_dir,
            filename_prefix='api_server',
            when='midnight',
            interval=1,
            backupCount=config.get('backup_count', 30)
        )
        api_handler.setLevel(log_level)
        api_handler.setFormatter(formatter)
        
        # 为API相关的logger添加专用处理器
        api_logger = logging.getLogger('api_server')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(log_level)
        
        # 4. 分析服务专用日志（按日期轮转，按月分目录）
        analysis_handler = DailyRotatingFileHandler(
            base_dir=log_dir,
            filename_prefix='analysis_service',
            when='midnight',
            interval=1,
            backupCount=config.get('backup_count', 30)
        )
        analysis_handler.setLevel(log_level)
        analysis_handler.setFormatter(formatter)
        
        # 为分析服务相关的logger添加专用处理器
        analysis_logger = logging.getLogger('analysis_service')
        analysis_logger.addHandler(analysis_handler)
        analysis_logger.setLevel(log_level)
        
        # 5. 错误专用日志（按日期轮转，按月分目录）
        error_handler = DailyRotatingFileHandler(
            base_dir=log_dir,
            filename_prefix='error',
            when='midnight',
            interval=1,
            backupCount=config.get('backup_count', 30)
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        cls._initialized = True
        
        # 记录初始化信息
        logger = logging.getLogger('system')
        logger.info("=" * 50)
        logger.info("🚀 智能分析系统日志系统初始化完成")
        logger.info(f"📁 日志根目录: {log_dir.absolute()}")
        logger.info(f"📊 日志级别: {config.get('level', 'INFO')}")
        logger.info(f"📅 按日期轮转: 每天午夜自动轮转")
        logger.info(f"📂 按月分目录: logs/YYYY-MM/")
        logger.info(f"📝 主日志: logs/{monthly_dir.name}/app.log")
        logger.info(f"🔧 API日志: logs/{monthly_dir.name}/api_server.log")
        logger.info(f"🧪 分析日志: logs/{monthly_dir.name}/analysis_service.log")
        logger.info(f"❌ 错误日志: logs/{monthly_dir.name}/error.log")
        logger.info(f"🗂️ 保留天数: {config.get('backup_count', 30)} 天")
        logger.info("=" * 50)
    
    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """获取默认日志配置"""
        try:
            # 尝试从配置文件读取
            from ..resource.config import get_config
            config_obj = get_config()
            logging_config = config_obj.get_logging_config()
            
            return {
                'level': logging_config.get('level', 'INFO'),
                'format': logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'log_dir': 'logs',
                'app_log_file': logging_config.get('file', 'logs/app.log').split('/')[-1],
                'max_size': logging_config.get('max_size', 10*1024*1024),
                'backup_count': logging_config.get('backup_count', 5)
            }
        except:
            # 使用硬编码默认配置
            return {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'log_dir': 'logs',
                'app_log_file': 'app.log',
                'max_size': 10*1024*1024,
                'backup_count': 5
            }
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            配置好的日志器
        """
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def log_operation(cls, operation: str, details: str = "", level: str = "INFO"):
        """
        记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
            level: 日志级别
        """
        logger = cls.get_logger('operation')
        log_method = getattr(logger, level.lower(), logger.info)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        if details:
            log_method(f"[{timestamp}] 🔄 {operation} - {details}")
        else:
            log_method(f"[{timestamp}] 🔄 {operation}")
    
    @classmethod
    def log_api_request(cls, method: str, endpoint: str, status_code: int = None, duration: float = None):
        """
        记录API请求日志
        
        Args:
            method: HTTP方法
            endpoint: API端点
            status_code: 状态码
            duration: 请求耗时
        """
        logger = cls.get_logger('api_server')
        
        status_emoji = "✅" if status_code and 200 <= status_code < 300 else "❌" if status_code and status_code >= 400 else "🔄"
        duration_str = f" ({duration:.2f}s)" if duration else ""
        status_str = f" [{status_code}]" if status_code else ""
        
        logger.info(f"{status_emoji} {method} {endpoint}{status_str}{duration_str}")
    
    @classmethod
    def log_analysis_step(cls, task_id: str, step: str, status: str = "进行中", details: str = ""):
        """
        记录分析步骤日志
        
        Args:
            task_id: 任务ID
            step: 步骤名称
            status: 步骤状态
            details: 详细信息
        """
        logger = cls.get_logger('analysis_service')
        
        status_emoji = {
            "开始": "🚀",
            "进行中": "🔄", 
            "完成": "✅",
            "失败": "❌",
            "跳过": "⏭️"
        }.get(status, "📝")
        
        message = f"[{task_id}] {status_emoji} {step} - {status}"
        if details:
            message += f" | {details}"
        
        logger.info(message)
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查日志系统是否已初始化"""
        return cls._initialized

# 便捷函数
def initialize_logging(config: Dict[str, Any] = None):
    """初始化日志系统"""
    LoggerManager.initialize(config)

def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return LoggerManager.get_logger(name)

def log_operation(operation: str, details: str = "", level: str = "INFO"):
    """记录操作日志"""
    LoggerManager.log_operation(operation, details, level)

def log_api_request(method: str, endpoint: str, status_code: int = None, duration: float = None):
    """记录API请求日志"""
    LoggerManager.log_api_request(method, endpoint, status_code, duration)

def log_analysis_step(task_id: str, step: str, status: str = "进行中", details: str = ""):
    """记录分析步骤日志"""
    LoggerManager.log_analysis_step(task_id, step, status, details) 