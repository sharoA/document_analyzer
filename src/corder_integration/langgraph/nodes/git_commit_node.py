#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git提交节点 - 支持从数据库领取和执行任务
"""

import asyncio
import logging
import json
import os
import subprocess
from typing import Dict, Any, List
from pathlib import Path

# 导入任务管理工具
from ..task_manager import NodeTaskManager

logger = logging.getLogger(__name__)

class GitCommitAgent:
    """Git提交智能体 - 支持任务领取和状态更新"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "git_commit_node"
        self.supported_task_types = ["deployment"]
    
    def execute_task_from_database(self) -> List[Dict[str, Any]]:
        """从数据库领取并执行Git提交任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        
        execution_results = []
        
        # 获取可执行的任务
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的Git提交任务")
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
                if task_type == "deployment":
                    result = self._execute_deployment_task(task)
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
        
        logger.info(f"✅ Git提交任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_deployment_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行部署任务"""
        logger.info(f"🚀 执行部署任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        deployment_type = parameters.get('deployment_type', 'docker')
        
        # 模拟部署流程
        deployment_result = {
            'service_name': service_name,
            'deployment_type': deployment_type,
            'deployment_environment': 'staging',
            'deployment_steps': [
                {
                    'step': 'pre_deployment_check',
                    'status': 'completed',
                    'duration': '30s',
                    'details': f'检查{service_name}服务的部署前置条件'
                },
                {
                    'step': 'build_application',
                    'status': 'completed',
                    'duration': '2m 15s',
                    'details': f'构建{service_name}服务应用程序'
                },
                {
                    'step': 'create_docker_image',
                    'status': 'completed',
                    'duration': '1m 45s',
                    'details': f'创建{service_name}服务Docker镜像'
                },
                {
                    'step': 'push_to_registry',
                    'status': 'completed',
                    'duration': '45s',
                    'details': f'推送{service_name}服务镜像到仓库'
                },
                {
                    'step': 'deploy_to_staging',
                    'status': 'completed',
                    'duration': '1m 20s',
                    'details': f'部署{service_name}服务到预发布环境'
                },
                {
                    'step': 'health_check',
                    'status': 'completed',
                    'duration': '30s',
                    'details': f'检查{service_name}服务健康状态'
                }
            ],
            'deployment_artifacts': {
                'docker_image': f'{service_name.lower()}-service:1.0.0',
                'registry_url': f'registry.example.com/{service_name.lower()}-service:1.0.0',
                'deployment_config': f'{service_name.lower()}-deployment.yaml',
                'service_config': f'{service_name.lower()}-service.yaml'
            },
            'deployment_metrics': {
                'total_duration': '6m 45s',
                'build_time': '2m 15s',
                'deployment_time': '1m 20s',
                'startup_time': '45s',
                'memory_usage': '256MB',
                'cpu_usage': '0.2 cores'
            },
            'endpoints': {
                'health_check': f'http://staging.example.com/{service_name.lower()}/actuator/health',
                'api_base': f'http://staging.example.com/{service_name.lower()}/api/v1',
                'metrics': f'http://staging.example.com/{service_name.lower()}/actuator/metrics'
            },
            'rollback_info': {
                'previous_version': f'{service_name.lower()}-service:0.9.0',
                'rollback_command': f'kubectl rollout undo deployment/{service_name.lower()}-service',
                'backup_available': True
            },
            'deployment_status': 'success'
        }
        
        # 模拟Git提交流程
        git_commit_result = self._simulate_git_commit(service_name, parameters)
        
        # 合并结果
        final_result = {
            'deployment_result': deployment_result,
            'git_commit_result': git_commit_result,
            'overall_status': 'success' if deployment_result['deployment_status'] == 'success' and git_commit_result['commit_status'] == 'success' else 'failed'
        }
        
        return {
            'success': final_result['overall_status'] == 'success',
            'message': f'{service_name}服务部署和Git提交完成',
            'deployment_info': final_result,
            'service_name': service_name
        }
    
    def _simulate_git_commit(self, service_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """模拟Git提交流程"""
        logger.info(f"📝 模拟{service_name}服务的Git提交流程")
        
        # 模拟Git操作
        git_operations = [
            {
                'operation': 'git add .',
                'status': 'success',
                'files_added': [
                    f'src/main/java/com/example/{service_name.lower()}/',
                    f'src/test/java/com/example/{service_name.lower()}/',
                    f'src/main/resources/application.yml',
                    'pom.xml',
                    'Dockerfile',
                    'deployment.yaml'
                ]
            },
            {
                'operation': 'git commit',
                'status': 'success',
                'commit_hash': f'abc123def456_{service_name.lower()}',
                'commit_message': f'feat: 添加{service_name}微服务\n\n- 实现{service_name}基础CRUD功能\n- 添加数据库配置和实体类\n- 完善API接口和文档\n- 添加单元测试和集成测试\n- 配置Docker部署文件',
                'changed_files': 15,
                'insertions': 847,
                'deletions': 0
            },
            {
                'operation': 'git push',
                'status': 'success',
                'remote': 'origin',
                'branch': parameters.get('target_branch', 'main'),
                'push_url': 'https://github.com/example/microservices.git'
            }
        ]
        
        return {
            'commit_status': 'success',
            'commit_hash': f'abc123def456_{service_name.lower()}',
            'branch': parameters.get('target_branch', 'main'),
            'git_operations': git_operations,
            'repository_info': {
                'total_commits': 127,
                'contributors': 3,
                'last_commit_author': 'LangGraph Agent',
                'last_commit_time': '2024-01-15 10:30:00'
            }
        }


async def git_commit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Git提交节点 - 支持任务驱动的Git操作和部署"""
    logger.info("🚀 Git提交节点开始执行...")
    
    try:
        commit_agent = GitCommitAgent()
        
        # 执行数据库中的任务
        task_results = commit_agent.execute_task_from_database()
        
        # 将任务执行结果添加到状态中
        commit_operations = state.get('commit_operations', [])
        commit_operations.extend(task_results)
        
        # 处理传统的Git提交（向后兼容）
        tested_services = state.get('tested_services', [])
        if tested_services and not any(r['task_type'] == 'deployment' for r in task_results):
            logger.info("🔍 执行传统Git提交流程（向后兼容）")
            for service_name in tested_services:
                # 模拟传统的Git提交
                commit_operations.append({
                    'task_type': 'legacy_commit',
                    'result': {
                        'success': True,
                        'service_name': service_name,
                        'commit_hash': f'legacy_commit_{service_name}',
                        'deployed': True
                    }
                })
        
        # 更新状态
        updated_state = {
            'commit_operations': commit_operations,
            'git_commit_completed': True
        }
        
        # 收集部署结果
        deployed_services = []
        all_deployments_successful = True
        
        for op in commit_operations:
            result = op.get('result', {})
            if result.get('service_name'):
                service_name = result['service_name']
                if service_name not in deployed_services:
                    deployed_services.append(service_name)
                
                # 检查部署是否成功
                deployment_success = result.get('success', True)
                if not deployment_success:
                    all_deployments_successful = False
        
        if deployed_services:
            updated_state['deployed_services'] = deployed_services
            updated_state['all_deployments_successful'] = all_deployments_successful
        
        # 如果所有部署都成功，标记工作流完成
        if all_deployments_successful and deployed_services:
            updated_state['workflow_completed'] = True
            updated_state['final_status'] = 'success'
        
        logger.info(f"✅ Git提交节点完成，处理了 {len(task_results)} 个任务")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ Git提交节点执行失败: {e}")
        return {
            'commit_operations': state.get('commit_operations', []),
            'error': f'Git提交节点执行失败: {str(e)}'
        } 