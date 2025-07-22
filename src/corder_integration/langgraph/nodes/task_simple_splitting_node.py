#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版任务拆分节点 - 使用火山引擎LLM将设计文档拆解成SQL格式的执行任务
"""

import logging
import json
import re
import uuid
import yaml
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# 导入LLM客户端
from src.utils.volcengine_client import VolcengineClient, VolcengineConfig

logger = logging.getLogger(__name__)

class TaskSimpleSplittingNode:
    """简化版任务拆分节点 - 使用LLM智能解析"""
    
    def __init__(self):
        self.task_types = [
            'git_extraction',   # 提取Git地址
            'git_clone',        # 下载代码  
            'code_analysis',    # 分析结构
            'config',           # 配置环境
            'database',         # 建表
            'api',              # 开发接口
            'integration_test', # 集成测试
            'deployment'        # 代码提交
        ]
        
        # 初始化LLM客户端
        self.llm_client = None
        self.llm_provider = None
        self._init_llm_client()
        
    def _init_llm_client(self):
        """初始化LLM客户端"""
        config = {}
        
        # 尝试多个可能的配置文件路径
        config_paths = [
            'config.yaml',
            os.path.join(os.getcwd(), 'config.yaml'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../config.yaml'),
            '/Users/renyu/Documents/ai_project/document_analyzer/config.yaml'
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
                volcengine_config = VolcengineConfig(
                    api_key=config['volcengine']['api_key'],
                    model_id=config['volcengine']['model'],
                    base_url=config['volcengine']['endpoint'],
                    temperature=config['volcengine'].get('temperature', 0.1),
                    max_tokens=config['volcengine'].get('max_tokens', 4000)
                )
                self.llm_client = VolcengineClient(volcengine_config)
                self.llm_provider = "volcengine"
                logger.info(f"✅ 使用火山引擎LLM客户端：{config['volcengine']['model']}")
            except Exception as e:
                logger.error(f"❌ 火山引擎初始化失败: {e}")
        
        # 最终检查
        if not self.llm_client:
            logger.error("❌ LLM客户端初始化失败！将使用规则化解析")
            self.llm_provider = "none"
        else:
            logger.info(f"✅ LLM客户端初始化成功: {self.llm_provider}")
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """节点主入口"""
        logger.info("🚀 开始简化版任务拆分")
        
        try:
            # 获取设计文档
            design_doc = state.get('design_doc', '')
            project_name = state.get('project_name', 'default_project')
            
            logger.info(f"📄 设计文档长度: {len(design_doc)}")
            logger.info(f"📋 项目名称: {project_name}")
            
            # 智能解析设计文档
            if self.llm_client:
                parsed_info = self._llm_parse_design_document(design_doc)
            else:
                parsed_info = self._rule_parse_design_document(design_doc)
            
            # 生成任务序列
            tasks = self._generate_task_sequence(parsed_info, project_name)
            
            # 生成SQL文件
            sql_content = self._generate_sql_content(tasks)
            output_file = self._save_sql_file(sql_content, project_name)
            
            logger.info(f"✅ 任务拆分完成，生成 {len(tasks)} 个任务")
            logger.info(f"📁 SQL文件保存到: {output_file}")
            
            # 同时保存到SQLite数据库用于工作流
            self._save_to_database(tasks)
            
            return {
                'identified_services': parsed_info.get('services', []),
                'service_dependencies': parsed_info.get('dependencies', {}),
                'task_execution_plan': {'total_tasks': len(tasks), 'sql_file': output_file},
                'parallel_tasks': [{'task_id': task['task_id'], 'task_type': task['task_type']} for task in tasks]
            }
            
        except Exception as e:
            logger.error(f"❌ 任务拆分失败: {e}")
            return {
                'identified_services': [],
                'service_dependencies': {},
                'task_execution_plan': {},
                'parallel_tasks': []
            }
    
    def _llm_parse_design_document(self, design_doc: str) -> Dict[str, Any]:
        """使用LLM智能解析设计文档"""
        logger.info("🤖 使用LLM智能解析设计文档...")
        
        # 使用增强版Jinja2风格的结构化提示词模板（基于你的修改优化）
        prompt = f"""你是任务管理专家，基于设计文档生成具体的开发任务信息。

设计文档内容：
{design_doc}

**重要约束：严格使用设计文档中的真实内容，禁止编造。**

**设计文档关键信息参考（Jinja2模板风格）：**
- GitLab仓库：用户服务 http://localhost:30000/ls/zqyl-user-center-service.git，确权开立服务 http://localhost:30000/ls/crcl-open.git
- 接口路径：/general/multiorgManage/queryCompanyUnitList，/crcl-open-api/lsLimit/listUnitLimitByCompanyId，/crcl-open-api/lsLimit/listUnitLimitByCompanyIdExport
- 表名：t_cust_multiorg_unit
- 数据库：jdbc:mysql://localhost:6446/dbwebappdb，用户名密码：dbwebapp/dbwebapp

请以JSON格式返回以下信息：

{{
    "services": [
        {{
            "name": "服务名称（如：用户服务、确权开立服务）",
            "description": "服务功能描述",
            "git_repository": "Git仓库完整地址",
            "controller_name": "主要控制器名称",
            "repo_name": "仓库目录名"
        }}
    ],
    "git_repositories": [
        "http://localhost:30000/ls/zqyl-user-center-service.git",
        "http://localhost:30000/ls/crcl-open.git"
    ],
    "apis": [
        {{
            "path": "完整API路径",
            "method": "HTTP方法（GET/POST）",
            "service": "所属服务名称",
            "description": "接口功能描述",
            "request_params": {{
                "参数名1": "参数说明(必填/可选)",
                "参数名2": "参数说明(必填/可选)"
            }},
            "response_params": {{
                "字段名1": "字段说明",
                "字段名2": "字段说明"
            }},
            "business_logic": "详细的业务逻辑描述",
            "data_source": "数据来源和获取方式",
            "content_type": "数据格式（application/json或其他）",
            "validation_rules": {{
                "参数名1": "校验规则描述",
                "参数名2": "校验规则描述"
            }},
            "dependencies": ["依赖的其他接口路径"]
        }}
    ],
    "databases": [
        {{
            "table_name": "t_cust_multiorg_unit",
            "database_url": "jdbc:mysql://localhost:6446/dbwebappdb",
            "username": "dbwebapp", 
            "password": "dbwebapp",
            "description": "表功能描述",
            "fields": ["主要字段列表"]
        }}
    ],
    "service_dependencies": {{
        "确权开立服务": ["用户服务"]
    }},
    "technical_stack": ["Spring Boot", "MySQL", "Feign", "MyBatis"],
    "main_features": ["主要功能特性描述"]
}}

**API参数详细结构示例（按照你的修改规范）：**
对于导出类接口，应包含：
- project_path: 项目路径
- api_path: API完整路径  
- http_method: HTTP方法
- content_type: 内容类型（特别是Excel导出的application/vnd.openxmlformats-officedocument.spreadsheetml.sheet）
- request_params: 请求参数详细说明
- response_params: 响应参数详细说明
- business_logic: 业务逻辑描述
- data_source: 数据来源说明
- export_format: 导出格式（如xlsx）
- export_headers: 导出表头
- validation_rules: 参数校验规则

**必须严格按照文档内容提取：**
1. 真实的GitLab仓库地址（端口30000）
2. 具体的API接口路径（三个接口）
3. 数据库连接信息（localhost:6446）
4. 表名t_cust_multiorg_unit
5. 服务间调用关系（确权开立服务调用用户服务）
6. 服务划分严格按照文档内容，不要合并或拆分服务
7. 关注接口特殊要求中的依赖关系描述

**输出要求：**
- 只返回JSON格式，不要其他解释文字
- 严格使用文档中的真实URL和路径
- APIs数组中每个接口都要包含完整的参数结构
- 不要编造不存在的信息"""
        
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": "你是系统架构专家，专门分析软件设计文档。请严格按照Jinja2模板风格提取信息，不要编造。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000  # 增加token限制以支持更详细的API参数结构
            )
            
            # 提取JSON内容
            json_str = self._extract_json_from_response(response)
            parsed_info = json.loads(json_str)
            
            # 转换为标准格式，兼容新的详细结构化输出
            standardized_info = {
                # 服务信息处理（支持新的详细结构）
                'services': [service['name'] if isinstance(service, dict) else service for service in parsed_info.get('services', [])],
                'git_repositories': parsed_info.get('git_repositories', []),
                
                # API信息处理（支持新的详细参数结构）
                'apis': [api.get('path', api) if isinstance(api, dict) else api for api in parsed_info.get('apis', [])], 
                
                # 数据库信息处理（支持新的详细结构）
                'databases': [db.get('table_name', db) if isinstance(db, dict) else db for db in parsed_info.get('databases', [])],
                
                'dependencies': parsed_info.get('service_dependencies', {}),
                'technical_stack': parsed_info.get('technical_stack', []),
                'main_features': parsed_info.get('main_features', []),
                
                # 保存详细信息用于后续任务生成
                'detailed_services': parsed_info.get('services', []),
                'detailed_apis': parsed_info.get('apis', []),
                'detailed_databases': parsed_info.get('databases', [])
            }
            
            logger.info(f"✅ 优化版LLM解析完成 - 服务: {len(standardized_info.get('services', []))}, API: {len(standardized_info.get('apis', []))}")
            logger.info(f"📋 识别的服务: {standardized_info.get('services', [])}")
            logger.info(f"🔗 Git仓库: {len(standardized_info.get('git_repositories', []))}个")
            logger.info(f"🌐 API详情: {len(standardized_info.get('detailed_apis', []))}个接口包含完整参数")
            
            return standardized_info
            
        except Exception as e:
            logger.error(f"❌ 优化版LLM解析失败: {e}")
            # 回退到规则化解析
            return self._rule_parse_design_document(design_doc)
    
    def _extract_json_from_response(self, response: str) -> str:
        """从LLM响应中提取JSON内容"""
        # 查找JSON代码块
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*?\})'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # 如果没有找到JSON，返回整个响应
        return response.strip()
    
    def _rule_parse_design_document(self, design_doc: str) -> Dict[str, Any]:
        """规则化解析设计文档（备用方案）"""
        logger.info("📋 使用规则化方式解析设计文档...")
        
        parsed_info = {
            'services': [],
            'git_repositories': [],
            'apis': [],
            'databases': [],
            'dependencies': {}
        }
        
        # 🔧 优化服务名称提取
        service_patterns = [
            r'(用户服务|确权开立服务)',  # 直接匹配核心服务
            r'服务[:：]\s*(zqyl-user-center-service|crcl-open)',  # 明确的服务名
        ]
        
        found_services = set()
        for pattern in service_patterns:
            matches = re.findall(pattern, design_doc, re.IGNORECASE)
            for match in matches:
                service_name = match if isinstance(match, str) else match[-1]
                if service_name and len(service_name) > 2:
                    found_services.add(service_name.strip())
        
        # 标准化服务名称
        standardized_services = []
        for service in found_services:
            if 'user' in service.lower() or '用户' in service:
                if '用户服务' not in standardized_services:
                    standardized_services.append('用户服务')
            elif 'crcl' in service.lower() or '确权' in service or '开立' in service:
                if '确权开立服务' not in standardized_services:
                    standardized_services.append('确权开立服务')
        
        # 如果没有识别到标准服务，使用默认值
        if not standardized_services:
            standardized_services = ['用户服务', '确权开立服务']
        
        parsed_info['services'] = standardized_services
        
        # 提取Git仓库地址
        git_patterns = [
            r'http[s]?://[^\s]+\.git',
            r'git@[^\s]+\.git',
        ]
        
        for pattern in git_patterns:
            matches = re.findall(pattern, design_doc)
            for match in matches:
                if match and match not in parsed_info['git_repositories']:
                    parsed_info['git_repositories'].append(match)
        
        # 提取API接口
        api_patterns = [
            r'GET\s+(/[^\s\[\]]+)',
            r'POST\s+(/[^\s\[\]]+)',
            r'接口[:：]\s*(/[^\s\[\]]+)',
            r'(/[\w\-]+/[\w\-]+/[\w\-]+)',
        ]
        
        found_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, design_doc)
            for match in matches:
                if match and match.startswith('/') and len(match) > 5:
                    found_apis.add(match)
        
        parsed_info['apis'] = list(found_apis)
        
        logger.info(f"✅ 规则解析完成 - 服务: {len(parsed_info['services'])}, API: {len(parsed_info['apis'])}")
        return parsed_info
    
    def _generate_task_sequence(self, parsed_info: Dict[str, Any], project_name: str) -> List[Dict[str, Any]]:
        """生成任务序列"""
        logger.info("🔄 开始生成任务序列...")
        
        tasks = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        base_path = f"/Users/renyu/Documents/create_project/{project_name}"
        
        services = parsed_info.get('services', ['用户服务', '确权开立服务'])
        if not services:
            services = ['用户服务', '确权开立服务']  # 默认服务
        
        task_counter = 1
        
        # 1. git_extraction - 系统级任务
        tasks.append({
            'task_id': f'task_{task_counter:03d}',
            'service_name': '系统',
            'task_type': 'git_extraction',
            'priority': task_counter,
            'status': 'pending',
            'dependencies': '[]',
            'estimated_duration': '5分钟',
            'description': '从设计文档提取GitLab仓库地址',
            'deliverables': json.dumps(['GitLab仓库地址清单', '仓库访问验证报告'], ensure_ascii=False),
            'implementation_details': f'解析设计文档，提取仓库地址: {", ".join(parsed_info.get("git_repositories", []))}',
            'completion_criteria': '成功提取并验证GitLab仓库地址可访问性',
            'parameters': json.dumps({
                'repositories': parsed_info.get('git_repositories', []),
                'extraction_method': 'llm_enhanced' if self.llm_client else 'regex_pattern'
            }, ensure_ascii=False),
            'created_at': current_time,
            'updated_at': current_time
        })
        task_counter += 1
        
        # 2. git_clone - 为每个服务生成
        for service in services:
            service_repo = self._get_service_repo_name(service)
            tasks.append({
                'task_id': f'task_{task_counter:03d}',
                'service_name': service,
                'task_type': 'git_clone',
                'priority': task_counter,
                'status': 'pending',
                'dependencies': '["task_001"]',
                'estimated_duration': '10分钟',
                'description': f'下载{service}代码到{base_path}/{service_repo}',
                'deliverables': json.dumps([f'{service}源码目录'], ensure_ascii=False),
                'implementation_details': f'使用git clone命令下载{service}代码到指定目录，确保项目结构完整可编译',
                'completion_criteria': '代码下载完成，项目目录存在且包含pom.xml文件',
                'parameters': json.dumps({
                    'repo_name': service_repo,
                    'target_path': f'{base_path}/{service_repo}',
                    'branch': 'master'
                }, ensure_ascii=False),
                'created_at': current_time,
                'updated_at': current_time
            })
            task_counter += 1
        
        # 3. code_analysis - 为每个服务生成
        clone_dependencies = [f'task_{i:03d}' for i in range(2, 2 + len(services))]
        for i, service in enumerate(services):
            service_repo = self._get_service_repo_name(service)
            controller_name = self._get_controller_name(service)
            
            tasks.append({
                'task_id': f'task_{task_counter:03d}',
                'service_name': service,
                'task_type': 'code_analysis',
                'priority': task_counter,
                'status': 'pending',
                'dependencies': json.dumps([clone_dependencies[i]]),
                'estimated_duration': '20分钟',
                'description': f'分析{service}代码结构，确定{controller_name}添加位置',
                'deliverables': json.dumps(['代码结构从Controller层开始到数据获取的完整路径'], ensure_ascii=False),
                'implementation_details': f'分析项目package结构和controller层，找到或创建{controller_name}类的最佳位置',
                'completion_criteria': f'确定{controller_name}的包路径和文件位置，明确依赖的Service层结构',
                'parameters': json.dumps({
                    'project_path': f'{base_path}/{service_repo}',
                    'target_controller': controller_name,
                    'analysis_scope': 'controller,service,mapper'
                }, ensure_ascii=False),
                'created_at': current_time,
                'updated_at': current_time
            })
            task_counter += 1
        
        # 4. config - 为每个服务生成数据库配置
        analysis_dependencies = [f'task_{i:03d}' for i in range(2 + len(services), 2 + 2*len(services))]
        for i, service in enumerate(services):
            tasks.append({
                'task_id': f'task_{task_counter:03d}',
                'service_name': service,
                'task_type': 'config',
                'priority': task_counter,
                'status': 'pending',
                'dependencies': json.dumps([analysis_dependencies[i]]),
                'estimated_duration': '15分钟',
                'description': f'配置{service}数据库连接：jdbc:mysql://localhost:6446/dbwebappdb',
                'deliverables': json.dumps(['数据库配置文件', '连接测试报告'], ensure_ascii=False),
                'implementation_details': '修改application.yml文件，配置数据库连接信息包括URL、用户名密码和连接池设置',
                'completion_criteria': 'application.yml文件已更新，数据库连接配置正确且可连通',
                'parameters': json.dumps({
                    'database_url': 'jdbc:mysql://localhost:6446/dbwebappdb',
                    'username': 'dbwebapp',
                    'password': 'dbwebapp'
                }, ensure_ascii=False),
                'created_at': current_time,
                'updated_at': current_time
            })
            task_counter += 1
        
        # 5. database - 建表任务
        config_dependencies = [f'task_{i:03d}' for i in range(2 + 2*len(services), 2 + 3*len(services))]
        for i, service in enumerate(services):
            table_name = 't_cust_multiorg_unit' if '用户' in service else 't_limit_info'
            
            tasks.append({
                'task_id': f'task_{task_counter:03d}',
                'service_name': service,
                'task_type': 'database',
                'priority': task_counter,
                'status': 'pending',
                'dependencies': json.dumps([config_dependencies[i]]),
                'estimated_duration': '15分钟',
                'description': f'创建{table_name}表，包含业务字段和索引',
                'deliverables': json.dumps(['建表SQL脚本', 'Entity实体类', 'Mapper接口文件'], ensure_ascii=False),
                'implementation_details': '编写建表SQL脚本，定义主键、索引和字段约束，创建对应的Entity和Mapper文件',
                'completion_criteria': '表结构创建成功，Entity和Mapper文件可正常编译，支持基本CRUD操作',
                'parameters': json.dumps({
                    'table_name': table_name,
                    'sql_location': f'src/main/resources/sql/{table_name}.sql'
                }, ensure_ascii=False),
                'created_at': current_time,
                'updated_at': current_time
            })
            task_counter += 1
        
        # 6. api - 接口开发任务
        database_dependencies = [f'task_{i:03d}' for i in range(2 + 3*len(services), 2 + 4*len(services))]
        apis = parsed_info.get('apis', [])
        if not apis:
            apis = ['/general/multiorgManage/queryCompanyUnitList', 
                   '/crcl-open-api/lsLimit/listUnitLimitByCompanyId',
                   '/crcl-open-api/lsLimit/listUnitLimitByCompanyIdExport']
        
        for i, api in enumerate(apis):
            service = services[i % len(services)]
            dep_task = database_dependencies[i % len(database_dependencies)]
            
            tasks.append({
                'task_id': f'task_{task_counter:03d}',
                'service_name': service,
                'task_type': 'api',
                'priority': task_counter,
                'status': 'pending',
                'dependencies': json.dumps([dep_task]),
                'estimated_duration': '60分钟',
                'description': f'实现GET {api}接口',
                'deliverables': json.dumps(['Controller类', 'Service业务逻辑层', '接口文档'], ensure_ascii=False),
                'implementation_details': f'在Controller中实现{api}接口，支持条件查询和分页，返回规定的字段格式',
                'completion_criteria': '接口可正常访问，返回数据格式符合规范，支持条件查询和分页功能',
                'parameters': json.dumps({
                    'api_path': api,
                    'http_method': 'GET',
                    'content_type': 'application/json'
                }, ensure_ascii=False),
                'created_at': current_time,
                'updated_at': current_time
            })
            task_counter += 1
        
        # 7. integration_test - 集成测试
        api_dependencies = [f'task_{i:03d}' for i in range(2 + 4*len(services), task_counter)]
        tasks.append({
            'task_id': f'task_{task_counter:03d}',
            'service_name': '系统',
            'task_type': 'integration_test',
            'priority': task_counter,
            'status': 'pending',
            'dependencies': json.dumps(api_dependencies),
            'estimated_duration': '30分钟',
            'description': '测试服务间调用的完整流程',
            'deliverables': json.dumps(['集成测试用例', '测试数据脚本', '测试报告'], ensure_ascii=False),
            'implementation_details': '编写集成测试用例，验证服务间调用正确性和数据完整性',
            'completion_criteria': '所有测试用例通过，接口调用链路正常，数据返回格式正确',
            'parameters': json.dumps({
                'test_scenarios': ['组织单元额度查询测试'],
                'test_data': {'gwCompanyId': 1, 'unitName': '测试单元', 'bizType': 80}
            }, ensure_ascii=False),
            'created_at': current_time,
            'updated_at': current_time
        })
        task_counter += 1
        
        # 8. deployment - 代码提交
        tasks.append({
            'task_id': f'task_{task_counter:03d}',
            'service_name': '系统',
            'task_type': 'deployment',
            'priority': task_counter,
            'status': 'pending',
            'dependencies': json.dumps([f'task_{task_counter-1:03d}']),
            'estimated_duration': '20分钟',
            'description': '提交代码到GitLab仓库，commit message: feat: 新增组织单元额度管理功能',
            'deliverables': json.dumps(['Git提交记录', '代码合并报告', '部署文档'], ensure_ascii=False),
            'implementation_details': '执行git add、git commit和git push命令，提交所有新增和修改的代码文件',
            'completion_criteria': '代码成功提交到GitLab仓库，commit信息清晰，无冲突',
            'parameters': json.dumps({
                'repositories': [{'path': f'{base_path}/{self._get_service_repo_name(s)}', 'changes': f'新增{s}相关功能'} for s in services]
            }, ensure_ascii=False),
            'created_at': current_time,
            'updated_at': current_time
        })
        
        logger.info(f"✅ 生成任务序列完成，共 {len(tasks)} 个任务")
        return tasks
    
    def _get_service_repo_name(self, service_name: str) -> str:
        """根据服务名称获取仓库名"""
        if '用户' in service_name:
            return 'zqyl-user-center-service'
        elif '确权' in service_name or '开立' in service_name:
            return 'crcl-open'
        else:
            return service_name.replace('服务', '-service').lower()
    
    def _get_controller_name(self, service_name: str) -> str:
        """根据服务名称获取Controller名"""
        if '用户' in service_name:
            return 'MultiorgManageController'
        elif '确权' in service_name or '开立' in service_name:
            return 'LsLimitController'
        else:
            return f'{service_name.replace("服务", "")}Controller'
    
    def _generate_sql_content(self, tasks: List[Dict[str, Any]]) -> str:
        """生成SQL插入语句"""
        logger.info("🔄 生成SQL内容...")
        
        sql_lines = []
        sql_lines.append("INSERT INTO execution_tasks (task_id,service_name,task_type,priority,status,dependencies,estimated_duration,description,deliverables,implementation_details,completion_criteria,parameters,created_at,updated_at) VALUES")
        
        task_values = []
        for task in tasks:
            # 转义SQL字符串
            def escape_sql_string(s):
                if s is None:
                    return 'NULL'
                return "'" + str(s).replace("'", "''").replace("\\", "\\\\") + "'"
            
            values = [
                escape_sql_string(task['task_id']),
                escape_sql_string(task['service_name']),
                escape_sql_string(task['task_type']),
                str(task['priority']),
                escape_sql_string(task['status']),
                escape_sql_string(task['dependencies']),
                escape_sql_string(task['estimated_duration']),
                escape_sql_string(task['description']),
                escape_sql_string(task['deliverables']),
                escape_sql_string(task['implementation_details']),
                escape_sql_string(task['completion_criteria']),
                escape_sql_string(task['parameters']),
                escape_sql_string(task['created_at']),
                escape_sql_string(task['updated_at'])
            ]
            
            task_values.append(f"\t ({','.join(values)})")
        
        sql_lines.append(',\n'.join(task_values) + ';')
        
        return '\n'.join(sql_lines)
    
    def _save_sql_file(self, sql_content: str, project_name: str) -> str:
        """保存SQL文件"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        filename = f"execution_tasks_{timestamp}.sql"
        filepath = f"/Users/renyu/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            logger.info(f"✅ SQL文件保存成功: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ SQL文件保存失败: {e}")
            return ""
    
    def _save_to_database(self, tasks: List[Dict[str, Any]]):
        """保存任务到SQLite数据库"""
        try:
            from src.corder_integration.langgraph.task_manager import TaskManager
            task_manager = TaskManager()
            
            for task in tasks:
                task_manager.create_task(
                    task_id=task['task_id'],
                    task_type=task['task_type'],
                    status=task['status'],
                    description=task['description'],
                    parameters=json.loads(task['parameters']),
                    dependencies=json.loads(task['dependencies']),
                    priority=task['priority']
                )
            
            logger.info(f"✅ 任务已保存到数据库，共 {len(tasks)} 个")
            
        except Exception as e:
            logger.warning(f"⚠️ 保存到数据库失败: {e}")

# 创建节点实例
task_simple_splitting_node = TaskSimpleSplittingNode()