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
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class SimpleDailyRotatingHandler(logging.handlers.TimedRotatingFileHandler):
    """
    简化的按日期轮转文件处理器
    去除复杂的Windows兼容性处理，避免生成过多临时文件
    """
    
    def __init__(self, base_dir, filename_prefix, when='midnight', interval=1, backupCount=30, encoding='utf-8'):
        self.base_dir = Path(base_dir)
        self.filename_prefix = filename_prefix
        
        # 创建当前月份目录
        current_month = datetime.now().strftime('%Y-%m')
        self.current_month_dir = self.base_dir / current_month
        self.current_month_dir.mkdir(parents=True, exist_ok=True)
        
        # 构建完整的日志文件路径
        log_filename = self.current_month_dir / f"{filename_prefix}.log"
        
        # 调用父类构造函数
        super().__init__(
            filename=str(log_filename),
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding
        )
    
    def doRollover(self):
        """简化的日志轮转，如果需要则创建新的月份目录"""
        try:
            # 检查是否需要创建新的月份目录
            current_month = datetime.now().strftime('%Y-%m')
            new_month_dir = self.base_dir / current_month
            
            if new_month_dir != self.current_month_dir:
                # 需要创建新的月份目录
                new_month_dir.mkdir(exist_ok=True)
                self.current_month_dir = new_month_dir
                
                # 更新文件路径
                new_log_filename = self.current_month_dir / f"{self.filename_prefix}.log"
                
                # 关闭当前文件流
                if self.stream:
                    self.stream.close()
                    self.stream = None
                
                # 更新基础文件名
                self.baseFilename = str(new_log_filename)
            
            # 执行标准轮转
            super().doRollover()
            
        except Exception as e:
            # 简单的错误处理，不创建额外文件
            print(f"日志轮转失败: {e}", file=sys.stderr)
            # 尝试重新打开当前文件
            if self.stream is None:
                try:
                    self.stream = self._open()
                except Exception:
                    pass

class LoggerManager:
    """日志管理器 - 线程安全的日志系统管理"""
    
    _initialized = False
    _loggers = {}
    _init_lock = threading.Lock()
    
    @classmethod
    def initialize(cls, config: Dict[str, Any] = None):
        """
        初始化日志系统 - 线程安全
        
        Args:
            config: 日志配置字典，如果为None则使用默认配置
        """
        # 双重检查锁定模式，确保线程安全的单例初始化
        if cls._initialized:
            return
            
        with cls._init_lock:
            if cls._initialized:
                return
        
        # 获取配置
        if config is None:
            config = cls._get_default_config()
        
        # 确保日志目录存在
        log_dir = Path(config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)
        
        # 创建按日期分组的子目录
        current_month = datetime.now().strftime('%Y-%m')
        monthly_dir = log_dir / current_month
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
        
        # 2. 主应用日志（简化轮转）
        try:
            file_handler = SimpleDailyRotatingHandler(
                base_dir=log_dir,
                filename_prefix='app',
                when='midnight',
                interval=1,
                backupCount=config.get('backup_count', 30)
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"创建主应用日志处理器失败: {e}", file=sys.stderr)
        
        # 3. API服务器专用日志（简化轮转）
        try:
            api_handler = SimpleDailyRotatingHandler(
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
            # 防止传播到根logger，避免重复记录
            api_logger.propagate = False
        except Exception as e:
            print(f"创建API服务器日志处理器失败: {e}", file=sys.stderr)
        
        # 4. 只在有实际错误时创建错误日志（移除预创建的错误处理器）
        # 不再预创建错误日志处理器，避免空文件
        
        cls._initialized = True
        
        # 记录初始化信息
        logger = logging.getLogger('system')
        logger.info("=" * 50)
        logger.info("🚀 智能分析系统日志系统初始化完成")
        logger.info(f"📁 日志根目录: {log_dir.absolute()}")
        logger.info(f"📊 日志级别: {config.get('level', 'INFO')}")
        logger.info(f"📅 按日期轮转: 每天午夜自动轮转")
        logger.info(f"📂 按月分目录: logs/YYYY-MM/")
        logger.info(f"📝 主日志: logs/{current_month}/app.log")
        logger.info(f"🔧 API日志: logs/{current_month}/api_server.log")
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
                'backup_count': logging_config.get('backup_count', 7)  # 减少到7天
            }
        except:
            # 使用硬编码默认配置
            return {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'log_dir': 'logs',
                'backup_count': 7  # 减少到7天
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
    def create_error_logger_if_needed(cls):
        """只在有实际错误时才创建错误日志处理器"""
        if hasattr(cls, '_error_handler_created'):
            return
            
        try:
            log_dir = Path('logs')
            current_month = datetime.now().strftime('%Y-%m')
            monthly_dir = log_dir / current_month
            monthly_dir.mkdir(parents=True, exist_ok=True)
            
            error_handler = SimpleDailyRotatingHandler(
                base_dir=log_dir,
                filename_prefix='error',
                when='midnight',
                interval=1,
                backupCount=7
            )
            error_handler.setLevel(logging.ERROR)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            error_handler.setFormatter(formatter)
            
            root_logger = logging.getLogger()
            root_logger.addHandler(error_handler)
            
            cls._error_handler_created = True
            
        except Exception as e:
            print(f"创建错误日志处理器失败: {e}", file=sys.stderr)
    
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
            status: 状态
            details: 详细信息
        """
        logger = cls.get_logger('analysis')
        status_emoji = "✅" if status == "完成" else "❌" if status == "失败" else "🔄"
        details_str = f" - {details}" if details else ""
        
        logger.info(f"{status_emoji} [{task_id}] {step}: {status}{details_str}")
    
    @classmethod
    def log_error(cls, error: Exception, context: str = ""):
        """
        记录错误日志，只在有实际错误时创建错误日志文件
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        # 只在有实际错误时才创建错误日志处理器
        cls.create_error_logger_if_needed()
        
        logger = cls.get_logger('error')
        context_str = f"[{context}] " if context else ""
        logger.error(f"{context_str}❌ {str(error)}", exc_info=True)
    
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

def log_error(error: Exception, context: str = ""):
    """记录错误日志"""
    LoggerManager.log_error(error, context) 