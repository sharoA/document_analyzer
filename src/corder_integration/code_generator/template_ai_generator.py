#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板+AI混合代码生成器
结合预定义模板和AI智能改造，生成高质量的Java代码
"""

import logging
from typing import Dict, List, Any, Optional
from src.corder_integration.code_generator.java_templates import JavaTemplateManager

logger = logging.getLogger(__name__)


class TemplateAIGenerator:
    """模板+AI混合代码生成器"""
    
    def __init__(self, llm_client=None):
        self.template_manager = JavaTemplateManager()
        self.llm_client = llm_client
        self.llm_provider = getattr(llm_client, 'provider_name', 'unknown') if llm_client else 'none'
        logger.info(f"✅ 模板+AI生成器初始化完成 (LLM: {self.llm_provider})")
    
    def generate_code(self, interface_name: str, input_params: List[Dict], 
                     output_params: Dict, description: str, http_method: str,
                     project_context: Dict[str, Any], api_path: str = '', 
                     business_logic: str = '') -> Dict[str, str]:
        """
        使用模板+AI混合模式生成代码
        
        Args:
            interface_name: 接口名称
            input_params: 输入参数列表
            output_params: 输出参数字典
            description: 业务描述
            http_method: HTTP方法
            project_context: 项目上下文
            api_path: API路径
            business_logic: 业务逻辑描述
            
        Returns:
            生成的代码字典 {代码类型: 代码内容}
        """
        
        logger.info(f"🎨 开始模板+AI混合代码生成: {interface_name}")
        
        try:
            # 1. 构建模板变量
            template_vars = self.template_manager.build_template_variables(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path, business_logic
            )
            
            # 2. 生成基础模板代码
            template_codes = self._generate_template_codes(template_vars)
            
            # 3. 使用AI增强代码（如果LLM可用）
            if self.llm_client:
                enhanced_codes = self._enhance_templates_with_ai(
                    template_codes, template_vars, interface_name, input_params, 
                    output_params, description, business_logic, project_context
                )
                return enhanced_codes
            else:
                logger.warning("⚠️ LLM客户端不可用，返回基础模板代码")
                return template_codes
                
        except Exception as e:
            logger.error(f"❌ 模板+AI代码生成失败: {e}")
            # 返回基础模板代码作为后备
            try:
                template_vars = self.template_manager.build_template_variables(
                    interface_name, input_params, output_params, description, 
                    http_method, project_context, api_path, business_logic
                )
                return self._generate_template_codes(template_vars)
            except Exception as fallback_error:
                logger.error(f"❌ 后备模板生成也失败: {fallback_error}")
                return self._generate_fallback_code(interface_name, description)
    
    def _generate_template_codes(self, template_vars: Dict[str, str]) -> Dict[str, str]:
        """根据模板变量生成基础代码"""
        
        codes = {}
        templates = self.template_manager.get_all_templates()
        
        for code_type, template in templates.items():
            try:
                # 应用模板变量
                code = self.template_manager.apply_template_variables(template, template_vars)
                codes[code_type] = code
                logger.debug(f"✅ 生成{code_type}模板代码成功")
                
            except Exception as e:
                logger.error(f"❌ 生成{code_type}模板代码失败: {e}")
                
        return codes
    
    def _enhance_templates_with_ai(self, template_codes: Dict[str, str], template_vars: Dict[str, str],
                                 interface_name: str, input_params: List[Dict], output_params: Dict,
                                 description: str, business_logic: str, project_context: Dict[str, Any]) -> Dict[str, str]:
        """使用AI增强和完善模板代码"""
        
        logger.info(f"🤖 使用{self.llm_provider}增强模板代码...")
        
        enhanced_codes = {}
        
        # 定义增强优先级（重要的代码类型优先增强）
        enhancement_priority = [
            'service_impl',  # 最重要：业务逻辑实现
            'controller',    # 次重要：API入口
            'service_interface',  # 接口定义
            'request_dto',   # 请求参数
            'response_dto',  # 响应参数
            'entity',        # 数据实体
            'mapper'         # 数据访问层
        ]
        
        # 按优先级增强代码
        for code_type in enhancement_priority:
            if code_type in template_codes:
                try:
                    enhanced_code = self._enhance_single_template(
                        code_type, template_codes[code_type], template_vars,
                        interface_name, input_params, output_params, 
                        description, business_logic, project_context
                    )
                    enhanced_codes[code_type] = enhanced_code
                    
                except Exception as e:
                    logger.error(f"❌ {code_type} AI增强失败: {e}")
                    enhanced_codes[code_type] = template_codes[code_type]
        
        # 添加未增强的模板代码
        for code_type, template_code in template_codes.items():
            if code_type not in enhanced_codes:
                enhanced_codes[code_type] = template_code
        
        return enhanced_codes
    
    def _enhance_single_template(self, code_type: str, template_code: str, template_vars: Dict[str, str],
                               interface_name: str, input_params: List[Dict], output_params: Dict,
                               description: str, business_logic: str, project_context: Dict[str, Any]) -> str:
        """增强单个模板代码"""
        
        try:
            # 构建增强prompt
            enhancement_prompt = self._build_enhancement_prompt(
                code_type, template_code, template_vars, interface_name,
                input_params, output_params, description, business_logic, project_context
            )
            
            # 调用LLM
            messages = [
                {
                    "role": "system", 
                    "content": "你是Java代码优化专家。请根据业务需求优化给定的模板代码，保持代码结构清晰，添加必要的业务逻辑。重要：请使用具体的类名，不要使用{{}}模板变量语法。只返回优化后的Java代码，不要添加额外说明。"
                },
                {"role": "user", "content": enhancement_prompt}
            ]

            logger.info(f"增强模板代码入参：{messages}")
            
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            if response:
                # 兼容不同LLM客户端的响应格式
                enhanced_code = ""
                if isinstance(response, str):
                    enhanced_code = response.strip()
                elif isinstance(response, dict) and 'choices' in response and len(response['choices']) > 0:
                    enhanced_code = response['choices'][0]['message']['content'].strip()
                elif hasattr(response, 'content'):
                    enhanced_code = response.content.strip()
                
                if enhanced_code:
                    # 提取代码块
                    enhanced_code = self._extract_code_block(enhanced_code)
                    
                    logger.info(f"✅ {code_type} AI增强完成")
                    return enhanced_code
                else:
                    logger.warning(f"⚠️ {code_type} AI响应格式无法解析，使用原始模板")
                    return template_code
            else:
                logger.warning(f"⚠️ {code_type} AI响应为空，使用原始模板")
                return template_code
                
        except Exception as e:
            logger.error(f"❌ {code_type} AI增强异常: {e}")
            return template_code
    
    def _build_enhancement_prompt(self, code_type: str, template_code: str, template_vars: Dict[str, str],
                                interface_name: str, input_params: List[Dict], output_params: Dict,
                                description: str, business_logic: str, project_context: Dict[str, Any]) -> str:
        """构建增强prompt"""
        
        # 根据代码类型定制prompt
        if code_type == 'service_impl':
            focus_points = [
                "实现完整的业务逻辑",
                "添加数据验证和转换",
                "处理异常情况",
                "添加事务管理",
                "优化数据库查询逻辑"
            ]
        elif code_type == 'controller':
            focus_points = [
                "完善参数验证",
                "统一响应格式",
                "添加API文档注解",
                "改进错误处理",
                "优化日志记录"
            ]
        elif code_type in ['request_dto', 'response_dto']:
            focus_points = [
                "添加详细的字段验证",
                "完善API文档注解",
                "优化字段类型选择",
                "添加字段描述"
            ]
        else:
            focus_points = [
                "改进代码结构",
                "添加必要注释",
                "优化实现逻辑"
            ]
        
        prompt = f"""
请优化以下{code_type}代码模板，重点关注：
{chr(10).join(f'- {point}' for point in focus_points)}

## 当前模板代码：
```java
{template_code}
```

## 业务需求：
- 接口名称：{interface_name}
- 功能描述：{description}
- 业务逻辑：{business_logic}

## 输入参数：
{self._format_params_for_prompt(input_params)}

## 输出参数：
{self._format_output_params_for_prompt(output_params)}

## 技术要求：
- 基础包名：{template_vars.get('PACKAGE_NAME', 'com.main')}
- 使用Spring Boot + MyBatis Plus
- 遵循DDD分层架构
- 保持原有类名和包结构
- 请求DTO类名：{template_vars.get('REQUEST_DTO_NAME', f'{interface_name}Req')}
- 响应DTO类名：{template_vars.get('RESPONSE_DTO_NAME', f'{interface_name}Resp')}
- Service类名：{template_vars.get('SERVICE_NAME', f'{interface_name}Service')}

**重要：请使用具体的类名（如 {template_vars.get('REQUEST_DTO_NAME', f'{interface_name}Req')}），不要使用模板变量语法（如 {{{{REQUEST_DTO_NAME}}}}）**

请返回优化后的完整Java代码（只要代码，不要额外说明）：
"""
        
        return prompt
    
    def _extract_code_block(self, response: str) -> str:
        """从AI响应中提取代码块"""
        
        # 优先提取java代码块
        if '```java' in response:
            start_marker = response.find('```java') + 7
            end_marker = response.find('```', start_marker)
            if end_marker != -1:
                return response[start_marker:end_marker].strip()
        
        # 其次提取普通代码块
        if '```' in response:
            start_marker = response.find('```') + 3
            end_marker = response.find('```', start_marker)
            if end_marker != -1:
                return response[start_marker:end_marker].strip()
        
        # 如果没有代码块标记，直接返回响应内容
        return response.strip()
    
    def _format_params_for_prompt(self, input_params: List[Dict]) -> str:
        """格式化输入参数用于prompt"""
        if not input_params:
            return "无输入参数"
        
        formatted = []
        for param in input_params:
            name = param.get('name', 'unknown')
            param_type = param.get('type', 'String')
            desc = param.get('description', '')
            required = param.get('required', False)
            formatted.append(f"- {name} ({param_type}): {desc} {'[必填]' if required else '[可选]'}")
        
        return '\n'.join(formatted)
    
    def _format_output_params_for_prompt(self, output_params: Dict) -> str:
        """格式化输出参数用于prompt"""
        if not output_params:
            return "标准响应格式（code, message, data）"
        
        formatted = []
        for name, info in output_params.items():
            param_type = info.get('type', 'String')
            desc = info.get('description', '')
            formatted.append(f"- {name} ({param_type}): {desc}")
        
        return '\n'.join(formatted)
    
    def _generate_fallback_code(self, interface_name: str, description: str) -> Dict[str, str]:
        """生成最基础的后备代码"""
        
        logger.warning("🔄 生成最基础的后备代码")
        
        return {
            'controller': f'''package com.main.interfaces.facade;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/{interface_name.lower()}")
public class {interface_name}Controller {{
    
    @PostMapping
    public String {interface_name}() {{
        // TODO: 实现{description}
        return "success";
    }}
}}''',
            'service_interface': f'''package com.main.application.service;

public interface {interface_name}Service {{
    
    String {interface_name}();
}}''',
            'service_impl': f'''package com.main.application.service.impl;

import com.main.application.service.{interface_name}Service;
import org.springframework.stereotype.Service;

@Service
public class {interface_name}ServiceImpl implements {interface_name}Service {{
    
    @Override
    public String {interface_name}() {{
        // TODO: 实现{description}
        return "success";
    }}
}}'''
        } 