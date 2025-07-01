#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务规划器
负责解析markdown详细设计文档，分解开发任务，制定执行计划
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .config import get_coder_config, get_config_manager
from ..utils.task_storage import get_task_storage

logger = logging.getLogger(__name__)

@dataclass
class TaskItem:
    """任务项"""
    id: str
    name: str
    description: str
    type: str  # backend, frontend, database, test
    priority: int  # 1-5, 1最高
    estimated_hours: float
    dependencies: List[str]  # 依赖的任务ID列表
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_module: str = ""  # 分配的模块
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ExecutionPlan:
    """执行计划"""
    plan_id: str
    project_name: str
    total_tasks: int
    estimated_total_hours: float
    tasks: List[TaskItem]
    dependencies_graph: Dict[str, List[str]]
    execution_order: List[str]  # 按执行顺序排列的任务ID
    created_at: str
    branch_name: str = ""
    project_structure: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['tasks'] = [task.to_dict() for task in self.tasks]
        return result

class DesignDocumentParser:
    """设计文档解析器"""
    
    def __init__(self):
        self.config = get_coder_config()
    
    def parse_markdown_document(self, document_content: str) -> Dict[str, Any]:
        """
        解析Markdown设计文档
        
        Args:
            document_content: 文档内容
            
        Returns:
            解析结果字典
        """
        result = {
            'project_info': self._extract_project_info(document_content),
            'technical_requirements': self._extract_technical_requirements(document_content),
            'business_logic': self._extract_business_logic(document_content),
            'api_design': self._extract_api_design(document_content),
            'database_design': self._extract_database_design(document_content),
            'ui_components': self._extract_ui_components(document_content),
            'branch_info': self._extract_branch_info(document_content),
            'git_info': self._extract_git_info(document_content),
            'project_structure': self._extract_project_structure(document_content)
        }
        
        logger.info("设计文档解析完成")
        return result
    
    def _extract_project_info(self, content: str) -> Dict[str, str]:
        """提取项目基本信息"""
        project_info = {}
        
        # 提取项目名称
        name_match = re.search(r'项目名称[：:]\s*(.+)', content, re.IGNORECASE)
        if name_match:
            project_info['name'] = name_match.group(1).strip()
        else:
            # 尝试从标题提取
            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            if title_match:
                project_info['name'] = title_match.group(1).strip()
        
        # 提取项目描述
        desc_match = re.search(r'项目描述[：:]\s*(.+)', content, re.IGNORECASE)
        if desc_match:
            project_info['description'] = desc_match.group(1).strip()
        
        # 提取版本信息
        version_match = re.search(r'版本[：:]\s*(.+)', content, re.IGNORECASE)
        if version_match:
            project_info['version'] = version_match.group(1).strip()
        
        return project_info
    
    def _extract_technical_requirements(self, content: str) -> Dict[str, Any]:
        """提取技术要求"""
        tech_requirements = {}
        
        # 提取后端技术栈
        backend_pattern = r'后端.*?技术.*?栈.*?[:：]\s*(.+?)(?=\n|前端|数据库|$)'
        backend_match = re.search(backend_pattern, content, re.IGNORECASE | re.DOTALL)
        if backend_match:
            tech_requirements['backend'] = backend_match.group(1).strip()
        
        # 提取前端技术栈
        frontend_pattern = r'前端.*?技术.*?栈.*?[:：]\s*(.+?)(?=\n|后端|数据库|$)'
        frontend_match = re.search(frontend_pattern, content, re.IGNORECASE | re.DOTALL)
        if frontend_match:
            tech_requirements['frontend'] = frontend_match.group(1).strip()
        
        # 提取数据库要求
        db_pattern = r'数据库.*?[:：]\s*(.+?)(?=\n|技术|架构|$)'
        db_match = re.search(db_pattern, content, re.IGNORECASE | re.DOTALL)
        if db_match:
            tech_requirements['database'] = db_match.group(1).strip()
        
        return tech_requirements
    
    def _extract_business_logic(self, content: str) -> List[Dict[str, str]]:
        """提取业务逻辑"""
        business_logic = []
        
        # 查找功能模块
        module_pattern = r'###?\s*(.+?功能|.+?模块|.+?服务).*?\n(.*?)(?=###?|$)'
        modules = re.findall(module_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for module_name, module_content in modules:
            business_logic.append({
                "module": module_name.strip(),
                "description": module_content.strip()[:500]  # 限制长度
            })
        
        return business_logic
    
    def _extract_api_design(self, content: str) -> List[Dict[str, str]]:
        """提取API设计"""
        apis = []
        
        # 查找API接口定义
        api_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+).*?\n(.+?)(?=GET|POST|PUT|DELETE|PATCH|###?|$)'
        api_matches = re.findall(api_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for method, path, description in api_matches:
            apis.append({
                "method": method.upper(),
                "path": path,
                "description": description.strip()[:200]
            })
        
        return apis
    
    def _extract_database_design(self, content: str) -> List[Dict[str, str]]:
        """提取数据库设计"""
        tables = []
        
        # 查找表结构定义
        table_pattern = r'(?:表|Table)[:：]\s*(\w+).*?\n(.*?)(?=(?:表|Table)[:：]|###?|$)'
        table_matches = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for table_name, table_desc in table_matches:
            tables.append({
                "name": table_name.strip(),
                "description": table_desc.strip()[:300]
            })
        
        return tables
    
    def _extract_ui_components(self, content: str) -> List[Dict[str, str]]:
        """提取UI组件"""
        components = []
        
        # 查找组件定义
        component_pattern = r'组件[:：]\s*(.+?)\n(.*?)(?=组件[:：]|###?|$)'
        comp_matches = re.findall(component_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for comp_name, comp_desc in comp_matches:
            components.append({
                "name": comp_name.strip(),
                "description": comp_desc.strip()[:200]
            })
        
        return components
    
    def _extract_git_info(self, content: str) -> Dict[str, str]:
        """提取Git相关信息"""
        git_info = {}
        
        # 查找Git仓库URL
        git_url_patterns = [
            r'(?:git\s*[:：]\s*|仓库\s*[:：]\s*|repository\s*[:：]\s*|远程仓库\s*[:：]\s*)(https?://[^\s]+\.git)',
            r'(?:git\s*[:：]\s*|仓库\s*[:：]\s*|repository\s*[:：]\s*|远程仓库\s*[:：]\s*)(git@[^\s]+\.git)',
            r'(https?://github\.com/[^/\s]+/[^/\s]+(?:\.git)?)',
            r'(https?://gitlab\.com/[^/\s]+/[^/\s]+(?:\.git)?)',
            r'(https?://gitee\.com/[^/\s]+/[^/\s]+(?:\.git)?)'
        ]
        
        for pattern in git_url_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                remote_url = match.group(1)
                # 确保URL以.git结尾
                if not remote_url.endswith('.git') and ('github.com' in remote_url or 'gitlab.com' in remote_url or 'gitee.com' in remote_url):
                    remote_url += '.git'
                git_info['remote_url'] = remote_url
                break
        
        # 查找Git用户信息
        user_patterns = [
            r'git\s*用户\s*[:：]\s*(.+)',
            r'git\s*user\s*[:：]\s*(.+)',
            r'作者\s*[:：]\s*(.+)'
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                git_info['user'] = match.group(1).strip()
                break
        
        return git_info
    
    def _extract_branch_info(self, content: str) -> Dict[str, str]:
        """提取分支信息"""
        branch_info = {}
        
        # 查找分支相关信息
        branch_patterns = [
            r'分支[:：]\s*(.+)',
            r'branch[:：]\s*(.+)',
            r'版本分支[:：]\s*(.+)',
            r'git\s+branch[:：]\s*(.+)'
        ]
        
        for pattern in branch_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                branch_info['name'] = match.group(1).strip()
                break
        
        # 查找远程仓库URL（为了向后兼容，也在branch_info中查找）
        remote_patterns = [
            r'远程[:：]\s*(https?://[^\s]+\.git)',
            r'remote[:：]\s*(https?://[^\s]+\.git)',
            r'远程仓库[:：]\s*(https?://[^\s]+\.git)'
        ]
        
        for pattern in remote_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                branch_info['remote_url'] = match.group(1).strip()
                break
        
        return branch_info
    
    def _extract_project_structure(self, content: str) -> Dict[str, Any]:
        """提取项目结构信息"""
        structure = {}
        
        # 查找目录结构
        structure_pattern = r'目录结构|项目结构|Project Structure'
        if re.search(structure_pattern, content, re.IGNORECASE):
            # 找到结构定义后的内容
            struct_match = re.search(
                r'(?:目录结构|项目结构|Project Structure).*?\n(.*?)(?=###?|$)',
                content, 
                re.DOTALL | re.IGNORECASE
            )
            if struct_match:
                structure['description'] = struct_match.group(1).strip()
        
        return structure

class TaskPlanner:
    """任务规划器"""
    
    def __init__(self):
        self.config = get_coder_config()
        self.config_manager = get_config_manager()
        self.document_parser = DesignDocumentParser()
        self.task_storage = get_task_storage()
    
    def create_execution_plan(
        self, 
        document_content: str, 
        project_name: Optional[str] = None
    ) -> ExecutionPlan:
        """
        创建执行计划
        
        Args:
            document_content: 设计文档内容
            project_name: 项目名称（可选，如果不提供则从git远程URL中提取）
            
        Returns:
            执行计划对象
        """
        logger.info("开始创建执行计划")
        
        # 解析设计文档
        parsed_doc = self.document_parser.parse_markdown_document(document_content)
        
        # 先确定分支名称
        branch_name = self._determine_branch_name(parsed_doc)
        
        # 如果没有提供项目名称，从git远程URL中提取
        if not project_name:
            project_name = self._extract_project_name_from_git_url(parsed_doc)
            # 如果从git URL提取失败，再尝试从文档中获取并规范化
            if not project_name or project_name == 'UnknownProject':
                doc_project_name = parsed_doc.get('project_info', {}).get('name', 'UnknownProject')
                project_name = self._normalize_project_name(doc_project_name)
        
        # 确保项目名称符合路径规范（无中文、无特殊字符）
        project_name = self._normalize_project_name(project_name)
        
        # 生成任务列表
        tasks = self._generate_tasks(parsed_doc)
        
        # 分析任务依赖关系
        dependencies_graph = self._analyze_dependencies(tasks)
        
        # 计算执行顺序
        execution_order = self._calculate_execution_order(tasks, dependencies_graph)
        
        # 创建执行计划
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            project_name=project_name,
            total_tasks=len(tasks),
            estimated_total_hours=sum(task.estimated_hours for task in tasks),
            tasks=tasks,
            dependencies_graph=dependencies_graph,
            execution_order=execution_order,
            created_at=datetime.now().isoformat(),
            branch_name=branch_name,
            project_structure=parsed_doc.get('project_structure')
        )
        
        logger.info(f"执行计划创建完成，共{len(tasks)}个任务，项目名称: {project_name}")
        return plan
    
    def _generate_tasks(self, parsed_doc: Dict[str, Any]) -> List[TaskItem]:
        """生成任务列表"""
        tasks = []
        task_id_counter = 1
        
        # 环境准备任务
        tasks.append(TaskItem(
            id=f"task_{task_id_counter:03d}",
            name="环境准备与分支管理",
            description="创建项目目录，切换Git分支，初始化项目结构",
            type="setup",
            priority=1,
            estimated_hours=0.5,
            dependencies=[],
            assigned_module="git_manager"
        ))
        task_id_counter += 1
        
        # 技术栈文档生成任务
        tasks.append(TaskItem(
            id=f"task_{task_id_counter:03d}",
            name="技术栈文档生成",
            description="生成backend-stack.md、frontend-stack.md等技术栈文档",
            type="docs",
            priority=2,
            estimated_hours=0.5,
            dependencies=["task_001"],
            assigned_module="code_generator"
        ))
        task_id_counter += 1
        
        # 后端任务生成
        backend_modules = parsed_doc.get('business_logic', [])
        for i, module in enumerate(backend_modules):
            tasks.append(TaskItem(
                id=f"task_{task_id_counter:03d}",
                name=f"后端开发 - {module.get('module', f'模块{i+1}')}",
                description=f"实现{module.get('module', f'模块{i+1}')}的后端逻辑",
                type="backend",
                priority=2,
                estimated_hours=2.0,
                dependencies=["task_002"],
                assigned_module="code_generator"
            ))
            task_id_counter += 1
        
        # API接口任务
        apis = parsed_doc.get('api_design', [])
        if apis:
            tasks.append(TaskItem(
                id=f"task_{task_id_counter:03d}",
                name="API接口实现",
                description=f"实现{len(apis)}个REST API接口",
                type="backend",
                priority=2,
                estimated_hours=len(apis) * 0.5,
                dependencies=["task_002"],
                assigned_module="code_generator"
            ))
            task_id_counter += 1
        
        # 数据库任务
        tables = parsed_doc.get('database_design', [])
        if tables:
            tasks.append(TaskItem(
                id=f"task_{task_id_counter:03d}",
                name="数据库层实现",
                description=f"实现{len(tables)}个数据表的Entity和Repository",
                type="database",
                priority=2,
                estimated_hours=len(tables) * 0.3,
                dependencies=["task_002"],
                assigned_module="code_generator"
            ))
            task_id_counter += 1
        
        # 前端任务生成
        ui_components = parsed_doc.get('ui_components', [])
        if ui_components:
            for i, component in enumerate(ui_components):
                tasks.append(TaskItem(
                    id=f"task_{task_id_counter:03d}",
                    name=f"前端组件 - {component.get('name', f'组件{i+1}')}",
                    description=f"实现{component.get('name', f'组件{i+1}')}前端组件",
                    type="frontend",
                    priority=3,
                    estimated_hours=1.5,
                    dependencies=["task_002"],
                    assigned_module="code_generator"
                ))
                task_id_counter += 1
        else:
            # 如果没有明确的组件，创建基础前端任务
            tasks.append(TaskItem(
                id=f"task_{task_id_counter:03d}",
                name="前端应用开发",
                description="创建Vue2前端应用，实现路由和基础组件",
                type="frontend",
                priority=3,
                estimated_hours=3.0,
                dependencies=["task_002"],
                assigned_module="code_generator"
            ))
            task_id_counter += 1
        
        # 单元测试任务
        tasks.append(TaskItem(
            id=f"task_{task_id_counter:03d}",
            name="后端单元测试",
            description="为后端代码编写JUnit单元测试",
            type="test",
            priority=4,
            estimated_hours=2.0,
            dependencies=[t.id for t in tasks if t.type == "backend"],
            assigned_module="test_generator"
        ))
        task_id_counter += 1
        
        tasks.append(TaskItem(
            id=f"task_{task_id_counter:03d}",
            name="前端单元测试",
            description="为前端组件编写Jest单元测试",
            type="test",
            priority=4,
            estimated_hours=1.5,
            dependencies=[t.id for t in tasks if t.type == "frontend"],
            assigned_module="test_generator"
        ))
        task_id_counter += 1
        
        # Git提交任务
        tasks.append(TaskItem(
            id=f"task_{task_id_counter:03d}",
            name="代码提交与推送",
            description="提交所有代码到Git仓库并推送到远程分支",
            type="git",
            priority=5,
            estimated_hours=0.5,
            dependencies=[t.id for t in tasks if t.type == "test"],
            assigned_module="git_manager"
        ))
        
        return tasks
    
    def _analyze_dependencies(self, tasks: List[TaskItem]) -> Dict[str, List[str]]:
        """分析任务依赖关系"""
        dependencies = {}
        
        for task in tasks:
            dependencies[task.id] = task.dependencies.copy()
        
        return dependencies
    
    def _calculate_execution_order(
        self, 
        tasks: List[TaskItem], 
        dependencies: Dict[str, List[str]]
    ) -> List[str]:
        """计算任务执行顺序（拓扑排序）"""
        from collections import defaultdict, deque
        
        # 构建图和入度表
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        # 初始化所有任务的入度为0
        for task in tasks:
            in_degree[task.id] = 0
        
        # 构建依赖图
        for task_id, deps in dependencies.items():
            for dep in deps:
                graph[dep].append(task_id)
                in_degree[task_id] += 1
        
        # 拓扑排序
        queue = deque([task_id for task_id in in_degree if in_degree[task_id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _determine_branch_name(self, parsed_doc: Dict[str, Any]) -> str:
        """确定Git分支名称"""
        branch_info = parsed_doc.get('branch_info', {})
        
        if branch_info.get('name'):
            return branch_info['name']
        else:
            # 尝试从项目信息中获取项目名称来生成默认分支
            project_info = parsed_doc.get('project_info', {})
            project_name = project_info.get('name', '')
            
            # 清理项目名称，移除特殊字符
            if project_name:
                # 移除特殊字符，保留字母数字和下划线
                clean_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', project_name)
                # 移除连续的下划线
                clean_name = re.sub(r'_+', '_', clean_name).strip('_')
                # 如果清理后的名称过长，截取前20个字符
                if len(clean_name) > 20:
                    clean_name = clean_name[:20]
                
                timestamp = datetime.now().strftime("%Y%m%d%H%M")
                return f"D_{timestamp}_{clean_name}_aigc"
            else:
                # 使用默认模式
                timestamp = datetime.now().strftime("%Y%m%d%H%M")
                return self.config.default_branch_pattern.format(timestamp=timestamp)
    
    def _extract_project_name_from_git_url(self, parsed_doc: Dict[str, Any]) -> str:
        """从git远程URL中提取项目名称"""
        # 1. 先尝试从文档中提取git URL
        git_url = self._extract_git_url_from_doc(parsed_doc)
        
        if git_url:
            return self._parse_project_name_from_url(git_url)
        
        # 2. 如果文档中没有git URL，尝试从配置中获取默认远程URL
        from ..resource.config import get_config
        try:
            main_config = get_config()
            coder_config = main_config.get_coder_agent_config()
            git_config = coder_config.get("git_config", {})
            default_remote_url = git_config.get("default_remote_url")
            
            if default_remote_url:
                return self._parse_project_name_from_url(default_remote_url)
        except Exception as e:
            logger.warning(f"获取默认远程URL失败: {e}")
        
        return 'UnknownProject'
    
    def _extract_git_url_from_doc(self, parsed_doc: Dict[str, Any]) -> Optional[str]:
        """从解析的文档中提取git URL"""
        # 检查是否有git配置信息
        git_info = parsed_doc.get('git_info', {})
        if git_info.get('remote_url'):
            return git_info['remote_url']
        
        # 检查branch_info中是否有远程URL
        branch_info = parsed_doc.get('branch_info', {})
        if branch_info.get('remote_url'):
            return branch_info['remote_url']
        
        return None
    
    def _parse_project_name_from_url(self, git_url: str) -> str:
        """从git URL中解析项目名称"""
        if not git_url:
            return 'UnknownProject'
        
        # 移除可能的前后空格
        git_url = git_url.strip()
        
        # 处理不同格式的git URL
        # 格式1: https://github.com/user/project.git
        # 格式2: git@github.com:user/project.git
        # 格式3: https://github.com/user/project
        
        try:
            # 检查是否是有效的git URL格式
            if not (git_url.startswith(('http://', 'https://', 'git@')) and 
                    ('github.com' in git_url or 'gitlab.com' in git_url or 'gitee.com' in git_url or '/' in git_url)):
                return 'UnknownProject'
            
            # 移除 .git 后缀
            if git_url.endswith('.git'):
                git_url = git_url[:-4]
            
            # 提取最后一个路径段作为项目名
            if '/' in git_url:
                project_name = git_url.split('/')[-1]
            elif ':' in git_url and '@' in git_url:
                # 处理 git@github.com:user/project 格式
                project_name = git_url.split(':')[-1].split('/')[-1]
            else:
                return 'UnknownProject'
            
            # 清理项目名称
            if project_name:
                # 移除特殊字符，保留字母数字、中文、下划线和连字符
                clean_name = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', project_name)
                # 移除连续的下划线
                clean_name = re.sub(r'_+', '_', clean_name).strip('_')
                return clean_name if clean_name else 'UnknownProject'
            
        except Exception as e:
            logger.warning(f"解析git URL失败: {e}")
        
        return 'UnknownProject'
    
    def _normalize_project_name(self, project_name: str) -> str:
        """
        规范化项目名称，确保符合文件系统路径要求
        将中文、特殊字符转换为英文路径格式
        """
        if not project_name or project_name == 'UnknownProject':
            return 'testproject'  # 默认项目名
        
        # 常见中文到英文的映射
        chinese_to_english = {
            '需求文档': 'requirements',
            '设计文档': 'design', 
            '链数优化': 'chain_optimization',
            '一局对接': 'business_integration',
            '用户管理': 'user_management',
            '产品管理': 'products_management',
            '订单管理': 'orders_management',
            '系统': 'system',
            '管理': 'management',
            '平台': 'platform',
            '项目': 'project',
            '应用': 'application',
            '服务': 'service',
            '模块': 'module',
            '组件': 'component',
            '对接': 'integration',
            '业务': 'business',
            '数据': 'data',
            '分析': 'analysis',
            '监控': 'monitor',
            '报告': 'report',
            '统计': 'statistics',
            '查询': 'query',
            '搜索': 'search',
            '导入': 'import',
            '导出': 'export',
            '配置': 'config',
            '设置': 'settings',
            '产品': 'products',
            '商品': 'products',
            '用户': 'users'
        }
        
        # 移除版本号信息（如V0, v1.0等）
        name = re.sub(r'[Vv]\d+(\.\d+)*', '', project_name).strip()
        
        # 先进行中文替换，并在替换时保持分隔符
        normalized_name = name
        for chinese, english in chinese_to_english.items():
            normalized_name = normalized_name.replace(chinese, f'_{english}_')
        
        # 处理特殊字符，将空格、连字符等转换为下划线
        normalized_name = re.sub(r'[\s\-\u4e00-\u9fff]', '_', normalized_name)
        
        # 移除其他特殊字符，只保留字母、数字、下划线
        normalized_name = re.sub(r'[^\w_]', '_', normalized_name)
        
        # 移除连续的下划线和连字符
        normalized_name = re.sub(r'[_\-]+', '_', normalized_name)
        
        # 移除前后的下划线
        normalized_name = normalized_name.strip('_')
        
        # 如果结果为空或太短，使用默认名称
        if not normalized_name or len(normalized_name) < 3:
            return 'testproject'
        
        # 确保以字母开头
        if not normalized_name[0].isalpha():
            normalized_name = 'project_' + normalized_name
        
        # 限制长度，但保持单词完整性
        if len(normalized_name) > 60:
            # 尝试在下划线处截断以保持单词完整性
            words = normalized_name.split('_')
            truncated = ''
            for word in words:
                new_length = len(truncated + '_' + word) if truncated else len(word)
                if new_length <= 60:
                    if truncated:
                        truncated += '_' + word
                    else:
                        truncated = word
                else:
                    break
            normalized_name = truncated if truncated else normalized_name[:60].rstrip('_')
        
        # 转换为小写
        normalized_name = normalized_name.lower()
        
        logger.info(f"项目名称规范化: '{project_name}' -> '{normalized_name}'")
        return normalized_name
    
    def save_execution_plan(self, plan: ExecutionPlan) -> str:
        """
        保存执行计划到文件系统
        
        Args:
            plan: 执行计划
            
        Returns:
            保存的文件路径
        """
        # 确保任务目录存在
        tasks_dir = self.config_manager.get_tasks_dir()
        os.makedirs(tasks_dir, exist_ok=True)
        
        # 保存任务分解结构化数据
        breakdown_file = os.path.join(tasks_dir, "task_breakdown.json")
        with open(breakdown_file, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 生成可读的执行计划文档
        plan_file = os.path.join(tasks_dir, "execution_plan.md")
        self._generate_plan_markdown(plan, plan_file)
        
        # 保存任务依赖关系图
        deps_file = os.path.join(tasks_dir, "task_dependencies.json")
        with open(deps_file, 'w', encoding='utf-8') as f:
            json.dump(plan.dependencies_graph, f, ensure_ascii=False, indent=2)
        
        # 保存进度跟踪文件
        progress_file = os.path.join(tasks_dir, "progress_tracker.json")
        progress_data = {
            "plan_id": plan.plan_id,
            "project_name": plan.project_name,
            "total_tasks": plan.total_tasks,
            "completed_tasks": 0,
            "progress_percentage": 0.0,
            "current_task": plan.execution_order[0] if plan.execution_order else None,
            "updated_at": datetime.now().isoformat()
        }
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"执行计划已保存到: {tasks_dir}")
        return tasks_dir
    
    def _generate_plan_markdown(self, plan: ExecutionPlan, file_path: str):
        """生成可读的执行计划Markdown文档"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 执行计划 - {plan.project_name}\n\n")
            f.write(f"**计划ID**: {plan.plan_id}\n")
            f.write(f"**创建时间**: {plan.created_at}\n")
            f.write(f"**总任务数**: {plan.total_tasks}\n")
            f.write(f"**预估总工时**: {plan.estimated_total_hours} 小时\n")
            f.write(f"**Git分支**: {plan.branch_name}\n\n")
            
            f.write("## 任务列表\n\n")
            
            # 按优先级分组显示任务
            priority_groups = {}
            for task in plan.tasks:
                if task.priority not in priority_groups:
                    priority_groups[task.priority] = []
                priority_groups[task.priority].append(task)
            
            for priority in sorted(priority_groups.keys()):
                f.write(f"### 优先级 {priority}\n\n")
                for task in priority_groups[priority]:
                    f.write(f"- **{task.name}** ({task.id})\n")
                    f.write(f"  - 类型: {task.type}\n")
                    f.write(f"  - 描述: {task.description}\n")
                    f.write(f"  - 预估工时: {task.estimated_hours} 小时\n")
                    f.write(f"  - 分配模块: {task.assigned_module}\n")
                    if task.dependencies:
                        f.write(f"  - 依赖任务: {', '.join(task.dependencies)}\n")
                    f.write("\n")
            
            f.write("## 执行顺序\n\n")
            for i, task_id in enumerate(plan.execution_order, 1):
                task = next(t for t in plan.tasks if t.id == task_id)
                f.write(f"{i}. {task.name} ({task_id})\n")
    
    def load_execution_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """
        加载执行计划
        
        Args:
            plan_id: 计划ID
            
        Returns:
            执行计划对象或None
        """
        try:
            tasks_dir = self.config_manager.get_tasks_dir()
            breakdown_file = os.path.join(tasks_dir, "task_breakdown.json")
            
            if not os.path.exists(breakdown_file):
                return None
            
            with open(breakdown_file, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            if plan_data.get('plan_id') != plan_id:
                return None
            
            # 重构任务对象
            tasks = []
            for task_data in plan_data.get('tasks', []):
                task = TaskItem(**task_data)
                tasks.append(task)
            
            plan = ExecutionPlan(
                plan_id=plan_data['plan_id'],
                project_name=plan_data['project_name'],
                total_tasks=plan_data['total_tasks'],
                estimated_total_hours=plan_data['estimated_total_hours'],
                tasks=tasks,
                dependencies_graph=plan_data['dependencies_graph'],
                execution_order=plan_data['execution_order'],
                created_at=plan_data['created_at'],
                branch_name=plan_data.get('branch_name', ''),
                project_structure=plan_data.get('project_structure')
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"加载执行计划失败: {e}")
            return None 