# -*- coding: utf-8 -*-
"""
Document Analyzer with Coder Agent Integration
文档分析器与编码智能体集成
"""

# 保持现有导出
try:
    from .utils import (
        TaskStorage,
        get_task_storage,
        OpenAIClient,
        get_openai_client
    )
except ImportError:
    pass

__version__ = "1.1.0"
__description__ = "Document Analyzer with AI-Powered Code Generation" 