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
from .core_business_generator import CoreBusinessGenerator
from .config.company_services_config import get_company_services_config


class DesignDocumentGenerator(BaseAnalysisService):
    """设计文档生成器"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.template_loader = self._init_template_loader()
        # 初始化核心业务生成器
        self.core_business_generator = CoreBusinessGenerator(llm_client, vector_db)
        
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
            
            
            self.logger.info(f"parsing_result: {parsing_result}")
            self.logger.info(f"content_analysis: {content_analysis}")
            
            
            # 生成表单数据结构
            form_data =  self._generate_form_data(content_analysis, parsing_result)
            
            result = {
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
    
   
    
    def _generate_form_data(self, content_analysis: Dict, parsing_result: Dict) -> Dict:
        """生成符合表单模板的结构化数据（调整后的版本）"""
        try:
            # 从content_analysis和parsing_result中提取关键信息
            content_summary = content_analysis.get("data", {}).get("summary", "")
            # 从parsing_result中提取文档内容 - 修正字段路径
            document_content = parsing_result.get("text_content", "")
            if not document_content:
                # 尝试从其他可能的字段路径获取文档内容
                document_structure = parsing_result.get("data", {}).get("documentStructure", {})
                content_summary_data = document_structure.get("contentSummary", {})
                abstract = content_summary_data.get("abstract", "")
                if abstract:
                    document_content = abstract
                else:
                    # 如果仍然没有内容，使用parsing_result的整体信息
                    document_content = str(parsing_result)[:2000]  # 截取前2000字符
            
            self.logger.info(f"提取到文档摘要长度: {len(content_summary)}, 文档内容长度: {len(document_content)}")
            self.logger.info(f"文档内容前2000字符: {document_content[:2000]}")
            
            
            # 提取项目名称（从文件名中提取）
            project_name = self._extract_project_name(parsing_result)
            
            # 第一步：生成功能需求说明  
            function_requirements_info = self._generate_function_requirements(content_summary, document_content)
            
            # 让LLM选择服务并同时获取company_services_config内相关的信息
            result = self._generate_service_info(content_analysis, document_content)
            service_info = result["service_info"]
            service_numbers = result["service_count"]
            data_resources = result["data_resources"] 
            data_info = result["data_info"]
            
            self.logger.info(f"生成约束条件 - 服务数量: {service_numbers}, 数据库数量: {data_resources}")
            
            # 第二步：使用核心业务生成器统一生成核心设计
            try:
                core_design = self.core_business_generator.generate_core_business_design(
                    content_analysis=content_analysis,
                    parsing_result=parsing_result,
                    document_content=document_content,
                    function_requirements_info=function_requirements_info,
                    service_numbers=service_numbers,
                    service_info=service_info,
                    data_resources=data_resources,
                    data_info=data_info
                )
                
                self.logger.info("核心业务设计统一生成成功")
                
                # 第三步：构建完整的表单数据结构
                form_data = {
                    "project_name": project_name,
                    "project_info": self._generate_project_info(document_content),
                    "function_requirements_info": function_requirements_info,
                    "project_architecture": core_design.get("project_architecture", "采用微服务架构模式"),
                    "service_numbers": service_numbers,
                    "service_info": service_info,
                    "data_resources": data_resources,
                    "data_info": data_info,
                    "technology": self._get_default_tech_stack(),
                    "service_details": core_design.get("service_details", []),  # 使用统一生成的结果
                    "execution": self._generate_execution_requirements(core_design)
                }
                
                self.logger.info(f"表单数据生成完成，包含{len(form_data.get('service_details', []))}个服务设计")
                return form_data
                
            except Exception as core_error:
                self.logger.error(f"核心业务生成失败: {core_error}")
                # 核心业务生成失败时抛出异常，不使用回退方案
                raise Exception(f"核心业务设计生成失败: {str(core_error)}")
            
        except Exception as e:
            self.logger.error(f"生成表单数据失败: {e}")
            raise
    
    def _extract_project_name(self, parsing_result: Dict) -> str:
        """从上传文件名中提取项目名称"""
        try:
            # 从parsing_result中获取文件名
            file_format = parsing_result.get("data", {}).get("fileFormat", {})
            filename = file_format.get("fileName", "")
            
            if not filename:
                return "业务系统优化项目"
            
            # 去掉文件扩展名
            import re
            name_without_ext = re.sub(r'\.[^.]*$', '', filename)
            
            # 直接返回去掉扩展名的文件名，如果为空则返回默认值
            return name_without_ext.strip() if name_without_ext.strip() else "业务系统优化项目"
            
        except Exception:
            return "业务系统优化项目"
    
    def _generate_project_info(self, document_content: str) -> str:
        """LLM生成项目介绍信息"""
        try:
            prompt = f"""
你是一个文档内容提取器，你的任务是从文档中准确提取指定内容，不能添加任何文档中没有的内容。

文档原文：
{document_content}

提取任务：
从上述文档中找到"需求背景"、"项目背景"、"背景"、"项目介绍"或类似章节，将该章节的完整内容提取出来。

提取规则：
1. 只提取文档中已有的内容，不能增加、修改或重新组织
2. 保持原文的表述和格式
3. 重点关注描述项目起因、现状问题、业务需求的段落
4. 如果找到多个背景相关章节，提取最主要的一个
5. 如果没有找到相关章节，返回"未找到需求背景内容"

输出要求：
- 直接输出提取的原文内容
- 不要添加任何解释、总结或补充说明
- 不要包含章节标题编号
"""
            
            if self.llm_client:
                response = self.llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                
                project_info = response.strip()
                
                self.logger.info(f"LLM生成项目介绍信息: {project_info}")
                
                # 如果LLM返回没有找到内容，使用默认内容
                if project_info == "未找到需求背景内容" or not project_info:
                    return "项目旨在优化现有业务系统，提升用户体验和系统性能。"
                
                return project_info
            else:
                return "llm未找到项目，旨在优化现有业务系统，提升用户体验和系统性能。"
                
        except Exception as e:
            self.logger.error(f"LLM生成项目介绍失败: {e}")
            return "项目旨在优化现有业务系统，提升用户体验和系统性能。"
    
    def _generate_function_requirements(self, content_summary: str, document_content: str) -> Dict:
        """LLM生成功能需求信息"""
        try:
            prompt = f"""
基于以下业务文档内容，生成详细的功能需求信息：

文档内容摘要：
{content_summary}

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
                    return self._get_default_function_requirements([], content_summary)
            else:
                return self._get_default_function_requirements([], content_summary)
                
        except Exception as e:
            self.logger.error(f"LLM生成功能需求失败: {e}")
            return self._get_default_function_requirements([], content_summary)
    
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
    

    
    def _count_services(self, design_data: Dict) -> int:
        """统计服务数量"""
        services = design_data.get("services", [])
        return max(len(services), 2)  # 至少2个服务
    
    def _generate_service_info(self, content_analysis: Dict, document_content: str) -> dict:
        """使用LLM从公司现有服务中智能选择合适的服务，返回完整信息"""
        # 获取公司现有服务配置
        company_config = get_company_services_config()
        existing_services = company_config.get_existing_services()
        
        if not existing_services:
            raise Exception("无法获取公司服务配置，请检查company_services.yaml文件")
        
        # 使用LLM选择服务 - 从content_analysis中提取crud_operations或使用空列表
        crud_operations = content_analysis.get("data", {}).get("crud_operations", [])
        llm_result = self._llm_select_services(content_analysis, existing_services, document_content)
        
        if not llm_result:
            raise Exception("LLM服务选择失败")
        
        # 从LLM返回结果中提取服务信息
        service_info = llm_result.get("service_info", [])
        service_count = llm_result.get("service_count", len(service_info))
        
        if not service_info:
            raise Exception("LLM未选择任何服务")
        
        # 从配置文件中获取每个服务的data_resources并统计
        all_data_resources = []
        for service in service_info:
            # 在existing_services中查找对应的服务
            for existing_service in existing_services:
                if (existing_service.get("service_name") == service.get("service_name") or 
                    existing_service.get("service_english_name") == service.get("service_english_name")):
                    # 从配置文件中获取data_resources
                    data_resources = existing_service.get("data_resources", [])
                    if isinstance(data_resources, list):
                        all_data_resources.extend(data_resources)
                    elif isinstance(data_resources, str):
                        all_data_resources.append(data_resources)
                    break
        
        # 统计数据库类型并去重
        unique_data_types = list(set(all_data_resources))
        data_info = [{"data_type": data_type.lower()} for data_type in unique_data_types]
        
        return {
            "service_info": service_info,
            "service_count": service_count,
            "data_resources": len(unique_data_types),
            "data_info": data_info
        }
    
    def _llm_select_services(self, content_analysis: Dict, existing_services: list, document_content: str) -> Dict:
        """使用LLM从现有服务中选择最合适的服务"""
        try:
            if not self.llm_client:
                self.logger.warning("LLM客户端不可用，跳过智能服务选择")
                return None
                
            # 加载服务选择模板
            if not self.template_loader:
                self.logger.warning("模板加载器不可用，跳过智能服务选择")
                return None
                
            template = self.template_loader.get_template('service_selection_prompts.jinja2')
            
            # 生成系统提示词
            system_prompt = template.module.system_prompt_service_selection()
            
       
            # 生成用户提示词  
            user_prompt = template.module.user_prompt_service_selection(
                document_content=document_content,
                content_analysis=content_analysis,
                existing_services=existing_services
            )
            
            self.logger.info(f"发送给LLM的用户提示词: {user_prompt[:500]}...")
            self.logger.info(f"文档内容长度: {len(document_content)}, 现有服务数量: {len(existing_services)}")
            
            # 调用LLM
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            self.logger.info(f"LLM服务选择原始响应: {response}")
            
            # 解析响应
            try:
                import json
                result_text = response.strip()
                # 清理可能的markdown格式
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()
                
                self.logger.info(f"清理后的JSON文本: {result_text}")
                result = json.loads(result_text)
                self.logger.info(f"解析后的结果: {result}")
            except json.JSONDecodeError as e:
                self.logger.error(f"解析LLM返回的JSON失败: {e}")
                raise Exception(f"服务选择响应格式错误: {e}")
            
            if result and "selected_services" in result:
                return {
                    "service_info": [
                        {
                            "service_name": service.get("service_name", ""),
                            "service_english_name": service.get("service_english_name", "")
                        }
                        for service in result["selected_services"]
                    ],
                    "service_count": result.get("service_count", len(result["selected_services"]))
                }
            
            raise Exception("LLM未返回有效的服务选择结果")
            
        except Exception as e:
            self.logger.error(f"LLM服务选择失败: {e}")
            return None
    
    def _generate_default_service_info_from_existing(self, existing_services: list) -> list:
        """从现有服务中选择默认服务（当LLM不可用时）"""
        service_info = []
        
        # 简单选择前2个现有服务
        for service in existing_services[:2]:
            service_info.append({
                "service_name": service.get("service_name", ""),
                "service_english_name": service.get("service_english_name", "")
            })
        
        return service_info
    
    def _generate_default_service_info(self, crud_operations: list) -> list:
        """当没有公司服务配置时返回空列表，让LLM自己决定"""
        return []
    
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

    

    def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """实现基类的抽象方法 - 暂时为空实现"""
        pass