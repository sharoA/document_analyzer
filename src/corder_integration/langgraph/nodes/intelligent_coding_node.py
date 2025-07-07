#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能编码节点 - 并行微服务代码生成
"""

import asyncio
import json
import logging
import os
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

class IntelligentCodingPrompts:
    """智能编码提示词管理器"""
    
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
            "service_analysis": "service_analysis_prompts.jinja2",
            "code_generation": "code_generation_prompts.jinja2",
            "api_design": "api_design_prompts.jinja2"
        }
        
        # 定义对应的默认模板文件映射
        default_template_files = {
            "service_analysis": "default/service_analysis_default_prompts.jinja2",
            "code_generation": "default/code_generation_default_prompts.jinja2",
            "api_design": "default/api_design_default_prompts.jinja2"
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
            "service_analysis": """
你是Spring Boot微服务开发专家。请分析服务设计：

服务名称：{service_name}
设计文档：{design_doc}
依赖服务：{dependencies}

请输出JSON格式的服务分析结果。
""",
            "code_generation": """
你是Java代码生成专家。请生成Spring Boot项目代码：

服务名称：{service_name}
服务分析：{service_analysis}
项目路径：{project_path}

请输出JSON格式的代码结构。
""",
            "api_design": """
你是RESTful API设计专家。请设计API接口：

服务名称：{service_name}
生成代码：{generated_code}

请输出JSON格式的API设计。
""",
            "service_interconnect": """
你是微服务集成专家。请设计服务间调用：

已完成服务：{completed_services}
服务依赖：{service_dependencies}
生成API：{generated_apis}

请输出JSON格式的集成方案。
"""
        }
        
        template_str = builtin_templates.get(prompt_type, "")
        if template_str:
            return template_str.format(**kwargs)
        return ""

async def intelligent_coding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    智能编码节点 - 并行生成多个SpringBoot微服务
    """
    
    logger.info(f"开始执行智能编码: {state['project_name']}")
    
    # 📋 获取待处理的服务列表
    pending_services = [
        service for service in state["identified_services"] 
        if service not in state["completed_services"]
    ]
    
    logger.info(f"待处理服务: {pending_services}")
    
    if not pending_services:
        logger.info("没有待处理的服务，跳过编码阶段")
        state["current_phase"] = "code_review"
        return state
    
    # 🔄 按执行批次并行处理服务
    for batch in state["parallel_tasks"]:
        batch_services = [s for s in batch.get("services", []) if s in pending_services]
        
        if batch_services:
            logger.info(f"处理批次: {batch.get('batch_id', 'unknown')}, 服务: {batch_services}")
            
            # 🚀 并发生成当前批次的服务
            batch_results = await asyncio.gather(*[
                generate_single_service(service, state) 
                for service in batch_services
            ], return_exceptions=True)
            
            # 📊 更新状态
            for service, result in zip(batch_services, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"服务 {service} 生成失败: {result}")
                    state["failed_services"].append(service)
                    state["execution_errors"].append(f"{service}: {str(result)}")
                elif result.get("success"):
                    logger.info(f"服务 {service} 生成成功")
                    state["completed_services"].append(service)
                    state["generated_services"][service] = result["generated_code"]
                    state["generated_apis"][service] = result["api_endpoints"]
                    state["generated_sql"][service] = result["sql_statements"]
                else:
                    logger.error(f"服务 {service} 生成失败: {result.get('error', 'Unknown error')}")
                    state["failed_services"].append(service)
                    state["execution_errors"].append(f"{service}: {result.get('error', 'Unknown error')}")
    
    # 🌐 生成服务间调用代码
    if len(state["completed_services"]) > 1:
        logger.info("生成服务间调用代码...")
        await generate_service_interconnections(state)
    
    # 📊 统计结果
    successful_count = len([s for s in state["completed_services"] if s in pending_services])
    failed_count = len([s for s in state["failed_services"] if s in pending_services])
    
    logger.info(f"智能编码完成，成功: {successful_count}, 失败: {failed_count}")
    logger.info(f"总体完成服务: {state['completed_services']}")
    logger.info(f"总体失败服务: {state['failed_services']}")
    
    # 🔄 更新阶段状态
    if len(state["completed_services"]) == len(state["identified_services"]):
        state["current_phase"] = "code_review"
        logger.info("所有服务编码完成，进入代码审查阶段")
    elif len(state["failed_services"]) >= len(state["identified_services"]) // 2:
        state["current_phase"] = "critical_error"
        logger.error("超过一半服务失败，标记为关键错误")
    else:
        # 还有待处理的服务，保持当前阶段
        logger.info("部分服务完成，等待下次处理")
    
    return state

async def generate_single_service(service_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """生成单个微服务的完整代码"""
    
    logger.info(f"开始生成服务: {service_name}")
    
    # 🔥 修改：使用火山引擎客户端
    if not VOLCENGINE_AVAILABLE:
        logger.error("火山引擎客户端不可用")
        return {
            "success": False,
            "error": "火山引擎客户端不可用"
        }
    
    try:
        # 获取火山引擎客户端和配置
        volcengine_client = get_volcengine_client()
        config = get_config()
        volcengine_config = config.get_volcengine_config()
        
        # 从配置中获取模型名称
        model_name = volcengine_config.get('model', 'ep-20250605091804-wmw6w')
        
        logger.info(f"使用火山引擎模型: {model_name}")
        
        prompts = IntelligentCodingPrompts()
        
        # 📋 分析服务需求
        logger.debug(f"分析服务需求: {service_name}")
        
        dependencies = state["service_dependencies"].get(service_name, [])
        dependencies_str = ', '.join(dependencies) if dependencies else '无'
        
        service_analysis_messages = [
            {
                "role": "system", 
                "content": "你是一个Spring Boot微服务开发专家，擅长将设计文档转换为技术实现方案。"
            },
            {
                "role": "user", 
                "content": prompts.get_prompt("service_analysis", service_name=service_name, design_doc=state["design_doc"], dependencies=dependencies_str)
            }
        ]
        
        service_analysis_result = volcengine_client.chat(
            messages=service_analysis_messages,
            temperature=0.3
        )
        
        # 💻 代码生成
        logger.debug(f"生成代码: {service_name}")
        
        project_path = state["project_paths"].get(service_name, f"./workspace/{state['project_name']}/{service_name}")
        
        code_generation_messages = [
            {
                "role": "system", 
                "content": "你是一个Java代码生成专家，擅长生成高质量的Spring Boot微服务代码。"
            },
            {
                "role": "user", 
                "content": prompts.get_prompt("code_generation", service_name=service_name, service_analysis=service_analysis_result)
            }
        ]
        
        code_generation_result = volcengine_client.chat(
            messages=code_generation_messages,
            temperature=0.2
        )
        
        # 🌐 API设计
        logger.debug(f"设计API: {service_name}")
        
        api_design_messages = [
            {
                "role": "system", 
                "content": "你是一个RESTful API设计专家，擅长设计标准化的Web API接口。"
            },
            {
                "role": "user", 
                "content": prompts.get_prompt("api_design", service_name=service_name, generated_code=code_generation_result)
            }
        ]
        
        api_design_result = volcengine_client.chat(
            messages=api_design_messages,
            temperature=0.2
        )
        
        # 解析结果并写入文件
        try:
            code_result = _extract_json_from_response(code_generation_result)
            api_result = _extract_json_from_response(api_design_result)
        except Exception as e:
            logger.error(f"解析 {service_name} 的LLM响应失败: {e}")
            return {
                "success": False,
                "error": f"解析LLM响应失败: {str(e)}"
            }
        
        # 写入生成的代码文件
        await write_service_files(service_name, code_result, project_path)
        
        logger.info(f"服务 {service_name} 代码生成完成")
        
        return {
            "success": True,
            "generated_code": code_result,
            "api_endpoints": api_result.get("endpoints", []),
            "sql_statements": code_result.get("sql_statements", [])
        }
        
    except Exception as e:
        logger.error(f"生成服务 {service_name} 失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_service_interconnections(state: Dict[str, Any]):
    """生成服务间调用代码"""
    
    logger.info("开始生成服务间调用代码")
    
    # 🔥 修改：使用火山引擎客户端
    if not VOLCENGINE_AVAILABLE:
        logger.error("火山引擎客户端不可用")
        state["execution_errors"].append("火山引擎客户端不可用")
        return
    
    try:
        volcengine_client = get_volcengine_client()
        prompts = IntelligentCodingPrompts()
        
        completed_services_str = ', '.join(state["completed_services"])
        service_dependencies_str = json.dumps(state["service_dependencies"], ensure_ascii=False)
        generated_apis_str = json.dumps(state["generated_apis"], ensure_ascii=False)
        
        interconnect_messages = [
            {
                "role": "system", 
                "content": "你是一个微服务集成专家，擅长设计服务间的调用和通信机制。"
            },
            {
                "role": "user", 
                "content": prompts.get_prompt("service_interconnect", completed_services=completed_services_str, service_dependencies=service_dependencies_str, generated_apis=generated_apis_str)
            }
        ]
        
        interconnect_result = volcengine_client.chat(
            messages=interconnect_messages,
            temperature=0.2
        )
        
        try:
            interconnect_data = _extract_json_from_response(interconnect_result)
            state["service_interconnections"] = interconnect_data
            logger.info("服务间调用代码生成成功")
        except Exception as e:
            logger.error(f"解析服务间调用响应失败: {e}")
            state["service_interconnections"] = {}
        
    except Exception as e:
        logger.error(f"生成服务间调用代码失败: {e}")
        state["execution_errors"].append(f"服务互联生成失败: {str(e)}")

async def write_service_files(service_name: str, code_data: Dict[str, Any], project_path: str):
    """写入服务代码文件"""
    
    logger.info(f"写入服务 {service_name} 的代码文件到: {project_path}")
    
    try:
        files = code_data.get("files", {})
        
        for file_path, content in files.items():
            full_path = os.path.join(project_path, file_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 写入文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"写入文件: {full_path}")
        
        logger.info(f"服务 {service_name} 文件写入完成，共 {len(files)} 个文件")
        
    except Exception as e:
        logger.error(f"写入服务 {service_name} 文件失败: {e}")
        raise

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