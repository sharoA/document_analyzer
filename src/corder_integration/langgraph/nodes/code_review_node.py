#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码审查节点 - 支持从数据库领取和执行任务
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

class CodeReviewAgent:
    """代码审查智能体 - 支持任务领取和状态更新"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "code_review_node"
        self.supported_task_types = ["code_analysis", "database", "api", "config"]
    
    def execute_task_from_database(self, project_task_id: str = None) -> List[Dict[str, Any]]:
        """从数据库领取并执行代码审查任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        if project_task_id:
            logger.info(f"🏷️ 过滤项目任务标识: {project_task_id}")
        
        execution_results = []
        
        # 🔧 修复：获取可执行的任务时传递项目标识
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types, project_task_id)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的代码审查任务")
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
                if task_type == "code_analysis":
                    result = self._execute_code_review_analysis_task(task)
                elif task_type == "database":
                    result = self._execute_database_review_task(task)
                elif task_type == "api":
                    result = self._execute_api_review_task(task)
                elif task_type == "config":
                    result = self._execute_config_review_task(task)
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
        
        logger.info(f"✅ 代码审查任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_code_review_analysis_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码审查分析任务"""
        logger.info(f"🔍 执行代码审查分析任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟代码审查流程
        review_result = {
            'service_name': service_name,
            'review_type': 'comprehensive_review',
            'quality_metrics': {
                'code_quality_score': 8.2,
                'test_coverage': 78.5,
                'complexity_rating': 'Medium',
                'maintainability_index': 82.1
            },
            'issues_found': [
                {
                    'severity': 'Medium',
                    'type': 'Code Style',
                    'description': f'{service_name}服务中存在命名不规范的变量',
                    'file': f'{service_name}Controller.java',
                    'line': 45,
                    'suggestion': '建议使用驼峰命名法'
                },
                {
                    'severity': 'Low',
                    'type': 'Performance',
                    'description': f'{service_name}服务查询可以优化',
                    'file': f'{service_name}Service.java',
                    'line': 123,
                    'suggestion': '建议添加缓存机制'
                }
            ],
            'recommendations': [
                f'建议为{service_name}服务添加更多单元测试',
                f'建议优化{service_name}服务的异常处理机制',
                f'建议为{service_name}服务添加API文档注解'
            ],
            'approval_status': 'approved_with_comments'
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务代码审查完成',
            'review_result': review_result,
            'service_name': service_name
        }
    
    def _execute_database_review_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库设计审查任务"""
        logger.info(f"🗄️ 执行数据库设计审查任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟数据库审查
        database_review = {
            'service_name': service_name,
            'review_type': 'database_design_review',
            'schema_quality': {
                'normalization_score': 9.1,
                'index_efficiency': 8.5,
                'constraint_coverage': 7.8,
                'performance_rating': 'Good'
            },
            'findings': [
                {
                    'severity': 'Low',
                    'type': 'Index Optimization',
                    'description': f'{service_name}表可以添加复合索引',
                    'table': f'{service_name.lower()}_table',
                    'suggestion': '建议在(status, created_at)上创建复合索引'
                },
                {
                    'severity': 'Medium',
                    'type': 'Data Type',
                    'description': f'{service_name}表的字段类型可以优化',
                    'table': f'{service_name.lower()}_table',
                    'field': 'status',
                    'suggestion': '建议使用ENUM类型替代VARCHAR'
                }
            ],
            'recommendations': [
                f'建议为{service_name}表添加软删除字段',
                f'建议为{service_name}表添加版本控制字段',
                f'建议考虑{service_name}表的分区策略'
            ],
            'approval_status': 'approved'
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务数据库设计审查完成',
            'database_review': database_review,
            'service_name': service_name
        }
    
    def _execute_api_review_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行API设计审查任务"""
        logger.info(f"🌐 执行API设计审查任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟API审查
        api_review = {
            'service_name': service_name,
            'review_type': 'api_design_review',
            'api_quality': {
                'restful_compliance': 9.2,
                'response_consistency': 8.8,
                'error_handling': 8.1,
                'documentation_quality': 7.5
            },
            'findings': [
                {
                    'severity': 'Low',
                    'type': 'RESTful Design',
                    'description': f'{service_name} API响应格式建议统一',
                    'endpoint': f'/api/v1/{service_name.lower()}',
                    'suggestion': '建议所有API返回统一的响应包装格式'
                },
                {
                    'severity': 'Medium',
                    'type': 'Error Handling',
                    'description': f'{service_name} API缺少详细的错误码',
                    'endpoint': 'multiple',
                    'suggestion': '建议添加业务错误码和详细错误信息'
                }
            ],
            'recommendations': [
                f'建议为{service_name} API添加OpenAPI 3.0文档',
                f'建议为{service_name} API添加请求限流机制',
                f'建议为{service_name} API添加版本控制策略',
                f'建议为{service_name} API添加缓存策略'
            ],
            'security_review': {
                'authentication': 'Required',
                'authorization': 'Role-based',
                'input_validation': 'Comprehensive',
                'data_sanitization': 'Required'
            },
            'approval_status': 'approved_with_conditions'
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务API设计审查完成',
            'api_review': api_review,
            'service_name': service_name
        }
    
    def _execute_config_review_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置审查任务"""
        logger.info(f"⚙️ 执行配置审查任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟配置审查
        config_review = {
            'service_name': service_name,
            'review_type': 'configuration_review',
            'config_quality': {
                'security_score': 8.7,
                'maintainability': 9.0,
                'environment_support': 8.3,
                'best_practices': 8.5
            },
            'findings': [
                {
                    'severity': 'High',
                    'type': 'Security',
                    'description': f'{service_name}配置中包含硬编码密码',
                    'file': 'application.yml',
                    'suggestion': '建议使用环境变量或外部配置管理系统'
                },
                {
                    'severity': 'Medium',
                    'type': 'Performance',
                    'description': f'{service_name}连接池配置可以优化',
                    'file': 'application.yml',
                    'suggestion': '建议根据实际负载调整连接池大小'
                },
                {
                    'severity': 'Low',
                    'type': 'Logging',
                    'description': f'{service_name}日志级别在生产环境中过于详细',
                    'file': 'application.yml',
                    'suggestion': '建议在生产环境中使用INFO级别'
                }
            ],
            'recommendations': [
                f'建议为{service_name}添加配置热刷新支持',
                f'建议为{service_name}添加健康检查配置',
                f'建议为{service_name}添加监控和指标配置',
                f'建议为{service_name}添加不同环境的配置文件'
            ],
            'security_checklist': {
                'environment_variables': 'Required',
                'sensitive_data_encryption': 'Required',
                'access_control': 'Configured',
                'audit_logging': 'Enabled'
            },
            'approval_status': 'requires_changes'
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务配置审查完成',
            'config_review': config_review,
            'service_name': service_name
        }


async def code_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """代码审查节点 - 支持任务驱动的代码审查"""
    logger.info("🚀 代码审查节点开始执行...")
    
    try:
        review_agent = CodeReviewAgent()
        
        # 🆕 获取项目任务标识
        project_task_id = state.get('project_task_id')
        if project_task_id:
            logger.info(f"🏷️ 代码审查节点获取项目标识: {project_task_id}")
        
        # 🔧 修复：执行数据库中的任务时传递项目标识
        task_results = review_agent.execute_task_from_database(project_task_id)
        
        # 将任务执行结果添加到状态中
        review_operations = state.get('review_operations', [])
        review_operations.extend(task_results)
        
        # 处理传统的代码审查（向后兼容）
        generated_services = state.get('generated_services', [])
        if generated_services and not any(r['task_type'] in ['code_analysis', 'database', 'api', 'config'] for r in task_results):
            logger.info("🔍 执行传统代码审查（向后兼容）")
            for service_name in generated_services:
                # 模拟传统的代码审查
                review_operations.append({
                    'task_type': 'legacy_review',
                    'result': {
                        'success': True,
                        'service_name': service_name,
                        'review_status': 'approved',
                        'issues_count': 2
                    }
                })
        
        # 更新状态
        updated_state = {
            'review_operations': review_operations,
            'code_review_completed': True
        }
        
        # 收集审查结果
        reviewed_services = []
        for op in review_operations:
            if op.get('result', {}).get('service_name'):
                service_name = op['result']['service_name']
                if service_name not in reviewed_services:
                    reviewed_services.append(service_name)
        
        if reviewed_services:
            updated_state['reviewed_services'] = reviewed_services
        
        logger.info(f"✅ 代码审查节点完成，处理了 {len(task_results)} 个任务")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ 代码审查节点执行失败: {e}")
        return {
            'review_operations': state.get('review_operations', []),
            'error': f'代码审查节点执行失败: {str(e)}'
        } 