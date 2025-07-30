"""
设计文档生成器
基于业务需求分析结果，生成标准化的技术设计文档
遵循单一职责原则，专注于设计文档生成
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
from .base_service import BaseAnalysisService


class DesignDocumentGenerator(BaseAnalysisService):
    """设计文档生成器"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.template_loader = self._init_template_loader()
        
    def _init_template_loader(self):
        """初始化Jinja2模板加载器"""
        # 获取prompts目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(current_dir, 'prompts')
        
        if os.path.exists(prompts_dir):
            return Environment(loader=FileSystemLoader(prompts_dir))
        else:
            self.logger.warning(f"Prompts目录不存在: {prompts_dir}")
            return None
    
    def generate_design_document(self, task_id: str, business_requirements: Dict, 
                                     content_analysis: Dict, parsing_result: Dict) -> Dict[str, Any]:
        """
        生成设计文档
        
        Args:
            task_id: 任务ID
            business_requirements: 业务需求分析结果
            content_analysis: 内容分析结果  
            parsing_result: 文档解析结果
            
        Returns:
            设计文档生成结果
        """
        start_time = time.time()
        
        try:
            self._log_analysis_start(task_id, "设计文档生成", 0)
            
            # Step 1: 生成设计文档数据结构
            design_data =  self._generate_design_data(
                business_requirements, content_analysis, parsing_result
            )
            
            # Step 2: 使用模板生成最终文档
            design_document =  self._render_design_document(design_data)
            
            # Step 3: 生成补充的架构图 ----当前版本不生成架构图
            # architecture_diagram =  self._generate_architecture_diagram(design_data)
            
            # Step 4: 生成表单数据结构
            form_data =  self._generate_form_data(design_data, content_analysis, parsing_result)
            
            result = {
                "markdown_content": design_document,
                "design_data": design_data,
                # "architecture_diagram": architecture_diagram,
                "form_data": form_data,
                "design_document_metadata": {
                    "generation_timestamp": datetime.now().isoformat(),
                    "template_version": "combined_document_demo_v1.0",
                    "generator": "DesignDocumentGenerator"
                }
            }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "设计文档生成", duration, len(str(result)))
            
            return self._create_response(
                success=True,
                data=result,
                metadata={"generation_duration": duration}
            )
            
        except Exception as e:
            self._log_error(task_id, "设计文档生成", e)
            return self._create_response(
                success=False,
                error=f"设计文档生成失败: {str(e)}"
            )
    
    def _generate_design_data(self, business_requirements: Dict, 
                                  content_analysis: Dict, parsing_result: Dict) -> Dict:
        """生成设计文档的数据结构"""
        
        if not self.template_loader:
            raise Exception("模板加载器未初始化")
        
        # 简单返回传入的数据，不再使用LLM生成JSON
        return {
            "project_name": "业务系统优化",
            "version": "V0.1",
            "content_analysis": content_analysis,
            "parsing_result": parsing_result,
            "business_requirements": business_requirements
        }
    
    def _render_design_document(self, design_data: Dict) -> str:
        """使用标准提示词生成设计文档"""
        
        if not self.template_loader:
            raise Exception("模板加载器未初始化")
        
        try:
            # 加载标准设计文档提示词模板
            prompt_template = self.template_loader.get_template('standard_design_document_prompts.jinja2')
            
            # 提取数据
            content_analysis = design_data.get("content_analysis", {})
            parsing_result = design_data.get("parsing_result", {})
            
            # 生成系统提示词
            system_prompt = prompt_template.module.system_prompt_standard_design()
            
            # 生成用户提示词
            user_prompt = prompt_template.module.user_prompt_standard_design(
                content_analysis, parsing_result
            )
            
            # 调用LLM生成标准格式文档
            markdown_document = self._call_llm_with_retry(user_prompt, system_prompt)
            
            if not markdown_document or len(markdown_document.strip()) < 100:
                raise Exception("生成的文档内容过短或为空")
                
            return markdown_document.strip()
            
        except Exception as e:
            self.logger.error(f"标准文档生成失败: {e}")
            raise
    
    def _generate_architecture_diagram(self, design_data: Dict) -> Dict:
        """生成架构图数据"""
        
        services = design_data.get("services", [])
        databases = design_data.get("databases", [])
        
        # 生成Mermaid格式的架构图
        mermaid_syntax = self._build_mermaid_diagram(services, databases)
        
        return {
            "type": "mermaid",
            "syntax": mermaid_syntax,
            "components": {
                "services": [{"name": s.get("name"), "type": "service"} for s in services],
                "databases": [{"name": d.get("name"), "type": "database"} for d in databases]
            }
        }
    
    def _generate_form_data(self, design_data: Dict, content_analysis: Dict, parsing_result: Dict) -> Dict:
        """生成符合表单模板的结构化数据"""
        try:
            # 从content_analysis和parsing_result中提取关键信息
            content_summary = content_analysis.get("data", {}).get("summary", "")
            crud_operations = content_analysis.get("data", {}).get("crud_analysis", {}).get("operations", [])
            document_content = parsing_result.get("text_content", "")
            
            # 提取项目名称
            project_name = self._extract_project_name(document_content)
            
            # 构建表单数据结构
            form_data = {
                "project_name": project_name,
                "project_info": self._generate_project_info(document_content, content_summary, crud_operations),
                "function_requirements_info": self._generate_function_requirements(crud_operations, content_summary, document_content),
                "project_architecture": self._generate_project_architecture(design_data, content_summary, document_content),
                "service_numbers": self._count_services(design_data),
                "service_info": self._generate_service_info(design_data, crud_operations),
                "data_resources": self._count_data_resources(design_data),
                "data_info": self._generate_data_info(design_data),
                "technology": self._generate_technology_stack(design_data),
                "service_details": self._generate_service_details(design_data, crud_operations, content_summary, document_content),
                "execution": self._generate_execution_requirements(design_data)
            }
            
            return form_data
            
        except Exception as e:
            self.logger.error(f"生成表单数据失败: {e}")
            # 返回基础表单数据结构
            return self._get_default_form_data()
    
    def _extract_project_name(self, document_content: str) -> str:
        """从文档内容中提取项目名称"""
        lines = document_content.split('\n')
        for line in lines[:10]:  # 检查前10行
            if any(keyword in line for keyword in ['项目', '需求', '系统', '平台']):
                # 提取可能的项目名称
                if '需求文档' in line:
                    project_name = line.replace('需求文档', '').strip()
                    if project_name:
                        return project_name
                elif '设计文档' in line:
                    project_name = line.replace('设计文档', '').strip()
                    if project_name:
                        return project_name
        return "业务系统优化项目"
    
    def _generate_project_info(self, document_content: str, content_summary: str, crud_operations: list) -> str:
        """LLM生成项目介绍信息"""
        try:
            prompt = f"""
基于以下业务文档内容，生成简洁专业的项目介绍信息：

文档内容摘要：
{content_summary}

主要业务操作：
{', '.join([f"{op.get('type', '')}: {op.get('description', '')}" for op in crud_operations])}

文档原文（前1000字）：
{document_content[:1000]}

要求：
1. 生成100-200字的项目介绍
2. 包含项目背景、建设目标、核心价值
3. 语言简洁专业，符合技术文档规范
4. 避免空泛描述，体现具体业务场景

请只返回项目介绍内容，不要包含其他解释文字。
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                project_info = response.strip()
                return project_info
            else:
                return content_summary[:300] if content_summary else "项目旨在优化现有业务系统，提升用户体验和系统性能。"
                
        except Exception as e:
            self.logger.error(f"LLM生成项目介绍失败: {e}")
            return content_summary[:300] if content_summary else "项目旨在优化现有业务系统，提升用户体验和系统性能。"
    
    def _generate_function_requirements(self, crud_operations: list, content_summary: str, document_content: str) -> Dict:
        """LLM生成功能需求信息"""
        try:
            prompt = f"""
基于以下业务文档内容，生成详细的功能需求信息：

文档内容摘要：
{content_summary}

主要业务操作：
{', '.join([f"{op.get('type', '')}: {op.get('description', '')}" for op in crud_operations])}

文档原文（前1500字）：
{document_content[:1500]}

请生成以下功能需求信息，返回JSON格式：
{{
    "adjust_info": "详细的功能调整说明，包含具体调整点和优化方向，100-200字",
    "filter_field": "详细的筛选查询功能说明，包含具体筛选条件，50-100字",
    "list_field": "详细的列表展示字段说明，包含关键业务字段，50-100字", 
    "total_field": "详细的统计汇总字段说明，包含关键指标字段，50-100字",
    "remarks": "功能需求的整体备注说明，包含实现要点和注意事项，100-150字"
}}

要求：
1. 基于实际业务文档内容生成
2. 内容具体详细，避免空泛描述
3. 符合实际项目开发需求
4. 体现具体的业务场景和功能点

请只返回JSON内容，不要包含其他解释文字。
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                try:
                    import json
                    result_text = response.strip()
                    # 清理可能的markdown格式
                    if result_text.startswith('```json'):
                        result_text = result_text.replace('```json', '').replace('```', '').strip()
                    elif result_text.startswith('```'):
                        result_text = result_text.replace('```', '').strip()
                    
                    function_requirements = json.loads(result_text)
                    return function_requirements
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析LLM返回的JSON失败: {e}")
                    return self._get_default_function_requirements(crud_operations, content_summary)
            else:
                return self._get_default_function_requirements(crud_operations, content_summary)
                
        except Exception as e:
            self.logger.error(f"LLM生成功能需求失败: {e}")
            return self._get_default_function_requirements(crud_operations, content_summary)
    
    def _get_default_function_requirements(self, crud_operations: list, content_summary: str) -> Dict:
        """获取默认功能需求信息"""
        # 基于CRUD操作生成功能需求描述
        adjust_info = []
        if crud_operations:
            for op in crud_operations:
                op_type = op.get("type", "")
                op_desc = op.get("description", "")
                if op_type == "CREATE":
                    adjust_info.append(f"- 新增{op_desc}功能")
                elif op_type == "UPDATE":
                    adjust_info.append(f"- 调整{op_desc}功能")
                elif op_type == "READ":
                    adjust_info.append(f"- 查询{op_desc}功能")
                elif op_type == "DELETE":
                    adjust_info.append(f"- 删除{op_desc}功能")
        
        return {
            "adjust_info": '\n'.join(adjust_info) if adjust_info else content_summary[:500],
            "filter_field": "支持按条件筛选查询",
            "list_field": "列表展示相关数据字段",
            "total_field": "统计汇总相关字段",
            "remarks": "按照业务需求进行功能调整和优化"
        }
    
    def _generate_project_architecture(self, design_data: Dict, content_summary: str, document_content: str) -> str:
        """LLM生成项目架构描述"""
        try:
            prompt = f"""
基于以下业务文档内容，生成详细的项目架构设计描述：

文档内容摘要：
{content_summary}

文档原文（前1500字）：
{document_content[:1500]}

设计数据参考：
{str(design_data)[:500]}

请生成项目架构描述，要求：
1. 200-300字的架构描述
2. 包含架构模式选择（如微服务、单体、分层等）
3. 包含关键技术组件（数据库、缓存、消息队列等）
4. 说明架构的核心特点（高可用、可扩展、安全性等）
5. 体现具体业务场景和技术选型理由
6. 语言专业、条理清晰

请只返回架构描述内容，不要包含其他解释文字。
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                architecture = response.strip()
                return architecture
            else:
                return self._get_default_project_architecture(design_data)
                
        except Exception as e:
            self.logger.error(f"LLM生成项目架构失败: {e}")
            return self._get_default_project_architecture(design_data)
    
    def _get_default_project_architecture(self, design_data: Dict) -> str:
        """获取默认项目架构描述"""
        tech_stack = design_data.get("tech_stack", {})
        backend_framework = tech_stack.get("后端框架", "Spring Boot + Spring Cloud")
        database = tech_stack.get("数据库", "MySQL")
        cache = tech_stack.get("缓存", "Redis")
        
        return f"采用{backend_framework}微服务架构，使用{database}作为主数据库，{cache}作为缓存层，确保系统的高可用性和可扩展性。"
    
    def _count_services(self, design_data: Dict) -> int:
        """统计服务数量"""
        services = design_data.get("services", [])
        return max(len(services), 2)  # 至少2个服务
    
    def _generate_service_info(self, design_data: Dict, crud_operations: list) -> list:
        """生成服务信息"""
        services = design_data.get("services", [])
        service_info = []
        
        if services:
            for service in services:
                service_info.append({
                    "service_name": service.get("name", "业务服务"),
                    "service_english_name": service.get("english_name", "business-service")
                })
        else:
            # 基于CRUD操作推断服务
            if any(op.get("type") == "CREATE" for op in crud_operations):
                service_info.append({
                    "service_name": "用户服务",
                    "service_english_name": "user-center-service"
                })
            service_info.append({
                "service_name": "业务服务",
                "service_english_name": "business-service"
            })
        
        return service_info
    
    def _count_data_resources(self, design_data: Dict) -> int:
        """统计数据资源数量"""
        databases = design_data.get("databases", [])
        return max(len(databases), 2)  # 至少2个数据资源（MySQL + Redis）
    
    def _generate_data_info(self, design_data: Dict) -> list:
        """生成数据库信息"""
        databases = design_data.get("databases", [])
        data_info = []
        
        for db in databases:
            db_type = db.get("type", "MySQL").lower()
            data_info.append({
                "data_type": db_type
            })
        
        if not data_info:
            data_info = [
                {"data_type": "mysql"},
                {"data_type": "redis"}
            ]
        
        return data_info
    
    def _generate_technology_stack(self, design_data: Dict) -> Dict:
        """生成技术栈信息"""
        return design_data.get("tech_stack", self._get_default_tech_stack())
    
    def _generate_table_sql(self, service_name: str, crud_operations: list, content_summary: str) -> str:
        """AI生成数据库表SQL"""
        try:
            # 构建提示词
            prompt = f"""
基于以下业务需求，为{service_name}生成对应的MySQL数据库表结构（CREATE TABLE语句）：

业务背景：
{content_summary}

CRUD操作需求：
{', '.join([f"{op.get('type', '')}: {op.get('description', '')}" for op in crud_operations])}

要求：
1. 生成完整的CREATE TABLE语句
2. 包含合理的字段类型、长度、约束
3. 添加适当的索引
4. 使用utf8mb4字符集
5. 包含id主键、创建时间、更新时间等通用字段
6. 字段要有中文注释

请只返回SQL语句，不要包含其他解释文字。
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                sql_content = response.strip()
                # 清理可能的markdown格式
                if sql_content.startswith('```sql'):
                    sql_content = sql_content.replace('```sql', '').replace('```', '').strip()
                elif sql_content.startswith('```'):
                    sql_content = sql_content.replace('```', '').strip()
                
                return sql_content
            else:
                return f"-- {service_name}相关数据表SQL（需要根据具体业务需求设计表结构）"
                
        except Exception as e:
            self.logger.error(f"AI生成SQL失败: {e}")
            return f"-- {service_name}相关数据表SQL（AI生成失败，需要手动设计）"

    def _generate_api_design(self, service_type: str, crud_operations: list, content_summary: str, document_content: str) -> list:
        """LLM生成API接口设计"""
        try:
            prompt = f"""
基于以下业务文档内容，为{service_type}生成详细的API接口设计：

文档内容摘要：
{content_summary}

主要业务操作：
{', '.join([f"{op.get('type', '')}: {op.get('description', '')}" for op in crud_operations])}

文档原文（前1500字）：
{document_content[:1500]}

请为{service_type}生成API接口设计，返回JSON数组格式：
[
  {{
    "interface_type": "接口类型（新增/查询/修改/删除）",
    "uri": "具体的API路径，如/api/user/create",
    "method": "HTTP方法（GET/POST/PUT/DELETE）",
    "description": "详细的接口功能描述，50-100字",
    "request_params": "详细的请求参数JSON结构，包含具体字段和类型",
    "response_params": "详细的响应参数JSON结构，包含具体字段和类型",
    "special_requirements": "特殊要求说明，包含验证、权限、性能等要求，50-100字"
  }}
]

要求：
1. 基于实际业务文档内容生成
2. API路径要具体、符合RESTful规范
3. 请求/响应参数要详细、真实，包含具体的业务字段
4. 接口描述要准确反映业务功能
5. 生成2-4个核心API接口
6. 特殊要求要考虑实际开发场景

请只返回JSON数组内容，不要包含其他解释文字。
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                try:
                    import json
                    result_text = response.strip()
                    # 清理可能的markdown格式
                    if result_text.startswith('```json'):
                        result_text = result_text.replace('```json', '').replace('```', '').strip()
                    elif result_text.startswith('```'):
                        result_text = result_text.replace('```', '').strip()
                    
                    api_designs = json.loads(result_text)
                    return api_designs if isinstance(api_designs, list) else [api_designs]
                except json.JSONDecodeError as e:
                    self.logger.error(f"解析LLM返回的API设计JSON失败: {e}")
                    return self._get_default_api_design(service_type, crud_operations)
            else:
                return self._get_default_api_design(service_type, crud_operations)
                
        except Exception as e:
            self.logger.error(f"LLM生成API设计失败: {e}")
            return self._get_default_api_design(service_type, crud_operations)
    
    def _get_default_api_design(self, service_type: str, crud_operations: list) -> list:
        """获取默认API设计"""
        apis = []
        for op in crud_operations:
            op_type = op.get("type", "")
            op_desc = op.get("description", "")
            
            if op_type == "CREATE" and service_type == "用户":
                apis.append({
                    "interface_type": "新增",
                    "uri": "/api/user/create",
                    "method": "POST",
                    "description": f"新增{op_desc}",
                    "request_params": "{}",
                    "response_params": "{}",
                    "special_requirements": "数据校验和权限控制"
                })
            elif op_type == "READ" and service_type == "业务":
                apis.append({
                    "interface_type": "查询",
                    "uri": "/api/business/query",
                    "method": "GET",
                    "description": f"查询{op_desc}",
                    "request_params": "{}",
                    "response_params": "{}",
                    "special_requirements": "分页查询和缓存优化"
                })
        
        return apis if apis else [{
            "interface_type": "查询",
            "uri": f"/api/{service_type.lower()}/list",
            "method": "GET",
            "description": f"{service_type}数据查询",
            "request_params": "{}",
            "response_params": "{}",
            "special_requirements": "基础CRUD操作"
        }]

    def _generate_service_details(self, design_data: Dict, crud_operations: list, content_summary: str = "", document_content: str = "") -> list:
        """生成详细服务设计"""
        service_details = []
        
        # 为用户服务生成SQL和API
        user_sql = self._generate_table_sql("用户管理", crud_operations, content_summary)
        user_apis = self._generate_api_design("用户", crud_operations, content_summary, document_content)
        
        # 为业务服务生成SQL和API
        business_sql = self._generate_table_sql("业务数据", crud_operations, content_summary)
        business_apis = self._generate_api_design("业务", crud_operations, content_summary, document_content)
        
        # 为API设计添加SQL信息
        for api in user_apis:
            api["data_table_sql"] = user_sql
            api["dependence_service"] = ["auth-service"]
            
        for api in business_apis:
            api["data_table_sql"] = business_sql
            api["dependence_service"] = ["user-service"]
        
        # 用户服务
        service_details.append({
            "service_name": "用户服务",
            "service_english_name": "user-center-service",
            "service_duty": "用户管理、权限控制、角色管理",
            "core_modules": "- 用户注册模块\n- 权限管理模块\n- 角色管理模块",
            "API设计": user_apis if user_apis else [{
                "interface_type": "新增",
                "uri": "/api/user/create",
                "method": "POST",
                "description": "用户注册",
                "request_params": "{}",
                "response_params": "{}",
                "data_table_sql": user_sql,
                "dependence_service": ["auth-service"],
                "special_requirements": "密码加密和手机验证"
            }]
        })
        
        # 业务服务
        service_details.append({
            "service_name": "业务服务",
            "service_english_name": "business-service",
            "service_duty": "核心业务逻辑处理",
            "core_modules": "- 业务数据模块\n- 业务流程模块",
            "API设计": business_apis if business_apis else [{
                "interface_type": "查询",
                "uri": "/api/business/query",
                "method": "GET",
                "description": "业务数据查询",
                "request_params": "{}",
                "response_params": "{}",
                "data_table_sql": business_sql,
                "dependence_service": ["user-service"],
                "special_requirements": "数据权限控制"
            }]
        })
        
        return service_details
    
    def _generate_execution_requirements(self, design_data: Dict) -> Dict:
        """生成执行要求"""
        services = design_data.get("services", [])
        databases = design_data.get("databases", [])
        
        return {
            "service_scope": "本次没有新增服务，服务范围为：",
            "services": services,
            "data_scope": "本次没有新增数据库，数据库范围为：",
            "databases": databases,
            "scope_interface": "本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。"
        }
    
    def _get_default_form_data(self) -> Dict:
        """获取默认表单数据"""
        return {
            "project_name": "业务系统优化项目",
            "project_info": "项目旨在优化现有业务系统，提升用户体验和系统性能。",
            "function_requirements_info": {
                "adjust_info": "根据业务需求进行系统功能调整和优化",
                "filter_field": "支持按条件筛选查询",
                "list_field": "列表展示相关数据字段",
                "total_field": "统计汇总相关字段",
                "remarks": "按照业务需求进行功能调整和优化"
            },
            "project_architecture": "采用Spring Boot + Spring Cloud微服务架构，使用MySQL作为主数据库，Redis作为缓存层。",
            "service_numbers": 2,
            "service_info": [
                {"service_name": "用户服务", "service_english_name": "user-center-service"},
                {"service_name": "业务服务", "service_english_name": "business-service"}
            ],
            "data_resources": 2,
            "data_info": [
                {"data_type": "mysql"},
                {"data_type": "redis"}
            ],
            "technology": self._get_default_tech_stack(),
            "service_details": [],
            "execution": {
                "service_scope": "本次没有新增服务，服务范围为：",
                "services": [],
                "data_scope": "本次没有新增数据库，数据库范围为：",
                "databases": [],
                "scope_interface": "本次新增接口，已经按服务范围进行划分，详见设计文档2服务设计部分。"
            }
        }

    def _build_mermaid_diagram(self, services: list, databases: list) -> str:
        """构建Mermaid格式架构图"""
        
        lines = ["graph TD"]
        
        # 添加前端节点
        lines.append('    Frontend["前端(Vue2)"]')
        
        # 添加网关节点
        lines.append('    Gateway["API网关"]')
        
        # 添加服务节点
        for i, service in enumerate(services):
            service_id = f"Service{i+1}"
            service_name = service.get("name", f"服务{i+1}")
            lines.append(f'    {service_id}["{service_name}"]')
        
        # 添加数据库节点
        for i, db in enumerate(databases):
            db_id = f"DB{i+1}"
            db_name = db.get("name", f"数据库{i+1}")
            db_type = db.get("type", "Database")
            lines.append(f'    {db_id}[("{db_name}<br/>{db_type}")]')
        
        # 添加连接关系
        lines.append('    Frontend --> Gateway')
        
        for i, service in enumerate(services):
            service_id = f"Service{i+1}"
            lines.append(f'    Gateway --> {service_id}')
            
            # 服务连接到数据库
            for j, db in enumerate(databases):
                db_id = f"DB{j+1}"
                lines.append(f'    {service_id} --> {db_id}')
        
        return '\n'.join(lines)
    
    def _validate_and_enhance_design_data(self, design_data: Dict, business_requirements: Dict) -> Dict:
        """验证并增强设计数据"""
        
        # 确保必要字段存在
        if "project_name" not in design_data:
            # 从业务需求中推断项目名称
            functional_reqs = business_requirements.get("functional_requirements", [])
            if functional_reqs:
                first_req = functional_reqs[0]
                design_data["project_name"] = first_req.get("name", "业务需求优化")
            else:
                design_data["project_name"] = "业务系统优化"
        
        # 确保技术栈完整
        if "tech_stack" not in design_data or not design_data["tech_stack"]:
            design_data["tech_stack"] = self._get_default_tech_stack()
        
        # 确保服务列表存在
        if "services" not in design_data:
            design_data["services"] = []
        
        # 确保数据库列表存在  
        if "databases" not in design_data:
            design_data["databases"] = self._get_default_databases()
        
        # 根据业务需求补充功能需求
        design_data["functional_requirements"] = business_requirements.get("functional_requirements", [])
        
        return design_data
    
    def _get_default_tech_stack(self) -> Dict[str, str]:
        """获取默认技术栈"""
        return {
            "后端框架": "Spring Boot 2.7.x + Spring Cloud 2021.x",
            "数据访问": "MyBatis Plus 3.5.x", 
            "数据库": "MySQL 8.0",
            "缓存": "Redis 6.0",
            "分布式锁": "redisson",
            "消息队列": "Apache RocketMQ",
            "服务发现": "Nacos",
            "配置中心": "Nacos",
            "后端分页": "pageHelper",
            "调度框架": "XXL-JOB",
            "Excel处理": "Alibaba EasyExcel",
            "日志和监控": "SLF4J",
            "注解和工具": "Lombok",
            "部署": "将代码提交到git分支即可",
            "开发语言版本": "java 1.8"
        }
    
    def _get_default_databases(self) -> list:
        """获取默认数据库配置"""
        return [
            {
                "name": "用户数据库",
                "type": "MySQL",
                "config": {
                    "url": "jdbc:mysql://localhost:6446/dbwebappdb?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&characterEncoding=utf8&useUnicode=true",
                    "username": "dbwebapp", 
                    "password": "dbwebapp",
                    "driver-class-name": "com.mysql.cj.jdbc.Driver"
                }
            },
            {
                "name": "缓存",
                "type": "Redis",
                "config": {
                    "host": "localhost",
                    "port": "6379",
                    "db": "0", 
                    "password": "''"
                }
            }
        ]
    
   
    
    def _call_llm_with_retry(self, prompt: str, system_prompt: str, max_retries: int = 3) -> str:
        """带重试机制的LLM调用"""
        
        for attempt in range(max_retries):
            try:
                response = self._call_llm(prompt, system_prompt)
                if response:
                    return response
            except Exception as e:
                self.logger.warning(f"LLM调用失败，尝试 {attempt + 1}/{max_retries}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
        
        raise Exception("LLM调用失败，已达最大重试次数")

    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 16000) -> Optional[str]:
        """调用LLM进行分析"""
        if not self.llm_client:
            raise ValueError("LLM客户端未初始化")
        
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt or "你是一个专业的技术架构师"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            self.logger.error(f"LLM调用失败: {str(e)}")
            return None

    def _parse_json_response(self, response: str, step_name: str) -> Dict:
        """解析JSON响应，包含错误处理"""
        try:
            # 尝试提取JSON部分
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"{step_name}JSON解析失败: {str(e)}")
            return {
                "error": f"JSON解析失败: {str(e)}",
                "raw_response": response,
                "step": step_name
            }

    def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """实现基类的抽象方法 - 暂时为空实现"""
        pass