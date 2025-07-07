#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LangGraph编码智能体Jinja2模版生成器

基于配置文件和Jinja2模版，生成可执行的LangGraph编码智能体实现。

使用方法:
    python template_generator.py --config project_config.yaml --template LangGraph_Jinja2_Template.md --output generated_implementation.md

功能特性:
    - 支持多种配置文件格式（YAML、JSON）
    - 灵活的模版变量替换
    - 内置验证和错误处理
    - 多种输出格式支持
    - 批量生成支持
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import json
from jinja2 import Environment, FileSystemLoader, Template
from jinja2.exceptions import TemplateError, TemplateNotFound
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('template_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TemplateGenerator:
    """LangGraph编码智能体模版生成器"""
    
    def __init__(self, template_dir: str = "."):
        """
        初始化模版生成器
        
        Args:
            template_dir: 模版文件目录
        """
        self.template_dir = Path(template_dir)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 注册自定义过滤器
        self.jinja_env.filters['indent'] = self._indent_filter
        self.jinja_env.filters['snake_case'] = self._snake_case_filter
        self.jinja_env.filters['camel_case'] = self._camel_case_filter
        self.jinja_env.filters['pascal_case'] = self._pascal_case_filter
        
        logger.info(f"模版生成器已初始化，模版目录: {self.template_dir}")
    
    @staticmethod
    def _indent_filter(text: str, indent: int = 4) -> str:
        """缩进过滤器"""
        if not text:
            return text
        lines = text.split('\n')
        return '\n'.join(' ' * indent + line if line.strip() else line for line in lines)
    
    @staticmethod
    def _snake_case_filter(text: str) -> str:
        """转换为snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()
    
    @staticmethod
    def _camel_case_filter(text: str) -> str:
        """转换为camelCase"""
        components = text.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    @staticmethod
    def _pascal_case_filter(text: str) -> str:
        """转换为PascalCase"""
        return ''.join(x.title() for x in text.split('_'))
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            配置字典
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
            
            logger.info(f"配置文件加载成功: {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        验证配置文件
        
        Args:
            config: 配置字典
            
        Returns:
            是否验证通过
        """
        required_fields = [
            'name', 'agent_name', 'state_class_name', 'orchestrator_class_name',
            'workflow_nodes', 'workflow_edges', 'condition_functions'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"配置文件缺少必填字段: {', '.join(missing_fields)}")
            return False
        
        # 验证工作流节点
        if not isinstance(config['workflow_nodes'], list) or len(config['workflow_nodes']) == 0:
            logger.error("workflow_nodes 必须是非空列表")
            return False
        
        # 验证工作流边
        if not isinstance(config['workflow_edges'], list) or len(config['workflow_edges']) == 0:
            logger.error("workflow_edges 必须是非空列表")
            return False
        
        # 验证条件函数
        if not isinstance(config['condition_functions'], list):
            logger.error("condition_functions 必须是列表")
            return False
        
        logger.info("配置文件验证通过")
        return True
    
    def render_template(self, template_file: str, config: Dict[str, Any]) -> str:
        """
        渲染模版
        
        Args:
            template_file: 模版文件路径
            config: 配置字典
            
        Returns:
            渲染后的内容
        """
        try:
            template = self.jinja_env.get_template(template_file)
            
            # 准备模版变量
            template_vars = {
                'project_config': config
            }
            
            # 渲染模版
            rendered_content = template.render(**template_vars)
            
            logger.info(f"模版渲染成功: {template_file}")
            return rendered_content
            
        except TemplateNotFound:
            logger.error(f"模版文件不存在: {template_file}")
            raise
        except TemplateError as e:
            logger.error(f"模版渲染错误: {e}")
            raise
        except Exception as e:
            logger.error(f"渲染模版时发生未知错误: {e}")
            raise
    
    def save_output(self, content: str, output_file: str) -> None:
        """
        保存输出文件
        
        Args:
            content: 渲染后的内容
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"输出文件保存成功: {output_file}")
            
        except Exception as e:
            logger.error(f"保存输出文件失败: {e}")
            raise
    
    def generate_project(self, config_file: str, template_file: str, output_file: str) -> None:
        """
        生成项目实现
        
        Args:
            config_file: 配置文件路径
            template_file: 模版文件路径
            output_file: 输出文件路径
        """
        try:
            # 加载配置
            config = self.load_config(config_file)
            
            # 验证配置
            if not self.validate_config(config):
                raise ValueError("配置文件验证失败")
            
            # 渲染模版
            rendered_content = self.render_template(template_file, config)
            
            # 保存输出
            self.save_output(rendered_content, output_file)
            
            logger.info(f"项目生成成功: {output_file}")
            
        except Exception as e:
            logger.error(f"生成项目失败: {e}")
            raise
    
    def batch_generate(self, config_files: List[str], template_file: str, output_dir: str) -> None:
        """
        批量生成项目
        
        Args:
            config_files: 配置文件列表
            template_file: 模版文件路径
            output_dir: 输出目录
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        failed_configs = []
        
        for config_file in config_files:
            try:
                config = self.load_config(config_file)
                project_name = config.get('name', 'unknown_project')
                
                output_file = output_path / f"{project_name}_implementation.md"
                
                self.generate_project(config_file, template_file, str(output_file))
                success_count += 1
                
            except Exception as e:
                logger.error(f"批量生成失败 - 配置文件: {config_file}, 错误: {e}")
                failed_configs.append(config_file)
        
        logger.info(f"批量生成完成 - 成功: {success_count}, 失败: {len(failed_configs)}")
        
        if failed_configs:
            logger.warning(f"失败的配置文件: {', '.join(failed_configs)}")
    
    def list_templates(self) -> List[str]:
        """列出可用的模版文件"""
        templates = []
        for file_path in self.template_dir.glob("*.md"):
            if "template" in file_path.name.lower() or "jinja" in file_path.name.lower():
                templates.append(file_path.name)
        return templates
    
    def create_sample_config(self, output_file: str) -> None:
        """创建示例配置文件"""
        sample_config = {
            "name": "MyProject",
            "agent_name": "我的编码智能体",
            "base_framework": "核心功能生成.md",
            "service_type": "微服务",
            "tech_stack": "Spring Boot",
            "state_class_name": "MyAgentState",
            "orchestrator_class_name": "MyWorkflowOrchestrator",
            "workflow_nodes": [
                {"name": "task_splitting", "function_name": "task_splitting_node"},
                {"name": "git_management", "function_name": "git_management_node"}
            ],
            "workflow_edges": [
                {"type": "simple", "from": "task_splitting", "to": "git_management"}
            ],
            "condition_functions": [
                {"name": "check_completion", "description": "检查完成状态", "logic": "return 'completed'"}
            ],
            "database": {"type": "memory"},
            "sample_requirements": "示例需求文档",
            "sample_design": "示例设计文档"
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"示例配置文件已创建: {output_file}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LangGraph编码智能体模版生成器")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成命令
    generate_parser = subparsers.add_parser('generate', help='生成项目实现')
    generate_parser.add_argument('--config', '-c', required=True, help='配置文件路径')
    generate_parser.add_argument('--template', '-t', required=True, help='模版文件路径')
    generate_parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    
    # 批量生成命令
    batch_parser = subparsers.add_parser('batch', help='批量生成项目')
    batch_parser.add_argument('--configs', nargs='+', required=True, help='配置文件列表')
    batch_parser.add_argument('--template', '-t', required=True, help='模版文件路径')
    batch_parser.add_argument('--output-dir', '-d', required=True, help='输出目录')
    
    # 列出模版命令
    list_parser = subparsers.add_parser('list', help='列出可用模版')
    list_parser.add_argument('--template-dir', default='.', help='模版目录')
    
    # 创建示例配置命令
    sample_parser = subparsers.add_parser('sample', help='创建示例配置文件')
    sample_parser.add_argument('--output', '-o', default='sample_config.yaml', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'generate':
            generator = TemplateGenerator()
            generator.generate_project(args.config, args.template, args.output)
            
        elif args.command == 'batch':
            generator = TemplateGenerator()
            generator.batch_generate(args.configs, args.template, args.output_dir)
            
        elif args.command == 'list':
            generator = TemplateGenerator(args.template_dir)
            templates = generator.list_templates()
            if templates:
                print("可用模版:")
                for template in templates:
                    print(f"  - {template}")
            else:
                print("未找到模版文件")
                
        elif args.command == 'sample':
            generator = TemplateGenerator()
            generator.create_sample_config(args.output)
            
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 