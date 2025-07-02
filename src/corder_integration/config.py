#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体配置管理
"""

import os
import yaml
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class CoderAgentConfig:
    """编码智能体配置"""
    
    # 项目路径配置
    project_root: str = "D:/new_project"
    tasks_dir: str = "tasks"
    test_project_dir: str = "test-project"
    tech_stack_docs_dir: str = "docs/tech-stack"
    
    # Git配置
    default_branch_pattern: str = "D_{timestamp}_aigc"
    git_commit_prefix: Dict[str, str] = None
    
    # 代码生成配置
    backend_framework: str = "spring_boot"
    backend_version: str = "2.7.x"
    backend_java_version: str = "8"
    frontend_framework: str = "vue2"
    backend_package_prefix: str = "com"
    
    # 测试配置
    test_coverage_target: float = 0.8
    backend_test_framework: str = "junit5"
    frontend_test_framework: str = "jest"
    
    # AI配置
    ai_provider: str = "volcengine"  # AI提供商：openai 或 volcengine
    code_generation_model: str = "ep-20250605091804-wmw6w"
    review_model: str = "ep-20250605091804-wmw6w"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # 模板配置
    backend_template_path: str = "templates/back_construct.md"
    frontend_template_path: str = "templates/fronted_construct.md"
    
    def __post_init__(self):
        if self.git_commit_prefix is None:
            self.git_commit_prefix = {
                "feat": "新功能",
                "fix": "修复问题", 
                "test": "添加测试",
                "docs": "文档更新",
                "refactor": "重构代码",
                "style": "代码格式",
                "chore": "构建变更"
            }

class CoderConfigManager:
    """编码智能体配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config = None
        self._coder_config = None
    
    def load_config(self) -> CoderAgentConfig:
        """加载配置"""
        if self._coder_config is not None:
            return self._coder_config
        
        # 加载主配置文件
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            self._config = {}
        
        # 获取编码智能体配置
        coder_config_data = self._config.get('coder_agent', {})
        
        # 展平嵌套配置
        flattened_config = {}
        for key, value in coder_config_data.items():
            if isinstance(value, dict):
                # 处理嵌套配置，如git_config, code_generation等
                if key == 'git_config':
                    # 将git_config下的配置提升到顶层
                    if 'default_branch_pattern' in value:
                        flattened_config['default_branch_pattern'] = value['default_branch_pattern']
                    if 'commit_prefix' in value:
                        flattened_config['git_commit_prefix'] = value['commit_prefix']
                elif key == 'code_generation':
                    # 将code_generation下的配置提升到顶层
                    flattened_config.update(value)
                # 忽略其他嵌套配置，保持向后兼容
            else:
                flattened_config[key] = value
        
        # 创建配置对象
        self._coder_config = CoderAgentConfig(**flattened_config)
        
        return self._coder_config
    
    def get_project_path(self, relative_path: str = "") -> str:
        """获取项目路径"""
        config = self.load_config()
        base_path = Path(config.project_root)
        if relative_path:
            return str(base_path / relative_path)
        return str(base_path)
    
    def get_tasks_dir(self) -> str:
        """获取任务目录"""
        config = self.load_config()
        return self.get_project_path(config.tasks_dir)
    
    def get_test_project_dir(self) -> str:
        """获取测试项目目录"""
        config = self.load_config()
        return self.get_project_path(config.test_project_dir)
    
    def get_tech_stack_docs_dir(self) -> str:
        """获取技术栈文档目录"""
        config = self.load_config()
        return self.get_project_path(config.tech_stack_docs_dir)
    
    def get_backend_template(self) -> str:
        """获取后端模板路径"""
        config = self.load_config()
        return config.backend_template_path
    
    def get_frontend_template(self) -> str:
        """获取前端模板路径"""
        config = self.load_config()
        return config.frontend_template_path

# 全局配置管理器实例
_config_manager = CoderConfigManager()

def get_coder_config() -> CoderAgentConfig:
    """获取编码智能体配置"""
    return _config_manager.load_config()

def get_config_manager() -> CoderConfigManager:
    """获取配置管理器"""
    return _config_manager 