#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版模板+AI代码生成器
专门解决设计文档特殊要求和表结构映射问题
"""

import logging
import re
from typing import Dict, List, Any, Optional
from .template_ai_generator import TemplateAIGenerator

logger = logging.getLogger(__name__)


class EnhancedTemplateAIGenerator(TemplateAIGenerator):
    """增强版模板+AI代码生成器 - 支持设计文档特殊要求"""
    
    def __init__(self, llm_client=None):
        super().__init__(llm_client)
        logger.info("✅ 增强版模板+AI生成器初始化完成")
    
    def generate_code(self, interface_name: str, input_params: List[Dict], 
                     output_params: Dict, description: str, http_method: str,
                     project_context: Dict[str, Any], api_path: str = '', 
                     business_logic: str = '') -> Dict[str, str]:
        """
        增强版代码生成，处理设计文档特殊要求
        """
        
        logger.info(f"🎨 开始增强版代码生成: {interface_name}")
        
        try:
            # 1. 解析设计文档特殊要求
            special_requirements = self._parse_special_requirements(business_logic, description)
            
            # 2. 解析表结构信息
            table_structure = self._parse_table_structure_from_context(project_context)
            
            # 3. 构建增强的模板变量
            template_vars = self._build_enhanced_template_variables(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path, business_logic, 
                special_requirements, table_structure
            )
            
            # 4. 生成基础模板代码
            template_codes = self._generate_template_codes(template_vars)
            
            # 5. 使用AI增强代码（重点处理特殊要求）
            if self.llm_client:
                enhanced_codes = self._enhance_with_special_requirements(
                    template_codes, template_vars, interface_name, input_params, 
                    output_params, description, business_logic, project_context,
                    special_requirements, table_structure
                )
                return enhanced_codes
            else:
                logger.warning("⚠️ LLM客户端不可用，返回增强的模板代码")
                return self._apply_special_requirements_to_templates(
                    template_codes, special_requirements, table_structure
                )
                
        except Exception as e:
            logger.error(f"❌ 增强版代码生成失败: {e}")
            # 回退到父类方法
            return super().generate_code(
                interface_name, input_params, output_params, description, 
                http_method, project_context, api_path, business_logic
            )
    
    def _parse_special_requirements(self, business_logic: str, description: str) -> Dict[str, Any]:
        """解析设计文档中的特殊要求"""
        
        requirements = {
            'use_pagehelper': False,
            'external_service_calls': [],
            'pagination_required': False,
            'excel_export': False,
            'validation_rules': []
        }
        
        full_text = f"{business_logic} {description}".lower()
        
        # 检测PageHelper分页
        if 'pagehelper' in full_text or '分页' in full_text:
            requirements['use_pagehelper'] = True
            requirements['pagination_required'] = True
            logger.info("🔍 检测到PageHelper分页要求")
        
        # 检测服务调用
        service_call_patterns = [
            r'调用([^服务]*服务).*?(/[\w/]+)接口',
            r'需要调用\s*([^的]*)\s*的\s*(/[\w/]+)\s*接口',
            r'调用.*?([^service]*service).*?(/[\w/]+)'
        ]
        
        for pattern in service_call_patterns:
            matches = re.findall(pattern, business_logic + description, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    service_name = match[0].strip()
                    endpoint = match[1].strip()
                    requirements['external_service_calls'].append({
                        'service_name': service_name,
                        'endpoint': endpoint,
                        'description': f'调用{service_name}的{endpoint}接口'
                    })
                    logger.info(f"🔍 检测到服务调用: {service_name} -> {endpoint}")
        
        # 检测Excel导出
        if 'excel' in full_text or '导出' in full_text or 'export' in full_text:
            requirements['excel_export'] = True
            logger.info("🔍 检测到Excel导出要求")
        
        return requirements
    
    def _parse_table_structure_from_context(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """从项目上下文中解析表结构信息"""
        
        table_info = {
            'has_table_definition': False,
            'table_name': '',
            'columns': [],
            'create_sql': ''
        }
        
        # 从项目上下文的document_content中查找CREATE TABLE语句
        document_content = project_context.get('document_content', '')
        
        # 查找CREATE TABLE语句
        create_table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\)\s*ENGINE'
        match = re.search(create_table_pattern, document_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            table_info['has_table_definition'] = True
            table_info['table_name'] = match.group(1)
            table_info['create_sql'] = match.group(0)
            
            # 解析列定义
            columns_text = match.group(2)
            column_lines = [line.strip() for line in columns_text.split(',') if line.strip()]
            
            for line in column_lines:
                if line.startswith('PRIMARY KEY') or line.startswith('KEY'):
                    continue
                    
                # 解析列定义
                parts = line.split()
                if len(parts) >= 2:
                    column_name = parts[0]
                    column_type = parts[1]
                    
                    # 提取注释
                    comment_match = re.search(r"COMMENT\s+'([^']*)'", line)
                    comment = comment_match.group(1) if comment_match else ''
                    
                    # 检查是否可空
                    nullable = 'NOT NULL' not in line
                    
                    table_info['columns'].append({
                        'name': column_name,
                        'type': column_type,
                        'comment': comment,
                        'nullable': nullable
                    })
            
            logger.info(f"🔍 解析到表结构: {table_info['table_name']} ({len(table_info['columns'])}列)")
        
        return table_info
    
    def _build_enhanced_template_variables(self, interface_name: str, input_params: List[Dict], 
                                         output_params: Dict, description: str, http_method: str,
                                         project_context: Dict[str, Any], api_path: str, 
                                         business_logic: str, special_requirements: Dict[str, Any],
                                         table_structure: Dict[str, Any]) -> Dict[str, str]:
        """构建增强的模板变量"""
        
        # 获取基础模板变量
        base_vars = self.template_manager.build_template_variables(
            interface_name, input_params, output_params, description, 
            http_method, project_context, api_path, business_logic
        )
        
        # 添加增强变量
        enhanced_vars = base_vars.copy()
        
        # 根据表结构调整实体相关变量
        if table_structure['has_table_definition']:
            enhanced_vars['TABLE_NAME'] = table_structure['table_name']
            enhanced_vars['ENTITY_FIELDS'] = self._build_entity_fields_from_table(table_structure)
            enhanced_vars['MAPPER_METHODS'] = self._build_mapper_methods_from_table(table_structure, interface_name)
        
        # 根据特殊要求调整业务逻辑
        if special_requirements['use_pagehelper']:
            enhanced_vars['PAGINATION_IMPORTS'] = 'import com.github.pagehelper.PageHelper;\nimport com.github.pagehelper.PageInfo;'
            enhanced_vars['PAGINATION_LOGIC'] = 'PageHelper.startPage(request.getPage(), request.getPageRow());'
        
        # 服务调用逻辑
        if special_requirements['external_service_calls']:
            service_calls = []
            for call in special_requirements['external_service_calls']:
                service_calls.append(f"// 调用{call['service_name']}: {call['endpoint']}")
            enhanced_vars['EXTERNAL_SERVICE_CALLS'] = '\n            '.join(service_calls)
        
        return enhanced_vars
    
    def _build_entity_fields_from_table(self, table_structure: Dict[str, Any]) -> str:
        """根据表结构生成实体字段"""
        
        fields = []
        for column in table_structure['columns']:
            name = column['name']
            db_type = column['type']
            comment = column['comment']
            nullable = column['nullable']
            
            # 跳过标准字段
            if name in ['id', 'create_time', 'modify_time', 'update_time']:
                continue
            
            # 映射Java类型
            java_type = self._map_db_type_to_java(db_type)
            
            field_lines = []
            if comment:
                field_lines.append(f'    @ApiModelProperty("{comment}")')
            
            # 添加验证注解
            if not nullable:
                field_lines.append('    @NotNull(message = "不能为空")')
                if java_type == 'String':
                    field_lines.append('    @NotBlank(message = "不能为空白")')
            
            field_lines.append(f'    @TableField("{name}")')
            field_lines.append(f'    private {java_type} {self._to_camel_case(name)};')
            
            fields.append('\n'.join(field_lines))
        
        return '\n\n'.join(fields) if fields else '    // TODO: 定义实体字段'
    
    def _build_mapper_methods_from_table(self, table_structure: Dict[str, Any], interface_name: str) -> str:
        """根据表结构生成Mapper方法"""
        
        # 基础查询方法
        methods = [f"List<{interface_name}> selectByCondition(@Param('condition') {interface_name}Req condition);"]
        
        # 分页查询方法
        methods.append(f"List<{interface_name}> selectPageList(@Param('condition') {interface_name}Req condition);")
        
        return '\n    '.join(methods)
    
    def _map_db_type_to_java(self, db_type: str) -> str:
        """映射数据库类型到Java类型"""
        
        db_type_lower = db_type.lower()
        
        if 'varchar' in db_type_lower or 'char' in db_type_lower or 'text' in db_type_lower:
            return 'String'
        elif 'bigint' in db_type_lower:
            return 'Long'
        elif 'int' in db_type_lower:
            return 'Integer'
        elif 'tinyint' in db_type_lower:
            return 'Integer'
        elif 'decimal' in db_type_lower or 'numeric' in db_type_lower:
            return 'BigDecimal'
        elif 'datetime' in db_type_lower or 'timestamp' in db_type_lower:
            return 'LocalDateTime'
        elif 'date' in db_type_lower:
            return 'LocalDate'
        elif 'time' in db_type_lower:
            return 'LocalTime'
        else:
            return 'String'
    
    def _to_camel_case(self, snake_str: str) -> str:
        """下划线转驼峰命名"""
        
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    def _enhance_with_special_requirements(self, template_codes: Dict[str, str], 
                                         template_vars: Dict[str, str],
                                         interface_name: str, input_params: List[Dict], 
                                         output_params: Dict, description: str, 
                                         business_logic: str, project_context: Dict[str, Any],
                                         special_requirements: Dict[str, Any],
                                         table_structure: Dict[str, Any]) -> Dict[str, str]:
        """使用AI增强代码，重点处理特殊要求"""
        
        logger.info(f"🤖 使用AI增强代码，处理特殊要求...")
        
        enhanced_codes = {}
        
        # 优先处理Service实现（业务逻辑核心）
        if 'service_impl' in template_codes:
            enhanced_codes['service_impl'] = self._enhance_service_with_requirements(
                template_codes['service_impl'], template_vars, interface_name,
                special_requirements, table_structure, business_logic
            )
        
        # 处理Controller（API入口）
        if 'controller' in template_codes:
            enhanced_codes['controller'] = self._enhance_controller_with_requirements(
                template_codes['controller'], template_vars, interface_name,
                special_requirements, api_path=template_vars.get('API_PATH', '')
            )
        
        # 处理其他代码类型
        for code_type in ['service_interface', 'request_dto', 'response_dto', 'entity', 'mapper']:
            if code_type in template_codes and code_type not in enhanced_codes:
                enhanced_codes[code_type] = self._enhance_single_template(
                    code_type, template_codes[code_type], template_vars,
                    interface_name, input_params, output_params, 
                    description, business_logic, project_context
                )
        
        return enhanced_codes
    
    def _enhance_service_with_requirements(self, service_code: str, template_vars: Dict[str, str],
                                         interface_name: str, special_requirements: Dict[str, Any],
                                         table_structure: Dict[str, Any], business_logic: str) -> str:
        """增强Service实现，添加特殊要求逻辑"""
        
        enhancement_prompt = f"""
请增强以下Service实现代码，重点添加具体的业务逻辑：

## 当前Service代码：
```java
{service_code}
```

## 特殊要求：
{self._format_special_requirements(special_requirements)}

## 表结构信息：
{self._format_table_structure(table_structure)}

## 业务逻辑：
{business_logic}

## 增强要求：
1. 替换所有TODO注释为具体实现
2. 添加PageHelper分页逻辑（如果需要）
3. 添加外部服务调用代码（如果需要）
4. 添加数据查询和转换逻辑
5. 添加异常处理和日志记录
6. 使用具体的类名，不要使用模板变量

请返回完整的增强后的Service实现代码：
"""
        
        return self._call_llm_for_enhancement(enhancement_prompt, service_code)
    
    def _enhance_controller_with_requirements(self, controller_code: str, template_vars: Dict[str, str],
                                            interface_name: str, special_requirements: Dict[str, Any],
                                            api_path: str) -> str:
        """增强Controller代码，添加完整的API实现"""
        
        enhancement_prompt = f"""
请增强以下Controller代码，添加完整的API实现：

## 当前Controller代码：
```java
{controller_code}
```

## API路径：
{api_path}

## 特殊要求：
{self._format_special_requirements(special_requirements)}

## 增强要求：
1. 添加完整的参数验证
2. 添加详细的Swagger API文档注解
3. 添加分页参数处理（如果需要）
4. 添加异常处理和统一响应格式
5. 替换所有占位符为具体实现
6. 添加请求和响应日志记录

请返回完整的增强后的Controller代码：
"""
        
        return self._call_llm_for_enhancement(enhancement_prompt, controller_code)
    
    def _format_special_requirements(self, special_requirements: Dict[str, Any]) -> str:
        """格式化特殊要求"""
        
        formatted = []
        
        if special_requirements['use_pagehelper']:
            formatted.append("- 使用PageHelper进行分页查询")
        
        if special_requirements['external_service_calls']:
            formatted.append("- 需要调用外部服务：")
            for call in special_requirements['external_service_calls']:
                formatted.append(f"  * {call['service_name']}: {call['endpoint']}")
        
        if special_requirements['excel_export']:
            formatted.append("- 支持Excel导出功能")
        
        return '\n'.join(formatted) if formatted else "无特殊要求"
    
    def _format_table_structure(self, table_structure: Dict[str, Any]) -> str:
        """格式化表结构信息"""
        
        if not table_structure['has_table_definition']:
            return "无表结构定义"
        
        formatted = [f"表名: {table_structure['table_name']}"]
        formatted.append("字段:")
        
        for column in table_structure['columns']:
            formatted.append(f"- {column['name']} ({column['type']}): {column['comment']}")
        
        return '\n'.join(formatted)
    
    def _call_llm_for_enhancement(self, prompt: str, original_code: str) -> str:
        """调用LLM进行代码增强"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "你是Java企业级开发专家。请根据要求增强代码，确保代码完整可用，包含具体的业务逻辑实现。"
                },
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            
            if response:
                enhanced_code = self._extract_code_block(response)
                if enhanced_code and len(enhanced_code) > len(original_code) * 0.8:
                    logger.info("✅ AI代码增强成功")
                    return enhanced_code
                else:
                    logger.warning("⚠️ AI增强结果不理想，使用模板代码")
                    return original_code
            else:
                logger.warning("⚠️ AI响应为空，使用模板代码")
                return original_code
                
        except Exception as e:
            logger.error(f"❌ AI代码增强失败: {e}")
            return original_code
    
    def _apply_special_requirements_to_templates(self, template_codes: Dict[str, str],
                                                special_requirements: Dict[str, Any],
                                                table_structure: Dict[str, Any]) -> Dict[str, str]:
        """在没有LLM的情况下，直接应用特殊要求到模板"""
        
        enhanced_codes = template_codes.copy()
        
        # 简单的字符串替换增强
        for code_type, code in enhanced_codes.items():
            if 'TODO: 实现' in code and special_requirements['use_pagehelper']:
                code = code.replace(
                    'TODO: 实现',
                    'TODO: 实现 - 使用PageHelper分页'
                )
            
            if special_requirements['external_service_calls']:
                for call in special_requirements['external_service_calls']:
                    code = code.replace(
                        '// TODO: 实现业务逻辑',
                        f'// TODO: 调用{call["service_name"]}: {call["endpoint"]}\n        // TODO: 实现业务逻辑'
                    )
            
            enhanced_codes[code_type] = code
        
        return enhanced_codes