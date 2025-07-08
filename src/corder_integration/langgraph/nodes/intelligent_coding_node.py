#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能编码节点 - 支持从数据库领取和执行任务
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

class IntelligentCodingAgent:
    """智能编码智能体 - 支持任务领取和状态更新"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.node_name = "intelligent_coding_node"
        self.supported_task_types = ["code_analysis", "database", "api", "config"]
    
    def execute_task_from_database(self) -> List[Dict[str, Any]]:
        """从数据库领取并执行智能编码任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        
        execution_results = []
        
        # 获取可执行的任务
        available_tasks = self.task_manager.get_node_tasks(self.supported_task_types)
        
        if not available_tasks:
            logger.info("ℹ️ 没有可执行的智能编码任务")
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
                    result = self._execute_code_analysis_task(task)
                elif task_type == "database":
                    result = self._execute_database_task(task)
                elif task_type == "api":
                    result = self._execute_api_task(task)
                elif task_type == "config":
                    result = self._execute_config_task(task)
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
        
        logger.info(f"✅ 智能编码任务执行完成，共处理 {len(execution_results)} 个任务")
        return execution_results
    
    def _execute_code_analysis_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码分析任务"""
        logger.info(f"🔍 执行代码分析任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟代码分析流程
        analysis_result = {
            'service_name': service_name,
            'analysis_type': 'static_analysis',
            'findings': [
                {
                    'type': 'architecture_pattern',
                    'description': f'{service_name}服务架构分析',
                    'recommendation': '建议使用分层架构模式'
                },
                {
                    'type': 'dependencies',
                    'description': f'{service_name}依赖分析',
                    'dependencies': ['spring-boot-starter-web', 'spring-boot-starter-data-jpa']
                }
            ],
            'complexity_score': 6.5,
            'maintainability_index': 78.2
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务代码分析完成',
            'analysis_result': analysis_result,
            'service_name': service_name
        }
    
    def _execute_database_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据库设计任务"""
        logger.info(f"🗄️ 执行数据库设计任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟数据库设计
        database_design = {
            'service_name': service_name,
            'database_type': 'mysql',
            'entities': [
                {
                    'name': f'{service_name}_entity',
                    'table_name': f'{service_name.lower()}_table',
                    'fields': [
                        {'name': 'id', 'type': 'BIGINT', 'primary_key': True, 'auto_increment': True},
                        {'name': 'name', 'type': 'VARCHAR(255)', 'nullable': False},
                        {'name': 'status', 'type': 'VARCHAR(50)', 'nullable': False},
                        {'name': 'created_at', 'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
                        {'name': 'updated_at', 'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'}
                    ]
                }
            ],
            'indexes': [
                {'name': f'idx_{service_name.lower()}_name', 'columns': ['name'], 'unique': True},
                {'name': f'idx_{service_name.lower()}_status', 'columns': ['status']}
            ]
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务数据库设计完成',
            'database_design': database_design,
            'service_name': service_name
        }
    
    def _execute_api_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行API设计任务"""
        logger.info(f"🌐 执行API设计任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟API设计
        api_design = {
            'service_name': service_name,
            'base_path': f'/api/v1/{service_name.lower()}',
            'endpoints': [
                {
                    'path': f'/{service_name.lower()}',
                    'method': 'GET',
                    'summary': f'获取{service_name}列表',
                    'parameters': [
                        {'name': 'page', 'type': 'integer', 'default': 0},
                        {'name': 'size', 'type': 'integer', 'default': 20}
                    ],
                    'responses': {
                        '200': f'{service_name}列表获取成功'
                    }
                },
                {
                    'path': f'/{service_name.lower()}',
                    'method': 'POST',
                    'summary': f'创建{service_name}',
                    'requestBody': f'{service_name}CreateRequest',
                    'responses': {
                        '201': f'{service_name}创建成功',
                        '400': '请求参数错误'
                    }
                },
                {
                    'path': f'/{service_name.lower()}/{{id}}',
                    'method': 'GET',
                    'summary': f'获取{service_name}详情',
                    'parameters': [
                        {'name': 'id', 'type': 'integer', 'required': True}
                    ],
                    'responses': {
                        '200': f'{service_name}详情获取成功',
                        '404': f'{service_name}不存在'
                    }
                },
                {
                    'path': f'/{service_name.lower()}/{{id}}',
                    'method': 'PUT',
                    'summary': f'更新{service_name}',
                    'parameters': [
                        {'name': 'id', 'type': 'integer', 'required': True}
                    ],
                    'requestBody': f'{service_name}UpdateRequest',
                    'responses': {
                        '200': f'{service_name}更新成功',
                        '404': f'{service_name}不存在'
                    }
                },
                {
                    'path': f'/{service_name.lower()}/{{id}}',
                    'method': 'DELETE',
                    'summary': f'删除{service_name}',
                    'parameters': [
                        {'name': 'id', 'type': 'integer', 'required': True}
                    ],
                    'responses': {
                        '204': f'{service_name}删除成功',
                        '404': f'{service_name}不存在'
                    }
                }
            ]
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务API设计完成',
            'api_design': api_design,
            'service_name': service_name
        }
    
    def _execute_config_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行配置生成任务"""
        logger.info(f"⚙️ 执行配置生成任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        
        # 模拟配置生成
        config_files = {
            'application.yml': {
                'server': {
                    'port': 8080,
                    'servlet': {
                        'context-path': f'/{service_name.lower()}'
                    }
                },
                'spring': {
                    'application': {
                        'name': f'{service_name.lower()}-service'
                    },
                    'datasource': {
                        'url': f'jdbc:mysql://localhost:3306/{service_name.lower()}_db',
                        'username': '${DB_USERNAME:root}',
                        'password': '${DB_PASSWORD:password}',
                        'driver-class-name': 'com.mysql.cj.jdbc.Driver'
                    },
                    'jpa': {
                        'hibernate': {
                            'ddl-auto': 'update'
                        },
                        'show-sql': True,
                        'properties': {
                            'hibernate': {
                                'format_sql': True
                            }
                        }
                    }
                },
                'logging': {
                    'level': {
                        'com.example': 'DEBUG',
                        'org.springframework': 'INFO'
                    }
                }
            },
            'pom.xml_dependencies': [
                'spring-boot-starter-web',
                'spring-boot-starter-data-jpa',
                'mysql-connector-java',
                'spring-boot-starter-validation',
                'spring-boot-starter-actuator',
                'spring-boot-starter-test'
            ],
            'dockerfile': f"""FROM openjdk:11-jre-slim
COPY target/{service_name.lower()}-service-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]"""
        }
        
        return {
            'success': True,
            'message': f'{service_name}服务配置生成完成',
            'config_files': config_files,
            'service_name': service_name
        }


async def intelligent_coding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能编码节点 - 支持任务驱动的代码生成"""
    logger.info("🚀 智能编码节点开始执行...")
    
    try:
        coding_agent = IntelligentCodingAgent()
        
        # 执行数据库中的任务
        task_results = coding_agent.execute_task_from_database()
        
        # 将任务执行结果添加到状态中
        coding_operations = state.get('coding_operations', [])
        coding_operations.extend(task_results)
        
        # 处理传统的并行任务（向后兼容）
        parallel_tasks = state.get('parallel_tasks', [])
        if parallel_tasks and not any(r['task_type'] in ['code_analysis', 'database', 'api', 'config'] for r in task_results):
            logger.info("🔍 执行传统并行任务（向后兼容）")
            for service_name in parallel_tasks:
                # 模拟传统的代码生成
                coding_operations.append({
                    'task_type': 'legacy_coding',
                    'result': {
                        'success': True,
                        'service_name': service_name,
                        'generated_files': ['Controller.java', 'Service.java', 'Repository.java']
                    }
                })
        
        # 更新状态
        updated_state = {
            'coding_operations': coding_operations,
            'intelligent_coding_completed': True
        }
        
        # 收集生成的服务信息
        generated_services = []
        for op in coding_operations:
            if op.get('result', {}).get('service_name'):
                service_name = op['result']['service_name']
                if service_name not in generated_services:
                    generated_services.append(service_name)
        
        if generated_services:
            updated_state['generated_services'] = generated_services
        
        logger.info(f"✅ 智能编码节点完成，处理了 {len(task_results)} 个任务")
        return updated_state
        
    except Exception as e:
        logger.error(f"❌ 智能编码节点执行失败: {e}")
        return {
            'coding_operations': state.get('coding_operations', []),
            'error': f'智能编码节点执行失败: {str(e)}'
        } 