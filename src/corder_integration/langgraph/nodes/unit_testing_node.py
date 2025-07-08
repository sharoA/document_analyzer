#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试节点 - 支持从数据库领取和执行任务
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List
from pathlib import Path

# 导入任务管理工具
from ..task_manager import NodeTaskManager

logger = logging.getLogger(__name__)

class UnitTestingAgent:
    """单元测试智能体 - 支持任务领取和状态更新"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "unit_testing_node"
        self.supported_task_types = ["integration_test"]
    
    def execute_task_from_database(self) -> List[Dict[str, Any]]:
        """从数据库领取并执行单元测试任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        
        execution_results = []
        
        # 获取可执行的任务
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的单元测试任务")
            return []
        
        logger.info(f"📋 找到 {len(available_tasks)} 个可执行任务")
        
        for task in available_tasks:
            task_id = task['task_id']
            task_type = task['task_type']
            
            logger.info(f"🚀 开始执行任务: {task_id} ({task_type})")
            
            # 领取任务
            if not self.task_manager.claim_task(task_id, self.node_name):
                logger.warning(f"⚠️ 任务 {task_id} 领取失败，跳过")
                continue
            
            try:
                # 执行任务
                if task_type == "integration_test":
                    result = self._execute_integration_test_task(task)
                else:
                    logger.warning(f"⚠️ 未支持的任务类型: {task_type}")
                    result = {'success': False, 'message': f'未支持的任务类型: {task_type}'}
                
                # 更新任务状态
                if result.get('success'):
                    self.task_manager.update_task_status(task_id, 'completed', result)
                    logger.info(f"✅ 任务 {task_id} 执行成功")
                else:
                    self.task_manager.update_task_status(task_id, 'failed', result)
                    logger.error(f"❌ 任务 {task_id} 执行失败: {result.get('message')}")
                
                execution_results.append({
                    'task_id': task_id,
                    'task_type': task_type,
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"❌ 任务 {task_id} 执行异常: {e}")
                error_result = {'success': False, 'message': f'执行异常: {str(e)}'}
                self.task_manager.update_task_status(task_id, 'failed', error_result)
                
                execution_results.append({
                    'task_id': task_id,
                    'task_type': task_type,
                    'result': error_result
                })
        
        logger.info(f"✅ 单元测试任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_integration_test_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行集成测试任务"""
        logger.info(f"🧪 执行集成测试任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟集成测试执行
        test_result = {
            'service_name': service_name,
            'test_type': 'integration_test',
            'test_environment': 'test',
            'execution_summary': {
                'total_tests': 25,
                'passed_tests': 23,
                'failed_tests': 2,
                'skipped_tests': 0,
                'execution_time': '2m 15s',
                'success_rate': 92.0
            },
            'test_categories': {
                'api_tests': {
                    'total': 10,
                    'passed': 9,
                    'failed': 1,
                    'success_rate': 90.0
                },
                'database_tests': {
                    'total': 8,
                    'passed': 8,
                    'failed': 0,
                    'success_rate': 100.0
                },
                'business_logic_tests': {
                    'total': 7,
                    'passed': 6,
                    'failed': 1,
                    'success_rate': 85.7
                }
            },
            'failed_tests': [
                {
                    'test_name': f'{service_name}ControllerTest.testCreateWithInvalidData',
                    'error_message': 'Expected validation error but none was thrown',
                    'category': 'api_tests',
                    'severity': 'Medium'
                },
                {
                    'test_name': f'{service_name}ServiceTest.testConcurrentUpdate',
                    'error_message': 'Concurrent modification not handled properly',
                    'category': 'business_logic_tests',
                    'severity': 'High'
                }
            ],
            'performance_metrics': {
                'average_response_time': '245ms',
                'max_response_time': '1.2s',
                'min_response_time': '15ms',
                'memory_usage': '128MB',
                'cpu_usage': '15%'
            },
            'recommendations': [
                f'修复{service_name}服务的并发更新问题',
                f'加强{service_name}服务的输入验证测试',
                f'优化{service_name}服务的响应时间',
                f'增加{service_name}服务的错误边界测试'
            ],
            'coverage_report': {
                'line_coverage': 87.5,
                'branch_coverage': 82.3,
                'method_coverage': 91.2,
                'class_coverage': 95.0
            },
            'test_status': 'completed_with_failures'
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务集成测试完成',
            'test_result': test_result,
            'service_name': service_name,
            'test_passed': test_result['execution_summary']['success_rate'] >= 90.0
        }


async def unit_testing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """单元测试节点 - 支持任务驱动的测试执行"""
    logger.info("🚀 单元测试节点开始执行...")
    
    try:
        testing_agent = UnitTestingAgent()
        
        # 执行数据库中的任务
        task_results = testing_agent.execute_task_from_database()
        
        # 将任务执行结果添加到状态中
        testing_operations = state.get('testing_operations', [])
        testing_operations.extend(task_results)
        
        # 处理传统的测试执行（向后兼容）
        reviewed_services = state.get('reviewed_services', [])
        if reviewed_services and not any(r['task_type'] == 'integration_test' for r in task_results):
            logger.info("🔍 执行传统测试流程（向后兼容）")
            for service_name in reviewed_services:
                # 模拟传统的测试执行
                testing_operations.append({
                    'task_type': 'legacy_testing',
                    'result': {
                        'success': True,
                        'service_name': service_name,
                        'tests_passed': 18,
                        'tests_total': 20,
                        'coverage': 85.5
                    }
                })
        
        # 更新状态
        updated_state = {
            'testing_operations': testing_operations,
            'unit_testing_completed': True
        }
        
        # 收集测试结果
        tested_services = []
        all_tests_passed = True
        
        for op in testing_operations:
            result = op.get('result', {})
            if result.get('service_name'):
                service_name = result['service_name']
                if service_name not in tested_services:
                    tested_services.append(service_name)
                
                # 检查测试是否通过
                test_passed = result.get('test_passed', True)
                if not test_passed:
                    all_tests_passed = False
        
        if tested_services:
            updated_state['tested_services'] = tested_services
            updated_state['all_tests_passed'] = all_tests_passed
        
        logger.info(f"✅ 单元测试节点完成，处理了 {len(task_results)} 个任务")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ 单元测试节点执行失败: {e}")
        return {
            'testing_operations': state.get('testing_operations', []),
            'error': f'单元测试节点执行失败: {str(e)}'
        } 