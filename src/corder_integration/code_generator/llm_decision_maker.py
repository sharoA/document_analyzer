#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型决策器
专门负责调用大模型进行决策，判断在哪些类下实现接口功能
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMDecisionMaker:
    """大模型决策器 - 单一职责：调用大模型进行决策"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
    
    def decide_implementation_classes(self, project_structure: Dict[str, Any], 
                                    api_keyword: str, business_logic: str) -> Dict[str, Any]:
        """
        决策在哪些类下实现接口功能
        
        Args:
            project_structure: 项目结构信息
            api_keyword: API关键字
            business_logic: 业务逻辑描述
            
        Returns:
            决策结果
        """
        logger.info(f"🤖 开始LLM决策：{api_keyword}")
        
        if not self.llm_client:
            logger.error("❌ LLM客户端未初始化")
            return self._get_default_decision()
        
        try:
            # 1. 准备输入数据
            input_data = self._prepare_input_data(project_structure, api_keyword, business_logic)
            
            # 2. 加载提示词模板
            prompt_template = self._load_prompt_template("strategy1_implementation_decision.jinja2")
            
            # 3. 生成完整提示词
            prompt = self._generate_prompt(prompt_template, input_data)
            
            # 4. 调用大模型
            response = self._call_llm(prompt)
            
            # 5. 解析结果
            decision = self._parse_llm_response(response)
            
            logger.info(f"✅ LLM决策完成")
            return decision
            
        except Exception as e:
            logger.error(f"❌ LLM决策失败: {e}")
            return self._get_default_decision()
    
    def _prepare_input_data(self, project_structure: Dict[str, Any], 
                           api_keyword: str, business_logic: str) -> Dict[str, Any]:
        """准备输入数据"""
        
        # 提取各层信息
        controllers = project_structure.get('controllers', {})
        services = project_structure.get('services', {})
        mappers = project_structure.get('mappers', {})
        entities = project_structure.get('entities', {})
        
        # 根据包路径区分Application Service和Domain Service
        application_services = {}
        domain_services = {}
        feign_clients = {}
        
        for service_name, service_info in services.items():
            package = service_info.get('package', '')
            if 'application/service' in package or 'application.service' in package:
                application_services[service_name] = service_info
            elif 'domain/service' in package or 'domain.service' in package:
                domain_services[service_name] = service_info
            elif 'application/feign' in package or 'application.feign' in package:
                feign_clients[service_name] = service_info
            else:
                # 默认归类到application service
                application_services[service_name] = service_info
        
        # 构造输入数据
        input_data = {
            'api_keyword': api_keyword,
            'business_logic': business_logic,
            'base_package': project_structure.get('base_package', ''),
            'project_path': project_structure.get('project_path', ''),
            'controllers': self._format_class_info(controllers),
            'services': self._format_class_info(application_services),  # 兼容原有命名
            'application_services': self._format_class_info(application_services),
            'domain_services': self._format_class_info(domain_services),
            'mappers': self._format_class_info(mappers),
            'entities': self._format_class_info(entities),
            'feign_clients': self._format_class_info(feign_clients),
            'total_classes': len(controllers) + len(services) + len(mappers) + len(entities)
        }
        
        return input_data
    
    def _format_class_info(self, class_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化类信息"""
        formatted = []
        
        for class_name, class_info in class_dict.items():
            formatted.append({
                'class_name': class_name,
                'package': class_info.get('package', ''),
                'file_path': class_info.get('file_path', ''),
                'methods': class_info.get('methods', []),
                'annotations': class_info.get('annotations', [])
            })
        
        return formatted
    
    def _load_prompt_template(self, template_name: str) -> str:
        """加载提示词模板"""
        template_path = self.prompts_dir / template_name
        
        if not template_path.exists():
            # 如果模板不存在，返回默认模板
            return self._get_default_prompt_template()
        
        try:
            return template_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"⚠️ 加载提示词模板失败: {e}")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self) -> str:
        """获取默认提示词模板"""
        return """你是一个Java Spring Boot项目的DDD架构师，需要分析项目结构并决定如何实现新的API接口功能。

## 项目信息
- API关键字: {{ api_keyword }}
- 业务逻辑: {{ business_logic }}
- 基础包名: {{ base_package }}

## DDD架构分层要求
当前后端采用DDD（领域驱动设计）架构，请严格遵循以下分层结构：

1. **Controller层** (interfaces/rest): 对外REST接口，负责接收HTTP请求和参数校验
2. **Application Service层** (application/service): 应用服务，协调业务流程，不包含业务逻辑
3. **Domain Service层** (domain/service): 领域服务，核心业务逻辑的实现
4. **Domain Mapper层** (domain/mapper): 数据访问层接口，定义数据库操作方法
5. **Feign Client层** (application/feign): 外部服务调用接口，处理微服务间通信
6. **DTO层** (interfaces/dto): 数据传输对象，用于接口入参和出参
7. **Entity层** (domain/entity): 领域实体，表示业务核心概念
8. **XML映射** (resources/mapper): MyBatis SQL映射，具体的SQL实现

## 现有项目结构分析

### Controller层 (interfaces/rest)
{% if controllers %}
{% for controller in controllers %}
- {{ controller.class_name }}
  - 包名: {{ controller.package }}
  - 现有方法: {{ controller.methods | join(', ') }}
  - 注解: {{ controller.annotations | join(', ') }}
{% endfor %}
{% else %}
暂无Controller类
{% endif %}

### Application Service层 (application/service)
{% if services %}
{% for service in services %}
- {{ service.class_name }}
  - 包名: {{ service.package }}
  - 现有方法: {{ service.methods | join(', ') }}
  - 注解: {{ service.annotations | join(', ') }}
{% endfor %}
{% else %}
暂无Application Service类
{% endif %}

### Domain Service层 (domain/service)
{% if domain_services %}
{% for service in domain_services %}
- {{ service.class_name }}
  - 包名: {{ service.package }}
  - 现有方法: {{ service.methods | join(', ') }}
  - 注解: {{ service.annotations | join(', ') }}
{% endfor %}
{% else %}
暂无Domain Service类
{% endif %}

### Domain Mapper层 (domain/mapper)
{% if mappers %}
{% for mapper in mappers %}
- {{ mapper.class_name }}
  - 包名: {{ mapper.package }}
  - 现有方法: {{ mapper.methods | join(', ') }}
  - 注解: {{ mapper.annotations | join(', ') }}
{% endfor %}
{% else %}
暂无Mapper类
{% endif %}

### Feign Client层 (application/feign)
{% if feign_clients %}
{% for feign in feign_clients %}
- {{ feign.class_name }}
  - 包名: {{ feign.package }}
  - 现有方法: {{ feign.methods | join(', ') }}
  - 注解: {{ feign.annotations | join(', ') }}
{% endfor %}
{% else %}
暂无Feign Client类
{% endif %}

## 决策原则
请根据DDD架构原则和业务需求，决定如何实现新的API接口功能：

### Controller层决策原则
1. 如果存在功能相关的Controller且职责单一，优先选择 `enhance_existing`
2. 如果现有Controller职责过重或业务领域不同，选择 `create_new`
3. 考虑REST API的资源分组和版本管理

### Application Service层决策原则
1. 如果存在相关的应用服务且流程相似，优先选择 `enhance_existing`
2. 如果业务流程复杂或涉及不同的业务上下文，选择 `create_new`
3. 应用服务应当薄薄一层，主要负责编排和协调

### Domain Service层决策原则
1. 如果存在相关的领域服务且业务逻辑相关，优先选择 `enhance_existing`
2. 如果涉及新的业务领域或核心逻辑差异很大，选择 `create_new`
3. 领域服务应当承载核心业务逻辑

### Domain Mapper层决策原则
1. 如果操作相同的数据表或实体，优先选择 `enhance_existing`
2. 如果涉及新的数据表或查询逻辑复杂，选择 `create_new`
3. 每个Mapper通常对应一个聚合根或核心实体

### Feign Client层决策原则
1. 如果调用相同的外部服务，优先选择 `enhance_existing`
2. 如果调用新的外部服务或不同的服务版本，选择 `create_new`
3. 按照外部服务进行分组

## 输出格式
请严格按照以下JSON格式返回决策结果：

```json
{
  "controller": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  },
  "application_service": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  },
  "domain_service": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  },
  "mapper": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  },
  "feign_client": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  },
  "dto": {
    "action": "create_new",
    "request_dto": "请求DTO类名",
    "response_dto": "响应DTO类名",
    "package_path": "建议的包路径",
    "reason": "DTO通常需要为每个接口单独创建"
  },
  "entity": {
    "action": "enhance_existing 或 create_new",
    "target_class": "目标类名（如果是enhance_existing）",
    "package_path": "建议的包路径",
    "reason": "详细的决策原因，说明为什么选择这种方式"
  }
}
```

请仔细分析项目结构，遵循DDD架构原则，给出合理的决策建议。"""
    
    def _generate_prompt(self, template: str, input_data: Dict[str, Any]) -> str:
        """生成完整提示词"""
        try:
            # 简单的模板替换（如果需要更复杂的模板引擎，可以使用Jinja2）
            prompt = template
            
            # 替换变量
            for key, value in input_data.items():
                if isinstance(value, str):
                    prompt = prompt.replace(f"{{{{ {key} }}}}", value)
                elif isinstance(value, list):
                    # 简单处理列表
                    if value and isinstance(value[0], dict):
                        # 格式化类信息
                        formatted_list = []
                        for item in value:
                            if key in ['controllers', 'services', 'mappers']:
                                formatted_list.append(f"- {item.get('class_name', '')}")
                                formatted_list.append(f"  包名: {item.get('package', '')}")
                                formatted_list.append(f"  现有方法: {', '.join(item.get('methods', []))}")
                        prompt = prompt.replace(f"{{{{ {key} }}}}", '\n'.join(formatted_list))
            
            return prompt
            
        except Exception as e:
            logger.error(f"❌ 生成提示词失败: {e}")
            return f"分析项目结构并决策实现方案：API关键字={input_data.get('api_keyword', '')}, 业务逻辑={input_data.get('business_logic', '')}"
    
    def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat(messages)
            logger.debug(f"🤖 LLM响应: {response}")
            return response
        except Exception as e:
            logger.error(f"❌ 调用LLM失败: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\\{[^}]+\\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                decision = json.loads(json_str)
                return self._validate_decision(decision)
            
            # 如果没有找到JSON，尝试简单解析
            return self._parse_simple_response(response)
            
        except Exception as e:
            logger.error(f"❌ 解析LLM响应失败: {e}")
            return self._get_default_decision()
    
    def _parse_simple_response(self, response: str) -> Dict[str, Any]:
        """简单解析响应"""
        decision = self._get_default_decision()
        
        # 简单的关键词匹配
        if "enhance_existing" in response.lower():
            decision['controller']['action'] = 'enhance_existing'
            decision['service']['action'] = 'enhance_existing'
        
        return decision
    
    def _validate_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """验证决策结果"""
        required_keys = ['controller', 'application_service', 'domain_service', 'mapper', 'feign_client', 'dto', 'entity']
        
        for key in required_keys:
            if key not in decision:
                if key == 'dto':
                    decision[key] = {
                        'action': 'create_new',
                        'request_dto': f'{decision.get("api_keyword", "Api")}Req',
                        'response_dto': f'{decision.get("api_keyword", "Api")}Resp',
                        'package_path': 'interfaces.dto',
                        'reason': 'DTO通常需要为每个接口单独创建'
                    }
                else:
                    decision[key] = {
                        'action': 'create_new',
                        'target_class': '',
                        'package_path': self._get_default_package_path(key),
                        'reason': f'默认创建新{key}'
                    }
            else:
                # 验证action值
                if decision[key].get('action') not in ['enhance_existing', 'create_new']:
                    decision[key]['action'] = 'create_new'
                
                # 确保必要字段存在
                if 'target_class' not in decision[key]:
                    decision[key]['target_class'] = ''
                if 'package_path' not in decision[key]:
                    decision[key]['package_path'] = self._get_default_package_path(key)
                if 'reason' not in decision[key]:
                    decision[key]['reason'] = '默认决策'
        
        # 兼容原有的service字段
        if 'service' not in decision and 'application_service' in decision:
            decision['service'] = decision['application_service']
        
        return decision
    
    def _get_default_package_path(self, layer_type: str) -> str:
        """获取默认包路径"""
        package_mapping = {
            'controller': 'interfaces.rest',
            'application_service': 'application.service',
            'domain_service': 'domain.service',
            'mapper': 'domain.mapper',
            'feign_client': 'application.feign',
            'dto': 'interfaces.dto',
            'entity': 'domain.entity'
        }
        return package_mapping.get(layer_type, 'unknown')
    
    def _get_default_decision(self) -> Dict[str, Any]:
        """获取默认决策"""
        return {
            'controller': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'interfaces.rest',
                'reason': '默认创建新Controller'
            },
            'application_service': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'application.service',
                'reason': '默认创建新Application Service'
            },
            'domain_service': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'domain.service',
                'reason': '默认创建新Domain Service'
            },
            'mapper': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'domain.mapper',
                'reason': '默认创建新Mapper'
            },
            'feign_client': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'application.feign',
                'reason': '默认创建新Feign Client'
            },
            'dto': {
                'action': 'create_new',
                'request_dto': 'ApiReq',
                'response_dto': 'ApiResp',
                'package_path': 'interfaces.dto',
                'reason': 'DTO通常需要为每个接口单独创建'
            },
            'entity': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'domain.entity',
                'reason': '默认创建新Entity'
            },
            # 兼容原有的service字段
            'service': {
                'action': 'create_new',
                'target_class': '',
                'package_path': 'application.service',
                'reason': '默认创建新Service'
            }
        }
    
    def get_decision_summary(self, decision: Dict[str, Any]) -> str:
        """获取决策摘要"""
        summary = "实现决策摘要:\\n"
        
        for component, decision_info in decision.items():
            action = decision_info.get('action', 'unknown')
            target_class = decision_info.get('target_class', 'N/A')
            reason = decision_info.get('reason', 'N/A')
            
            summary += f"- {component}: {action}"
            if target_class:
                summary += f" ({target_class})"
            summary += f" - {reason}\\n"
        
        return summary