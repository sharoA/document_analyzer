#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跳过任务拆解阶段的测试脚本
直接使用现有数据库数据测试后续节点
"""

import asyncio
import logging
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入工作流程相关模块
from src.corder_integration.langgraph.workflow_orchestrator import (
    LangGraphWorkflowOrchestrator, 
    CodingAgentState
)
from src.corder_integration.langgraph.nodes.task_splitting_node import TaskStorageManager

class TaskDataParser:
    """任务数据解析器"""
    
    def parse_markdown_tasks(self, file_path: str) -> List[Dict[str, Any]]:
        """解析Markdown表格中的任务数据"""
        logger.info(f"📊 开始解析任务文件: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tasks = []
        lines = content.strip().split('\n')
        
        # 跳过表头和分隔线
        data_lines = lines[2:]  # 跳过表头和分隔线
        
        for line in data_lines:
            if line.strip() and '|' in line:
                # 解析表格行
                columns = [col.strip() for col in line.split('|')[1:-1]]  # 去掉首尾空元素
                
                if len(columns) >= 11:  # 确保有足够的列
                    task = {
                        'task_id': columns[0],
                        'service_name': columns[1],
                        'task_type': columns[2],
                        'priority': int(columns[3]) if columns[3].isdigit() else 1,
                        'status': columns[4],
                        'dependencies': self._parse_json_field(columns[5]),
                        'estimated_duration': columns[6],
                        'description': columns[7],
                        'deliverables': self._parse_json_field(columns[8]),
                        'implementation_details': columns[9],
                        'completion_criteria': columns[10],
                        'parameters': self._parse_json_field(columns[11]) if len(columns) > 11 else {}
                    }
                    tasks.append(task)
        
        logger.info(f"✅ 成功解析 {len(tasks)} 个任务")
        return tasks
    
    def _parse_json_field(self, field_str: str) -> Any:
        """解析JSON字段"""
        try:
            # 处理转义字符
            cleaned = field_str.replace('\\u', '\\u').replace('\\"', '"')
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # 如果解析失败，尝试简单的列表解析
            if field_str.startswith('[') and field_str.endswith(']'):
                try:
                    # 简单的数组解析
                    content = field_str[1:-1].strip()
                    if not content:
                        return []
                    items = [item.strip(' "') for item in content.split(',')]
                    return items
                except:
                    return []
            return field_str if field_str != '[]' else []

class TestWorkflowManager:
    """测试工作流程管理器"""
    
    def __init__(self):
        self.db_path = "coding_agent_workflow.db"
        self.task_storage = TaskStorageManager(self.db_path)
        self.orchestrator = LangGraphWorkflowOrchestrator(
            use_sqlite=True,
            db_path="workflow_checkpoints.db"
        )
    
    def load_tasks_from_database(self) -> List[Dict[str, Any]]:
        """从数据库加载task_001到task_012的任务数据"""
        logger.info("📋 从数据库加载现有任务数据...")
        
        try:
            # 直接从数据库读取指定的任务
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 🔍 调试：先查看所有任务ID
                cursor.execute('SELECT task_id FROM execution_tasks ORDER BY task_id')
                all_task_ids = [row[0] for row in cursor.fetchall()]
                logger.info(f"🔍 数据库中所有任务ID: {all_task_ids}")
                
                # 查询task_001到task_012的数据
                task_ids = [f'task_{str(i).zfill(3)}' for i in range(1, 13)]  # task_001 到 task_012
                logger.info(f"🔍 要查询的任务ID: {task_ids}")
                
                # 🔍 先测试简单查询
                cursor.execute("SELECT task_id FROM execution_tasks WHERE task_id = 'task_001'")
                test_result = cursor.fetchone()
                logger.info(f"🔍 task_001单独查询结果: {test_result}")
                
                placeholders = ','.join(['?' for _ in task_ids])
                query = f"""
                    SELECT task_id, service_name, task_type, priority, status, dependencies,
                           estimated_duration, description, deliverables,
                           implementation_details, completion_criteria, parameters
                    FROM execution_tasks 
                    WHERE task_id IN ({placeholders})
                    ORDER BY task_id
                """
                logger.info(f"🔍 执行SQL查询: {query}")
                logger.info(f"🔍 查询参数: {task_ids}")
                
                cursor.execute(query, task_ids)
                
                tasks = []
                for row in cursor.fetchall():
                    task = {
                        'task_id': row[0],
                        'service_name': row[1],
                        'task_type': row[2],
                        'priority': row[3],
                        'status': 'pending',  # 重置状态为pending
                        'dependencies': json.loads(row[5] or '[]'),
                        'estimated_duration': row[6],
                        'description': row[7],
                        'deliverables': json.loads(row[8] or '[]'),
                        'implementation_details': row[9],
                        'completion_criteria': row[10],
                        'parameters': json.loads(row[11] or '{}')
                    }
                    tasks.append(task)
                
                logger.info(f"✅ 成功加载 {len(tasks)} 个任务")
                return tasks
                
        except Exception as e:
            logger.error(f"❌ 从数据库加载任务失败: {e}")
            return []
    
    def reset_task_status(self, task_ids: List[str]) -> bool:
        """重置指定任务的状态为pending"""
        logger.info("🔄 重置任务状态为pending...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 重置状态
                placeholders = ','.join(['?' for _ in task_ids])
                cursor.execute(f"""
                    UPDATE execution_tasks 
                    SET status = 'pending', updated_at = CURRENT_TIMESTAMP
                    WHERE task_id IN ({placeholders})
                """, task_ids)
                
                logger.info(f"✅ 成功重置 {len(task_ids)} 个任务状态")
                return True
                
        except Exception as e:
            logger.error(f"❌ 重置任务状态失败: {e}")
            return False
    
    def setup_test_database(self, tasks: List[Dict[str, Any]]) -> bool:
        """设置测试数据库，重置任务状态"""
        logger.info("🔧 设置测试环境...")
        
        try:
            # 提取任务ID列表
            task_ids = [task['task_id'] for task in tasks]
            
            # 重置任务状态
            success = self.reset_task_status(task_ids)
            
            if success:
                logger.info(f"✅ 成功重置 {len(tasks)} 个任务状态")
                
                # 验证数据
                pending_tasks = self.task_storage.get_pending_tasks()
                logger.info(f"📋 数据库中共有 {len(pending_tasks)} 个待执行任务")
                return True
            else:
                logger.error("❌ 重置任务状态失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 设置测试数据库失败: {e}")
            return False
    
    def create_initial_state(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建初始状态，模拟任务拆解完成的结果"""
        logger.info("🏗️ 创建初始状态...")
        
        # 从任务中提取服务信息
        services = list(set([task['service_name'] for task in tasks if task['service_name'] != '系统']))
        
        # 构建服务依赖关系
        service_dependencies = {}
        for service in services:
            service_dependencies[service] = []
        
        # 从任务依赖中推断服务依赖
        for task in tasks:
            if task['dependencies']:
                # 查找依赖任务的服务
                for dep_task_id in task['dependencies']:
                    dep_task = next((t for t in tasks if t['task_id'] == dep_task_id), None)
                    if dep_task and dep_task['service_name'] != task['service_name']:
                        if task['service_name'] not in service_dependencies:
                            service_dependencies[task['service_name']] = []
                        if dep_task['service_name'] not in service_dependencies[task['service_name']]:
                            service_dependencies[task['service_name']].append(dep_task['service_name'])
        
        # 构建任务执行计划
        task_execution_plan = {
            'total_tasks': len(tasks),
            'services_count': len(services),
            'phases': [
                {'phase': 'git_management', 'tasks': [t for t in tasks if t['task_type'] in ['git_extraction', 'git_clone']]},
                {'phase': 'intelligent_coding', 'tasks': [t for t in tasks if t['task_type'] in ['code_analysis', 'database', 'api', 'config']]},
                {'phase': 'testing', 'tasks': [t for t in tasks if t['task_type'] in ['integration_test']]},
                {'phase': 'deployment', 'tasks': [t for t in tasks if t['task_type'] in ['deployment']]}
            ]
        }
        
        # 创建初始状态
        initial_state = {
            # 输入状态
            'design_doc': "模拟设计文档 - 用户服务和确权开立服务的微服务架构设计",
            'project_name': "zqyl_microservices_test",
            
            # 任务拆分结果（模拟完成）
            'identified_services': services,
            'service_dependencies': service_dependencies,
            'task_execution_plan': task_execution_plan,
            'parallel_tasks': [t for t in tasks if not t['dependencies']],
            
            # Git管理状态
            'git_repo_url': None,
            'target_branch': "feature/test_implementation",
            'project_paths': {
                '用户服务': './zqyl-user-center-service',
                '确权开立服务': './crcl-open'
            },
            'output_path': './workspace/test_project',
            'repo_initialized': False,
            
            # 代码生成状态
            'generated_services': {},
            'generated_apis': {},
            'generated_sql': {},
            'service_interconnections': {},
            
            # 测试状态
            'unit_test_results': {},
            'test_coverage': {},
            'interface_compatibility': {},
            
            # 质量检查状态
            'code_review_results': {},
            'static_analysis_results': {},
            'security_scan_results': {},
            
            # Git提交状态
            'commit_hashes': {},
            'push_results': {},
            'pr_urls': {},
            
            # 执行控制状态
            'current_phase': 'git_management',  # 跳过task_splitting，直接从git_management开始
            'completed_services': [],
            'failed_services': [],
            'retry_count': 0,
            'execution_errors': []
        }
        
        logger.info(f"✅ 初始状态创建完成，包含 {len(services)} 个服务")
        return initial_state
    
    async def run_test_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """运行测试工作流程，从git_management节点开始"""
        logger.info("🚀 开始测试工作流程...")
        
        try:
            # 获取检查点管理器
            checkpointer_context = self.orchestrator._get_checkpointer_context()
            
            # 检查是否为异步上下文管理器
            if hasattr(checkpointer_context, '__aenter__'):
                # 使用异步上下文管理器
                async with checkpointer_context as checkpointer:
                    return await self._execute_with_checkpointer(checkpointer, initial_state)
            else:
                # 直接使用检查点管理器
                return await self._execute_with_checkpointer(checkpointer_context, initial_state)
            
        except Exception as e:
            logger.error(f"❌ 测试工作流程执行失败: {e}")
            raise
    
    async def _execute_with_checkpointer(self, checkpointer, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """使用检查点管理器执行工作流程"""
        # 编译工作流图
        compiled_graph = self.orchestrator.graph.compile(checkpointer=checkpointer)
        
        # 生成配置和线程ID
        config = {
            "configurable": {
                "thread_id": f"test_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        # 从git_management节点开始执行（跳过task_splitting）
        logger.info("⏭️ 跳过任务拆解，从Git管理节点开始执行...")
        
        # 直接调用git_management节点开始
        final_state = await compiled_graph.ainvoke(
            initial_state,
            config=config
        )
        
        logger.info("✅ 测试工作流程执行完成")
        return final_state
    
    def generate_test_report(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试报告"""
        logger.info("📊 生成测试报告...")
        
        report = {
            'test_summary': {
                'start_phase': 'git_management',
                'final_phase': final_state.get('current_phase', 'unknown'),
                'completed_services': final_state.get('completed_services', []),
                'failed_services': final_state.get('failed_services', []),
                'execution_errors': final_state.get('execution_errors', [])
            },
            'git_management_results': {
                'repo_initialized': final_state.get('repo_initialized', False),
                'project_paths': final_state.get('project_paths', {})
            },
            'coding_results': {
                'generated_services': len(final_state.get('generated_services', {})),
                'generated_apis': len(final_state.get('generated_apis', {})),
                'generated_sql': len(final_state.get('generated_sql', {}))
            },
            'test_results': {
                'unit_test_results': final_state.get('unit_test_results', {}),
                'test_coverage': final_state.get('test_coverage', {})
            }
        }
        
        logger.info("✅ 测试报告生成完成")
        return report

async def main():
    """主函数"""
    logger.info("🎯 开始跳过任务拆解的工作流程测试")
    
    try:
        # 1. 设置测试环境
        test_manager = TestWorkflowManager()
        
        # 2. 从数据库加载现有任务数据 (task_001到task_012)
        tasks = test_manager.load_tasks_from_database()
        
        if not tasks:
            logger.error("❌ 数据库中没有找到task_001到task_012的任务数据")
            return
        
        logger.info(f"📋 成功加载 {len(tasks)} 个任务：{[t['task_id'] for t in tasks]}")
        
        # 3. 重置任务状态
        if not test_manager.setup_test_database(tasks):
            logger.error("❌ 任务状态重置失败")
            return
        
        # 4. 创建初始状态
        initial_state = test_manager.create_initial_state(tasks)
        
        # 5. 运行工作流程
        final_state = await test_manager.run_test_workflow(initial_state)
        
        # 6. 生成测试报告
        report = test_manager.generate_test_report(final_state)
        
        # 7. 输出结果
        print("\n" + "="*60)
        print("🎉 测试完成！")
        print("="*60)
        print(f"最终阶段: {report['test_summary']['final_phase']}")
        print(f"完成的服务: {report['test_summary']['completed_services']}")
        print(f"失败的服务: {report['test_summary']['failed_services']}")
        print(f"执行错误: {len(report['test_summary']['execution_errors'])}")
        print("="*60)
        
        # 保存详细报告
        import json
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_report': report,
                'final_state': final_state
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 详细报告已保存到: {report_file}")
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 