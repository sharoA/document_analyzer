#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体测试
"""

import unittest
import asyncio
import tempfile
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.corder_integration.coder_agent import CoderAgent
from src.corder_integration.task_planner import TaskPlanner, DesignDocumentParser, TaskItem
from src.corder_integration.git_manager import GitManager
from src.corder_integration.config import CoderAgentConfig

class TestDesignDocumentParser(unittest.TestCase):
    """测试设计文档解析器"""
    
    def setUp(self):
        self.parser = DesignDocumentParser()
    
    def test_parse_project_info(self):
        """测试项目信息解析"""
        document = """
# 用户管理系统

## 项目信息
项目名称: UserManagementSystem
版本: 1.0.0
描述: 用户管理系统
"""
        result = self.parser.parse_markdown_document(document)
        
        project_info = result['project_info']
        self.assertEqual(project_info.get('name'), 'UserManagementSystem')
        self.assertEqual(project_info.get('version'), '1.0.0')
    
    def test_parse_technical_requirements(self):
        """测试技术要求解析"""
        document = """
## 技术要求
后端技术栈: Java 8 + Spring Boot
前端技术栈: Vue 2.x + Element UI
数据库: MySQL
"""
        result = self.parser.parse_markdown_document(document)
        
        tech_req = result['technical_requirements']
        self.assertIn('Java 8', tech_req.get('backend', ''))
        self.assertIn('Vue 2.x', tech_req.get('frontend', ''))
        self.assertIn('MySQL', tech_req.get('database', ''))
    
    def test_parse_api_design(self):
        """测试API设计解析"""
        document = """
## API设计
- GET /api/users - 获取用户列表
- POST /api/users - 创建用户
- PUT /api/users/{id} - 更新用户
"""
        result = self.parser.parse_markdown_document(document)
        
        apis = result['api_design']
        self.assertGreater(len(apis), 0)
    
    def test_parse_database_design(self):
        """测试数据库设计解析"""
        document = """
## 数据库设计

### 用户表
表: users
字段: id, username, email
"""
        result = self.parser.parse_markdown_document(document)
        
        tables = result['database_design']
        self.assertGreater(len(tables), 0)
        
        user_table = next((t for t in tables if 'users' in t.get('name', '')), None)
        self.assertIsNotNone(user_table)

class TestTaskPlanner(unittest.TestCase):
    """测试任务规划器"""
    
    def setUp(self):
        self.task_planner = TaskPlanner()
    
    def test_generate_tasks(self):
        """测试任务生成"""
        parsed_doc = {
            'project_info': {'name': 'TestProject'},
            'business_logic': [
                {'module': '用户管理功能', 'description': '用户CRUD操作'}
            ],
            'api_design': [
                {'method': 'GET', 'path': '/api/users', 'description': '获取用户'}
            ],
            'database_design': [
                {'name': 'users', 'description': '用户表'}
            ],
            'ui_components': [],
            'branch_info': {},
            'project_structure': {}
        }
        
        tasks = self.task_planner._generate_tasks(parsed_doc)
        
        # 应该包含基础任务
        self.assertGreater(len(tasks), 0)
        
        # 检查任务类型
        task_types = [task.type for task in tasks]
        self.assertIn('setup', task_types)
        self.assertIn('docs', task_types)
        self.assertIn('backend', task_types)
    
    def test_calculate_execution_order(self):
        """测试执行顺序计算"""
        tasks = [
            TaskItem("task_001", "任务1", "描述1", "setup", 1, 1.0, [], "module1"),
            TaskItem("task_002", "任务2", "描述2", "backend", 2, 2.0, ["task_001"], "module2"),
            TaskItem("task_003", "任务3", "描述3", "test", 3, 1.0, ["task_002"], "module3")
        ]
        
        dependencies = self.task_planner._analyze_dependencies(tasks)
        execution_order = self.task_planner._calculate_execution_order(tasks, dependencies)
        
        # 检查执行顺序
        self.assertEqual(execution_order[0], "task_001")
        self.assertEqual(execution_order[1], "task_002")
        self.assertEqual(execution_order[2], "task_003")

class TestGitManager(unittest.TestCase):
    """测试Git管理器"""
    
    def setUp(self):
        self.git_manager = GitManager()
    
    @patch('subprocess.run')
    def test_run_git_command(self, mock_run):
        """测试Git命令执行"""
        mock_run.return_value.stdout = "test output"
        mock_run.return_value.stderr = ""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.git_manager._run_git_command(['git', 'status'], temp_dir)
            self.assertEqual(result, "test output")
    
    def test_determine_branch_name(self):
        """测试分支名称确定"""
        config = CoderAgentConfig()
        
        # 使用默认模式
        branch_name = self.git_manager._determine_branch_name({})
        self.assertIn("D_", branch_name)
        self.assertIn("_aigc", branch_name)
    
    def test_analyze_existing_structure(self):
        """测试项目结构分析"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一些测试文件
            os.makedirs(os.path.join(temp_dir, 'src', 'main', 'java'), exist_ok=True)
            
            with open(os.path.join(temp_dir, 'pom.xml'), 'w') as f:
                f.write('<?xml version="1.0"?><project></project>')
            
            analysis = self.git_manager.analyze_existing_structure(temp_dir)
            
            self.assertTrue(analysis['project_exists'])
            self.assertTrue(analysis['has_backend'])

class TestCoderAgent(unittest.TestCase):
    """测试编码智能体"""
    
    def setUp(self):
        self.coder_agent = CoderAgent()
    
    @patch('src.corder_integration.coder_agent.get_task_storage')
    def test_list_recent_tasks(self, mock_get_task_storage):
        """测试获取最近任务"""
        mock_storage = Mock()
        mock_storage.get_all_tasks.return_value = [
            {'id': '1', 'filename': 'test1.md', 'status': 'completed'},
            {'id': '2', 'filename': 'test2.md', 'status': 'pending'}
        ]
        mock_get_task_storage.return_value = mock_storage
        
        tasks = self.coder_agent.list_recent_tasks(10)
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]['filename'], 'test1.md')
    
    def test_generate_project_summary(self):
        """测试项目摘要生成"""
        with patch.object(self.coder_agent, 'get_project_status') as mock_status:
            mock_status.return_value = {
                'git_status': {'is_git_repo': True, 'current_branch': 'main'},
                'workflow_status': {'current_state': 'completed'},
                'structure_analysis': {'has_backend': True, 'has_frontend': True, 'existing_files': ['file1', 'file2']}
            }
            
            summary = self.coder_agent.generate_project_summary()
            
            self.assertIn('project_overview', summary)
            self.assertIn('development_progress', summary)
            self.assertIn('files_overview', summary)
            self.assertTrue(summary['project_overview']['git_initialized'])

class TestCoderAgentIntegration(unittest.IsolatedAsyncioTestCase):
    """编码智能体集成测试"""
    
    async def test_process_design_document_planning_only(self):
        """测试仅规划模式"""
        document_content = """
# 测试项目

## 项目信息
项目名称: TestProject
版本: 1.0.0

## 业务逻辑
### 用户管理功能
- 用户注册和登录

## API设计
- POST /api/users - 创建用户
- GET /api/users - 获取用户列表

## 数据库设计
### 用户表
表: users
字段: id, username, email
"""
        
        coder_agent = CoderAgent()
        
        with patch.object(coder_agent.task_storage, 'create_task') as mock_create, \
             patch.object(coder_agent.task_storage, 'update_task_status') as mock_update:
            
            mock_create.return_value = 'test_task_id'
            
            result = await coder_agent.process_design_document(
                document_content=document_content,
                project_name="TestProject",
                execute_immediately=False
            )
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('execution_plan', result)
            self.assertIsNotNone(result['execution_plan'])
            
            # 验证任务存储调用
            mock_create.assert_called_once()
            mock_update.assert_called()

def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDesignDocumentParser))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskPlanner))
    suite.addTests(loader.loadTestsFromTestCase(TestGitManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCoderAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestCoderAgentIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 