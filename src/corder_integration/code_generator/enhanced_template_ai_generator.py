#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版模板+AI代码生成器
专门解决设计文档特殊要求和表结构映射问题
"""

import logging
import re
import time
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
        """使用智能文件复用和专门化提示词模板增强代码"""
        
        logger.info(f"🤖 使用智能文件复用和专门化提示词模板增强代码...")
        
        # 🆕 集成智能文件复用管理器
        try:
            from .intelligent_file_reuse_manager import IntelligentFileReuseManager
            
            file_manager = IntelligentFileReuseManager(self.llm_client)
            
            # 🔧 修复：设置设计文档内容
            design_document = project_context.get('design_document', '') or \
                             project_context.get('document_content', '') or \
                             business_logic
            if design_document:
                file_manager.set_document_content(design_document)
                logger.info(f"✅ 设置设计文档内容，长度: {len(design_document)}")
            else:
                logger.warning("⚠️ 未找到设计文档内容")
            
            # 分析项目结构
            project_path = project_context.get('optimized_project_path', project_context.get('project_path', ''))
            if project_path:
                file_manager.analyze_project_structure(project_path)
                
                # 决策文件复用策略
                api_path = project_context.get('current_api_path', '')
                reuse_strategy = file_manager.decide_file_reuse_strategy(
                    api_path, interface_name, business_logic
                )
                
                logger.info(f"📋 智能文件复用策略:")
                for component, strategy in reuse_strategy.items():
                    logger.info(f"   {component}: {strategy['action']} - {strategy['reason']}")
                
                # 根据复用策略生成完整调用链
                complete_calling_chain = file_manager.generate_complete_calling_chain(
                    interface_name, reuse_strategy, input_params, output_params, business_logic
                )
                
                if complete_calling_chain:
                    logger.info(f"✅ 智能文件复用生成了 {len(complete_calling_chain)} 个组件")
                    
                    # 🔧 处理现有文件的方法添加
                    updated_files = {}
                    new_files = {}
                    
                    for component_type, generated_code in complete_calling_chain.items():
                        strategy_key = self._map_component_to_strategy_key(component_type)
                        component_strategy = reuse_strategy.get(strategy_key, {})
                        
                        if component_strategy.get('action') == 'add_method':
                            # 需要在现有文件中添加方法
                            target_file = component_strategy.get('target_file')
                            if target_file:
                                updated_files[target_file] = {
                                    'type': component_type,
                                    'new_method': generated_code,
                                    'method_name': interface_name
                                }
                        else:
                            # 创建新文件
                            new_files[component_type] = generated_code
                    
                    # 🔧 执行文件更新操作
                    if updated_files:
                        self._update_existing_files_with_new_methods(updated_files, project_context)
                    
                    # 返回需要创建的新文件
                    if new_files:
                        logger.info(f"📝 需要创建 {len(new_files)} 个新文件")
                        return new_files
                    else:
                        logger.info(f"✅ 所有代码都已添加到现有文件中，无需创建新文件")
                        return {'file_updates_completed': 'true'}  # 标记已完成文件更新
        
        except Exception as e:
            logger.warning(f"⚠️ 智能文件复用失败，回退到传统模式: {e}")
        
        # 🔄 回退到原有的专门化提示词模板增强逻辑
        enhanced_codes = {}
        
        # 首先生成Service接口（如果存在），为后续ServiceImpl提供方法信息
        if 'service_interface' in template_codes:
            try:
                enhanced_codes['service_interface'] = self._enhance_single_template_with_requirements(
                    'service_interface', template_codes['service_interface'], template_vars,
                    interface_name, input_params, output_params, 
                    description, business_logic, project_context,
                    special_requirements, table_structure
                )
                # 将生成的Service接口代码添加到项目上下文中
                project_context['service_interface_code'] = enhanced_codes['service_interface']
                logger.info("✅ Service接口代码已添加到项目上下文")
            except Exception as e:
                logger.error(f"❌ service_interface AI增强失败: {e}")
                enhanced_codes['service_interface'] = template_codes['service_interface']
                project_context['service_interface_code'] = template_codes['service_interface']
        
        # 然后生成ServiceImpl，这时可以获取到Service接口信息
        if 'service_impl' in template_codes:
            enhanced_codes['service_impl'] = self._enhance_service_impl_with_specialized_prompt(
                template_codes['service_impl'], interface_name, input_params, output_params,
                description, business_logic, project_context, special_requirements
            )
            # 将ServiceImpl代码添加到上下文，供Mapper生成使用
            project_context['service_impl_code'] = enhanced_codes['service_impl']
        
        # 使用专门的Mapper接口提示词模板
        if 'mapper' in template_codes:
            enhanced_codes['mapper'] = self._enhance_mapper_with_specialized_prompt(
                template_codes['mapper'], interface_name, input_params, output_params,
                description, business_logic, project_context, special_requirements
            )
            # 将Mapper代码添加到上下文，供XML生成使用  
            project_context['mapper_code'] = enhanced_codes['mapper']
        
        # 使用专门的Mapper XML提示词模板
        if 'mapper_xml' in template_codes:
            enhanced_codes['mapper_xml'] = self._enhance_mapper_xml_with_specialized_prompt(
                template_codes['mapper_xml'], interface_name, input_params, output_params,
                description, business_logic, project_context, table_structure
            )
        
        # 对其他代码类型使用原有的增强方法
        for code_type, template_code in template_codes.items():
            if code_type not in enhanced_codes:
                try:
                    enhanced_code = self._enhance_single_template_with_requirements(
                        code_type, template_code, template_vars,
                        interface_name, input_params, output_params, 
                        description, business_logic, project_context,
                        special_requirements, table_structure
                    )
                    enhanced_codes[code_type] = enhanced_code
                    
                except Exception as e:
                    logger.error(f"❌ {code_type} AI增强失败: {e}")
                    enhanced_codes[code_type] = template_code
        
    def _map_component_to_strategy_key(self, component_type: str) -> str:
        """将组件类型映射到策略键"""
        
        mapping = {
            'controller_method': 'controller',
            'application_service': 'application_service',
            'domain_service': 'domain_service',
            'mapper': 'mapper',
            'feign_client': 'feign_client',
            'xml_mapping': 'xml_file'
        }
        
        return mapping.get(component_type, component_type)
    
    def _update_existing_files_with_new_methods(self, updated_files: Dict[str, Dict], 
                                              project_context: Dict[str, Any]) -> None:
        """在现有文件中添加新方法"""
        
        logger.info(f"📝 更新 {len(updated_files)} 个现有文件...")
        
        for file_path, update_info in updated_files.items():
            try:
                # 读取现有文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # 根据组件类型选择合适的方法添加策略
                component_type = update_info['type']
                new_method = update_info['new_method']
                method_name = update_info['method_name']
                
                if component_type == 'controller_method':
                    updated_content = self._add_method_to_controller(
                        existing_content, new_method, method_name
                    )
                elif component_type == 'application_service':
                    updated_content = self._add_method_to_service(
                        existing_content, new_method, method_name
                    )
                elif component_type == 'domain_service':
                    updated_content = self._add_method_to_service(
                        existing_content, new_method, method_name
                    )
                elif component_type == 'mapper':
                    updated_content = self._add_method_to_mapper(
                        existing_content, new_method, method_name
                    )
                elif component_type == 'xml_mapping':
                    updated_content = self._add_mapping_to_xml(
                        existing_content, new_method, method_name
                    )
                else:
                    logger.warning(f"⚠️ 未知的组件类型: {component_type}")
                    continue
                
                # 创建备份
                backup_path = f"{file_path}.backup_{int(time.time())}"
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"📄 创建备份文件: {backup_path}")
                
                # 写入更新后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                logger.info(f"✅ 成功更新文件: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ 更新文件失败 {file_path}: {e}")
    
    def _add_method_to_controller(self, existing_content: str, new_method: str, 
                                method_name: str) -> str:
        """在Controller中添加新方法"""
        
        # 查找类的结束位置（最后一个大括号）
        lines = existing_content.split('\n')
        
        # 从后往前找到最后一个方法的结束位置
        insert_position = -1
        brace_count = 0
        
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line == '}':
                brace_count += 1
                if brace_count == 1:  # 找到类的结束大括号
                    insert_position = i
                    break
        
        if insert_position > 0:
            # 在类结束大括号前插入新方法
            lines.insert(insert_position, '')  # 空行
            lines.insert(insert_position + 1, new_method)
            lines.insert(insert_position + 2, '')  # 空行
            
            return '\n'.join(lines)
        else:
            logger.warning(f"⚠️ 无法找到Controller类的结束位置")
            return existing_content + '\n\n' + new_method
    
    def _add_method_to_service(self, existing_content: str, new_method: str, 
                             method_name: str) -> str:
        """在Service中添加新方法"""
        
        # 类似Controller的处理逻辑
        return self._add_method_to_controller(existing_content, new_method, method_name)
    
    def _add_method_to_mapper(self, existing_content: str, new_method: str, 
                            method_name: str) -> str:
        """在Mapper接口中添加新方法"""
        
        # Mapper接口的处理，在接口结束前添加方法声明
        lines = existing_content.split('\n')
        
        insert_position = -1
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line == '}':
                insert_position = i
                break
        
        if insert_position > 0:
            # 提取方法声明部分（去除实现）
            method_declaration = self._extract_method_declaration(new_method)
            
            lines.insert(insert_position, '')
            lines.insert(insert_position + 1, f'    {method_declaration}')
            lines.insert(insert_position + 2, '')
            
            return '\n'.join(lines)
        else:
            return existing_content + '\n\n    ' + self._extract_method_declaration(new_method)
    
    def _add_mapping_to_xml(self, existing_content: str, new_mapping: str, 
                          method_name: str) -> str:
        """在XML文件中添加新的SQL映射"""
        
        # 在mapper标签结束前添加新的SQL映射
        if '</mapper>' in existing_content:
            insertion_point = existing_content.rfind('</mapper>')
            updated_content = (existing_content[:insertion_point] + 
                             '\n' + new_mapping + '\n' + 
                             existing_content[insertion_point:])
            return updated_content
        else:
            return existing_content + '\n' + new_mapping
    
    def _extract_method_declaration(self, method_implementation: str) -> str:
        """从方法实现中提取方法声明"""
        
        import re
        
        # 查找方法签名（从public到第一个{）
        match = re.search(r'(public\s+[^{]+)', method_implementation, re.DOTALL)
        if match:
            declaration = match.group(1).strip()
            # 确保以分号结尾
            if not declaration.endswith(';'):
                declaration += ';'
            return declaration
        
        return f"// TODO: 添加{method_implementation[:50]}..."
        
    def _enhance_service_with_requirements(self, service_code: str, template_vars: Dict[str, str],
                                         interface_name: str, special_requirements: Dict[str, Any],
                                         table_structure: Dict[str, Any], business_logic: str) -> str:
        
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
    
    def _extract_service_interface_methods(self, service_interface_code: str, interface_name: str) -> List[Dict[str, Any]]:
        """从Service接口代码中提取方法信息 - 增强版支持多行方法签名"""
        
        methods = []
        
        if not service_interface_code:
            logger.warning("⚠️ Service接口代码为空，使用默认方法")
            # 如果没有Service接口代码，返回默认方法
            methods.append({
                'name': f'query{interface_name}List',
                'return_type': f'{interface_name}Resp',
                'parameters': f'{interface_name}Req request',
                'description': f'查询{interface_name}列表'
            })
            return methods
        
        # 使用正则表达式提取方法定义
        import re
        logger.info(f"🔍 分析Service接口代码，提取方法定义...")
        
        # 🔧 改进的方法提取策略：多种模式组合
        
        # 模式1: 带注释的方法 (支持多行参数)
        commented_pattern = r'/\*\*.*?\*/\s*(\w+(?:<[^>]*>)?)\s+(\w+)\s*\(\s*(.*?)\s*\)\s*;'
        matches = re.findall(commented_pattern, service_interface_code, re.DOTALL)
        
        if not matches:
            # 模式2: 简单方法签名 (支持多行参数)
            simple_pattern = r'(\w+(?:<[^>]*>)?)\s+(\w+)\s*\(\s*(.*?)\s*\)\s*;'
            matches = re.findall(simple_pattern, service_interface_code, re.DOTALL)
        
        if not matches:
            # 模式3: 更宽松的匹配，处理复杂泛型
            loose_pattern = r'((?:List<\w+>|\w+(?:<[^>]*>)?)\s*)\s+(\w+)\s*\(\s*(.*?)\s*\)\s*;'
            matches = re.findall(loose_pattern, service_interface_code, re.DOTALL)
        
        logger.info(f"🔍 找到 {len(matches)} 个方法定义")
        
        for i, match in enumerate(matches):
            return_type, method_name, parameters = match
            
            # 🔧 清理参数字符串，移除多余的空白字符和换行
            cleaned_parameters = re.sub(r'\s+', ' ', parameters.strip())
            cleaned_return_type = re.sub(r'\s+', ' ', return_type.strip())
            
            method_info = {
                'name': method_name.strip(),
                'return_type': cleaned_return_type,
                'parameters': cleaned_parameters,
                'description': f'{method_name}方法'
            }
            methods.append(method_info)
            logger.info(f"  方法{i+1}: {method_name}({cleaned_parameters}) -> {cleaned_return_type}")
        
        # 🔧 增强的回退机制：如果仍然没有找到方法，尝试更细致的分析
        if not methods:
            logger.warning("⚠️ 常规方法提取失败，尝试逐行分析...")
            methods = self._extract_methods_line_by_line(service_interface_code, interface_name)
        
        # 最后的回退：从接口名推导
        if not methods:
            logger.warning("⚠️ 所有方法提取都失败，从接口名推导默认方法")
            # 根据接口名生成可能的方法名
            possible_method_names = [
                f'query{interface_name}List',
                f'get{interface_name}List', 
                f'{interface_name}',  # 直接使用接口名作为方法名
                f'list{interface_name}',
                f'search{interface_name}'
            ]
            
            for method_name in possible_method_names:
                methods.append({
                    'name': method_name,
                    'return_type': f'{interface_name}Resp',
                    'parameters': f'{interface_name}Req request',
                    'description': f'{method_name}方法'
                })
                logger.info(f"  推导方法: {method_name}")
        
        return methods
    
    def _extract_methods_line_by_line(self, service_interface_code: str, interface_name: str) -> List[Dict[str, Any]]:
        """逐行分析提取方法 - 处理复杂多行方法签名"""
        
        methods = []
        lines = service_interface_code.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳过注释、空行、包声明、类声明等
            if (not line or line.startswith('//') or line.startswith('/*') or 
                line.startswith('*') or line.startswith('package') or 
                line.startswith('import') or line.startswith('public interface') or
                line.startswith('public class') or line == '{' or line == '}'):
                i += 1
                continue
            
            # 检查是否是方法声明的开始
            # 寻找包含 '(' 的行，这通常是方法声明
            if '(' in line and not line.strip().startswith('//'):
                method_signature = line
                
                # 如果方法签名跨多行，继续读取
                while i < len(lines) - 1 and ';' not in method_signature:
                    i += 1
                    next_line = lines[i].strip()
                    if next_line:
                        method_signature += ' ' + next_line
                
                # 解析完整的方法签名
                method_info = self._parse_method_signature(method_signature)
                if method_info:
                    methods.append(method_info)
                    logger.info(f"  逐行提取方法: {method_info['name']}({method_info['parameters']}) -> {method_info['return_type']}")
            
            i += 1
        
        return methods
    
    def _parse_method_signature(self, signature: str) -> Dict[str, Any]:
        """解析单个方法签名"""
        
        import re
        
        # 移除多余空白和分号
        signature = re.sub(r'\s+', ' ', signature.strip().rstrip(';'))
        
        # 尝试匹配: [修饰符] 返回类型 方法名(参数)
        pattern = r'(?:public\s+|private\s+|protected\s+)?(.*?)\s+(\w+)\s*\((.*?)\)'
        match = re.search(pattern, signature)
        
        if match:
            return_type_part = match.group(1).strip()
            method_name = match.group(2).strip()
            parameters = match.group(3).strip()
            
            # 清理返回类型（移除可能的注解）
            return_type = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', return_type_part).strip()
            
            return {
                'name': method_name,
                'return_type': return_type,
                'parameters': parameters,
                'description': f'{method_name}方法'
            }
        
        return None
    
    def _extract_mapper_calls_from_service_impl(self, service_impl_code: str, interface_name: str) -> List[Dict[str, Any]]:
        """从ServiceImpl代码中提取Mapper方法调用"""
        
        calls = []
        
        if not service_impl_code:
            # 默认的Mapper方法调用
            calls.append({
                'method_name': 'selectByCondition',
                'parameters': f'{interface_name} condition',
                'return_type': f'List<{interface_name}>',
                'context': f'在query{interface_name}List方法中调用',
                'description': '根据条件查询记录列表'
            })
            return calls
        
        # 使用正则表达式提取Mapper方法调用
        import re
        
        # 查找类似 mapperName.methodName(params) 的调用
        mapper_call_pattern = r'(\w+[Mm]apper)\.(\w+)\s*\(([^)]*)\)'
        matches = re.findall(mapper_call_pattern, service_impl_code)
        
        for match in matches:
            mapper_name, method_name, parameters = match
            calls.append({
                'method_name': method_name,
                'parameters': self._infer_parameter_types(parameters, interface_name),
                'return_type': self._infer_return_type(method_name, interface_name),
                'context': f'在ServiceImpl中调用',
                'description': f'{method_name}方法调用'
            })
        
        # 如果没有找到调用，添加默认的
        if not calls:
            calls.append({
                'method_name': 'selectByCondition',
                'parameters': f'{interface_name} condition',
                'return_type': f'List<{interface_name}>',
                'context': 'ServiceImpl默认调用',
                'description': '根据条件查询记录列表'
            })
        
        return calls
    
    def _infer_parameter_types(self, parameters: str, interface_name: str) -> str:
        """推断参数类型"""
        if not parameters.strip():
            return f'@Param("condition") {interface_name} condition'
        
        # 简单的参数类型推断
        if 'condition' in parameters.lower():
            return f'@Param("condition") {interface_name} condition'
        elif 'id' in parameters.lower():
            return '@Param("id") Long id'
        else:
            return parameters
    
    def _infer_return_type(self, method_name: str, interface_name: str) -> str:
        """推断返回类型"""
        if 'list' in method_name.lower() or 'select' in method_name.lower():
            if 'by' in method_name.lower() and not 'list' in method_name.lower():
                return interface_name  # 单个对象
            return f'List<{interface_name}>'  # 列表
        elif 'count' in method_name.lower():
            return 'Integer'
        elif 'insert' in method_name.lower() or 'update' in method_name.lower() or 'delete' in method_name.lower():
            return 'Integer'
        else:
            return interface_name
    
    def _enhance_service_impl_with_specialized_prompt(self, template_code: str, interface_name: str,
                                                    input_params: List[Dict], output_params: Dict,
                                                    description: str, business_logic: str,
                                                    project_context: Dict[str, Any], 
                                                    special_requirements: Dict[str, Any]) -> str:
        """使用专门化提示词增强ServiceImpl代码"""
        
        try:
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # 设置Jinja2环境
            template_dir = os.path.join(os.path.dirname(__file__), '../langgraph/prompts')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # 加载Service实现提示词模板
            template = env.get_template('service_implementation_prompts.jinja2')
            
            # 从Service接口代码中提取方法信息（如果有的话）
            service_interface_methods = self._extract_service_interface_methods(
                project_context.get('service_interface_code', ''), interface_name
            )
            
            # 渲染提示词
            prompt = template.module.service_implementation_prompt(
                interface_name=interface_name,
                service_interface_methods=service_interface_methods,
                request_params=input_params,
                response_params=output_params,
                business_logic=business_logic,
                project_context=project_context
            )
            
            logger.info(f"🎯 使用专门化Service实现提示词，方法数: {len(service_interface_methods)}")
            
            # 调用LLM生成代码
            messages = [
                {"role": "system", "content": "你是Java ServiceImpl代码生成专家。根据要求生成完整的ServiceImpl实现类。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            
            if response:
                enhanced_code = self._extract_code_block(str(response))
                logger.info("✅ ServiceImpl专门化增强完成")
                return enhanced_code
            else:
                logger.warning("⚠️ ServiceImpl LLM响应为空，使用原始模板")
                return template_code
                
        except Exception as e:
            logger.error(f"❌ ServiceImpl专门化增强失败: {e}")
            return template_code
    
    def _enhance_mapper_with_specialized_prompt(self, template_code: str, interface_name: str,
                                              input_params: List[Dict], output_params: Dict,
                                              description: str, business_logic: str,
                                              project_context: Dict[str, Any], 
                                              special_requirements: Dict[str, Any]) -> str:
        """使用专门化提示词增强Mapper接口代码"""
        
        try:
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # 设置Jinja2环境
            template_dir = os.path.join(os.path.dirname(__file__), '../langgraph/prompts')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # 加载Mapper接口提示词模板
            template = env.get_template('mapper_interface_prompts.jinja2')
            
            # 从ServiceImpl代码中提取Mapper方法调用信息
            service_impl_mapper_calls = self._extract_mapper_calls_from_service_impl(
                project_context.get('service_impl_code', template_code), interface_name
            )
            
            # 渲染提示词
            prompt = template.module.mapper_interface_prompt(
                interface_name=interface_name,
                service_impl_mapper_calls=service_impl_mapper_calls,
                request_params=input_params,
                response_params=output_params,
                business_logic=business_logic,
                project_context=project_context
            )
            
            logger.info(f"🎯 使用专门化Mapper接口提示词，方法调用数: {len(service_impl_mapper_calls)}")
            
            # 调用LLM生成代码
            messages = [
                {"role": "system", "content": "你是MyBatis Mapper接口代码生成专家。根据ServiceImpl的调用需求生成完整的Mapper接口。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            if response:
                enhanced_code = self._extract_code_block(str(response))
                logger.info("✅ Mapper接口专门化增强完成")
                return enhanced_code
            else:
                logger.warning("⚠️ Mapper接口LLM响应为空，使用原始模板")
                return template_code
                
        except Exception as e:
            logger.error(f"❌ Mapper接口专门化增强失败: {e}")
            return template_code
    
    def _enhance_mapper_xml_with_specialized_prompt(self, template_code: str, interface_name: str,
                                                  input_params: List[Dict], output_params: Dict,
                                                  description: str, business_logic: str,
                                                  project_context: Dict[str, Any], 
                                                  table_structure: Dict[str, Any]) -> str:
        """使用专门化提示词增强Mapper XML代码"""
        
        try:
            from jinja2 import Environment, FileSystemLoader
            import os
            
            # 设置Jinja2环境
            template_dir = os.path.join(os.path.dirname(__file__), '../langgraph/prompts')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # 加载Mapper XML提示词模板
            template = env.get_template('mapper_xml_prompts.jinja2')
            
            # 从Mapper接口代码中提取方法信息
            mapper_methods = self._extract_mapper_methods_from_interface(
                project_context.get('mapper_code', template_code), interface_name
            )
            
            # 从Entity或表结构中提取字段信息
            entity_fields = self._extract_entity_fields(
                project_context.get('entity_code', ''), table_structure, interface_name
            )
            
            # 确定表名
            table_name = table_structure.get('table_name', f't_{interface_name.lower()}')
            
            # 渲染提示词
            prompt = template.module.mapper_xml_prompt(
                interface_name=interface_name,
                mapper_methods=mapper_methods,
                entity_fields=entity_fields,
                table_name=table_name,
                project_context=project_context
            )
            
            logger.info(f"🎯 使用专门化Mapper XML提示词，方法数: {len(mapper_methods)}, 字段数: {len(entity_fields)}")
            
            # 调用LLM生成代码
            messages = [
                {"role": "system", "content": "你是MyBatis XML映射文件生成专家。根据Mapper接口生成完整的XML配置文件。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=3000
            )
            
            if response:
                enhanced_code = self._extract_code_block(str(response))
                logger.info("✅ Mapper XML专门化增强完成")
                return enhanced_code
            else:
                logger.warning("⚠️ Mapper XML LLM响应为空，使用原始模板")
                return template_code
                
        except Exception as e:
            logger.error(f"❌ Mapper XML专门化增强失败: {e}")
            return template_code
    
    def _extract_mapper_methods_from_interface(self, mapper_code: str, interface_name: str) -> List[Dict[str, Any]]:
        """从Mapper接口代码中提取方法信息"""
        
        methods = []
        
        if not mapper_code:
            # 默认方法
            methods.extend([
                {
                    'name': 'selectByCondition',
                    'return_type': f'List<{interface_name}>',
                    'parameters': f'@Param("condition") {interface_name} condition',
                    'sql_type': 'SELECT',
                    'description': '根据条件查询'
                },
                {
                    'name': 'selectByPrimaryKey',
                    'return_type': interface_name,
                    'parameters': '@Param("id") Long id',
                    'sql_type': 'SELECT',
                    'description': '根据主键查询'
                }
            ])
            return methods
        
        # 从代码中提取方法
        import re
        method_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*;'
        matches = re.findall(method_pattern, mapper_code)
        
        for match in matches:
            return_type, method_name, parameters = match
            methods.append({
                'name': method_name,
                'return_type': return_type,
                'parameters': parameters.strip(),
                'sql_type': self._infer_sql_type(method_name),
                'description': f'{method_name}方法'
            })
        
        return methods
    
    def _extract_entity_fields(self, entity_code: str, table_structure: Dict[str, Any], interface_name: str) -> List[Dict[str, Any]]:
        """提取实体字段信息"""
        
        fields = []
        
        # 如果有表结构信息，优先使用
        if table_structure.get('has_table_definition') and table_structure.get('columns'):
            for column in table_structure['columns']:
                fields.append({
                    'java_name': self._snake_to_camel(column['name']),
                    'java_type': self._sql_type_to_java_type(column['type']),
                    'column_name': column['name'],
                    'jdbc_type': self._sql_type_to_jdbc_type(column['type'])
                })
        else:
            # 默认字段
            default_fields = [
                {'java_name': 'id', 'java_type': 'Long', 'column_name': 'id', 'jdbc_type': 'BIGINT'},
                {'java_name': 'name', 'java_type': 'String', 'column_name': 'name', 'jdbc_type': 'VARCHAR'},
                {'java_name': 'status', 'java_type': 'String', 'column_name': 'status', 'jdbc_type': 'VARCHAR'},
                {'java_name': 'createTime', 'java_type': 'LocalDateTime', 'column_name': 'create_time', 'jdbc_type': 'TIMESTAMP'},
                {'java_name': 'updateTime', 'java_type': 'LocalDateTime', 'column_name': 'update_time', 'jdbc_type': 'TIMESTAMP'}
            ]
            fields.extend(default_fields)
        
        return fields
    
    def _infer_sql_type(self, method_name: str) -> str:
        """推断SQL类型"""
        method_lower = method_name.lower()
        if method_lower.startswith('select') or method_lower.startswith('get') or method_lower.startswith('find'):
            return 'SELECT'
        elif method_lower.startswith('insert') or method_lower.startswith('add'):
            return 'INSERT'
        elif method_lower.startswith('update') or method_lower.startswith('modify'):
            return 'UPDATE'
        elif method_lower.startswith('delete') or method_lower.startswith('remove'):
            return 'DELETE'
        else:
            return 'SELECT'
    
    def _sql_type_to_java_type(self, sql_type: str) -> str:
        """SQL类型转Java类型"""
        sql_type_lower = sql_type.lower()
        if 'int' in sql_type_lower or 'bigint' in sql_type_lower:
            return 'Long' if 'bigint' in sql_type_lower else 'Integer'
        elif 'varchar' in sql_type_lower or 'text' in sql_type_lower or 'char' in sql_type_lower:
            return 'String'
        elif 'decimal' in sql_type_lower or 'numeric' in sql_type_lower:
            return 'BigDecimal'
        elif 'datetime' in sql_type_lower or 'timestamp' in sql_type_lower:
            return 'LocalDateTime'
        elif 'date' in sql_type_lower:
            return 'LocalDate'
        elif 'time' in sql_type_lower:
            return 'LocalTime'
        elif 'bit' in sql_type_lower or 'boolean' in sql_type_lower:
            return 'Boolean'
        else:
            return 'String'
    
    def _sql_type_to_jdbc_type(self, sql_type: str) -> str:
        """SQL类型转JDBC类型"""
        sql_type_lower = sql_type.lower()
        if 'bigint' in sql_type_lower:
            return 'BIGINT'
        elif 'int' in sql_type_lower:
            return 'INTEGER'
        elif 'varchar' in sql_type_lower or 'char' in sql_type_lower:
            return 'VARCHAR'
        elif 'text' in sql_type_lower:
            return 'LONGVARCHAR'
        elif 'decimal' in sql_type_lower or 'numeric' in sql_type_lower:
            return 'DECIMAL'
        elif 'datetime' in sql_type_lower or 'timestamp' in sql_type_lower:
            return 'TIMESTAMP'
        elif 'date' in sql_type_lower:
            return 'DATE'
        elif 'time' in sql_type_lower:
            return 'TIME'
        elif 'bit' in sql_type_lower or 'boolean' in sql_type_lower:
            return 'BOOLEAN'
        else:
            return 'VARCHAR'
    
    def _snake_to_camel(self, snake_str: str) -> str:
        """下划线转驼峰命名"""
        if not snake_str:
            return snake_str
        
        components = snake_str.split('_')
        return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    def _enhance_single_template_with_requirements(self, code_type: str, template_code: str, 
                                                 template_vars: Dict[str, str],
                                                 interface_name: str, input_params: List[Dict], 
                                                 output_params: Dict, description: str, 
                                                 business_logic: str, project_context: Dict[str, Any],
                                                 special_requirements: Dict[str, Any], 
                                                 table_structure: Dict[str, Any]) -> str:
        """使用特殊要求增强单个模板"""
        
        try:
            # 调用父类的方法进行基础增强
            enhanced_code = self._enhance_single_template(
                code_type, template_code, template_vars,
                interface_name, input_params, output_params, 
                description, business_logic, project_context
            )
            
            # 添加特殊要求处理
            if special_requirements.get('use_pagehelper') and 'service_impl' in code_type.lower():
                enhanced_code = enhanced_code.replace(
                    'TODO: 实现业务逻辑',
                    'TODO: 实现业务逻辑 - 使用PageHelper分页'
                )
            
            return enhanced_code
            
        except Exception as e:
            logger.error(f"❌ {code_type} 特殊要求增强失败: {e}")
            return template_code