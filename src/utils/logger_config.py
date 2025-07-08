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
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    自定义的按日期轮转文件处理器，支持按月分目录
    线程安全的日志轮转机制，适用于Windows环境
    """
    
    # 类级别的锁，用于保护轮转操作
    _rollover_lock = threading.Lock()
    
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
        """执行日志轮转，如果需要则创建新的月份目录"""
        # 使用类级别锁保护轮转操作，避免多线程冲突
        with self._rollover_lock:
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
                    
                    # 安全地关闭当前文件流
                    self._safe_close_stream()
                    
                    # 更新基础文件名
                    self.baseFilename = str(new_log_filename)
                
                # 执行标准轮转（带重试机制）
                self._safe_rollover_enhanced()
                
            except Exception as e:
                # 如果轮转失败，记录错误但不中断程序
                print(f"日志轮转失败: {e}", file=sys.stderr)
                # 尝试重新打开文件流
                self._ensure_stream_open()

    def _safe_close_stream(self):
        """安全地关闭文件流"""
        if self.stream:
            try:
                self.stream.flush()
                self.stream.close()
                self.stream = None
            except Exception as e:
                print(f"关闭日志文件流失败: {e}", file=sys.stderr)
    

    

    
    def _ensure_stream_open(self):
        """确保文件流是打开的"""
        if self.stream is None:
            try:
                self.stream = self._open()
            except Exception as e:
                print(f"重新打开日志文件失败: {e}", file=sys.stderr)
    
    def emit(self, record):
        """
        重写emit方法，添加异常处理，避免日志写入失败导致程序崩溃
        """
        try:
            super().emit(record)
        except Exception as e:
            # 日志写入失败时，尝试输出到stderr，但不中断程序
            try:
                print(f"日志写入失败: {e}", file=sys.stderr)
                print(f"失败的日志记录: {self.format(record)}", file=sys.stderr)
            except:
                # 如果连stderr都失败了，就静默忽略
                pass

    def _safe_rollover_enhanced(self):
        """增强的安全日志轮转，特别针对Windows文件锁定问题"""
        max_retries = 5
        base_delay = 0.1
        
        # 首先尝试关闭所有可能的文件句柄
        self._force_close_handles()
        
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt)  # 指数退避
                
                if attempt > 0:
                    print(f"日志轮转重试 {attempt}/{max_retries}", file=sys.stderr)
                    time.sleep(delay)
                
                # 对于Windows，我们使用更温和的轮转策略
                if os.name == 'nt':  # Windows
                    self._windows_safe_rollover()
                else:
                    # Unix/Linux系统使用标准轮转
                    super().doRollover()
                
                # 轮转成功，重新打开文件流
                self._ensure_stream_open()
                return
                
            except (PermissionError, OSError) as e:
                if attempt == max_retries - 1:
                    # 最终失败，使用备用策略
                    print(f"日志轮转最终失败，使用备用策略: {e}", file=sys.stderr)
                    self._fallback_rollover_enhanced()
                    return
                    
            except Exception as e:
                print(f"日志轮转异常: {e}", file=sys.stderr)
                self._fallback_rollover_enhanced()
                return
        
    def _force_close_handles(self):
        """强制关闭所有可能的文件句柄"""
        try:
            if hasattr(self, 'stream') and self.stream:
                self.stream.flush()
                self.stream.close()
                self.stream = None
            
            # 给系统一点时间释放文件句柄
            time.sleep(0.05)
            
        except Exception as e:
            print(f"强制关闭文件句柄失败: {e}", file=sys.stderr)
    
    def _windows_safe_rollover(self):
        """Windows安全轮转策略"""
        import tempfile
        
        # 获取当前日志文件路径
        current_file = Path(self.baseFilename)
        
        if not current_file.exists():
            return
        
        # 生成带时间戳的备份文件名
        timestamp = datetime.now().strftime('%Y-%m-%d')
        backup_file = current_file.parent / f"{current_file.stem}.{timestamp}"
        
        # 如果备份文件已存在，添加序号
        counter = 1
        while backup_file.exists():
            backup_file = current_file.parent / f"{current_file.stem}.{timestamp}.{counter}"
            counter += 1
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', 
                prefix=f"{self.filename_prefix}_", 
                suffix='.log',
                dir=current_file.parent,
                delete=False,
                encoding=self.encoding
            ) as temp_file:
                temp_path = Path(temp_file.name)
            
            # 将当前文件重命名为备份文件
            current_file.rename(backup_file)
            
            # 将临时文件重命名为当前文件
            temp_path.rename(current_file)
            
            print(f"日志轮转完成: {current_file} -> {backup_file}", file=sys.stderr)
            
        except Exception as e:
            print(f"Windows安全轮转失败: {e}", file=sys.stderr)
            raise

    def _fallback_rollover_enhanced(self):
        """增强的备用轮转策略"""
        try:
            current_file = Path(self.baseFilename)
            
            # 策略1: 如果文件太大，尝试创建备份
            if current_file.exists():
                file_size = current_file.stat().st_size
                
                if file_size > 10 * 1024 * 1024:  # 大于10MB
                    # 生成唯一的备份文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    backup_file = current_file.parent / f"{current_file.stem}_{timestamp}.log"
                    
                    try:
                        # 尝试复制内容到备份文件
                        shutil.copy2(current_file, backup_file)
                        print(f"创建日志备份: {backup_file}", file=sys.stderr)
                        
                        # 清空原文件
                        with open(current_file, 'w', encoding=self.encoding) as f:
                            f.write(f"# 日志轮转于 {datetime.now()}\n")
                            
                    except Exception as e:
                        print(f"备份策略失败: {e}", file=sys.stderr)
                        # 如果备份失败，创建一个新文件
                        self._create_new_log_file()
                else:
                    # 文件不大，直接清空
                    try:
                        with open(current_file, 'w', encoding=self.encoding) as f:
                            f.write(f"# 日志轮转于 {datetime.now()}\n")
                    except Exception as e:
                        print(f"清空日志文件失败: {e}", file=sys.stderr)
                        self._create_new_log_file()
            
            # 确保文件流重新打开
            self._ensure_stream_open()
            
        except Exception as e:
            print(f"增强备用轮转策略失败: {e}", file=sys.stderr)
            self._create_new_log_file()
    
    def _create_new_log_file(self):
        """创建新的日志文件（最后手段）"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            current_file = Path(self.baseFilename)
            new_file = current_file.parent / f"{current_file.stem}_{timestamp}.log"
            
            # 更新基础文件名
            self.baseFilename = str(new_file)
            
            # 创建新文件
            with open(new_file, 'w', encoding=self.encoding) as f:
                f.write(f"# 新日志文件创建于 {datetime.now()}\n")
            
            print(f"创建新日志文件: {new_file}", file=sys.stderr)
            
        except Exception as e:
            print(f"创建新日志文件失败: {e}", file=sys.stderr)

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
        try:
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
        except Exception as e:
            print(f"创建主应用日志处理器失败: {e}", file=sys.stderr)
        
        # 3. API服务器专用日志（按日期轮转，按月分目录）
        try:
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
        except Exception as e:
            print(f"创建API服务器日志处理器失败: {e}", file=sys.stderr)
        
        # 4. 分析服务专用日志（按日期轮转，按月分目录）
        try:
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
        except Exception as e:
            print(f"创建分析服务日志处理器失败: {e}", file=sys.stderr)
        
        # 5. 错误专用日志（按日期轮转，按月分目录）
        try:
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
        except Exception as e:
            print(f"创建错误日志处理器失败: {e}", file=sys.stderr)
        
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