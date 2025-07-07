#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph编码智能体提示词模板

包含以下模板文件：
- task_splitting_prompts.jinja2: 任务拆分节点主提示词模板
- task_splitting_default_prompts.jinja2: 任务拆分节点默认提示词模板
- intelligent_coding_prompts.jinja2: 智能编码节点主提示词模板
- intelligent_coding_default_prompts.jinja2: 智能编码节点默认提示词模板

模板加载优先级：
1. 主提示词模板（详细版本）
2. 默认提示词模板（简化版本）
3. 内置提示词模板（最后备选）
"""

# 这个模块包含所有的Jinja2提示词模板文件 