"""
核心业务设计统一生成器
基于业务需求分析结果和约束条件，统一生成服务设计、API设计、数据库设计
遵循单一职责原则，专注于核心业务设计的统一生成
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
from .config.company_services_config import get_company_services_config

class CoreBusinessGenerator:
    """核心业务设计统一生成器"""
    
    def __init__(self, llm_client=None, vector_db=None):
        """初始化核心业务生成器"""
        self.llm_client = llm_client
        self.vector_db = vector_db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.template_loader = self._init_template_loader()
        
    def _init_template_loader(self):
        """初始化Jinja2模板加载器"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(current_dir, 'prompts')
        
        if os.path.exists(prompts_dir):
            return Environment(loader=FileSystemLoader(prompts_dir))
        else:
            self.logger.warning(f"Prompts目录不存在: {prompts_dir}")
            return None
    
    def generate_core_business_design(
        self,
        content_analysis: Dict,
        parsing_result: Dict,
        document_content: str,
        function_requirements_info: Dict,
        service_numbers: int,
        service_info: List[Dict],
        data_resources: int,
        data_info: List[Dict]
    ) -> Dict[str, Any]:
        """
        统一生成核心业务设计
        
        Args:
            content_analysis: 内容分析结果
            parsing_result: 文档解析结果
            document_content: 原始文档内容
            function_requirements_info: 功能需求信息
            service_numbers: 预期服务数量
            service_info: 服务基本信息
            data_resources: 数据库资源数量
            data_info: 数据库信息
            
        Returns:
            包含service_details和project_architecture的字典
            
        Raises:
            ValueError: 输入参数无效
            Exception: 生成过程失败
        """
        try:
            self.logger.info("开始核心业务设计统一生成")
            
            # 验证输入参数
            self._validate_inputs(document_content, service_info, data_info)
            
            # 使用模板生成提示词并调用LLM
            design_result = self._generate_with_llm(
                content_analysis=content_analysis,
                parsing_result=parsing_result,
                document_content=document_content,
                function_requirements_info=function_requirements_info,
                service_numbers=service_numbers,
                service_info=service_info,
                data_resources=data_resources,
                data_info=data_info
            )
            
            # 验证生成结果
            self._validate_generated_design(design_result)
            
            self.logger.info(f"核心业务设计生成成功，包含{len(design_result.get('service_details', []))}个服务")
            return design_result
                
        except Exception as e:
            self.logger.error(f"核心业务设计生成失败: {e}")
            raise
    
    def _validate_inputs(self, document_content: str, service_info: List[Dict], data_info: List[Dict]) -> None:
        """验证输入参数的有效性"""
        # 放宽文档内容验证 - 允许较短的文档内容
        if not document_content or len(document_content.strip()) < 10:
            self.logger.warning("文档内容较短，可能影响生成质量")
            
        # 放宽服务信息验证 - 允许空服务信息，生成器会使用默认值
        if not service_info or len(service_info) == 0:
            self.logger.warning("服务信息为空，将使用默认服务配置")
            
        # 放宽数据库信息验证 - 允许空数据库信息，生成器会使用默认值
        if not data_info or len(data_info) == 0:
            self.logger.warning("数据库信息为空，将使用默认数据库配置")
    
    def _generate_with_llm(self, **kwargs) -> Dict:
        """使用LLM生成核心业务设计"""
        if not self.template_loader:
            raise Exception("模板加载器未初始化")
            
        if not self.llm_client:
            raise Exception("LLM客户端不可用")
        
        try:
            # 加载模板
            prompt_template = self.template_loader.get_template('core_business_design_prompts.jinja2')
            
            # 生成系统提示词
            system_prompt = prompt_template.module.system_prompt_core_business_design()
            
            # 生成用户提示词
            user_prompt = prompt_template.module.user_prompt_core_business_design(
                content_analysis=kwargs.get('content_analysis'),
                parsing_result=kwargs.get('parsing_result'),
                document_content=kwargs.get('document_content'),
                function_requirements_info=kwargs.get('function_requirements_info'),
                service_numbers=kwargs.get('service_numbers'),
                service_info=kwargs.get('service_info'),
                data_resources=kwargs.get('data_resources'),
                data_info=kwargs.get('data_info')
            )
            
            self.logger.info(f"生成的用户提示词: {user_prompt}")
            
            # 调用LLM
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1  # 降低温度提高准确性
            )
            
            # 解析JSON响应
            design_result = self._parse_json_response(response, "核心业务设计生成")
            
            # 确保生成的service_details包含完整的服务信息
            design_result = self._enrich_service_details(design_result, kwargs.get('service_info', []))
            
            return design_result
            
        except Exception as e:
            self.logger.error(f"LLM生成核心业务设计失败: {e}")
            raise
    
    def _enrich_service_details(self, design_result: Dict, service_info: List[Dict]) -> Dict:
        """确保生成的service_details包含完整的服务信息"""
        if not design_result.get('service_details') or not service_info:
            return design_result
        
        service_details = design_result['service_details']
        
        # 为每个生成的服务补全信息
        for service_detail in service_details:
            service_name = service_detail.get('service_name', '')
            service_english_name = service_detail.get('service_english_name', '')
            
            # 在service_info中查找匹配的服务
            matching_service = None
            for service in service_info:
                if (service.get('service_name') == service_name or 
                    service.get('service_english_name') == service_english_name):
                    matching_service = service
                    break
            
            # 如果找到匹配的服务，补全缺失的字段
            if matching_service:
                # 确保包含关键字段
                if not service_detail.get('gitlab') and matching_service.get('gitlab'):
                    service_detail['gitlab'] = matching_service['gitlab']
                
                if not service_detail.get('business_domain') and matching_service.get('business_domain'):
                    service_detail['business_domain'] = matching_service['business_domain']
                
                if not service_detail.get('data_resources') and matching_service.get('data_resources'):
                    service_detail['data_resources'] = matching_service['data_resources']
                
                self.logger.info(f"为服务 {service_name} 补全信息: gitlab={service_detail.get('gitlab')}")
        
        return design_result
    
    def _parse_json_response(self, response: str, step_name: str) -> Dict:
        """解析JSON响应，包含错误处理"""
        try:
            # 清理响应文本
            response_text = response.strip()
            
            # 提取JSON部分
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif response_text.startswith('{') and response_text.endswith('}'):
                json_str = response_text
            else:
                # 尝试找到第一个 { 和最后一个 }
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx + 1]
                else:
                    raise ValueError("无法找到有效的JSON内容")
            
            parsed_data = json.loads(json_str)
            self.logger.info("JSON解析成功")
            return parsed_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"{step_name}JSON解析失败: {str(e)}")
            self.logger.error(f"原始响应: {response[:500]}...")
            raise Exception(f"JSON解析失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"{step_name}响应处理失败: {str(e)}")
            raise
    
    def _validate_generated_design(self, design_data: Dict) -> None:
        """验证生成的设计数据质量"""
        if not isinstance(design_data, dict):
            raise ValueError("生成的设计数据不是字典格式")
            
        # 检查必需字段
        if "service_details" not in design_data:
            raise ValueError("生成的设计缺少service_details字段")
            
        service_details = design_data["service_details"]
        if not isinstance(service_details, list) or len(service_details) == 0:
            raise ValueError("service_details为空或格式错误")
        
        # 验证每个服务的结构
        for i, service in enumerate(service_details):
            self._validate_service_structure(service, i)
        
      
    
    def _validate_service_structure(self, service: Dict, index: int) -> None:
        """验证单个服务的结构"""
        required_fields = [
            "service_name", "service_english_name", "service_duty", 
            "core_modules", "api_design"
        ]
        
        for field in required_fields:
            if field not in service:
                raise ValueError(f"服务{index}缺少{field}字段")
        
        # 验证api_design结构
        api_design = service.get("api_design", [])
        if not isinstance(api_design, list):
            raise ValueError(f"服务{index}的api_design不是列表格式")
        
        # 验证每个API的必需字段
        for j, api in enumerate(api_design):
            required_api_fields = [
                "interface_type", "uri", "method", "description",
                "request_params", "response_params"
            ]
            for field in required_api_fields:
                if field not in api:
                    raise ValueError(f"服务{index}的API{j}缺少{field}字段")