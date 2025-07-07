#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码审查节点 - 自动化代码质量检查
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# 🔥 修改：使用火山引擎客户端替代OpenAI
try:
    from ....utils.volcengine_client import get_volcengine_client
    from ....resource.config import get_config
    VOLCENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"火山引擎客户端不可用: {e}")
    VOLCENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)

class CodeReviewPrompts:
    """代码审查提示词管理器"""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.prompts_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._load_prompts()
    
    def _load_prompts(self):
        """加载提示词模板"""
        self.templates = {}
        self.default_templates = {}
        
        # 定义模板文件映射
        template_files = {
            "quality_review": "quality_review_prompts.jinja2",
            "architecture_review": "architecture_review_prompts.jinja2"
        }
        
        # 定义对应的默认模板文件映射
        default_template_files = {
            "quality_review": "default/quality_review_default_prompts.jinja2",
            "architecture_review": "default/architecture_review_default_prompts.jinja2"
        }
        
        # 逐个加载专门的模板文件
        for prompt_type, template_file in template_files.items():
            try:
                template = self.jinja_env.get_template(template_file)
                self.templates[prompt_type] = template
                logger.info(f"模板 {template_file} 加载成功")
            except Exception as e:
                logger.warning(f"加载模板 {template_file} 失败: {e}")
                self.templates[prompt_type] = None
        
        # 逐个加载对应的默认模板文件
        for prompt_type, default_template_file in default_template_files.items():
            try:
                default_template = self.jinja_env.get_template(default_template_file)
                self.default_templates[prompt_type] = default_template
                logger.info(f"默认模板 {default_template_file} 加载成功")
            except Exception as e:
                logger.warning(f"加载默认模板 {default_template_file} 失败: {e}")
                self.default_templates[prompt_type] = None
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """获取渲染后的提示词"""
        try:
            # 首先尝试从专门的模板文件获取
            if prompt_type in self.templates and self.templates[prompt_type]:
                template = self.templates[prompt_type]
                if hasattr(template.module, f"{prompt_type}_prompt"):
                    macro = getattr(template.module, f"{prompt_type}_prompt")
                    return macro(**kwargs)
            
            # 其次尝试从对应的默认模板获取
            if prompt_type in self.default_templates and self.default_templates[prompt_type]:
                default_template = self.default_templates[prompt_type]
                if hasattr(default_template.module, f"{prompt_type}_prompt"):
                    macro = getattr(default_template.module, f"{prompt_type}_prompt")
                    return macro(**kwargs)
            
            # 最后使用内置默认提示词
            logger.warning(f"未找到提示词类型: {prompt_type}，使用内置默认提示词")
            return self._get_builtin_default_prompt(prompt_type, **kwargs)
            
        except Exception as e:
            logger.error(f"渲染提示词失败: {e}")
            return self._get_builtin_default_prompt(prompt_type, **kwargs)
    
    def _get_builtin_default_prompt(self, prompt_type: str, **kwargs) -> str:
        """获取内置默认提示词（最后备选方案）"""
        builtin_templates = {
            "quality_review": """
请审查以下Spring Boot服务的代码质量：

服务名称：{service_name}
生成的代码：
{service_code}

请从以下维度进行评估：
1. 代码质量和规范性
2. 性能优化建议
3. 安全性检查
4. 架构设计合理性
5. 异常处理完善性

请以JSON格式输出审查结果：
{{
    "overall_score": 85,
    "quality_issues": [],
    "security_issues": [],
    "has_critical_issues": false,
    "security_risk": false,
    "pass_review": true
}}
""",
            "architecture_review": """
请评估以下微服务系统的架构一致性：

项目名称：{project_name}
服务列表：{completed_services}
服务依赖：{service_dependencies}
生成的API：{generated_apis}

请评估：
1. 服务间接口设计一致性
2. 数据模型一致性
3. 错误处理标准化
4. 认证授权方案统一性
5. 监控和日志规范一致性

请以JSON格式输出评估结果：
{{
    "consistency_score": 90,
    "consistency_issues": [],
    "architecture_violations": [],
    "overall_health": "good"
}}
"""
        }
        
        template_str = builtin_templates.get(prompt_type, "")
        if template_str:
            return template_str.format(**kwargs)
        return ""

async def code_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    代码审查节点 - 质量检查
    """
    
    logger.info(f"开始执行代码审查: {state['project_name']}")
    
    client = get_volcengine_client()
    prompts = CodeReviewPrompts()
    
    try:
        review_results = {}
        
        # 🔍 对每个已生成的服务进行代码审查
        for service_name, service_code in state["generated_services"].items():
            logger.info(f"审查服务: {service_name}")
            
            # 执行代码质量审查
            quality_review = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个代码审查专家，擅长分析Java Spring Boot代码的质量、性能和最佳实践。"
                    },
                    {
                        "role": "user", 
                        "content": prompts.get_prompt("quality_review", 
                                                     service_name=service_name, 
                                                     service_code=json.dumps(service_code, ensure_ascii=False, indent=2))
                    }
                ],
                temperature=0.2
            )
            
            try:
                review_result = _extract_json_from_response(quality_review.choices[0].message.content)
                review_results[service_name] = review_result
                
                logger.info(f"服务 {service_name} 审查完成，评分: {review_result.get('overall_score', 'N/A')}")
                
            except Exception as e:
                logger.error(f"解析服务 {service_name} 的审查结果失败: {e}")
                review_results[service_name] = {
                    "overall_score": 0,
                    "quality_issues": [],
                    "security_issues": [],
                    "has_critical_issues": True,
                    "security_risk": False,
                    "pass_review": False,
                    "error": str(e)
                }
        
        # 🧠 执行整体架构一致性检查
        logger.info("执行整体架构一致性检查...")
        
        architecture_review = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "你是一个微服务架构专家，擅长评估微服务系统的整体架构一致性。"
                },
                {
                    "role": "user", 
                    "content": prompts.get_prompt("architecture_review",
                                                  project_name=state['project_name'],
                                                  completed_services=state['completed_services'],
                                                  service_dependencies=json.dumps(state['service_dependencies'], ensure_ascii=False),
                                                  generated_apis=json.dumps(state['generated_apis'], ensure_ascii=False))
                }
            ],
            temperature=0.2
        )
        
        try:
            arch_result = _extract_json_from_response(architecture_review.choices[0].message.content)
        except Exception as e:
            logger.error(f"解析架构审查结果失败: {e}")
            arch_result = {
                "consistency_score": 0,
                "consistency_issues": [],
                "architecture_violations": [],
                "overall_health": "poor",
                "error": str(e)
            }
        
        # 🔄 更新状态
        state["code_review_results"] = review_results
        state["static_analysis_results"] = arch_result
        state["current_phase"] = "unit_testing"
        
        logger.info(f"代码审查完成，审查了 {len(review_results)} 个服务")
        
        return state
        
    except Exception as e:
        logger.error(f"代码审查失败: {str(e)}")
        state["execution_errors"].append(f"代码审查失败: {str(e)}")
        state["current_phase"] = "error"
        return state

def _extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """从LLM响应中提取JSON内容"""
    try:
        # 尝试直接解析
        return json.loads(response_text)
    except json.JSONDecodeError:
        # 尝试提取代码块中的JSON
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 尝试提取{}包围的内容
        brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if brace_match:
            return json.loads(brace_match.group(0))
        
        # 如果都失败，返回空对象
        logger.warning(f"无法从响应中提取JSON: {response_text[:200]}...")
        return {} 