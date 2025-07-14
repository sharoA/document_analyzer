#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能编码节点 - 支持从数据库领取和执行任务，基于项目分析生成企业级代码
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List
from pathlib import Path

# 导入任务管理工具
from src.corder_integration.langgraph.task_manager import NodeTaskManager
# 导入项目分析API
from src.apis.project_analysis_api import ProjectAnalysisAPI
# 导入LLM客户端
from src.utils.volcengine_client import VolcengineClient
from src.utils.openai_client import OpenAIClient
# 导入模板+AI代码生成器
from src.corder_integration.code_generator.enhanced_template_ai_generator import EnhancedTemplateAIGenerator

logger = logging.getLogger(__name__)

class IntelligentCodingAgent:
    """智能编码智能体 - 支持任务领取和基于项目分析的代码生成"""
    
    def __init__(self):
        self.task_manager = NodeTaskManager()
        self.project_analysis_api = ProjectAnalysisAPI()
        self.node_name = "intelligent_coding_node"
        self.supported_task_types = ["code_analysis", "database", "api", "config"]
        
        # ReAct模式配置
        self.react_config = {
            'enabled': True,              # 是否启用ReAct模式
            'max_iterations': 6,          # 最大ReAct循环次数
            'temperature': 0.1,           # ReAct模式的温度参数
            'max_tokens': 4000,           # 每次ReAct调用的最大token数
            'fallback_on_failure': True,  # ReAct失败时是否使用fallback
            'log_react_steps': True,      # 是否记录ReAct步骤
            'use_templates': True         # 🆕 新增：是否使用模板驱动生成
        }
        
        # 初始化LLM客户端 - 从配置文件读取
        self.llm_client = None
        self.llm_provider = None
        
        # 直接读取配置文件 - 使用绝对路径
        import yaml
        import os
        config = {}
        
        # 尝试多个可能的配置文件路径
        config_paths = [
            'config.yaml',
            os.path.join(os.getcwd(), 'config.yaml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../config.yaml'),
            'D:/ai_project/document_analyzer/config.yaml'
        ]
        
        config_loaded = False
        for config_path in config_paths:
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    logger.info(f"✅ 成功加载配置文件: {config_path}")
                    config_loaded = True
                    break
            except Exception as e:
                logger.warning(f"⚠️ 加载配置文件失败 {config_path}: {e}")
        
        if not config_loaded:
            logger.error(f"❌ 所有配置文件路径都加载失败: {config_paths}")
        
        # 优先使用火山引擎
        if config and config.get('volcengine', {}).get('api_key'):
            try:
                from src.utils.volcengine_client import VolcengineClient, VolcengineConfig
                volcengine_config = VolcengineConfig(
                    api_key=config['volcengine']['api_key'],
                    model_id=config['volcengine']['model'],
                    base_url=config['volcengine']['endpoint'],
                    temperature=config['volcengine'].get('temperature', 0.7),
                    max_tokens=config['volcengine'].get('max_tokens', 4000)
                )
                self.llm_client = VolcengineClient(volcengine_config)
                self.llm_provider = "volcengine"
                logger.info(f"✅ 使用火山引擎LLM客户端：{config['volcengine']['model']}")
            except Exception as e:
                logger.error(f"❌ 火山引擎初始化失败: {e}")
                import traceback
                logger.error(f"❌ 详细错误: {traceback.format_exc()}")
        
        # fallback到openai
        if not self.llm_client and config and config.get('openai', {}).get('api_key'):
            try:
                from src.utils.openai_client import OpenAIClient
                self.llm_client = OpenAIClient()
                self.llm_provider = "openai"
                logger.info("✅ 使用OpenAI LLM客户端")
            except Exception as e2:
                logger.error(f"❌ OpenAI客户端初始化失败: {e2}")
                
        # 最终检查
        if not self.llm_client:
            logger.error("❌ 所有LLM客户端初始化都失败！将无法执行代码生成任务")
            self.llm_provider = "none"
        else:
            logger.info(f"✅ LLM客户端初始化成功: {self.llm_provider}")
        
        # 🆕 初始化增强版模板+AI代码生成器
        self.template_ai_generator = EnhancedTemplateAIGenerator(self.llm_client)
        logger.info("✅ 增强版模板+AI代码生成器初始化完成")
    
    def configure_react_mode(self, **config_updates):
        """配置ReAct模式参数"""
        
        logger.info(f"🔧 更新ReAct配置: {config_updates}")
        
        # 验证配置参数
        valid_keys = {'enabled', 'max_iterations', 'temperature', 'max_tokens', 
                     'fallback_on_failure', 'log_react_steps'}
        
        for key in config_updates:
            if key not in valid_keys:
                logger.warning(f"⚠️ 无效的ReAct配置项: {key}")
                continue
            
            old_value = self.react_config.get(key)
            self.react_config[key] = config_updates[key]
            logger.info(f"✅ {key}: {old_value} -> {config_updates[key]}")
        
        logger.info(f"🎯 当前ReAct配置: {self.react_config}")
    
    def get_react_status(self) -> Dict[str, Any]:
        """获取ReAct模式状态信息"""
        
        return {
            'react_enabled': self.react_config.get('enabled', False),
            'llm_provider': self.llm_provider,
            'llm_available': self.llm_client is not None,
            'react_config': self.react_config.copy(),
            'supported_features': [
                'multi_iteration_reasoning',
                'step_by_step_generation', 
                'automatic_validation',
                'fallback_protection',
                'progress_monitoring'
            ]
        }
    
    def get_available_tools(self) -> Dict[str, Any]:
        """获取ReAct模式可用的工具列表"""
        
        return {
            'analyze_java_project': {
                'description': '分析Java项目结构、架构模式、技术栈等',
                'parameters': {
                    'project_path': 'Java项目根目录路径', 
                    'service_name': '服务名称（可选）'
                },
                'usage': '当需要了解项目架构、包结构、命名规范时使用'
            },
            'get_project_context': {
                'description': '获取项目上下文信息用于代码生成',
                'parameters': {
                    'project_path': 'Java项目根目录路径',
                    'service_name': '服务名称'
                },
                'usage': '在生成代码前获取项目的技术栈和架构信息'
            },
            'analyze_code_patterns': {
                'description': '分析项目的命名模式、分层结构等',
                'parameters': {
                    'project_path': 'Java项目根目录路径'
                },
                'usage': '当需要了解项目编码规范和模式时使用'
            }
        }
    
    def execute_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        
        logger.info(f"🔧 执行工具调用: {tool_name}")
        
        try:
            if tool_name == 'analyze_java_project':
                return self._tool_analyze_java_project(parameters)
            elif tool_name == 'get_project_context':
                return self._tool_get_project_context(parameters)
            elif tool_name == 'analyze_code_patterns':
                return self._tool_analyze_code_patterns(parameters)
            else:
                return {
                    'success': False,
                    'error': f'未知的工具: {tool_name}',
                    'available_tools': list(self.get_available_tools().keys())
                }
                
        except Exception as e:
            logger.error(f"❌ 工具调用失败 {tool_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool_name': tool_name
            }
    
    def _tool_analyze_java_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """工具：分析Java项目"""
        
        project_path = parameters.get('project_path')
        service_name = parameters.get('service_name', 'analyzed_service')
        
        if not project_path:
            return {'success': False, 'error': 'project_path参数是必需的'}
        
        from src.utils.java_code_analyzer import JavaCodeAnalyzer
        
        analyzer = JavaCodeAnalyzer()
        analysis_result = analyzer.analyze_project(project_path, service_name)
        
        # 提取关键信息供大模型使用
        summary = analysis_result.get('summary', {})
        enterprise_arch = analysis_result.get('enterprise_architecture', {})
        
        return {
            'success': True,
            'tool_result': {
                'project_type': summary.get('architecture_type', 'unknown'),
                'is_spring_boot': summary.get('is_spring_boot', False),
                'is_mybatis_plus': summary.get('is_mybatis_plus', False),
                'total_java_files': summary.get('total_java_files', 0),
                'business_domains': summary.get('business_domains', []),
                'complexity_score': summary.get('complexity_score', 0),
                'maintainability_index': summary.get('maintainability_index', 0),
                'dto_usage_rate': summary.get('dto_usage_rate', 0),
                'components': summary.get('components_summary', {}),
                'layer_distribution': summary.get('layer_distribution', {}),
                'package_compliance': summary.get('package_compliance', 0)
            },
            'raw_analysis': analysis_result  # 完整分析结果
        }
    
    def _tool_get_project_context(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """工具：获取项目上下文用于代码生成"""
        
        project_path = parameters.get('project_path')
        service_name = parameters.get('service_name', 'service')
        
        if not project_path:
            return {'success': False, 'error': 'project_path参数是必需的'}
        
        # 使用项目分析API获取代码生成上下文
        try:
            context = self.project_analysis_api.analyze_project_for_code_generation(
                project_path, service_name
            )
            
            return {
                'success': True,
                'tool_result': {
                    'base_package': context.get('package_patterns', {}).get('base_package', 'com.main'),
                    'architecture_type': context.get('project_info', {}).get('architecture_type', 'unknown'),
                    'is_spring_boot': context.get('project_info', {}).get('is_spring_boot', False),
                    'is_mybatis_plus': context.get('project_info', {}).get('is_mybatis_plus', False),
                    'preferred_layer_style': context.get('architecture_patterns', {}).get('preferred_layer_style', 'layered'),
                    'dto_patterns': context.get('component_patterns', {}).get('dto_patterns', {}),
                    'service_patterns': context.get('component_patterns', {}).get('service_patterns', {}),
                    'technology_features': context.get('technology_stack', {}).get('mybatis_plus_features', []),
                    'generation_guidelines': context.get('generation_guidelines', [])
                },
                'full_context': context
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取项目上下文失败: {str(e)}'
            }
    
    def _tool_analyze_code_patterns(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """工具：分析代码模式"""
        
        project_path = parameters.get('project_path')
        
        if not project_path:
            return {'success': False, 'error': 'project_path参数是必需的'}
        
        from src.utils.java_code_analyzer import JavaCodeAnalyzer
        
        analyzer = JavaCodeAnalyzer()
        analysis_result = analyzer.analyze_project(project_path)
        
        patterns = {
            'naming_patterns': analysis_result.get('naming_analysis', {}),
            'layer_analysis': analysis_result.get('layer_analysis', {}),
            'package_analysis': analysis_result.get('package_analysis', {}),
            'components_detected': analysis_result.get('components_detected', {}),
            'enterprise_architecture': analysis_result.get('enterprise_architecture', {})
        }
        
        return {
            'success': True,
            'tool_result': patterns,
            'summary': f"发现 {len(patterns['naming_patterns'])} 种命名模式，{len(patterns['layer_analysis'])} 个分层"
        }
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """递归地将对象转换为JSON可序列化的格式"""
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # 处理自定义对象
            return self._make_json_serializable(obj.__dict__)
        else:
            # 基本类型（str, int, float, bool, None）直接返回
            return obj
    
    def execute_task_from_database(self) -> List[Dict[str, Any]]:
        """从数据库领取并执行智能编码任务"""
        logger.info(f"🎯 {self.node_name} 开始执行任务...")
        
        execution_results = []
        max_rounds = 10  # 防止无限循环的安全机制
        current_round = 0
        
        while current_round < max_rounds:
            current_round += 1
            logger.info(f"🔄 第{current_round}轮任务检查...")
            
            # 获取可执行的任务
            available_tasks = self.task_manager.get_node_tasks(self.supported_task_types)
            
            if not available_tasks:
                logger.info(f"ℹ️ 第{current_round}轮没有可执行的智能编码任务")
                break
            
            logger.info(f"📋 第{current_round}轮找到 {len(available_tasks)} 个可执行任务")
            
            round_execution_count = 0
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
                        result = self._execute_interface_generation_task(task)
                    elif task_type == "config":
                        result = self._execute_config_task(task)
                    else:
                        logger.warning(f"⚠️ 未支持的任务类型: {task_type}")
                        result = {'success': False, 'message': f'未支持的任务类型: {task_type}'}
                    
                    # 更新任务状态 - 使用安全的结果数据
                    safe_result = self._make_json_serializable(result)
                    if result.get('success'):
                        self.task_manager.update_task_status(task_id, 'completed', safe_result)
                        logger.info(f"✅ 任务 {task_id} 执行成功")
                    else:
                        self.task_manager.update_task_status(task_id, 'failed', safe_result)
                        logger.error(f"❌ 任务 {task_id} 执行失败: {result.get('message')}")
                    
                    execution_results.append({
                        'task_id': task_id,
                        'task_type': task_type,
                        'result': result
                    })
                    
                    round_execution_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 任务 {task_id} 执行异常: {e}")
                    error_result = {'success': False, 'message': f'执行异常: {str(e)}'}
                    safe_error_result = self._make_json_serializable(error_result)
                    self.task_manager.update_task_status(task_id, 'failed', safe_error_result)
                    
                    execution_results.append({
                        'task_id': task_id,
                        'task_type': task_type,
                        'result': error_result
                    })
                    
                    round_execution_count += 1
            
            logger.info(f"✅ 第{current_round}轮执行完成，处理了 {round_execution_count} 个任务")
            
            # 如果本轮没有执行任何任务，退出循环
            if round_execution_count == 0:
                logger.info("ℹ️ 本轮没有成功执行任何任务，结束循环")
                break
        
        if current_round >= max_rounds:
            logger.warning(f"⚠️ 达到最大轮次限制 {max_rounds}，强制结束")
        
        logger.info(f"✅ 智能编码任务执行完成，共处理 {len(execution_results)} 个任务，共{current_round}轮")
        return execution_results
    
    def _execute_code_analysis_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码分析任务"""
        logger.info(f"🔍 执行代码分析任务: {task['task_id']}")
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        project_path = parameters.get('project_path')
        
        if not project_path:
            return {
                'success': False,
                'message': 'project_path参数缺失，无法执行代码分析',
                'service_name': service_name
            }
        
        try:
            # 导入Java代码分析工具
            from src.utils.java_code_analyzer import JavaCodeAnalyzer
            
            # 创建分析器实例
            analyzer = JavaCodeAnalyzer()
            
            # 执行项目分析
            analysis_result = analyzer.analyze_project(project_path, service_name)
            
            # 导出分析报告
            report_path = analyzer.export_analysis_report(analysis_result)
            
            # 返回分析结果
            return {
                'success': True,
                'message': f'{service_name}服务Java代码分析完成',
                'analysis_result': analysis_result,
                'report_path': report_path,
                'service_name': service_name,
                'summary': {
                    'total_java_files': analysis_result['summary']['total_java_files'],
                    'is_spring_boot': analysis_result['summary']['is_spring_boot'],
                    'architecture_style': analysis_result['summary']['architecture_type'],  # 修复：字段名从architecture_style改为architecture_type
                    'complexity_score': analysis_result['summary']['complexity_score'],
                    'maintainability_index': analysis_result['summary']['maintainability_index'],
                    'components': analysis_result['components_detected']
                }
            }
            
        except FileNotFoundError as e:
            logger.error(f"❌ 项目路径不存在: {e}")
            return {
                'success': False,
                'message': f'项目路径不存在: {project_path}',
                'service_name': service_name
            }
        except Exception as e:
            logger.error(f"❌ Java代码分析失败: {e}")
            return {
                'success': False,
                'message': f'Java代码分析失败: {str(e)}',
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
    
    # 原有的_execute_api_task方法已被_execute_interface_generation_task替换
    # 该方法现在基于项目分析生成真实的企业级代码，而不是简单的模拟设计
    
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
                        'com.main': 'DEBUG',
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
    
    def _execute_interface_generation_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行基于项目分析和LLM的API接口生成任务"""
        logger.info(f"🌐 执行API接口生成任务: {task['task_id']}")
        
        # 检查LLM客户端
        if not self.llm_client:
            return {
                'success': False,
                'message': 'LLM客户端未初始化，无法执行代码生成',
                'service_name': task.get('service_name', 'unknown')
            }
        
        # 获取任务参数
        parameters = task.get('parameters', {})
        service_name = task.get('service_name', 'unknown_service')
        project_path = parameters.get('project_path')
        
        # 从任务参数中提取具体的接口信息
        api_path = parameters.get('api_path', '/api/example')
        http_method = parameters.get('http_method', 'GET')
        request_params = parameters.get('request_params', {})
        response_params = parameters.get('response_params', {})
        business_logic = parameters.get('business_logic', '示例业务逻辑')
        data_source = parameters.get('data_source', '')
        validation_rules = parameters.get('validation_rules', {})
        
        # 从API路径推导接口名称
        # 例如：/general/multiorgManage/queryCompanyUnitList -> QueryCompanyUnitList
        path_parts = [part for part in api_path.split('/') if part]
        if path_parts:
            # 取最后一个路径部分作为基础接口名
            last_part = path_parts[-1]
            
            # 处理驼峰命名和下划线命名
            if '_' in last_part:
                # 下划线命名：query_company_unit_list -> QueryCompanyUnitList
                words = last_part.split('_')
                interface_name = ''.join(word.capitalize() for word in words if word)
            else:
                # 驼峰命名：queryCompanyUnitList -> QueryCompanyUnitList
                # 先分割驼峰，然后重新组合
                import re
                words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', last_part)
                interface_name = ''.join(word.capitalize() for word in words if word)
            
            # 移除常见的动词前缀，保留核心业务名词
            original_name = interface_name
            for prefix in ['Query', 'Get', 'List', 'Find', 'Search', 'Export', 'Import']:
                if interface_name.startswith(prefix) and len(interface_name) > len(prefix):
                    interface_name = interface_name[len(prefix):]
                    break
            
            # 如果移除前缀后为空或太短，使用原名称
            if not interface_name or len(interface_name) < 3:
                interface_name = original_name
                
            # 确保首字母大写
            interface_name = interface_name[0].upper() + interface_name[1:] if interface_name else 'Example'
        else:
            interface_name = 'Example'
        
        # 构建接口规格信息（转换为统一格式）
        input_params = []
        for param_name, param_desc in request_params.items():
            input_params.append({
                'name': param_name,
                'type': 'String',  # 简化处理，后续可以根据描述推断类型
                'description': param_desc,
                'required': param_name not in ['unitCode', 'openStatus', 'unitList']  # 根据实际需求判断
            })
        
        output_params = {}
        for param_name, param_desc in response_params.items():
            output_params[param_name] = {
                'type': 'String',
                'description': param_desc
            }
        
        description = business_logic or f'{interface_name}接口'
        
        logger.info(f"📋 解析的接口信息:")
        logger.info(f"   - 接口名称: {interface_name}")
        logger.info(f"   - API路径: {api_path}")
        logger.info(f"   - HTTP方法: {http_method}")
        logger.info(f"   - 输入参数: {len(input_params)}个")
        logger.info(f"   - 输出参数: {len(output_params)}个")
        logger.info(f"   - 业务描述: {description}")
        
        if not project_path:
            return {
                'success': False,
                'message': 'project_path参数缺失，无法执行接口生成',
                'service_name': service_name
            }
        
        try:
            # 🎯 深度搜索最佳Java项目路径
            optimized_project_path = self._find_deep_java_project_path(project_path, service_name)
            
            # 🎯 基于API路径关键字查找现有文件结构
            api_keyword = self._extract_api_path_keyword(api_path)
            if api_keyword:
                existing_path = self._find_existing_path_by_keyword(optimized_project_path, api_keyword)
                if existing_path:
                    logger.info(f"🎯 基于API关键字 '{api_keyword}' 找到现有路径: {existing_path}")
                    # 如果找到现有路径，使用该路径作为项目基础路径
                    optimized_project_path = existing_path
            
            # 分析目标项目，获取代码生成上下文
            logger.info(f" 分析目标项目: {optimized_project_path}")
            project_context = self.project_analysis_api.analyze_project_for_code_generation(
                optimized_project_path, service_name
            )
            
            # 🎯 新增：将API路径添加到项目上下文，用于智能路径选择
            project_context['current_api_path'] = api_path
            project_context['optimized_project_path'] = optimized_project_path
            
            # 🆕 新增：将设计文档内容添加到项目上下文（用于增强版代码生成）
            document_content = parameters.get('document_content', '')
            if not document_content and hasattr(self, '_current_design_doc'):
                # 从编码代理的存储中获取设计文档
                document_content = self._current_design_doc
                logger.info(f"📄 从编码代理获取设计文档内容 ({len(document_content)} 字符)")
            
            if not document_content:
                # 从全局状态获取设计文档内容
                import inspect
                frame = inspect.currentframe()
                try:
                    # 查找调用栈中可能包含document_content的帧
                    while frame:
                        if 'document_content' in frame.f_locals:
                            document_content = frame.f_locals['document_content']
                            break
                        frame = frame.f_back
                except:
                    pass
            
            project_context['document_content'] = document_content
            logger.info(f"📄 设计文档内容已添加到项目上下文 ({len(document_content)} 字符)")
            
            # 🆕 新增：检查是否需要在现有Controller中添加接口
            if api_keyword:
                try:
                    from ...code_generator.controller_interface_manager import ControllerInterfaceManager
                    
                    # 初始化Controller接口管理器
                    controller_manager = ControllerInterfaceManager(self.llm_client)
                    
                    # 处理API接口请求
                    add_result = controller_manager.process_api_interface_request(
                        optimized_project_path, api_keyword, api_path, business_logic
                    )
                    
                    if add_result.get('success', False):
                        logger.info(f"✅ 成功在现有Controller中添加接口: {add_result.get('interface_name', '')}")
                        
                        # 🆕 新增：处理Service和Mapper层
                        # 使用现有的模块处理Service和Mapper
                        from ...code_generator.service_decision_maker import ServiceDecisionMaker
                        
                        service_decision_maker = ServiceDecisionMaker(self.llm_client)
                        service_mapper_result = self._handle_service_and_mapper_using_existing_modules(
                            add_result, interface_name, input_params, output_params, 
                            description, project_context, service_decision_maker
                        )
                        
                        # 合并结果
                        all_generated_files = add_result.get('results', [])
                        if service_mapper_result.get('success', False):
                            all_generated_files.extend(service_mapper_result.get('generated_files', []))
                        
                        # 返回成功结果
                        return {
                            'success': True,
                            'message': f'{add_result.get("interface_name", interface_name)}接口已添加到现有Controller中，并处理了Service/Mapper层',
                            'generated_files': all_generated_files,
                            'service_name': service_name,
                            'interface_name': add_result.get('interface_name', interface_name),
                            'api_path': api_path,
                            'llm_provider': self.llm_provider,
                            'generation_mode': 'add_to_existing_controller',
                            'controller_modified': True,
                            'service_mapper_handled': service_mapper_result.get('success', False),
                            'modification_details': {
                                'controller': add_result,
                                'service_mapper': service_mapper_result
                            }
                        }
                    else:
                        logger.info(f"⚠️ 未能在现有Controller中添加接口，将生成新文件")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Controller接口管理器处理失败: {e}, 将生成新文件")
            
            # 使用LLM生成代码
            logger.info(f" 调用{self.llm_provider}大模型生成代码...")
            generated_code = self._generate_code_with_llm(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path=api_path, business_logic=business_logic
            )
            
            # 生成输出文件路径
            # output_path = self._prepare_output_directory(service_name, project_path)  # 不再需要
            code_files = self._write_generated_code(generated_code, optimized_project_path, service_name, project_context)
            
            # 🆕 新增：任务完成后清理备份文件
            try:
                from ...code_generator.interface_adder import InterfaceAdder
                interface_adder = InterfaceAdder()
                cleaned_count = interface_adder.cleanup_backup_files(optimized_project_path)
                if cleaned_count > 0:
                    logger.info(f"🧹 已清理 {cleaned_count} 个备份文件")
            except Exception as e:
                logger.warning(f"⚠️ 清理备份文件时出错: {e}")
            
            return {
                'success': True,
                'message': f'{interface_name}接口生成完成',
                'generated_files': code_files,
                'service_name': service_name,
                'interface_name': interface_name,
                'api_path': api_path,
                'llm_provider': self.llm_provider,
                'generation_mode': 'new_files'
            }
            
        except FileNotFoundError as e:
            logger.error(f"❌ 项目路径不存在: {e}")
            return {
                'success': False,
                'message': f'项目路径不存在: {project_path}',
                'service_name': service_name
            }
        except Exception as e:
            logger.error(f"❌ 接口生成失败: {e}")
            return {
                'success': False,
                'message': f'接口生成失败: {str(e)}',
                'service_name': service_name
            }
    
    def _generate_code_with_llm(self, interface_name: str, input_params: List[Dict], 
                              output_params: Dict, description: str, http_method: str,
                              project_context: Dict[str, Any], api_path: str = '', business_logic: str = '') -> Dict[str, str]:
        """使用LLM基于项目上下文生成企业级接口代码"""
        
        logger.info(f"🔍 开始代码生成...")
        
        # 🎨 优先使用模板+AI混合模式
        if self.react_config.get('use_templates', True) and self.template_ai_generator:
            logger.info("🎨 使用模板+AI混合模式生成代码")
            try:
                generated_code = self.template_ai_generator.generate_code(
                    interface_name, input_params, output_params, description, 
                    http_method, project_context, api_path=api_path, business_logic=business_logic
                )
                if generated_code:
                    logger.info(f"✅ 模板+AI生成成功，生成代码类型: {list(generated_code.keys())}")
                    return generated_code
            except Exception as e:
                logger.warning(f"⚠️ 模板+AI生成失败，回退到传统模式: {e}")
        
        # 后备方案：检查是否启用ReAct模式
        use_react = self.react_config.get('enabled', True)
        
        if use_react:
            logger.info("🧠 启用ReAct模式进行代码生成")
            return self._generate_code_with_react(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path=api_path, business_logic=business_logic
            )
        else:
            logger.info("🔧 使用直接生成模式")
            # 原有的直接生成模式作为fallback
            return self._generate_code_direct(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path=api_path, business_logic=business_logic
            )
    
    def _generate_code_with_react(self, interface_name: str, input_params: List[Dict], 
                                output_params: Dict, description: str, http_method: str,
                                project_context: Dict[str, Any], api_path: str = '', business_logic: str = '') -> Dict[str, str]:
        """使用ReAct模式生成代码 - 思考-行动-观察循环，支持增量式生成"""
        
        logger.info(f"🧠 启动ReAct模式代码生成...")
        
        # 获取配置
        max_iterations = self.react_config.get('max_iterations', 6)
        temperature = self.react_config.get('temperature', 0.1)
        max_tokens = self.react_config.get('max_tokens', 4000)
        log_steps = self.react_config.get('log_react_steps', True)
        
        # 记录ReAct步骤
        react_steps = []
        
        # 构建项目上下文信息
        context_info = self._build_project_context_prompt(project_context)
        requirement_info = self._build_interface_requirement_prompt(
            interface_name, input_params, output_params, description, http_method, api_path=api_path, business_logic=business_logic
        )
        
        # 【新增】预检查目标文件是否存在
        project_path = project_context.get('project_path', '')
        service_name = project_context.get('service_name', 'unknown')
        existing_files_info = self._check_target_files_exist(interface_name, project_path, service_name, project_context)
        
        # ReAct模式的完整对话
        react_messages = [
            {
                "role": "system",
                "content": """你是一个专业的Java企业级后端开发工程师，精通Spring Boot、MyBatis Plus、DDD架构等技术栈。

**重要说明**: 
- 你只负责生成Java后端代码，不要生成任何前端代码（如JavaScript、React、Vue等）
- 所有生成的代码都必须是Java语言，文件扩展名为.java或.xml
- 严格遵循DDD（领域驱动设计）分层架构

**DDD架构分层要求**:
1. **Controller层** (interfaces/rest): 对外REST接口，负责接收HTTP请求
2. **Application Service层** (application/service): 应用服务，协调业务流程
3. **Domain Service层** (domain/service): 领域服务，核心业务逻辑
4. **Domain Mapper层** (domain/mapper): 数据访问层接口
5. **Feign Client层** (application/feign): 外部服务调用接口
6. **DTO层** (interfaces/dto): 数据传输对象
7. **Entity层** (domain/entity): 领域实体
8. **XML映射** (resources/mapper): MyBatis SQL映射

**调用链规范**:
- 查询类API: Controller → Application Service → Domain Service → Mapper → XML
- 外部调用API: Controller → Application Service → Feign Client
- 本地操作API: Controller → Application Service → Domain Service (或 Mapper)

**代码生成要求**:
- 必须生成完整的组件链，不能只生成Controller
- 如果是查询类接口，必须包含：Controller、Application Service、Domain Service、Mapper、XML
- 如果需要外部调用，必须包含：Feign Client
- 所有组件都要有完整的业务逻辑实现
- 遵循企业级代码规范和最佳实践

请根据项目上下文和需求使用ReAct推理模式生成完整的企业级Java后端代码。"""
            },
            {
                "role": "user",
                "content": f"""请使用ReAct推理模式为以下需求生成完整的企业级Java后端代码：

{context_info}

{requirement_info}

## 目标文件现状分析
{self._format_existing_files_info(existing_files_info)}

请开始你的ReAct推理循环，只生成Java后端代码："""
            }
        ]
        
        generated_code = {}
        current_iteration = 0
        
        try:
            while current_iteration < max_iterations:
                current_iteration += 1
                logger.info(f"🔄 ReAct循环第{current_iteration}/{max_iterations}轮...")
                
                # 调用LLM进行ReAct推理
                response = self.llm_client.chat(
                    messages=react_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # 解析ReAct响应
                thought, action, observation, code_blocks, tool_call, tool_params = self._parse_react_response(response)
                
                # 记录ReAct步骤
                step_record = {
                    'iteration': current_iteration,
                    'thought': thought,
                    'action': action,
                    'observation': observation,
                    'code_blocks_count': len(code_blocks) if code_blocks else 0,
                    'tool_call': tool_call,
                    'tool_params': tool_params
                }
                react_steps.append(step_record)
                
                # 记录日志
                if log_steps:
                    if thought:
                        logger.info(f"💭 思考: {thought[:150]}...")
                    if action:
                        logger.info(f"🎯 行动: {action[:150]}...")
                    if observation:
                        logger.info(f"👀 观察: {observation[:150]}...")
                
                # 处理工具调用
                if tool_call and tool_params is not None:
                    logger.info(f"🔧 执行工具调用: {tool_call}")
                    tool_result = self.execute_tool_call(tool_call, tool_params)
                    
                    # 将工具结果添加到对话中
                    tool_response = f"""**Tool Result**: {tool_call}
**Success**: {tool_result.get('success', False)}
**Result**: {json.dumps(tool_result.get('tool_result', {}), ensure_ascii=False, indent=2) if tool_result.get('success') else tool_result.get('error', 'Unknown error')}"""
                    
                    react_messages.append({"role": "user", "content": tool_response})
                    
                    if log_steps:
                        logger.info(f"🔧 工具结果: {tool_result.get('success', False)}")
                
                # 提取代码块
                if code_blocks:
                    new_code = self._extract_code_from_react_response(code_blocks)
                    
                    # 【新增】与现有代码合并（如果目标文件存在）
                    merged_code = self._merge_with_existing_code(new_code, existing_files_info, project_context)
                    generated_code.update(merged_code)
                    
                    logger.info(f"📝 本轮生成了 {len(new_code)} 个代码块，合并后共 {len(generated_code)} 个")
                
                # 【新增】每轮生成后立即写入并验证文件
                if generated_code:
                    written_files = self._write_generated_code(generated_code, project_path, service_name, project_context)
                    file_validation = self._validate_written_files(written_files)
                    
                    # 将文件验证结果添加到对话中
                    if file_validation['success']:
                        validation_message = f"""**文件写入验证**: ✅ 成功
**写入文件数**: {file_validation['written_count']}
**验证状态**: {', '.join([f"{name}: ✅" for name in file_validation['validated_files']])}"""
                    else:
                        validation_message = f"""**文件写入验证**: ❌ 失败
**失败原因**: {file_validation.get('error', 'Unknown error')}
**失败文件**: {', '.join(file_validation.get('failed_files', []))}"""
                    
                    react_messages.append({"role": "user", "content": validation_message})
                
                # 更新对话历史
                react_messages.append({"role": "assistant", "content": response})
                
                # 检查是否完成
                is_complete, completion_status = self._is_react_generation_complete_with_details(
                    generated_code, project_context
                )
                
                if is_complete:
                    logger.info("✅ ReAct代码生成完成")
                    if log_steps:
                        logger.info(f"🎯 完成状态: {completion_status}")
                    break
                
                # 添加下一轮指导
                next_guidance = self._get_next_react_guidance(generated_code, project_context)
                
                # 增强的指导信息
                progress_info = self._get_react_progress_info(generated_code, project_context)
                
                react_messages.append({
                    "role": "user", 
                    "content": f"""请继续ReAct循环（当前第{current_iteration}/{max_iterations}轮）：

{progress_info}

{next_guidance}

**Thought**: [继续分析还需要生成什么]
**Action**: [下一步要生成的代码组件]
**Observation**: [验证当前进度和文件状态]"""
                })
            
            # 验证和修正生成的代码
            validated_code = self._validate_and_fix_generated_code(generated_code, project_context)
            
            # 记录最终结果
            if log_steps:
                logger.info(f"🎊 ReAct完成摘要: 共{len(react_steps)}轮，生成{len(validated_code)}个代码组件")
                logger.info(f"📋 最终生成: {list(validated_code.keys())}")
            
            return validated_code
            
        except Exception as e:
            logger.error(f"❌ ReAct代码生成失败: {e}")
            
            # 记录失败步骤
            if log_steps:
                logger.info(f"📊 失败前ReAct步骤记录: {len(react_steps)}轮")
            
            # fallback到直接生成模式
            if self.react_config.get('fallback_on_failure', True):
                logger.info("🔄 ReAct失败，fallback到直接生成模式...")
                return self._generate_code_direct(
                    interface_name, input_params, output_params, description, 
                    http_method, project_context, api_path=api_path, business_logic=business_logic
                )
            else:
                # 如果不允许fallback，返回已生成的代码
                logger.warning("⚠️ ReAct失败且不允许fallback，返回已生成的代码")
                return self._validate_and_fix_generated_code(generated_code, project_context)
    
    def _check_target_files_exist(self, interface_name: str, project_path: str, 
                                 service_name: str, project_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """检查目标文件是否已存在"""
        
        logger.info(f"🔍 检查目标文件是否存在: {interface_name}")
        
        # 预测目标文件路径
        predicted_paths = self._determine_output_paths_default({
            'controller': '',
            'service': '',
            'request_dto': '',
            'response_dto': '',
            'entity': '',
            'mapper': ''
        }, project_path, service_name, project_context)
        
        existing_files_info = {}
        
        for code_type, file_path in predicted_paths.items():
            file_info = {
                'exists': False,
                'path': file_path,
                'size': 0,
                'content_preview': '',
                'classes_found': [],
                'methods_found': [],
                'needs_merge': False
            }
            
            if os.path.exists(file_path):
                file_info['exists'] = True
                file_info['size'] = os.path.getsize(file_path)
                
                try:
                    # 读取现有文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_info['content_preview'] = content[:300] + '...' if len(content) > 300 else content
                    
                    # 简单解析类名和方法名
                    import re
                    class_matches = re.findall(r'public\s+(?:class|interface)\s+(\w+)', content)
                    method_matches = re.findall(r'public\s+[^{]+\s+(\w+)\s*\([^)]*\)\s*\{', content)
                    
                    file_info['classes_found'] = class_matches
                    file_info['methods_found'] = method_matches
                    file_info['needs_merge'] = True
                    # 新增：检测是否已包含目标接口/方法
                    if interface_name in class_matches or any(interface_name in m for m in method_matches):
                        file_info['already_has_target'] = True
                    else:
                        file_info['already_has_target'] = False
                    
                    logger.info(f"📄 {code_type} 文件已存在: {Path(file_path).name} ({file_info['size']} bytes)")
                    
                except Exception as e:
                    logger.warning(f"⚠️ 读取现有文件失败 {file_path}: {e}")
                    file_info['already_has_target'] = False
            else:
                logger.info(f"📄 {code_type} 文件不存在，将生成新文件: {Path(file_path).name}")
                file_info['already_has_target'] = False
            
            existing_files_info[code_type] = file_info
        
        return existing_files_info
    
    def _format_existing_files_info(self, existing_files_info: Dict[str, Dict[str, Any]]) -> str:
        """格式化现有文件信息为可读文本"""
        
        info_parts = []
        existing_count = sum(1 for info in existing_files_info.values() if info['exists'])
        total_count = len(existing_files_info)
        
        info_parts.append(f"📊 文件现状: {existing_count}/{total_count} 个文件已存在")
        
        for code_type, file_info in existing_files_info.items():
            if file_info['exists']:
                info_parts.append(f"✅ {code_type}: {Path(file_info['path']).name} "
                                f"({file_info['size']} bytes, "
                                f"{len(file_info['classes_found'])} 类, "
                                f"{len(file_info['methods_found'])} 方法)")
            else:
                info_parts.append(f"⭕ {code_type}: {Path(file_info['path']).name} (需要生成)")
        
        if existing_count > 0:
            info_parts.append("\n⚠️ 对于已存在的文件，请进行智能合并，保留现有功能并添加新的API函数")
        
        return '\n'.join(info_parts)
    
    def _merge_with_existing_code(self, new_code: Dict[str, str], 
                                existing_files_info: Dict[str, Dict[str, Any]],
                                project_context: Dict[str, Any]) -> Dict[str, str]:
        """将新代码与现有代码智能合并"""
        
        merged_code = {}
        
        for code_type, new_content in new_code.items():
            file_info = existing_files_info.get(code_type, {})
            
            if file_info.get('exists') and file_info.get('needs_merge'):
                logger.info(f"🔗 智能合并 {code_type} 代码...")
                
                try:
                    # 读取现有文件内容
                    existing_path = file_info['path']
                    with open(existing_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    
                    # 执行智能合并
                    merged_content = self._intelligent_merge_api_functions(
                        existing_content, new_content, code_type
                    )
                    
                    merged_code[code_type] = merged_content
                    logger.info(f"✅ {code_type} 代码合并完成")
                    
                except Exception as e:
                    logger.warning(f"⚠️ {code_type} 代码合并失败，使用新代码: {e}")
                    merged_code[code_type] = new_content
            else:
                # 文件不存在或无需合并，直接使用新代码
                merged_code[code_type] = new_content
                logger.info(f"📝 {code_type} 使用新生成的代码")
        
        return merged_code
    
    def _intelligent_merge_api_functions(self, existing_content: str, new_content: str, code_type: str) -> str:
        """智能合并API函数"""
        
        import re
        
        # 提取新代码中的方法
        new_methods = re.findall(r'(public\s+[^{]+\{[^}]*\})', new_content, re.DOTALL)
        new_method_names = re.findall(r'public\s+[^{]+\s+(\w+)\s*\([^)]*\)', new_content)
        
        # 检查现有代码中是否已有同名方法
        existing_method_names = re.findall(r'public\s+[^{]+\s+(\w+)\s*\([^)]*\)', existing_content)
        
        merged_content = existing_content
        
        # 添加新方法（如果不存在同名方法）
        for i, method_name in enumerate(new_method_names):
            if method_name not in existing_method_names and i < len(new_methods):
                # 在类的结束大括号前插入新方法
                new_method = new_methods[i]
                
                # 找到类的结束位置
                class_end_pos = merged_content.rfind('}')
                if class_end_pos != -1:
                    # 在类结束前插入新方法
                    merged_content = (merged_content[:class_end_pos] + 
                                    f"\n    {new_method}\n" + 
                                    merged_content[class_end_pos:])
                    
                    logger.info(f"✅ 添加新方法: {method_name}")
                else:
                    logger.warning(f"⚠️ 无法定位类结束位置，跳过方法: {method_name}")
            else:
                logger.info(f"ℹ️ 方法 {method_name} 已存在，跳过")
        
        return merged_content
    
    def _validate_written_files(self, written_files: Dict[str, str]) -> Dict[str, Any]:
        """验证写入的文件是否成功"""
        
        validation_result = {
            'success': True,
            'written_count': len(written_files),
            'validated_files': [],
            'failed_files': [],
            'error': None
        }
        
        for code_type, file_path in written_files.items():
            try:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    # 验证文件是否为有效的Java代码
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 基本检查：是否包含package声明和class定义
                    if 'package ' in content and ('class ' in content or 'interface ' in content):
                        validation_result['validated_files'].append(code_type)
                        logger.info(f"✅ 文件验证成功: {Path(file_path).name}")
                    else:
                        validation_result['failed_files'].append(code_type)
                        validation_result['success'] = False
                        logger.warning(f"⚠️ 文件内容验证失败: {Path(file_path).name}")
                else:
                    validation_result['failed_files'].append(code_type)
                    validation_result['success'] = False
                    logger.error(f"❌ 文件不存在或为空: {Path(file_path).name}")
                    
            except Exception as e:
                validation_result['failed_files'].append(code_type)
                validation_result['success'] = False
                validation_result['error'] = str(e)
                logger.error(f"❌ 文件验证异常 {file_path}: {e}")
        
        return validation_result
    
    def _parse_react_response(self, response: str) -> tuple:
        """解析ReAct响应中的思考、行动、观察、工具调用和代码"""
        
        import re
        
        # 提取Thought
        thought_match = re.search(r'\*\*Thought\*\*:\s*(.*?)(?=\*\*Action\*\*|$)', response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""
        
        # 提取Action
        action_match = re.search(r'\*\*Action\*\*:\s*(.*?)(?=\*\*Observation\*\*|```|\*\*Tool Call\*\*|$)', response, re.DOTALL)
        action = action_match.group(1).strip() if action_match else ""
        
        # 提取Observation
        observation_match = re.search(r'\*\*Observation\*\*:\s*(.*?)(?=```|$)', response, re.DOTALL)
        observation = observation_match.group(1).strip() if observation_match else ""
        
        # 提取Tool Call
        tool_call_match = re.search(r'\*\*Tool Call\*\*:\s*(.*?)(?=\*\*Parameters\*\*|$)', response, re.DOTALL)
        tool_call = tool_call_match.group(1).strip() if tool_call_match else None
        
        # 提取Tool Parameters  
        tool_params = None
        if tool_call:
            params_match = re.search(r'\*\*Parameters\*\*:\s*(\{.*?\})', response, re.DOTALL)
            if params_match:
                try:
                    import json
                    tool_params = json.loads(params_match.group(1))
                except json.JSONDecodeError:
                    logger.warning("⚠️ 工具参数JSON解析失败")
                    tool_params = {}
        
        # 提取代码块
        code_blocks = re.findall(r'```java\n(.*?)\n```', response, re.DOTALL)
        
        return thought, action, observation, code_blocks, tool_call, tool_params
    
    def _extract_code_from_react_response(self, code_blocks: List[str]) -> Dict[str, str]:
        """从ReAct响应中提取代码"""
        
        extracted_code = {}
        
        for i, code_block in enumerate(code_blocks):
            code_content = code_block.strip()
            
            # 根据代码内容判断类型
            if '@RestController' in code_content or '@Controller' in code_content:
                extracted_code['controller'] = code_content
            elif '@Service' in code_content and 'class' in code_content:
                # 🔧 修复：区分Service接口和ServiceImpl实现类
                if 'implements' in code_content or code_content.strip().endswith('Impl {') or 'ServiceImpl' in code_content:
                    extracted_code['service_impl'] = code_content
                else:
                    extracted_code['service'] = code_content
            elif 'interface' in code_content and ('Service' in code_content or '@Service' in code_content):
                # 🔧 新增：明确识别Service接口
                extracted_code['service'] = code_content
            elif 'Request' in code_content and 'class' in code_content:
                extracted_code['request_dto'] = code_content
            elif 'Req' in code_content and 'class' in code_content:
                extracted_code['request_dto'] = code_content
            elif 'Response' in code_content and 'class' in code_content:
                extracted_code['response_dto'] = code_content
            elif 'Resp' in code_content and 'class' in code_content:
                extracted_code['response_dto'] = code_content
            elif '@Entity' in code_content or '@Table' in code_content:
                extracted_code['entity'] = code_content
            elif '@Mapper' in code_content or 'interface' in code_content and 'Mapper' in code_content:
                extracted_code['mapper'] = code_content
            else:
                # 🔧 改进：通用代码块处理
                extracted_code[f'java_code_{i+1}'] = code_content
                
        logger.info(f"📝 从ReAct响应提取到的代码类型: {list(extracted_code.keys())}")
        
        # 🔧 修复：确保Service接口和实现类配对，无论哪种情况都要生成完整的Service层
        service_interface_generated = False
        service_impl_generated = False
        
        # 检查是否有Service接口
        if 'service' in extracted_code:
            service_content = extracted_code['service']
            if 'interface' in service_content:
                service_interface_generated = True
                logger.info("✅ 检测到Service接口")
            elif 'class' in service_content and 'implements' not in service_content:
                # 这是一个Service类但不是接口实现模式
                logger.info("⚠️ 检测到Service类，但不是接口实现模式")
        
        # 检查是否有ServiceImpl
        if 'service_impl' in extracted_code:
            service_impl_generated = True
            logger.info("✅ 检测到ServiceImpl实现类")
        
        # 🔧 核心修复：如果只有ServiceImpl没有Service接口，自动生成Service接口
        if service_impl_generated and not service_interface_generated:
            logger.warning("⚠️ 检测到ServiceImpl但缺少Service接口，将自动生成Service接口")
            service_impl_content = extracted_code['service_impl']
            service_interface = self._generate_service_interface_from_impl(service_impl_content)
            if service_interface:
                extracted_code['service'] = service_interface
                logger.info("✅ 自动生成了Service接口")
            else:
                logger.error("❌ 自动生成Service接口失败")
        
        # 🔧 新增：如果只有Service类但不是接口模式，转换为接口+实现模式
        elif not service_impl_generated and 'service' in extracted_code:
            service_content = extracted_code['service']
            if 'class' in service_content and 'interface' not in service_content:
                logger.info("🔄 将Service类转换为接口+实现模式")
                
                # 生成Service接口
                service_interface = self._convert_service_class_to_interface(service_content)
                if service_interface:
                    extracted_code['service'] = service_interface
                    # 将原Service类改为ServiceImpl
                    service_impl = self._convert_service_class_to_impl(service_content)
                    if service_impl:
                        extracted_code['service_impl'] = service_impl
                    logger.info("✅ 成功转换为接口+实现模式")
        
        return extracted_code
    
    def _generate_service_interface_from_impl(self, service_impl_content: str) -> str:
        """从ServiceImpl实现类生成对应的Service接口"""
        
        try:
            import re
            
            # 提取类名
            class_match = re.search(r'class\s+(\w+)(?:Impl)?\s+(?:implements\s+\w+\s+)?{', service_impl_content)
            if not class_match:
                return None
            
            impl_class_name = class_match.group(1)
            service_interface_name = impl_class_name.replace('ServiceImpl', 'Service').replace('Impl', 'Service')
            
            # 提取包名
            package_match = re.search(r'package\s+([\w.]+);', service_impl_content)
            package_name = package_match.group(1) if package_match else 'com.example.service'
            
            # 提取公共方法
            methods = []
            method_pattern = r'public\s+(?!class)([^{]+\{)'
            for method_match in re.finditer(method_pattern, service_impl_content, re.DOTALL):
                method_signature = method_match.group(1).replace('{', '').strip()
                # 清理方法签名，移除实现细节
                if not any(keyword in method_signature.lower() for keyword in ['constructor', 'gettersetter']):
                    methods.append(f"    {method_signature};")
            
            # 生成Service接口
            service_interface = f"""package {package_name};

/**
 * {service_interface_name} - 业务服务接口
 */
public interface {service_interface_name} {{

{chr(10).join(methods)}

}}"""
            
            return service_interface
            
        except Exception as e:
            logger.error(f"❌ 生成Service接口失败: {e}")
            return None
    
    def _is_react_generation_complete(self, generated_code: Dict[str, str], 
                                    project_context: Dict[str, Any]) -> bool:
        """检查ReAct代码生成是否完成"""
        
        # 基本检查：至少需要controller和service
        required_components = ['controller', 'service', 'response_dto']
        
        # 如果有输入参数，还需要request_dto
        if any('request_dto' in code_type for code_type in generated_code.keys()):
            required_components.append('request_dto')
        
        # 如果使用MyBatis Plus，还需要entity和mapper
        if project_context.get('project_info', {}).get('is_mybatis_plus'):
            required_components.extend(['entity', 'mapper'])
        
        # 检查是否都生成了
        missing_components = [comp for comp in required_components if comp not in generated_code]
        
        if missing_components:
            logger.info(f"🔍 还需要生成: {missing_components}")
            return False
        
        logger.info("✅ 所有必需组件都已生成")
        return True
    
    def _is_react_generation_complete_with_details(self, generated_code: Dict[str, str], 
                                                 project_context: Dict[str, Any]) -> tuple:
        """检查ReAct代码生成是否完成，返回详细状态 - 支持DDD架构完整性检查"""
        
        # 🆕 DDD架构必需组件定义
        core_components = ['controller']  # Controller是必需的
        recommended_components = []
        
        # 根据业务需求动态添加必需组件
        has_request_params = any('Request' in code_type or 'Req' in code_type for code_type in generated_code.keys())
        has_response_params = any('Response' in code_type or 'Resp' in code_type for code_type in generated_code.keys())
        
        if has_request_params:
            core_components.append('request_dto')
        if has_response_params or not has_request_params:  # 至少需要响应DTO
            core_components.append('response_dto')
        
        # 🆕 增强：根据API类型判断必需组件
        api_path = project_context.get('current_api_path', '')
        
        # 如果是查询类API，需要完整的数据访问层
        if any(keyword in api_path.lower() for keyword in ['list', 'query', 'get', 'find', 'search']):
            recommended_components.extend(['application_service', 'domain_service', 'mapper', 'mapper_xml'])
            logger.info("🔍 检测到查询类API，需要完整的数据访问组件")
        
        # 如果是操作类API，可能需要Feign客户端或完整服务层
        elif any(keyword in api_path.lower() for keyword in ['create', 'update', 'delete', 'save', 'export']):
            recommended_components.extend(['application_service', 'domain_service'])
            logger.info("✏️ 检测到操作类API，需要服务层组件")
        
        # 🆕 智能组件推荐：如果项目上下文显示使用MyBatis Plus
        if project_context.get('project_info', {}).get('is_mybatis_plus'):
            recommended_components.extend(['entity', 'mapper'])
            logger.info("🗄️ 检测到MyBatis Plus项目，推荐Entity和Mapper组件")
        
        # 合并核心组件和推荐组件
        all_required_components = core_components + recommended_components
        
        # 检查当前生成的组件
        generated_components = list(generated_code.keys())
        
        # 🔧 修复：使用更智能的组件匹配
        matched_core = []
        matched_recommended = []
        
        for component in all_required_components:
            # 检查是否有匹配的组件
            if component in generated_components:
                if component in core_components:
                    matched_core.append(component)
                else:
                    matched_recommended.append(component)
            else:
                # 🆕 模糊匹配：尝试通过代码内容匹配
                for code_type, content in generated_code.items():
                    if self._is_component_match(component, code_type, content):
                        if component in core_components:
                            matched_core.append(component)
                        else:
                            matched_recommended.append(component)
                        break
        
        # 计算完成状态
        missing_core = [comp for comp in core_components if comp not in matched_core]
        missing_recommended = [comp for comp in recommended_components if comp not in matched_recommended]
        
        # 🆕 完成条件：至少完成所有核心组件
        if not missing_core:
            completion_status = {
                'status': 'complete',
                'core_components': len(matched_core),
                'recommended_components': len(matched_recommended),
                'total_components': len(generated_components),
                'missing_core': [],
                'missing_recommended': missing_recommended,
                'message': f'✅ 核心组件({len(matched_core)})已完成，推荐组件({len(matched_recommended)})已生成'
            }
            return True, completion_status
        else:
            completion_status = {
                'status': 'incomplete',
                'core_components': len(matched_core),
                'recommended_components': len(matched_recommended), 
                'total_components': len(generated_components),
                'missing_core': missing_core,
                'missing_recommended': missing_recommended,
                'message': f'❌ 还缺少{len(missing_core)}个核心组件: {", ".join(missing_core)}'
            }
            return False, completion_status
    
    def _is_component_match(self, required_component: str, code_type: str, code_content: str) -> bool:
        """检查代码类型和内容是否匹配所需组件"""
        
        # 组件匹配映射
        component_patterns = {
            'controller': ['@RestController', '@Controller', 'Controller'],
            'service': ['@Service', 'Service', 'interface'],
            'application_service': ['@Service', 'ApplicationService', 'Application'],
            'domain_service': ['@Service', 'DomainService', 'Domain'],
            'mapper': ['@Mapper', 'BaseMapper', 'Mapper'],
            'request_dto': ['Request', 'Req', 'DTO'],
            'response_dto': ['Response', 'Resp', 'DTO'],
            'entity': ['@Entity', '@TableName', 'Entity'],
            'feign_client': ['@FeignClient', 'FeignClient', 'Client'],
            'mapper_xml': ['mapper', '.xml', '<?xml']
        }
        
        if required_component in component_patterns:
            patterns = component_patterns[required_component]
            return any(pattern in code_content or pattern.lower() in code_type.lower() for pattern in patterns)
        
        return False
    
    def _get_react_progress_info(self, generated_code: Dict[str, str], 
                               project_context: Dict[str, Any]) -> str:
        """获取ReAct进度信息"""
        
        if not generated_code:
            return "🚀 开始代码生成，当前无已生成组件"
        
        # 分析已生成的组件
        component_types = {
            'controller': '控制器',
            'service': '服务层',
            'request_dto': '请求DTO',
            'response_dto': '响应DTO',
            'entity': '实体类',
            'mapper': '数据访问层'
        }
        
        generated_descriptions = []
        for comp_type, comp_name in component_types.items():
            if comp_type in generated_code:
                generated_descriptions.append(f"✅ {comp_name}")
            else:
                generated_descriptions.append(f"⏳ {comp_name}")
        
        is_mybatis_plus = project_context.get('project_info', {}).get('is_mybatis_plus', False)
        
        progress_text = f"""📊 当前进度（已生成{len(generated_code)}个组件）:
{chr(10).join(generated_descriptions)}

💡 技术栈信息:
- MyBatis Plus: {'启用' if is_mybatis_plus else '未启用'}
- 包结构: {project_context.get('package_patterns', {}).get('base_package', 'com.main')}"""
        
        return progress_text
    
    def _get_next_react_guidance(self, generated_code: Dict[str, str], 
                               project_context: Dict[str, Any]) -> str:
        """获取下一轮ReAct指导信息 - 支持DDD架构完整性指导"""
        
        generated_types = list(generated_code.keys())
        
        # 🆕 DDD架构组件优先级指导
        api_path = project_context.get('current_api_path', '')
        
        # 基础组件检查
        missing_guidance = []
        
        if not any('controller' in t.lower() for t in generated_types):
            missing_guidance.append("🎯 首先生成Controller层，作为REST接口入口")
        
        # 🆕 根据API类型提供精确指导
        if any(keyword in api_path.lower() for keyword in ['list', 'query', 'get', 'find', 'search']):
            # 查询类API需要完整的数据访问链路
            if not any('application' in t.lower() and 'service' in t.lower() for t in generated_types):
                missing_guidance.append("🔗 生成Application Service，协调业务流程")
            
            if not any('domain' in t.lower() and 'service' in t.lower() for t in generated_types):
                missing_guidance.append("🧠 生成Domain Service，处理核心业务逻辑")
            
            if not any('mapper' in t.lower() and '.xml' not in t.lower() for t in generated_types):
                missing_guidance.append("🗄️ 生成Mapper接口，定义数据访问方法")
                
            if not any('mapper' in t.lower() and 'xml' in t.lower() for t in generated_types):
                missing_guidance.append("📄 生成Mapper XML文件，编写SQL查询语句")
                
        elif any(keyword in api_path.lower() for keyword in ['export']):
            # 导出类API可能需要Feign客户端
            if not any('feign' in t.lower() for t in generated_types):
                missing_guidance.append("🌐 考虑生成Feign Client，调用外部服务")
                
        # DTO检查
        if not any('request' in t.lower() or 'req' in t.lower() for t in generated_types):
            missing_guidance.append("📥 生成Request DTO，定义输入参数结构")
            
        if not any('response' in t.lower() or 'resp' in t.lower() for t in generated_types):
            missing_guidance.append("📤 生成Response DTO，定义返回数据结构")
        
        # 实体层检查（如果使用MyBatis Plus）
        if project_context.get('project_info', {}).get('is_mybatis_plus'):
            if not any('entity' in t.lower() for t in generated_types):
                missing_guidance.append("🏗️ 生成Entity实体类，映射数据库表结构")
        
        if missing_guidance:
            guidance = "**下一步生成建议:**\n" + "\n".join(f"- {guide}" for guide in missing_guidance[:3])  # 限制最多3个建议
        else:
            guidance = "**继续完善代码:**\n- 🔍 检查现有代码是否完整\n- 🛠️ 优化代码质量和注释\n- ✅ 确认所有业务逻辑实现"
        
        # 🆕 添加DDD架构调用链指导
        guidance += "\n\n**DDD架构调用链:**\n"
        if any(keyword in api_path.lower() for keyword in ['list', 'query', 'get', 'find', 'search']):
            guidance += "Controller → Application Service → Domain Service → Mapper → XML"
        elif any(keyword in api_path.lower() for keyword in ['export']):
            guidance += "Controller → Application Service → Feign Client (外部调用)"
        else:
            guidance += "Controller → Application Service → Domain Service (或 Mapper)"
        
        return guidance
    
    def _generate_code_direct(self, interface_name: str, input_params: List[Dict], 
                            output_params: Dict, description: str, http_method: str,
                            project_context: Dict[str, Any], api_path: str = '', business_logic: str = '') -> Dict[str, str]:
        """直接生成模式（非ReAct）- 作为fallback使用"""
        
        logger.info(f"使用直接生成模式...")
        
        # 构建项目上下文信息
        context_info = self._build_project_context_prompt(project_context)
        
        # 构建接口需求信息
        requirement_info = self._build_interface_requirement_prompt(
            interface_name, input_params, output_params, description, http_method, api_path=api_path, business_logic=business_logic
        )
        
        # 构建代码生成指令
        generation_prompt = self._build_code_generation_prompt(context_info, requirement_info)
        
        # 调用LLM生成代码
        messages = [
            {
                "role": "system", 
                "content": """你是一个专业的Java企业级后端开发工程师，精通Spring Boot、MyBatis Plus等后端技术栈。

**重要说明**: 
- 你只负责生成Java后端代码，不要生成任何前端代码（如JavaScript、React、Vue等）
- 所有生成的代码都必须是Java语言，文件扩展名为.java或.xml
- 专注于企业级后端架构：Controller、Service、DTO、Entity、Mapper等

请根据项目上下文和需求生成高质量的企业级Java后端代码。"""
            },
            {
                "role": "user", 
                "content": generation_prompt
            }
        ]
        
        try:
            logger.info(f"🤖 调用{self.llm_provider}生成代码...")
            llm_response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,  # 代码生成使用较低温度
                max_tokens=4000   # 代码生成需要更多token
            )
            
            # 解析LLM响应中的代码
            generated_code = self._parse_llm_code_response(llm_response)
            
            # 验证和修正生成的代码
            validated_code = self._validate_and_fix_generated_code(generated_code, project_context)
            
            return validated_code
            
        except Exception as e:
            logger.error(f"❌ LLM代码生成失败: {e}")
            # 如果LLM生成失败，fallback到模板生成
            logger.info("🔄 LLM失败，使用模板生成fallback...")
            return self._generate_fallback_code(interface_name, input_params, output_params, 
                                              description, http_method, project_context, api_path=api_path, business_logic=business_logic)
    
    def _build_project_context_prompt(self, project_context: Dict[str, Any]) -> str:
        """构建项目上下文提示信息"""
        
        project_info = project_context.get('project_info', {})
        package_patterns = project_context.get('package_patterns', {})
        architecture_patterns = project_context.get('architecture_patterns', {})
        component_patterns = project_context.get('component_patterns', {})
        technology_stack = project_context.get('technology_stack', {})
        generation_guidelines = project_context.get('generation_guidelines', [])
        
        context_prompt = f"""
## 项目分析上下文

### 基础信息
- 项目架构: {project_info.get('architecture_type', 'unknown')}
- Spring Boot: {'是' if project_info.get('is_spring_boot') else '否'}
- MyBatis Plus: {'是' if project_info.get('is_mybatis_plus') else '否'}
- 基础包名: {package_patterns.get('base_package', 'com.main')}

### 架构模式
- 分层风格: {architecture_patterns.get('preferred_layer_style', 'unknown')}
- 有接口层: {'是' if architecture_patterns.get('has_interfaces_layer') else '否'}
- 有应用层: {'是' if architecture_patterns.get('has_application_layer') else '否'}
- 有领域层: {'是' if architecture_patterns.get('has_domain_layer') else '否'}

### 命名约定
- Request后缀: {component_patterns.get('dto_patterns', {}).get('request_suffix', 'Request')}
- Response后缀: {component_patterns.get('dto_patterns', {}).get('response_suffix', 'Response')}
- Service后缀: {component_patterns.get('service_patterns', {}).get('service_suffix', 'Service')}
- Controller后缀: {component_patterns.get('service_patterns', {}).get('controller_suffix', 'Controller')}

### 技术栈特性
- MyBatis Plus特性: {', '.join(technology_stack.get('mybatis_plus_features', []))}
- 常用依赖: {', '.join(technology_stack.get('common_dependencies', []))}

### 代码生成指导原则
{chr(10).join(f'- {guideline}' for guideline in generation_guidelines)}
"""
        return context_prompt.strip()
    
    def _build_interface_requirement_prompt(self, interface_name: str, input_params: List[Dict], 
                                          output_params: Dict, description: str, http_method: str,
                                          api_path: str = '', business_logic: str = '') -> str:
        """构建接口需求提示信息"""
        
        # 格式化输入参数
        input_params_text = ""
        if input_params:
            input_params_text = "\n".join([
                f"  - {param.get('name', 'field')}: {param.get('type', 'String')} "
                f"{'(必填)' if param.get('required', True) else '(可选)'} "
                f"- {param.get('description', '')}"
                for param in input_params
            ])
        else:
            input_params_text = "  无输入参数"
        
        # 格式化输出参数
        output_params_text = ""
        if output_params:
            if isinstance(output_params, dict):
                output_params_text = "\n".join([
                    f"  - {field_name}: {field_info.get('type', 'String') if isinstance(field_info, dict) else field_info} "
                    f"- {field_info.get('description', '') if isinstance(field_info, dict) else ''}"
                    for field_name, field_info in output_params.items()
                ])
            else:
                output_params_text = f"  - {output_params}"
        else:
            output_params_text = "  默认返回标准响应对象"
        
        # 处理API路径，生成合适的RequestMapping
        request_mapping = api_path if api_path else f"/api/v1/{interface_name.lower()}"
        
        requirement_prompt = f"""
## 接口需求规格

### 基本信息
- 接口名称: {interface_name}
- 功能描述: {description}
- HTTP方法: {http_method}
- 请求路径: {request_mapping}
- 业务逻辑: {business_logic if business_logic else description}

### 输入参数
{input_params_text}

### 输出参数
{output_params_text}

### 技术要求
- 使用SpringBoot REST风格接口
- 请求路径严格按照: {request_mapping}
- 类名应为: {interface_name}Controller
- 方法名根据业务逻辑命名（如：query、list、get等）
- 添加适当的参数校验注解
- 返回统一的响应格式
"""
        return requirement_prompt.strip()
    
    def _build_code_generation_prompt(self, context_info: str, requirement_info: str) -> str:
        """构建完整的代码生成提示"""
        
        prompt = f"""
{context_info}

{requirement_info}

## 代码生成要求

请根据以上项目上下文和接口需求，生成完整的企业级Java代码，包括：

1. **Controller类** - RESTful接口控制器
2. **Service类** - 业务逻辑服务层
3. **Request DTO** - 请求数据传输对象（如有输入参数）
4. **Response DTO** - 响应数据传输对象
5. **Entity类** - 实体类（如果使用MyBatis Plus）
6. **Mapper接口** - 数据访问层（如果使用MyBatis Plus）

### 代码质量要求：
- 严格遵循项目现有的包名、命名约定和架构模式
- 使用项目中已有的注解和技术栈特性
- 添加完整的JavaDoc注释和参数验证
- 生成的代码应该可以直接编译运行
- 每个类都包含必要的import语句

### 输出格式：
请使用以下格式输出代码，每个代码块用```java包围：

```java
// Controller类代码
[Controller代码内容]
```

```java
// Service类代码
[Service代码内容]
```

```java
// Request DTO代码（如需要）
[Request DTO代码内容]
```

```java
// Response DTO代码
[Response DTO代码内容]
```

```java
// Entity类代码（如使用MyBatis Plus）
[Entity代码内容]
```

```java
// Mapper接口代码（如使用MyBatis Plus）
[Mapper代码内容]
```

请开始生成代码：
"""
        return prompt.strip()
    
    def _parse_llm_code_response(self, llm_response: str) -> Dict[str, str]:
        """解析LLM响应中的代码块"""
        
        import re
        
        # 查找所有Java代码块
        code_blocks = re.findall(r'```java\n(.*?)\n```', llm_response, re.DOTALL)
        
        parsed_code = {}
        
        for i, code_block in enumerate(code_blocks):
            code_content = code_block.strip()
            
            # 根据代码内容判断类型
            if '@RestController' in code_content or '@Controller' in code_content:
                parsed_code['controller'] = code_content
            elif '@Service' in code_content:
                parsed_code['service'] = code_content
            elif 'Request' in code_content and 'class' in code_content:
                parsed_code['request_dto'] = code_content
            elif 'Response' in code_content and 'class' in code_content:
                parsed_code['response_dto'] = code_content
            elif '@TableName' in code_content or '@Entity' in code_content:
                parsed_code['entity'] = code_content
            elif 'BaseMapper' in code_content or '@Mapper' in code_content:
                parsed_code['mapper'] = code_content
            else:
                # 无法分类的代码，使用序号命名
                parsed_code[f'code_block_{i+1}'] = code_content
        
        logger.info(f"📝 解析到 {len(parsed_code)} 个代码块: {list(parsed_code.keys())}")
        return parsed_code
    
    def _validate_and_fix_generated_code(self, generated_code: Dict[str, str], 
                                       project_context: Dict[str, Any]) -> Dict[str, str]:
        """验证和修正生成的代码"""
        
        validated_code = {}
        base_package = project_context.get('package_patterns', {}).get('base_package', 'com.example')
        
        for code_type, code_content in generated_code.items():
            if not code_content.strip():
                continue
                
            # 基本验证：确保包名正确
            if not code_content.startswith('package'):
                # 添加包名
                if code_type == 'controller':
                    code_content = f"package {base_package}.interfaces.rest;\n\n{code_content}"
                elif code_type == 'service':
                    code_content = f"package {base_package}.application.service;\n\n{code_content}"
                elif code_type in ['request_dto', 'response_dto']:
                    code_content = f"package {base_package}.interfaces.dto;\n\n{code_content}"
                elif code_type == 'entity':
                    code_content = f"package {base_package}.domain.entity;\n\n{code_content}"
                elif code_type == 'mapper':
                    code_content = f"package {base_package}.domain.mapper;\n\n{code_content}"
            
            validated_code[code_type] = code_content
        
        logger.info(f"✅ 验证完成，有效代码块: {len(validated_code)} 个")
        return validated_code
    
    def _generate_fallback_code(self, interface_name: str, input_params: List[Dict], 
                              output_params: Dict, description: str, http_method: str,
                              project_context: Dict[str, Any], api_path: str = '', business_logic: str = '') -> Dict[str, str]:
        """生成fallback代码（当LLM失败时使用简化模板）"""
        
        logger.info("🔧 使用fallback模板生成代码...")
        
        base_package = project_context.get('package_patterns', {}).get('base_package', 'com.main')
        entity_name = interface_name
        
        # 使用实际的API路径
        request_mapping = api_path if api_path else f"/api/v1/{entity_name.lower()}"
        
        fallback_code = {}
        
        # 简化的Controller
        fallback_code['controller'] = f"""package {base_package}.interfaces.rest;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;

/**
 * {description}
 * 自动生成 - Fallback模式
 */
@RestController
@RequestMapping("{request_mapping}")
public class {entity_name}Controller {{

    @Autowired
    private {entity_name}Service {entity_name.lower()}Service;

    @{self._get_mapping_annotation(http_method)}
    public ResponseEntity<{entity_name}Response> process() {{
        // TODO: 实现{description}
        // 业务逻辑: {business_logic if business_logic else description}
        return ResponseEntity.ok(new {entity_name}Response());
    }}
}}"""
        
        # 简化的Service
        fallback_code['service'] = f"""package {base_package}.application.service;

import org.springframework.stereotype.Service;

/**
 * {entity_name}业务服务
 * 自动生成 - Fallback模式
 */
@Service
public class {entity_name}Service {{

    public {entity_name}Response process() {{
        // TODO: 实现{description}业务逻辑
        // 具体逻辑: {business_logic if business_logic else description}
        return new {entity_name}Response();
    }}
}}"""
        
        # 简化的Response DTO
        fallback_code['response_dto'] = f"""package {base_package}.interfaces.dto;

/**
 * {entity_name}响应对象
 * 自动生成 - Fallback模式
 */
public class {entity_name}Response {{
    
    private String message;
    private Object data;
    
    // TODO: 根据接口需求添加具体字段
    // 预期字段: {', '.join(output_params.keys()) if output_params else '待定义'}
    
    // TODO: 添加getter和setter方法
}}"""
        
        return fallback_code
    
    def _get_mapping_annotation(self, http_method: str) -> str:
        """根据HTTP方法获取对应的Spring注解"""
        method_mapping = {
            'GET': 'GetMapping',
            'POST': 'PostMapping', 
            'PUT': 'PutMapping',
            'DELETE': 'DeleteMapping',
            'PATCH': 'PatchMapping'
        }
        return method_mapping.get(http_method.upper(), 'GetMapping')
    
    def _generate_request_dto(self, entity_name: str, input_params: List[Dict], 
                            base_package: str, request_suffix: str, 
                            project_context: Dict[str, Any]) -> str:
        """生成Request DTO"""
        
        class_name = f"{entity_name}{request_suffix}"
        
        # 生成字段
        fields = []
        imports = set()
        
        for param in input_params:
            param_name = param.get('name', 'field')
            param_type = param.get('type', 'String')
            param_desc = param.get('description', '')
            required = param.get('required', True)
            
            # 处理类型映射
            java_type = self._map_to_java_type(param_type, imports)
            
            # 添加验证注解
            validation_annotations = []
            if required:
                validation_annotations.append("@NotNull")
                if java_type == "String":
                    validation_annotations.append("@NotBlank")
            
            # 生成字段定义
            field_code = []
            if param_desc:
                field_code.append(f"    /** {param_desc} */")
            
            for annotation in validation_annotations:
                field_code.append(f"    {annotation}")
            
            field_code.append(f"    private {java_type} {param_name};")
            fields.append('\n'.join(field_code))
        
        # 生成import语句
        import_statements = []
        if imports:
            import_statements.extend(sorted(imports))
        if any('@NotNull' in field for field in fields):
            import_statements.append("import javax.validation.constraints.NotNull;")
        if any('@NotBlank' in field for field in fields):
            import_statements.append("import javax.validation.constraints.NotBlank;")
        
        import_section = '\n'.join(import_statements) if import_statements else ""
        
        return f"""package {base_package}.interfaces.dto;

{import_section}

/**
 * {entity_name}请求对象
 * 自动生成，基于企业级项目架构
 */
public class {class_name} {{

{chr(10).join(fields)}

    // TODO: 添加getter和setter方法
}}"""
    
    def _map_to_java_type(self, param_type: str, imports: set) -> str:
        """将参数类型映射为Java类型"""
        
        type_mapping = {
            'string': 'String',
            'str': 'String',
            'int': 'Integer',
            'integer': 'Integer',
            'long': 'Long',
            'float': 'Float',
            'double': 'Double',
            'boolean': 'Boolean',
            'bool': 'Boolean',
            'date': 'LocalDate',
            'datetime': 'LocalDateTime',
            'timestamp': 'LocalDateTime',
            'time': 'LocalTime',
            'bigdecimal': 'BigDecimal',
            'decimal': 'BigDecimal'
        }
        
        # 处理泛型类型
        if 'list' in param_type.lower() or 'array' in param_type.lower():
            imports.add("import java.util.List;")
            return "List<String>"  # 简化处理
        
        # 处理日期时间类型的import
        java_type = type_mapping.get(param_type.lower(), 'String')
        
        if java_type in ['LocalDate', 'LocalDateTime', 'LocalTime']:
            imports.add(f"import java.time.{java_type};")
        elif java_type == 'BigDecimal':
            imports.add("import java.math.BigDecimal;")
        
        return java_type
    
    def _determine_output_paths_with_llm(self, generated_code: Dict[str, str], 
                                        project_path: str, service_name: str,
                                        project_context: Dict[str, Any]) -> Dict[str, str]:
        """使用LLM判断生成代码的输出路径和文件名"""
        
        if not self.llm_client:
            logger.warning("⚠️ LLM客户端未初始化，使用默认路径判断")
            return self._determine_output_paths_default(generated_code, project_path, service_name, project_context)
        
        try:
            # 构建项目结构分析prompt
            base_package = project_context.get('package_patterns', {}).get('base_package', 'com.example')
            
            # 从generated_code中分析接口名称（更可靠）
            interface_name = self._extract_interface_name_from_code(generated_code)
            
            # 预处理：强制确保所有代码都是Java代码
            java_code_analysis = self._analyze_code_types(generated_code)
            
            # 🔧 修复：先将ReAct模式的代码块映射到标准类型
            normalized_code = self._normalize_code_types(generated_code)
            
            structure_prompt = f"""
# Java后端项目路径分析任务

## 项目信息
- 项目根路径: {project_path}
- 服务名称: {service_name}
- 基础包名: {base_package}
- 接口名称: {interface_name}

## 项目架构信息
{self._build_project_structure_context(project_context)}

## 生成的Java代码分析
{java_code_analysis}

## 标准化后的代码类型
{self._format_normalized_code_info(normalized_code)}

## 任务要求
请为每个Java代码类型确定合适的输出路径。输出格式为JSON，包含相对路径、文件名和完整路径。

**重要要求**：
1. 这是Java后端项目，所有代码文件必须是.java扩展名
2. SQL映射文件使用.xml扩展名
3. 文件名必须与类名完全一致（{interface_name}Controller.java, {interface_name}Service.java等）
4. 包路径要符合企业级项目规范
5. 使用标准的分层架构目录结构
6. 绝对不要生成任何前端文件（.js, .jsx, .ts, .tsx, .html, .css等）

示例输出格式：
{{
    "controller": {{
        "relative_path": "src/main/java/{base_package.replace('.', '/')}/interfaces/rest", 
        "filename": "{interface_name}Controller.java",
        "full_path": "src/main/java/{base_package.replace('.', '/')}/interfaces/rest/{interface_name}Controller.java"
    }},
    "service": {{
        "relative_path": "src/main/java/{base_package.replace('.', '/')}/application/service", 
        "filename": "{interface_name}Service.java",
        "full_path": "src/main/java/{base_package.replace('.', '/')}/application/service/{interface_name}Service.java"
    }}
}}
"""
            
            logger.info(f"🤖 调用{self.llm_provider}判断Java文件输出路径...")
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": structure_prompt}],
                temperature=0.1
            )
            
            if response and isinstance(response, str):
                # 提取JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    import json
                    paths_config = json.loads(json_match.group())
                    
                    # 构建完整路径并验证文件扩展名
                    output_paths = {}
                    project_root = Path(project_path)
                    
                    # 🔧 修复：优先使用标准化的代码类型进行匹配
                    for code_type, path_info in paths_config.items():
                        # 先检查标准化代码中是否有该类型
                        if code_type in normalized_code:
                            target_code_type = code_type
                        # 再检查原始代码中是否有该类型
                        elif code_type in generated_code:
                            target_code_type = code_type
                        # 🔧 新增：尝试通过代码内容反向匹配
                        else:
                            target_code_type = self._find_matching_code_type(code_type, generated_code)
                        
                        if target_code_type:
                            file_name = path_info['filename']
                            
                            # 强制验证：Java代码必须是.java文件
                            if not file_name.endswith('.java') and not file_name.endswith('.xml'):
                                logger.warning(f"⚠️ 修正文件扩展名: {file_name}")
                                # 提取类名并强制使用.java扩展名
                                class_name = file_name.split('.')[0]
                                file_name = f"{class_name}.java"
                                
                            full_path = project_root / path_info['full_path']
                            # 如果路径包含非Java文件，强制修正
                            if '.js' in str(full_path) or 'frontend' in str(full_path):
                                logger.warning(f"⚠️ 检测到前端路径，使用默认Java路径: {full_path}")
                                return self._determine_output_paths_default(generated_code, project_path, service_name, project_context)
                            
                            # 🔧 修复：使用原始的代码类型作为键，确保后续匹配成功
                            output_paths[target_code_type] = str(full_path)
                    
                    if output_paths:
                        logger.info(f"✅ LLM路径判断成功，配置了 {len(output_paths)} 个Java文件路径")
                        for code_type, path in output_paths.items():
                            logger.info(f"📍 {code_type}: {Path(path).name}")
                        return output_paths
                    else:
                        logger.warning("⚠️ LLM路径判断未返回有效路径配置")
        
        except Exception as e:
            logger.warning(f"⚠️ LLM路径判断失败: {e}")
        
        # Fallback到默认路径判断
        logger.info("🔄 Fallback到默认Java路径判断...")
        return self._determine_output_paths_default(generated_code, project_path, service_name, project_context)
    
    def _normalize_code_types(self, generated_code: Dict[str, str]) -> Dict[str, str]:
        """标准化代码类型，将ReAct模式的java_code_x映射到标准类型"""
        
        normalized = {}
        
        for code_type, content in generated_code.items():
            content_lower = content.lower()
            
            # 直接映射标准类型
            if code_type in ['controller', 'service', 'service_impl', 'request_dto', 'response_dto', 'entity', 'mapper']:
                normalized[code_type] = content
                continue
            
            # 分析java_code_x类型的内容
            if code_type.startswith('java_code_'):
                mapped_type = None
                
                # 控制器检测
                if any(annotation in content for annotation in ['@RestController', '@Controller']):
                    mapped_type = 'controller'
                
                # Service实现类检测（优先检测）
                elif ('@Service' in content and 'class' in content and 
                      ('implements' in content or 'serviceimpl' in content_lower or content.strip().endswith('impl {'))):
                    mapped_type = 'service_impl'
                
                # Service接口检测
                elif 'interface' in content and ('service' in content_lower or '@Service' in content):
                    mapped_type = 'service'
                
                # DTO检测
                elif any(keyword in content_lower for keyword in ['request', 'req']) and 'class' in content:
                    mapped_type = 'request_dto'
                elif any(keyword in content_lower for keyword in ['response', 'resp']) and 'class' in content:
                    mapped_type = 'response_dto'
                
                # Entity检测
                elif any(annotation in content for annotation in ['@Entity', '@Table', '@TableName']):
                    mapped_type = 'entity'
                
                # Mapper检测
                elif '@Mapper' in content or ('interface' in content and 'mapper' in content_lower):
                    mapped_type = 'mapper'
                
                # 如果成功映射，使用映射类型；否则保持原名
                if mapped_type:
                    # 如果目标类型已存在，添加后缀避免覆盖
                    final_type = mapped_type
                    counter = 1
                    while final_type in normalized:
                        final_type = f"{mapped_type}_{counter}"
                        counter += 1
                    
                    normalized[final_type] = content
                    logger.info(f"🔄 代码块映射: {code_type} -> {final_type}")
                else:
                    # 无法识别的代码块，保持原名
                    normalized[code_type] = content
                    logger.warning(f"⚠️ 无法识别代码块类型: {code_type}")
            else:
                # 其他类型直接保留
                normalized[code_type] = content
        
        # 🔧 修复：确保service和service_impl都被正确保留，支持企业级接口隔离架构
        final_mapping = {}
        
        # 首先复制所有标准化的代码
        for code_type, content in normalized.items():
            final_mapping[code_type] = content
        
        # 检查是否需要为路径生成提供额外的映射
        # 注意：不要覆盖已存在的类型，只是确保路径生成能找到对应文件
        if 'service_impl' in final_mapping and 'service' not in final_mapping:
            logger.info("ℹ️ 检测到service_impl但缺少service，这是正常的（接口会被自动生成）")
        
        logger.info(f"📋 标准化后的代码类型: {list(final_mapping.keys())}")
        return final_mapping
    
    def _format_normalized_code_info(self, normalized_code: Dict[str, str]) -> str:
        """格式化标准化代码信息"""
        
        info_parts = ["📋 标准化后的代码类型映射:"]
        
        for code_type in normalized_code.keys():
            info_parts.append(f"✅ {code_type}: 需要生成 .java 文件")
        
        return '\n'.join(info_parts)
    
    def _find_matching_code_type(self, target_type: str, generated_code: Dict[str, str]) -> str:
        """通过代码内容反向匹配代码类型"""
        
        # 定义类型映射关系
        type_patterns = {
            'controller': ['@RestController', '@Controller'],
            'service': ['@Service'],
            'request_dto': ['Request', 'Req'],
            'response_dto': ['Response', 'Resp'],
            'entity': ['@Entity', '@TableName', 'Entity'],
            'mapper': ['@Mapper', 'BaseMapper', 'Mapper']
        }
        
        patterns = type_patterns.get(target_type, [])
        
        for code_type, content in generated_code.items():
            for pattern in patterns:
                if pattern in content:
                    return code_type
        
        return None
    
    def _analyze_code_types(self, generated_code: Dict[str, str]) -> str:
        """分析生成代码的类型，确保都是Java代码"""
        
        analysis_parts = []
        analysis_parts.append("📋 已生成的Java后端代码类型:")
        
        for code_type, content in generated_code.items():
            # 检查代码内容
            is_java_code = ('package ' in content and 
                           ('class ' in content or 'interface ' in content) and
                           ('public ' in content or 'private ' in content))
            
            if is_java_code:
                # 提取类名
                import re
                class_match = re.search(r'public\s+(?:class|interface)\s+(\w+)', content)
                class_name = class_match.group(1) if class_match else 'Unknown'
                
                analysis_parts.append(f"✅ {code_type}: Java类 '{class_name}' - 需要.java文件")
            else:
                analysis_parts.append(f"⚠️ {code_type}: 内容需要验证 - 强制使用.java扩展名")
        
        analysis_parts.append("\n⚠️ 重要提醒：所有文件都必须使用.java扩展名，不要生成任何前端文件")
        
        return '\n'.join(analysis_parts)
    
    def _extract_interface_name_from_code(self, generated_code: Dict[str, str]) -> str:
        """从生成的代码中提取接口名称"""
        
        # 优先从Controller代码中提取RequestMapping路径来推导接口名
        for code_type in ['controller', 'react_code_1', 'react_code_2', 'react_code_3', 'react_code_4', 'react_code_5']:
            if code_type in generated_code:
                content = generated_code[code_type]
                
                # 先尝试从@RequestMapping或方法名中提取业务接口名
                import re
                
                # 方法1：从方法名中提取（如 queryCompanyUnitList）
                method_matches = re.findall(r'public\s+[^)]+\s+(\w+)\s*\([^)]*\)', content)
                for method_name in method_matches:
                    if method_name not in ['toString', 'equals', 'hashCode', 'process', 'handle']:
                        # 从方法名推导接口名（去除动词前缀）
                        interface_name = method_name
                        for prefix in ['query', 'get', 'list', 'find', 'search', 'create', 'update', 'delete']:
                            if interface_name.lower().startswith(prefix):
                                interface_name = interface_name[len(prefix):]
                                break
                        if interface_name and len(interface_name) >= 3:
                            # 确保首字母大写
                            interface_name = interface_name[0].upper() + interface_name[1:]
                            return interface_name
                
                # 方法2：从@RequestMapping路径中提取
                mapping_match = re.search(r'@RequestMapping\s*\(\s*["\']([^"\']+)["\']', content)
                if mapping_match:
                    path = mapping_match.group(1)
                    path_parts = [part for part in path.split('/') if part and part != 'api' and not part.startswith('v')]
                    if path_parts:
                        last_part = path_parts[-1]
                        # 处理驼峰和下划线
                        if '_' in last_part:
                            words = last_part.split('_')
                            interface_name = ''.join(word.capitalize() for word in words if word)
                        else:
                            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', last_part)
                            interface_name = ''.join(word.capitalize() for word in words if word)
                        return interface_name
                
                # 方法3：从Controller类名中提取
                controller_match = re.search(r'public\s+class\s+(\w+)Controller', content)
                if controller_match:
                    return controller_match.group(1)
        
        # 方法4：从其他代码类型中查找业务相关的类名
        business_keywords = ['Req', 'Resp', 'Request', 'Response', 'DTO', 'Entity']
        for content in generated_code.values():
            import re
            class_matches = re.findall(r'public\s+class\s+(\w+)', content)
            for class_name in class_matches:
                # 查找包含业务关键词的类名
                for keyword in business_keywords:
                    if class_name.endswith(keyword):
                        base_name = class_name[:-len(keyword)]
                        if base_name and len(base_name) >= 3:
                            return base_name
        
        # 方法5：通用类名提取（去除常见后缀）
        for content in generated_code.values():
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', content)
            if class_match:
                class_name = class_match.group(1)
                for suffix in ['Controller', 'Service', 'ServiceImpl', 'Mapper', 'Dto', 'DTO', 'Handler', 'Utils', 'Factory']:
                    if class_name.endswith(suffix):
                        base_name = class_name[:-len(suffix)]
                        if base_name and len(base_name) >= 3:
                            return base_name
                # 如果没有匹配的后缀，返回原类名
                if len(class_name) >= 3:
                    return class_name
        
        return 'Example'  # 默认值
    
    def _determine_output_paths_default(self, generated_code: Dict[str, str], 
                                      project_path: str, service_name: str,
                                      project_context: Dict[str, Any]) -> Dict[str, str]:
        """默认路径判断逻辑（Fallback）- 支持基于API路径的智能目录选择"""
        
        logger.info(f"🔧 使用默认Java路径判断逻辑...{service_name}")
        
        # 🔧 修复：先标准化代码类型，确保ReAct模式的代码块能被正确处理
        normalized_code = self._normalize_code_types(generated_code)
        
        # 🔍 使用优化的深度搜索找到最佳Java项目路径
        optimal_project_path = self._find_deep_java_project_path(project_path, service_name)
        logger.info(f"📂 实际分析路径: {optimal_project_path}")
        
        # 获取项目根路径
        if optimal_project_path == '.' or not os.path.isabs(optimal_project_path):
            project_root = Path.cwd()
        else:
            project_root = Path(optimal_project_path)
        
        # 从代码中提取接口名称用于文件命名
        interface_name = self._extract_interface_name_from_code(generated_code)
        if not interface_name:
            interface_name = "Example"
        
        # 🎯 新增：尝试从项目上下文中获取API路径，构建智能包结构
        api_path = project_context.get('current_api_path', '')
        if api_path:
            layer_paths_result = self._get_contextual_package_structure(optimal_project_path, api_path, project_context)
            
            # 🆕 检查是否已经在现有Controller中添加了接口
            if isinstance(layer_paths_result, dict) and layer_paths_result.get('controller_interface_added'):
                logger.info(f"✅ 接口已添加到现有Controller，跳过新文件生成")
                return {}  # 返回空字典，表示不需要生成新文件
            
            layer_paths = layer_paths_result
            logger.info(f"🎯 使用基于API路径的智能包结构: {api_path}")
        else:
            # 回退到默认包结构
            package_patterns = project_context.get('package_patterns', {})
            base_package = package_patterns.get('base_package', 'com.main')
            package_path = base_package.replace('.', '/')
            
            layer_paths = {
                'controller': f'src/main/java/{package_path}/interfaces/rest',
                'service': f'src/main/java/{package_path}/application/service', 
                'service_impl': f'src/main/java/{package_path}/application/service/impl',
                'feign_client': f'src/main/java/{package_path}/application/feign',  # 🆕 Feign接口
                'application_service': f'src/main/java/{package_path}/application/service',  # 🆕 应用服务
                'domain_service': f'src/main/java/{package_path}/domain/service',  # 🆕 领域服务
                'request_dto': f'src/main/java/{package_path}/interfaces/dto',
                'response_dto': f'src/main/java/{package_path}/interfaces/dto',
                'entity': f'src/main/java/{package_path}/domain/entity',
                'mapper': f'src/main/java/{package_path}/domain/mapper',
                'mapper_xml': f'src/main/resources/mapper'  # 🔧 修复：正确的XML路径
            }
            
            logger.info(f"📦 使用默认包结构")
        
        # 打印标准化后的代码类型以便调试
        standardized_types = list(normalized_code.keys())
        logger.info(f"📋 标准化后的代码类型: {standardized_types}")
        
        # 为每个生成的代码确定输出路径
        output_paths = {}
        
        # 🔧 修复：遍历原始生成的代码，但使用标准化映射来确定路径
        for original_code_type, content in generated_code.items():
            # 找到对应的标准化类型
            standard_type = None
            for std_type, std_content in normalized_code.items():
                if std_content == content:
                    standard_type = std_type
                    break
            
            # 如果没找到标准化类型，尝试通过内容分析
            if not standard_type:
                if '@RestController' in content or '@Controller' in content:
                    standard_type = 'controller'
                elif '@Service' in content and 'class' in content:
                    # 🔧 修复：正确区分Service接口和ServiceImpl
                    if 'implements' in content or 'ServiceImpl' in content or content.strip().endswith('Impl {'):
                        standard_type = 'service_impl'
                    elif 'interface' in content:
                        standard_type = 'service'
                    else:
                        standard_type = 'service'  # 默认当作Service接口
                elif ('Request' in content or 'Req' in content) and 'class' in content:
                    standard_type = 'request_dto'
                elif ('Response' in content or 'Resp' in content) and 'class' in content:
                    standard_type = 'response_dto'
                elif '@Entity' in content or '@TableName' in content or 'Entity' in content:
                    standard_type = 'entity'
                elif '@Mapper' in content or 'BaseMapper' in content or 'Mapper' in content:
                    standard_type = 'mapper'
                else:
                    # 对于无法识别的类型，使用通用路径
                    standard_type = 'service'  # 默认当作Service处理
            
            # 确定文件名
            if standard_type == 'controller':
                file_name = f"{interface_name}Controller.java"
            elif standard_type == 'service':
                file_name = f"{interface_name}Service.java"
            elif standard_type == 'service_impl':
                file_name = f"{interface_name}ServiceImpl.java"  # 🔧 修复：ServiceImpl使用正确的文件名
            elif standard_type == 'application_service':
                file_name = f"{interface_name}Application.java"  # 修正为Application
            elif standard_type == 'domain_service':
                file_name = f"{interface_name}DomainService.java"
            elif standard_type == 'request_dto':
                file_name = f"{interface_name}Req.java"
            elif standard_type == 'response_dto':
                file_name = f"{interface_name}Resp.java"
            elif standard_type == 'entity':
                file_name = f"{interface_name}Entity.java"
            elif standard_type == 'mapper_xml':
                file_name = f"{interface_name}Mapper.xml"
            elif standard_type == 'mapper':
                file_name = f"{interface_name}Mapper.java"
            elif standard_type == 'feign_client':
                file_name = f"{interface_name}FeignClient.java"
            else:
                # 🔧 新增：从代码内容中提取实际类名
                import re
                class_match = re.search(r'public\s+(?:class|interface)\s+(\w+)', content)
                if class_match:
                    actual_class_name = class_match.group(1)
                    file_name = f"{actual_class_name}.java"
                else:
                    file_name = f"{interface_name}Unknown.java"
            
            # 构建完整路径
            if standard_type in layer_paths:
                relative_path = layer_paths[standard_type]
            else:
                # 默认路径
                package_patterns = project_context.get('package_patterns', {})
                base_package = package_patterns.get('base_package', 'com.main')
                package_path = base_package.replace('.', '/')
                relative_path = f'src/main/java/{package_path}/application/service'
            
            full_path = project_root / relative_path / file_name
            
            # 🔧 修复：使用原始代码类型作为键，确保后续写入时能匹配
            output_paths[original_code_type] = str(full_path)
            
            logger.info(f"📍 {original_code_type}: {file_name} -> {relative_path}")
        
        return output_paths
    
    def _find_deep_java_project_path(self, base_path: str, service_name: str = None) -> str:
        """深度搜索Java项目路径，优先识别多模块项目的深层结构"""
        
        logger.info(f"🔍 在 {base_path} 中查找最佳Java项目路径...")
        logger.info(f"🎯 目标服务名: {service_name}")
        
        potential_paths = []
        search_path = Path(base_path)
        
        # 递归查找所有包含src/main/java的目录
        for root, dirs, files in os.walk(search_path):
            # 跳过隐藏目录和不相关的目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'out', 'bin']]
            
            if 'src' in dirs:
                src_path = Path(root) / 'src'
                java_path = src_path / 'main' / 'java'
                
                if java_path.exists():
                    # 检查Java文件数量
                    java_files_count = 0
                    for java_file in java_path.rglob('*.java'):
                        java_files_count += 1
                    
                    if java_files_count > 0:
                        priority = self._calculate_enhanced_path_priority(root, service_name, java_files_count)
                        relative_path = str(Path(root).relative_to(search_path)) if root != str(search_path) else "."
                        relative_depth = len(Path(root).relative_to(search_path).parts)
                        
                        potential_paths.append({
                            'path': root,
                            'relative_path': relative_path,
                            'java_files': java_files_count,
                            'priority': priority,
                            'depth': relative_depth
                        })
                        
                        logger.info(f"   📁 发现Java项目: {Path(root).name}")
                        logger.info(f"      🎯 相对路径: {relative_path}")
                        logger.info(f"      📊 Java文件: {java_files_count}个")
                        logger.info(f"      📐 目录深度: {relative_depth}")
                        logger.info(f"      🏆 优先级分数: {priority}")
        
        if not potential_paths:
            logger.warning(f"⚠️ 未找到Java项目结构，使用原路径: {base_path}")
            return base_path
        
        # 排序：优先级高的在前面，深度作为次要排序条件
        potential_paths.sort(key=lambda x: (x['priority'], x['depth']), reverse=True)
        
        # 打印排序后的候选路径（前3个）
        logger.info(f"📋 排序后的候选路径（前3个）:")
        for i, path_info in enumerate(potential_paths[:3]):
            logger.info(f"   {i+1}. {path_info['relative_path']} (优先级: {path_info['priority']})")
        
        # 选择最佳路径
        best_path_info = potential_paths[0]
        best_path = best_path_info['path']
        
        logger.info(f"✅ 选择最佳Java项目路径:")
        logger.info(f"   📁 完整路径: {best_path}")
        logger.info(f"   📋 相对路径: {best_path_info['relative_path']}")
        logger.info(f"   🏆 最终优先级: {best_path_info['priority']}")
        
        return best_path
    
    def _extract_api_path_keyword(self, api_path: str) -> str:
        """从API路径中提取关键字（倒数第二个路径片段）"""
        if not api_path:
            return ""
        
        # 分割路径，过滤空字符串
        path_parts = [part for part in api_path.split('/') if part.strip()]
        
        # 如果路径片段少于2个，返回空字符串
        if len(path_parts) < 2:
            return ""
        
        # 返回倒数第二个片段
        keyword = path_parts[-2]
        logger.info(f"🔍 从API路径 {api_path} 提取关键字: {keyword}")
        return keyword

    def _find_existing_path_by_keyword(self, project_path: str, keyword: str) -> str:
        """根据关键字在项目中查找现有的相关路径结构"""
        if not keyword:
            return ""
        
        logger.info(f"🔍 在项目中搜索关键字相关路径: {keyword}")
        
        search_path = Path(project_path)
        matching_paths = []
        
        # 递归搜索包含关键字的目录
        for root, dirs, files in os.walk(search_path):
            # 跳过隐藏目录和构建目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', 'build', 'out', 'bin']]
            
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                dir_name_lower = dir_name.lower()
                keyword_lower = keyword.lower()
                
                # 检查目录名是否包含关键字
                if keyword_lower in dir_name_lower or dir_name_lower in keyword_lower:
                    # 检查这个目录下是否有Java文件
                    java_files_found = False
                    for java_file in dir_path.rglob('*.java'):
                        java_files_found = True
                        break
                    
                    if java_files_found:
                        # 计算匹配得分
                        exact_match = (dir_name_lower == keyword_lower)
                        contains_match = keyword_lower in dir_name_lower
                        score = 100 if exact_match else (50 if contains_match else 25)
                        
                        matching_paths.append({
                            'path': str(dir_path),
                            'dir_name': dir_name,
                            'score': score,
                            'relative_path': str(dir_path.relative_to(search_path))
                        })
                        
                        logger.info(f"   📁 找到匹配目录: {dir_name} (得分: {score})")
        
        if not matching_paths:
            logger.info(f"   ❌ 未找到包含关键字 '{keyword}' 的相关目录")
            return ""
        
        # 按得分排序，选择最佳匹配
        matching_paths.sort(key=lambda x: x['score'], reverse=True)
        best_match = matching_paths[0]
        
        logger.info(f"   ✅ 选择最佳匹配目录: {best_match['dir_name']} (路径: {best_match['relative_path']})")
        return best_match['path']

    def _get_contextual_package_structure(self, project_path: str, api_path: str, project_context: Dict[str, Any]) -> Dict[str, str]:
        """基于API路径获取符合DDD架构的包结构"""
        
        logger.info(f"🎯 构建DDD架构包结构，API路径: {api_path}")
        
        # 提取API关键字
        api_keyword = self._extract_api_path_keyword(api_path)
        
        # 🔧 改进：使用项目上下文中的包信息
        package_patterns = project_context.get('package_patterns', {})
        base_package = package_patterns.get('base_package', 'com.yljr.crcl')
        
        # 🎯 DDD架构包结构映射
        if api_keyword:
            # 基于API关键字构建包路径（例如：limit -> com.yljr.crcl.limit）
            contextual_package = f"{base_package}.{api_keyword}"
            contextual_package_path = contextual_package.replace('.', '/')
            logger.info(f"🏗️ 基于API关键字 '{api_keyword}' 构建包路径: {contextual_package}")
        else:
            # 使用默认包路径
            contextual_package_path = base_package.replace('.', '/')
            logger.info(f"🏗️ 使用默认包路径: {base_package}")
        
        # 检查当前路径是否已经在src目录中
        is_already_in_src = 'src/main/java' in project_path
        
        # 🆕 DDD分层架构路径配置
        if is_already_in_src:
            # 如果已经在src目录中，使用相对路径
            layer_paths = {
                'controller': f'{contextual_package_path}/interfaces/rest',
                'service': f'{contextual_package_path}/application/service',
                'service_impl': f'{contextual_package_path}/application/service/impl', 
                'feign_client': f'{contextual_package_path}/application/feign',  # 🆕 Feign接口
                'application_service': f'{contextual_package_path}/application/service',  # 🆕 应用服务
                'domain_service': f'{contextual_package_path}/domain/service',  # 🆕 领域服务
                'request_dto': f'{contextual_package_path}/interfaces/dto',
                'response_dto': f'{contextual_package_path}/interfaces/dto',
                'entity': f'{contextual_package_path}/domain/entity',
                'mapper': f'{contextual_package_path}/domain/mapper',
                'mapper_xml': f'resources/mapper'  # 🔧 修复：正确的XML路径
            }
        else:
            # 如果不在src目录中，使用完整路径
            layer_paths = {
                'controller': f'src/main/java/{contextual_package_path}/interfaces/rest',
                'service': f'src/main/java/{contextual_package_path}/application/service',
                'service_impl': f'src/main/java/{contextual_package_path}/application/service/impl',
                'feign_client': f'src/main/java/{contextual_package_path}/application/feign',  # 🆕 Feign接口
                'application_service': f'src/main/java/{contextual_package_path}/application/service',  # 🆕 应用服务
                'domain_service': f'src/main/java/{contextual_package_path}/domain/service',  # 🆕 领域服务
                'request_dto': f'src/main/java/{contextual_package_path}/interfaces/dto',
                'response_dto': f'src/main/java/{contextual_package_path}/interfaces/dto',
                'entity': f'src/main/java/{contextual_package_path}/domain/entity',
                'mapper': f'src/main/java/{contextual_package_path}/domain/mapper',
                'mapper_xml': f'src/main/resources/mapper'  # 🔧 修复：正确的XML路径
            }
        
        logger.info(f"✅ DDD架构路径配置完成，包含 {len(layer_paths)} 个分层")
        return layer_paths
    
    def _build_project_structure_context(self, project_context: Dict[str, Any]) -> str:
        """构建项目结构上下文信息 - 支持DDD架构"""
        
        package_patterns = project_context.get('package_patterns', {})
        architecture_patterns = project_context.get('architecture_patterns', {})
        
        context_text = f"""
### DDD分层架构规范
- 基础包名: {package_patterns.get('base_package', 'com.yljr.crcl')}
- 架构风格: DDD (Domain-Driven Design)

### 目录结构说明
- Controller层: interfaces/rest (对外REST接口)
- Application Service层: application/service (应用服务，协调业务流程)
- Feign Client层: application/feign (外部服务调用接口)
- Domain Service层: domain/service (领域服务，核心业务逻辑)
- Domain Mapper层: domain/mapper (数据访问层)
- DTO层: interfaces/dto (数据传输对象)
- Entity层: domain/entity (领域实体)
- XML映射文件: resources/mapper (MyBatis XML映射)

### 调用链说明
Controller -> Application Service -> Domain Service 或 Domain Mapper
如需调用外部服务: Controller -> Application Service -> Feign Client
如需本地数据: Controller -> Application Service -> Domain Mapper -> XML映射
"""
        return context_text.strip()
    
    def _write_generated_code(self, generated_code: Dict[str, str], project_path: str, 
                            service_name: str, project_context: Dict[str, Any]) -> Dict[str, str]:
        """写入生成的代码文件，确保类名和文件名一致"""
        
        logger.info(f"📝 开始写入生成的代码文件...")
        
        # 先验证和修正代码内容，确保类名一致性
        corrected_code = self._ensure_class_name_consistency(generated_code)
        
        # 确定输出路径
        if self.llm_client:
            output_paths = self._determine_output_paths_with_llm(corrected_code, project_path, service_name, project_context)
        else:
            output_paths = self._determine_output_paths_default(corrected_code, project_path, service_name, project_context)
        
        generated_files = {}
        
        for code_type, code_content in corrected_code.items():
            if code_type in output_paths:
                file_path = output_paths[code_type]
                
                # 检查是否已存在且包含目标接口/方法
                skip_write = False
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                    import re
                    class_matches = re.findall(r'public\s+(?:class|interface)\s+(\w+)', existing_content)
                    method_matches = re.findall(r'public\s+[^\{]+\s+(\w+)\s*\([^)]*\)\s*\{', existing_content)
                    if interface_name in class_matches or any(interface_name in m for m in method_matches):
                        logger.info(f"⏩ 跳过已存在且包含目标接口/方法的文件: {file_path}")
                        skip_write = True
                if skip_write:
                    continue
                
                try:
                    # 确保目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # 写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(code_content)
                    
                    logger.info(f"📝 已生成代码文件: {file_path}")
                    
                    # 验证文件是否正确写入
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info(f"✅ 文件写入验证成功: {file_path}")
                        generated_files[code_type] = file_path
                    else:
                        logger.error(f"❌ 文件写入验证失败: {file_path}")
                        
                except Exception as e:
                    logger.error(f"❌ 文件写入失败 {file_path}: {e}")
        
        logger.info(f"📊 代码生成完成，共写入 {len(generated_files)} 个文件到项目中")
        return generated_files
    
    def _ensure_class_name_consistency(self, generated_code: Dict[str, str]) -> Dict[str, str]:
        """确保所有生成代码中的类名保持一致"""
        
        # 提取核心接口名（去除后缀）
        interface_name = self._extract_interface_name_from_code(generated_code)
        logger.info(f"🔧 统一类名基础: {interface_name}")
        
        corrected_code = {}
        
        for code_type, content in generated_code.items():
            try:
                corrected_content = self._fix_class_names_in_content(content, interface_name, code_type)
                corrected_code[code_type] = corrected_content
                
                # 验证修正结果
                import re
                class_matches = re.findall(r'public\s+class\s+(\w+)', corrected_content)
                if class_matches:
                    logger.info(f"✅ {code_type} 类名: {class_matches[0]}")
                
            except Exception as e:
                logger.warning(f"⚠️ 修正 {code_type} 类名失败: {e}, 使用原内容")
                corrected_code[code_type] = content
        
        return corrected_code
    
    def _fix_class_names_in_content(self, content: str, interface_name: str, code_type: str) -> str:
        """修正代码内容中的类名"""
        
        import re
        
        # 根据代码类型确定目标类名
        if 'controller' in code_type.lower():
            target_class_name = f"{interface_name}Controller"
            service_class_name = f"{interface_name}Service"
            
            # 修正Controller类名
            content = re.sub(r'public\s+class\s+\w+Controller', f'public class {target_class_name}', content)
            
            # 修正Service注入的类名  
            content = re.sub(r'private\s+\w+Service\s+\w+Service;', f'private {service_class_name} {interface_name.lower()}Service;', content)
            content = re.sub(r'@Autowired\s+private\s+\w+Service\s+\w+;', f'@Autowired\n    private {service_class_name} {interface_name.lower()}Service;', content)
            
        elif 'service' in code_type.lower():
            target_class_name = f"{interface_name}Service"
            mapper_class_name = f"{interface_name}Mapper"
            
            # 修正Service类名
            content = re.sub(r'public\s+class\s+\w+Service', f'public class {target_class_name}', content)
            content = re.sub(r'public\s+interface\s+\w+Service', f'public interface {target_class_name}', content)
            
            # 修正Mapper注入的类名
            content = re.sub(r'private\s+\w+Mapper\s+\w+Mapper;', f'private {mapper_class_name} {interface_name.lower()}Mapper;', content)
            content = re.sub(r'@Autowired\s+private\s+\w+Mapper\s+\w+;', f'@Autowired\n    private {mapper_class_name} {interface_name.lower()}Mapper;', content)
            
        elif 'mapper' in code_type.lower():
            target_class_name = f"{interface_name}Mapper"
            content = re.sub(r'public\s+interface\s+\w+Mapper', f'public interface {target_class_name}', content)
            
        elif 'dto' in code_type.lower() or 'request' in code_type.lower():
            if 'request' in code_type.lower():
                target_class_name = f"{interface_name}Req"
            else:
                target_class_name = f"{interface_name}Resp"
            content = re.sub(r'public\s+class\s+\w+(Req|Request|Resp|Response|DTO|Dto)', f'public class {target_class_name}', content)
            
        elif 'entity' in code_type.lower():
            target_class_name = f"{interface_name}Entity"
            content = re.sub(r'public\s+class\s+\w+(Entity)?', f'public class {target_class_name}', content)
        
        elif 'application_service' in code_type.lower():
            target_class_name = f"{interface_name}Application"
            # 修正Application类名
            content = re.sub(r'public\s+class\s+\w+Application', f'public class {target_class_name}', content)
            content = re.sub(r'public\s+interface\s+\w+Application', f'public interface {target_class_name}', content)
        
        return content
    
    def _convert_service_class_to_interface(self, service_class_content: str) -> str:
        """将Service类转换为Service接口"""
        
        try:
            import re
            
            # 提取类名
            class_match = re.search(r'public\s+class\s+(\w+)(?:Service)?\s*(?:implements\s+\w+\s*)?{', service_class_content)
            if not class_match:
                logger.error("❌ 无法提取Service类名")
                return None
            
            class_name = class_match.group(1)
            if not class_name.endswith('Service'):
                class_name += 'Service'
            
            # 提取包名
            package_match = re.search(r'package\s+([\w.]+);', service_class_content)
            package_name = package_match.group(1) if package_match else 'com.example.service'
            
            # 提取公共方法签名（去除实现）
            methods = []
            # 匹配公共方法，但排除构造方法
            method_pattern = r'public\s+(?!class)([^{]+)\s*{'
            for method_match in re.finditer(method_pattern, service_class_content, re.MULTILINE):
                method_signature = method_match.group(1).strip()
                
                # 跳过构造方法和getter/setter
                if (class_name.replace('Service', '') not in method_signature and 
                    not any(keyword in method_signature.lower() for keyword in ['get', 'set']) and
                    not method_signature.startswith('static')):
                    methods.append(f"    {method_signature};")
            
            # 提取import语句
            imports = re.findall(r'import\s+([^;]+);', service_class_content)
            import_statements = []
            for imp in imports:
                if not imp.startswith('org.springframework.stereotype.Service'):
                    import_statements.append(f"import {imp};")
            
            import_section = '\n'.join(import_statements) if import_statements else ""
            
            # 生成Service接口
            service_interface = f"""package {package_name};

{import_section}

/**
 * {class_name} - 业务服务接口
 * 自动从Service类转换生成
 */
public interface {class_name} {{

{chr(10).join(methods)}

}}"""
            
            logger.info(f"✅ 成功转换Service类为接口: {class_name}")
            return service_interface
            
        except Exception as e:
            logger.error(f"❌ 转换Service类为接口失败: {e}")
            return None
    
    def _convert_service_class_to_impl(self, service_class_content: str) -> str:
        """将Service类转换为ServiceImpl实现类"""
        
        try:
            import re
            
            # 提取类名
            class_match = re.search(r'public\s+class\s+(\w+)(?:Service)?\s*(?:implements\s+\w+\s*)?{', service_class_content)
            if not class_match:
                logger.error("❌ 无法提取Service类名")
                return None
            
            class_name = class_match.group(1)
            if not class_name.endswith('Service'):
                class_name += 'Service'
            
            service_impl_name = class_name + 'Impl'
            
            # 修改类声明
            modified_content = re.sub(
                r'public\s+class\s+\w+(?:Service)?\s*(?:implements\s+\w+\s*)?{',
                f'public class {service_impl_name} implements {class_name} {{',
                service_class_content
            )
            
            # 确保有@Service注解
            if '@Service' not in modified_content:
                # 在package声明后添加@Service注解
                modified_content = re.sub(
                    r'(package\s+[^;]+;\s*\n)',
                    r'\1\nimport org.springframework.stereotype.Service;\n',
                    modified_content
                )
                
                # 在类声明前添加@Service注解
                modified_content = re.sub(
                    r'(public\s+class\s+' + service_impl_name + ')',
                    r'@Service\n\1',
                    modified_content
                )
            
            logger.info(f"✅ 成功转换Service类为实现类: {service_impl_name}")
            return modified_content
            
        except Exception as e:
            logger.error(f"❌ 转换Service类为实现类失败: {e}")
            return None
    
    def _handle_service_and_mapper_using_existing_modules(self, controller_result: Dict[str, Any],
                                                         interface_name: str, input_params: List[Dict], 
                                                         output_params: Dict, description: str,
                                                         project_context: Dict[str, Any],
                                                         service_decision_maker) -> Dict[str, Any]:
        """
        使用现有模块处理Service和Mapper层
        
        这个方法只是协调现有模块的工作，不包含具体实现逻辑
        """
        logger.info(f"🔧 使用现有模块处理Service和Mapper层: {interface_name}")
        
        try:
            generated_files = []
            
            # 从controller_result中提取Service分析信息
            service_analysis = None
            if controller_result.get('results'):
                for result in controller_result['results']:
                    if 'service_analysis' in result:
                        service_analysis = result['service_analysis']
                        break
            
            if service_analysis:
                # 根据Service分析结果决定下一步行动
                decision = service_analysis.get('decision', {})
                action = decision.get('action', 'create_new')
                
                logger.info(f"📋 Service决策结果: {action}")
                
                if action == 'modify_existing':
                    # 记录需要修改现有Service的信息
                    target_service = decision.get('target_service', {})
                    generated_files.append({
                        'type': 'service_modification_needed',
                        'target_service': target_service.get('class_name', 'Unknown'),
                        'action': 'modify_existing',
                        'interface_method': interface_name
                    })
                elif action == 'create_new':
                    # 记录需要创建新Service的信息
                    generated_files.append({
                        'type': 'service_creation_needed',
                        'service_name': f'{interface_name}Service',
                        'action': 'create_new',
                        'interface_method': interface_name
                    })
                
                # 如果项目使用MyBatis Plus，记录需要处理Mapper
                if project_context.get('project_info', {}).get('is_mybatis_plus'):
                    generated_files.append({
                        'type': 'mapper_handling_needed',
                        'mapper_name': f'{interface_name}Mapper',
                        'action': 'review_required'
                    })
                
                # 记录需要生成DTO
                generated_files.extend([
                    {
                        'type': 'dto_generation_needed',
                        'dto_name': f'{interface_name}Req',
                        'action': 'create_if_needed'
                    },
                    {
                        'type': 'dto_generation_needed', 
                        'dto_name': f'{interface_name}Resp',
                        'action': 'create_new'
                    }
                ])
            
            return {
                'success': True,
                'message': f'已分析Service和Mapper需求',
                'generated_files': generated_files,
                'files_count': len(generated_files),
                'note': '具体的Service和Mapper代码生成需要后续处理'
            }
            
        except Exception as e:
            logger.error(f"❌ Service和Mapper分析失败: {e}")
            return {
                'success': False,
                'message': f'Service和Mapper分析失败: {str(e)}',
                'error': str(e)
            }

    def _analyze_api_domain_similarity(self, api_path: str, existing_controllers: List[Dict]) -> Dict[str, Any]:
        """
        分析API路径与现有Controller的领域相似度
        使用LLM进行智能分析
        """
        if not self.llm_client:
            logger.warning("⚠️ LLM客户端未初始化，使用基于规则的匹配")
            return self._rule_based_domain_matching(api_path, existing_controllers)
        
        try:
            # 使用LLM分析领域相似度
            analysis_prompt = f"""
分析API路径与现有Controller的领域相似度：

API路径: {api_path}

现有Controllers:
{self._format_controllers_for_analysis(existing_controllers)}

请分析：
1. API路径的业务领域
2. 与哪个现有Controller最相关
3. 是否应该添加到现有Controller还是创建新的

返回格式:
{{
    "api_domain": "API的业务领域",
    "best_match_controller": "最匹配的Controller类名",
    "match_score": 0-100的匹配分数,
    "action": "add_to_existing" 或 "create_new",
    "reason": "判断理由"
}}
"""
            
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
                return analysis_result
            
        except Exception as e:
            logger.warning(f"⚠️ LLM分析失败: {e}, 使用基于规则的匹配")
        
        return self._rule_based_domain_matching(api_path, existing_controllers)
    
    def _rule_based_domain_matching(self, api_path: str, existing_controllers: List[Dict]) -> Dict[str, Any]:
        """基于规则的领域匹配"""
        # 提取API路径的关键词
        path_parts = [p for p in api_path.split('/') if p and p not in ['api', 'v1', 'v2']]
        if not path_parts:
            return {"action": "create_new", "reason": "无法提取有效路径"}
        
        # 查找最佳匹配
        best_match = None
        best_score = 0
        
        for controller in existing_controllers:
            controller_name = controller.get('class_name', '').lower()
            request_mapping = controller.get('request_mapping', '').lower()
            
            score = 0
            for part in path_parts:
                part_lower = part.lower()
                if part_lower in controller_name:
                    score += 50
                if part_lower in request_mapping:
                    score += 30
                    
            if score > best_score:
                best_score = score
                best_match = controller
        
        if best_score >= 50:
            return {
                "api_domain": path_parts[-1] if path_parts else "unknown",
                "best_match_controller": best_match.get('class_name', ''),
                "match_score": best_score,
                "action": "add_to_existing",
                "reason": f"路径关键词与Controller匹配度高 (score: {best_score})"
            }
        else:
            return {
                "api_domain": path_parts[-1] if path_parts else "unknown",
                "best_match_controller": None,
                "match_score": 0,
                "action": "create_new",
                "reason": "未找到相关的Controller"
            }
    
    def _format_controllers_for_analysis(self, controllers: List[Dict]) -> str:
        """格式化Controller信息用于分析"""
        formatted = []
        for ctrl in controllers[:10]:  # 只取前10个避免太长
            formatted.append(f"- {ctrl.get('class_name', 'Unknown')}: {ctrl.get('request_mapping', 'N/A')}")
        return '\n'.join(formatted)
    
    def _calculate_enhanced_path_priority(self, path: str, service_name: str, java_files_count: int) -> int:
        """
        使用LLM智能计算路径优先级，如果LLM不可用则使用基础规则
        """
        if not self.llm_client:
            # 基础规则：主要基于Java文件数量和路径深度
            priority = java_files_count
            path_depth = len(Path(path).parts)
            if path_depth >= 6:
                priority += 50
            return priority
        
        try:
            # 使用LLM智能评估路径优先级
            prompt = f"""
分析Java项目路径的优先级，用于选择最佳的代码生成位置：

路径: {path}
服务名: {service_name}
Java文件数量: {java_files_count}

请评估这个路径作为"{service_name}"服务代码生成位置的适合度。

考虑因素：
1. 路径是否与服务名相关
2. 项目结构的合理性
3. Java文件数量的意义
4. 目录层级的深度

返回一个0-1000的分数，分数越高表示越适合。
只返回数字，不要解释。
"""
            
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # 提取数字
            import re
            score_match = re.search(r'\d+', response)
            if score_match:
                return int(score_match.group())
            
        except Exception as e:
            logger.warning(f"⚠️ LLM路径优先级计算失败: {e}")
        
        # 回退到基础计算
        return java_files_count + len(Path(path).parts) * 10


async def intelligent_coding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """智能编码节点 - 支持任务驱动的代码生成"""
    logger.info("🚀 智能编码节点开始执行...")
    
    try:
        coding_agent = IntelligentCodingAgent()
        
        # 🆕 新增：将设计文档内容传递给编码代理
        design_doc = state.get('design_doc', '')
        if design_doc:
            logger.info(f"📄 从工作流状态获取设计文档 ({len(design_doc)} 字符)")
            # 设置到编码代理的全局变量中，供任务执行时使用
            coding_agent._current_design_doc = design_doc
        
        # 🆕 新增：递增重试计数器
        retry_count = state.get("retry_count", 0)
        if retry_count > 0:
            logger.info(f"🔄 智能编码节点重试，当前重试次数: {retry_count}")
        
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
        
        # 🆕 新增：递增重试计数器并更新状态
        updated_state = state.copy()  # 保留现有状态
        updated_state.update({
            'coding_operations': coding_operations,
            'intelligent_coding_completed': True,
            'retry_count': retry_count + 1  # 递增重试计数器
        })
        
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
        updated_state = state.copy()
        updated_state.update({
            'coding_operations': state.get('coding_operations', []),
            'error': f'智能编码节点执行失败: {str(e)}',
            'retry_count': state.get("retry_count", 0) + 1
        })
        return updated_state
