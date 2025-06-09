#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
包含各种实用工具类和函数
"""

# 使用绝对导入避免相对导入问题
try:
    from src.resource.config import (
        Config,
        get_config,
        get_logs_dir,
        get_uploads_dir,
        get_temp_dir,
        get_analysis_results_dir,
        get_cache_dir
    )
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    try:
        from ..resource.config import (
            Config,
            get_config,
            get_logs_dir,
            get_uploads_dir,
            get_temp_dir,
            get_analysis_results_dir,
            get_cache_dir
        )
    except ImportError:
        # 如果都失败，提供默认实现
        print("警告: 无法导入配置模块，使用默认配置")
        
        class Config:
            def get(self, key, default=None):
                return default
        
        def get_config():
            return Config()
        
        def get_logs_dir():
            return "logs"
        
        def get_uploads_dir():
            return "uploads"
        
        def get_temp_dir():
            return "uploads/temp"
        
        def get_analysis_results_dir():
            return "uploads/analysis_results"
        
        def get_cache_dir():
            return "uploads/cache"

try:
    from .task_storage import (
        TaskStorage,
        get_task_storage
    )
except ImportError:
    print("警告: 无法导入任务存储模块")
    TaskStorage = None
    get_task_storage = None

try:
    from .volcengine_client import (
        VolcengineConfig,
        VolcengineClient
    )
except ImportError:
    print("警告: 无法导入火山引擎客户端模块")
    VolcengineConfig = None
    VolcengineClient = None

try:
    from .openai_client import (
        OpenAIConfig,
        OpenAIClient
    )
except ImportError:
    print("警告: 无法导入OpenAI客户端模块")
    OpenAIConfig = None
    OpenAIClient = None

try:
    from .llm_logger import (
        DailyRotatingFileHandler,
        LLMLogger,
        log_llm_request,
        log_llm_response
    )
except ImportError:
    print("警告: 无法导入LLM日志模块")
    DailyRotatingFileHandler = None
    LLMLogger = None
    log_llm_request = None
    log_llm_response = None

__all__ = [
    # 配置管理
    'Config',
    'get_config',
    'get_logs_dir',
    'get_uploads_dir',
    'get_temp_dir',
    'get_analysis_results_dir',
    'get_cache_dir',
    
    # 任务存储
    'TaskStorage',
    'get_task_storage',
    
    # LLM客户端
    'VolcengineConfig',
    'VolcengineClient',
    'OpenAIConfig',
    'OpenAIClient',
    
    # 日志记录
    'DailyRotatingFileHandler',
    'LLMLogger',
    'log_llm_request',
    'log_llm_response'
]

__version__ = "1.0.0"
__description__ = """
工具模块提供了以下功能：

1. 配置管理 (config.py)
   - 应用程序配置加载和管理
   - 支持YAML和JSON格式
   - 目录路径管理
   - 各种服务配置

2. 任务存储 (task_storage.py)
   - 文件解析任务的存储和检索
   - SQLite数据库支持
   - 任务状态跟踪
   - 步骤进度管理

3. LLM客户端 (volcengine_client.py, openai_client.py)
   - 火山引擎API客户端
   - OpenAI API客户端
   - 统一的接口设计
   - 错误处理和重试机制

4. 日志记录 (llm_logger.py)
   - LLM交互日志记录
   - 日志文件轮转
   - 结构化日志输出
   - 请求响应跟踪
""" 