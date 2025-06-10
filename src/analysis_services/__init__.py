#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析服务模块
提供文档解析、内容分析和AI智能分析功能
"""

# 核心服务类
from .base_service import BaseAnalysisService
from .document_parser import DocumentParserService
from .content_analyzer import ContentAnalyzerService
from .ai_analyzer import AIAnalyzerService

# 向量数据库
from .vector_database import (
    VectorDatabase,
    MockVectorDatabase,
    ChromaVectorDatabase,
    VectorDatabaseFactory
)

# 服务管理器 - 使用同步版本
from .sync_service_manager import (
    SyncAnalysisServiceManager,
    initialize_service_manager,
    get_service_manager
)

# 工具函数 - 使用绝对导入避免相对导入问题
try:
    from src.utils.analysis_utils import (
        TextProcessor,
        DataValidator,
        HashGenerator,
        TimeUtils,
        FileUtils,
        LoggerUtils,
        ErrorHandler,
        validate_file_upload,
        save_analysis_result,
        ensure_analysis_directories,
        setup_analysis_logger,
        validate_input
    )
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    try:
        from ..utils.analysis_utils import (
            TextProcessor,
            DataValidator,
            HashGenerator,
            TimeUtils,
            FileUtils,
            LoggerUtils,
            ErrorHandler,
            validate_file_upload,
            save_analysis_result,
            ensure_analysis_directories,
            setup_analysis_logger,
            validate_input
        )
    except ImportError:
        print("警告: 无法导入分析工具模块，某些功能可能不可用")
        # 提供空的占位符
        TextProcessor = None
        DataValidator = None
        HashGenerator = None
        TimeUtils = None
        FileUtils = None
        LoggerUtils = None
        ErrorHandler = None
        validate_file_upload = None
        save_analysis_result = None
        ensure_analysis_directories = None
        setup_analysis_logger = None
        validate_input = None

# 配置函数 - 使用绝对导入避免相对导入问题
try:
    from src.resource.config import (
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
            get_logs_dir,
            get_uploads_dir,
            get_temp_dir,
            get_analysis_results_dir,
            get_cache_dir
        )
    except ImportError:
        print("警告: 无法导入配置模块，使用默认配置")
        # 提供默认实现
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

__all__ = [
    # 核心服务
    'BaseAnalysisService',
    'DocumentParserService',
    'ContentAnalyzerService',
    'AIAnalyzerService',
    
    # 向量数据库
    'VectorDatabase',
    'MockVectorDatabase',
    'ChromaVectorDatabase',
    'VectorDatabaseFactory',
    
    # 服务管理
    'SyncAnalysisServiceManager',
    'initialize_service_manager',
    'get_service_manager',
    
    # 工具类
    'TextProcessor',
    'DataValidator',
    'HashGenerator',
    'TimeUtils',
    'FileUtils',
    'LoggerUtils',
    'ErrorHandler',
    
    # 工具函数
    'validate_file_upload',
    'save_analysis_result',
    'ensure_analysis_directories',
    'setup_analysis_logger',
    'validate_input',
    
    # 配置函数
    'get_logs_dir',
    'get_uploads_dir',
    'get_temp_dir',
    'get_analysis_results_dir',
    'get_cache_dir'
]

__version__ = "1.0.0"
__description__ = """
分析服务模块提供了以下核心功能：

1. 文档解析服务 (DocumentParserService)
   - 支持多种文档格式：PDF、Word、PowerPoint、文本文件
   - 提取文档内容、元数据和结构信息
   - 智能内容清理和格式化

2. 内容分析服务 (ContentAnalyzerService)
   - 文本统计分析：字数、段落数、关键词频率
   - 语义分析：主题提取、情感分析
   - 结构分析：章节识别、层次结构
   - CRUD操作识别：增删改查功能点提取

3. AI智能分析服务 (AIAnalyzerService)
   - 需求分析：功能需求、非功能需求识别
   - 架构设计：系统架构、技术栈推荐
   - API设计：接口规范、数据模型设计
   - 代码生成：基础代码框架生成

4. 向量数据库支持 (VectorDatabase)
   - 文档向量化存储
   - 语义相似性搜索
   - 支持多种向量数据库：Chroma、Mock等

5. 统一服务管理 (AnalysisServiceManager)
   - 服务生命周期管理
   - 统一的分析流水线
   - 错误处理和日志记录
   - 结果聚合和报告生成

6. 目录管理
   - logs/: 日志文件存储
   - uploads/: 文件上传根目录
     - temp/: 临时文件
     - analysis_results/: 分析结果
     - cache/: 缓存文件
"""

# 初始化时确保目录存在
try:
    ensure_analysis_directories()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"初始化目录失败: {e}") 