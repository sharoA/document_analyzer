#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体集成模块
根据需求文档和详细设计文档自动生成高质量的代码，并完成相关的开发流程
"""

from .coder_agent import CoderAgent
from .task_planner import TaskPlanner  
from .code_generator import CodeGenerator
from .test_generator import TestGenerator
from .git_manager import GitManager
from .workflow_engine import WorkflowEngine

__all__ = [
    'CoderAgent',
    'TaskPlanner',
    'CodeGenerator', 
    'TestGenerator',
    'GitManager',
    'WorkflowEngine'
]

__version__ = "1.0.0"
__description__ = """
编码智能体集成模块提供以下功能：

1. 编码智能体核心 (coder_agent.py)
   - 主要的编码智能体控制器
   - 协调各个子模块的工作
   - 管理整个开发流程

2. 任务规划器 (task_planner.py)
   - 解析markdown详细设计文档
   - 分解开发任务
   - 制定执行计划

3. 代码生成器 (code_generator.py)
   - 基于设计文档生成后端代码（Java8 + Spring Boot）
   - 生成前端代码（Vue2）
   - 遵循DDD架构模式

4. 测试生成器 (test_generator.py)  
   - 生成单元测试
   - 执行测试并生成报告
   - 管理测试项目结构

5. Git管理器 (git_manager.py)
   - Git分支管理
   - 代码提交和推送
   - 版本控制操作

6. 工作流引擎 (workflow_engine.py)
   - 基于LangChain/LangGraph的工作流编排
   - 状态管理和流程控制
   - 错误处理和重试机制
""" 