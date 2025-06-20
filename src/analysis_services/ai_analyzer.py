"""
AI智能分析服务
基于LangChain PlanAndExecution框架实现AI系统架构设计师
按照7步骤工作流程生成完整的系统架构设计
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .base_service import BaseAnalysisService

class AIAnalyzerService(BaseAnalysisService):
    """基于LangChain的AI智能分析服务"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.planner = None
        
    async def analyze(self, task_id: str, input_data: Dict[str, Any], 
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行AI智能分析 - LangChain版本
        
        Args:
            task_id: 任务ID
            input_data: 包含内容分析结果的数据
            progress_callback: 进度回调函数
            
        Returns:
            AI分析结果字典
        """
        start_time = time.time()
        
        try:
            # 创建AI架构设计师规划器
            self.planner = AIArchitectPlanner(
                llm_client=self.llm_client,
                progress_callback=progress_callback
            )
            
            # 提取输入数据
            content_analysis = input_data.get("content_analysis", {})
            parsing_result = input_data.get("parsing_result", {})
            
            self._log_analysis_start(task_id, "AI架构设计", 0)
            
            # 执行架构设计
            design_result = await self.planner.execute_architecture_design(
                task_id, content_analysis, parsing_result
            )
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "AI架构设计", duration, len(str(design_result)))
            
            return self._create_response(
                success=True,
                data=design_result,
                metadata={
                    "analysis_method": "LangChain PlanAndExecution",
                    "framework": "AI系统架构设计师",
                    "compliance": "遵循AI系统架构设计师规范",
                    "analysis_duration": duration
                }
            )
            
        except Exception as e:
            self._log_error(task_id, "AI架构设计", e)
            return self._create_response(
                success=False,
                error=f"AI架构设计失败: {str(e)}"
            )
    
class AIArchitectPlanner:
    """AI系统架构设计师规划器"""
    
    def __init__(self, llm_client, progress_callback: Optional[Callable] = None):
        self.llm_client = llm_client
        self.progress_callback = progress_callback
        self.memory = ArchitectureMemory()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute_architecture_design(self, task_id: str, content_analysis: Dict, parsing_result: Dict) -> Dict:
        """执行完整的系统架构设计"""
        
        try:
            # 创建执行计划
            execution_plan = self._create_execution_plan(content_analysis, parsing_result)
            
            # 执行7个步骤
            results = {}
            
            # 步骤1: 需求分析与功能拆解 (10%)
            self._update_progress(10, "需求分析与功能拆解")
            results["business_requirements"] = await self._step1_requirements_analysis(content_analysis, parsing_result)
            self.memory.add_step_result("step1", results["business_requirements"])
 
            # 步骤2: 数据流程图与接口设计 (25%)
            self._update_progress(25, "设计数据流程与API接口")
            results["api_design"], results["data_flow"] = await self._step2_api_design(results["business_requirements"])
            self.memory.add_step_result("step2", {"api_design": results["api_design"], "data_flow": results["data_flow"]})
            
            # 步骤3: 前后端详细架构设计 (40%)
            self._update_progress(40, "前后端架构设计")
            results["frontend_arch"], results["backend_arch"] = await self._step3_architecture_design(results["business_requirements"])
            self.memory.add_step_result("step3", {"frontend_arch": results["frontend_arch"], "backend_arch": results["backend_arch"]})
            
            # 步骤4: 安全与权限方案设计 (55%)
            self._update_progress(55, "安全权限方案设计")
            results["security_design"] = await self._step4_security_design(results["api_design"])
            self.memory.add_step_result("step4", results["security_design"])
            
            # 步骤5: 消息队列与定时任务设计 (70%)
            self._update_progress(70, "MQ与定时任务设计")
            results["mq_design"], results["scheduler_design"] = await self._step5_mq_scheduler_design(results["business_requirements"])
            self.memory.add_step_result("step5", {"mq_design": results["mq_design"], "scheduler_design": results["scheduler_design"]})
            
            # 步骤6: 数据库设计与初始化SQL (85%)
            self._update_progress(85, "数据库设计")
            results["database_design"] = await self._step6_database_design(results["business_requirements"])
            self.memory.add_step_result("step6", results["database_design"])
            
            # 步骤7: LangChain集成方案设计 (95%)
            self._update_progress(95, "LangChain集成方案")
            results["langchain_integration"] = await self._step7_langchain_integration(results["business_requirements"])
            self.memory.add_step_result("step7", results["langchain_integration"])
            
            # 生成最终方案 (100%)
            final_result = await self._generate_final_architecture(results)
            self._update_progress(100, "AI架构设计完成", "ai_analyzed")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"架构设计执行失败: {str(e)}")
            raise
    
    def _update_progress(self, stage: int, message: str, status: str = "ai_analyzing"):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(stage, message, status)
        self.logger.info(f"架构设计进度: {stage}% - {message}")
    
    def _create_execution_plan(self, content_analysis: Dict, parsing_result: Dict) -> Dict:
        """创建执行计划"""
        return {
            "steps": [
                {"id": 1, "name": "需求分析与功能拆解", "progress": 10},
                {"id": 2, "name": "数据流程图与接口设计", "progress": 25},
                {"id": 3, "name": "前后端详细架构设计", "progress": 40},
                {"id": 4, "name": "安全与权限方案设计", "progress": 55},
                {"id": 5, "name": "消息队列与定时任务设计", "progress": 70},
                {"id": 6, "name": "数据库设计与初始化SQL", "progress": 85},
                {"id": 7, "name": "LangChain集成方案设计", "progress": 95}
            ],
            "input_analysis": content_analysis,
            "parsing_result": parsing_result
        }
    
    async def _step1_requirements_analysis(self, content_analysis: Dict, parsing_result: Dict) -> Dict:
        """步骤1: 需求分析与功能拆解"""
        
        system_prompt = """你是一个专业的业务分析师，专门处理金融科技和供应链金融系统的需求分析。根据文档分析结果，提取业务需求和功能要求。

请特别关注：
1. 变更分析中的changeType（新增/修改/删除）
2. 接口相关的校验规则调整
3. 前端功能的界面交互变更
4. 权限控制和业务规则变化

输出JSON格式：
{
    "functional_requirements": [
        {"id": "FR001", "name": "组织单元额度管理", "priority": "high", "complexity": "medium", "description": "新增组织单元额度列表页面，支持查询、筛选、导出功能", "change_type": "新增"}
    ],
    "non_functional_requirements": [
        {"type": "performance", "description": "页面响应时间<500ms", "metric": "latency", "target": "500ms"},
        {"type": "security", "description": "多组织企业权限控制", "metric": "access_control", "target": "role_based"}
    ],
    "business_entities": [
        {"name": "OrganizationUnit", "attributes": ["id", "name", "quotaAmount", "quotaType"], "relationships": ["belongs_to:enterprise"]},
        {"name": "Quota", "attributes": ["id", "name", "type", "allocatedAmount", "usedAmount"], "relationships": ["assigned_to:organization_unit"]}
    ],
    "user_stories": [
        {"as": "多组织企业管理员", "want": "查看各组织单元的额度分配情况", "so_that": "更好地管理资金配置"},
        {"as": "核心企业用户", "want": "重新推送已修改的业务数据", "so_that": "保持数据的准确性"}
    ],
    "api_requirements": [
        {"name": "确权业务申请", "change_type": "修改", "description": "调整bizSerialNo校验规则，允许特定条件下重复推送"}
    ],
    "ui_requirements": [
        {"component": "额度管理页面", "change_type": "修改", "description": "功能名称变更，新增组织单元额度按钮"},
        {"component": "组织单元额度列表", "change_type": "新增", "description": "新增独立的组织单元额度管理页面"}
    ],
    "complexity_assessment": {
        "level": "medium",
        "estimated_effort": "2-3人月",
        "risk_factors": ["多组织权限复杂度", "接口校验逻辑调整", "前后端联调"]
    }
}"""
        
        # 构建用户输入，整合两个数据源
        # 从content_analysis中提取数据
        content_data = content_analysis.get("data", {})
        change_analysis = content_data.get("change_analysis", {})
        
        # 从parsing_result中提取数据
        parsing_data = parsing_result.get("data", {})
        document_structure = parsing_data.get("documentStructure", {})
        content_summary = document_structure.get("contentSummary", {})
        content_keywords = document_structure.get("contentKeyWord", {})
        file_format = parsing_data.get("fileFormat", {})
        
        user_prompt = f"""
请根据以下文档分析结果，提取业务需求：

【文档基本信息】：
文件名：{file_format.get("fileName", "未知")}
文档类型：{file_format.get("primaryType", "未知")}
字符数：{file_format.get("technicalDetails", {}).get("charCount", 0)}
语言：{file_format.get("basicInfo", {}).get("language", "未知")}

【文档内容摘要】：
摘要：{content_summary.get("abstract", "无摘要")}
功能数量：{content_summary.get("functionCount", 0)}
功能列表：{json.dumps(content_summary.get("functionName", []), ensure_ascii=False)}
API数量：{content_summary.get("apiCount", 0)}
API列表：{json.dumps(content_summary.get("apiName", []), ensure_ascii=False)}

【关键词分析】：
主要关键词：{json.dumps(content_keywords.get("primaryKeywords", []), ensure_ascii=False, indent=2)}
语义集群：{json.dumps(content_keywords.get("semanticClusters", []), ensure_ascii=False, indent=2)}

【变更分析结果】：
{json.dumps(change_analysis, ensure_ascii=False, indent=2)}

请基于上述信息，按照JSON格式输出详细的需求分析结果。
注意：
1. 优先从变更分析中提取功能需求（change_analyses字段）
2. 参考文档摘要了解整体业务背景
3. 结合关键词分析理解业务领域
4. 将变更项转化为具体的功能需求和用户故事
"""
        
        response = await self._call_llm_with_retry(user_prompt, system_prompt)
        return self._parse_json_response(response, "需求分析")
    
    async def _step2_api_design(self, business_requirements: Dict) -> tuple:
        """步骤2: 数据流程图与接口设计"""
        
        # API接口设计
        api_system_prompt = """你是一个专业的API架构师。根据业务需求设计RESTful API接口。

输出JSON格式：
{
    "api_specification": {
        "version": "v1",
        "base_url": "/api/v1",
        "authentication": "JWT Bearer Token"
    },
    "interfaces": [
        {
            "resource": "users",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/users",
                    "description": "获取用户列表",
                    "parameters": {
                        "query": [{"name": "page", "type": "integer", "required": false}]
                    },
                    "responses": {
                        "200": {"description": "成功", "schema": "UserListResponse"}
                    },
                    "security": ["jwt_auth"]
                }
            ]
        }
    ],
    "data_models": [
        {
            "name": "User",
            "properties": {
                "id": {"type": "integer", "description": "用户ID"},
                "name": {"type": "string", "description": "用户名"}
            }
        }
    ]
}"""
        
        # 数据流程设计
        flow_system_prompt = """你是一个专业的系统架构师。设计系统数据流程和交互模式。

输出JSON格式：
{
    "data_flow_diagram": {
        "mermaid_syntax": "graph TD; A[前端] --> B[网关]; B --> C[服务层]",
        "components": [
            {"name": "前端层", "type": "Vue3", "responsibilities": ["用户交互", "数据展示"]},
            {"name": "网关层", "type": "Spring Gateway", "responsibilities": ["路由", "认证", "限流"]},
            {"name": "服务层", "type": "Spring Boot", "responsibilities": ["业务逻辑", "数据处理"]}
        ]
    },
    "interaction_patterns": [
        {"pattern": "Request-Response", "usage": "同步API调用"},
        {"pattern": "Event-Driven", "usage": "异步消息处理"}
    ],
    "performance_targets": {
        "response_time": "< 500ms",
        "throughput": "1000 req/s",
        "availability": "99.9%"
    }
}"""
        
        # 并行执行API设计和数据流程设计
        api_task = self._call_llm_with_retry(
            self._build_api_prompt(business_requirements),
            api_system_prompt
        )
        
        flow_task = self._call_llm_with_retry(
            self._build_flow_prompt(business_requirements),
            flow_system_prompt
        )
        
        api_response, flow_response = await asyncio.gather(api_task, flow_task)
        
        return (
            self._parse_json_response(api_response, "API设计"),
            self._parse_json_response(flow_response, "数据流程设计")
        )
    
    async def _step3_architecture_design(self, business_requirements: Dict) -> tuple:
        """步骤3: 前后端详细架构设计"""
        
        frontend_prompt = f"""
请根据以下业务需求设计前端架构：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的前端架构设计：
{{
    "framework": "Vue3",
    "architecture_pattern": "组件化架构",
    "state_management": "Pinia",
    "ui_components": [
        {{"name": "Layout", "description": "布局组件"}},
        {{"name": "DataTable", "description": "数据表格组件"}}
    ],
    "routing_strategy": "Vue Router",
    "build_tools": ["Vite", "TypeScript"]
}}
"""
        
        backend_prompt = f"""
请根据以下业务需求设计后端架构：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的后端架构设计：
{{
    "framework": "Spring Boot",
    "architecture_pattern": "分层架构",
    "microservices": [
        {{"name": "user-service", "description": "用户管理服务"}},
        {{"name": "document-service", "description": "文档处理服务"}}
    ],
    "service_discovery": "Nacos",
    "database": "MySQL + Redis"
}}
"""
        
        frontend_task = self._call_llm_with_retry(frontend_prompt, "你是前端架构师")
        backend_task = self._call_llm_with_retry(backend_prompt, "你是后端架构师")
        
        frontend_response, backend_response = await asyncio.gather(frontend_task, backend_task)
        
        return (
            self._parse_json_response(frontend_response, "前端架构设计"),
            self._parse_json_response(backend_response, "后端架构设计")
        )
    
    async def _step4_security_design(self, api_design: Dict) -> Dict:
        """步骤4: 安全与权限方案设计"""
        
        prompt = f"""
基于以下API设计，制定安全方案：
{json.dumps(api_design, ensure_ascii=False, indent=2)}

输出JSON格式的安全设计：
{{
    "authentication": {{
        "method": "JWT",
        "token_expiry": "24h",
        "refresh_strategy": "sliding_window"
    }},
    "authorization": {{
        "model": "RBAC",
        "roles": ["admin", "user", "viewer"],
        "permissions": ["read", "write", "delete"]
    }},
    "security_measures": [
        "API限流",
        "HTTPS强制",
        "XSS防护",
        "CSRF防护"
    ]
}}
"""
        
        response = await self._call_llm_with_retry(prompt, "你是安全架构师")
        return self._parse_json_response(response, "安全设计")
    
    async def _step5_mq_scheduler_design(self, business_requirements: Dict) -> tuple:
        """步骤5: 消息队列与定时任务设计"""
        
        mq_prompt = f"""
基于业务需求设计消息队列：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的MQ设计：
{{
    "message_broker": "RabbitMQ",
    "exchanges": [
        {{"name": "document.exchange", "type": "topic"}},
        {{"name": "notification.exchange", "type": "direct"}}
    ],
    "queues": [
        {{"name": "document.processing", "routing_key": "document.process"}},
        {{"name": "notification.email", "routing_key": "notify.email"}}
    ]
}}
"""
        
        scheduler_prompt = f"""
基于业务需求设计定时任务：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的定时任务设计：
{{
    "scheduler": "Quartz",
    "jobs": [
        {{"name": "DocumentCleanupJob", "cron": "0 0 2 * * ?", "description": "清理过期文档"}},
        {{"name": "ReportGenerationJob", "cron": "0 0 8 * * MON", "description": "生成周报"}}
    ]
}}
"""
        
        mq_task = self._call_llm_with_retry(mq_prompt, "你是消息队列架构师")
        scheduler_task = self._call_llm_with_retry(scheduler_prompt, "你是系统架构师")
        
        mq_response, scheduler_response = await asyncio.gather(mq_task, scheduler_task)
        
        return (
            self._parse_json_response(mq_response, "MQ设计"),
            self._parse_json_response(scheduler_response, "定时任务设计")
        )
    
    async def _step6_database_design(self, business_requirements: Dict) -> Dict:
        """步骤6: 数据库设计与初始化SQL"""
        
        prompt = f"""
基于业务需求设计数据库：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的数据库设计：
{{
    "database_type": "MySQL",
    "tables": [
        {{
            "name": "users",
            "columns": [
                {{"name": "id", "type": "BIGINT", "constraint": "PRIMARY KEY AUTO_INCREMENT"}},
                {{"name": "username", "type": "VARCHAR(50)", "constraint": "UNIQUE NOT NULL"}},
                {{"name": "email", "type": "VARCHAR(100)", "constraint": "NOT NULL"}}
            ],
            "indexes": ["INDEX idx_username (username)"]
        }}
    ],
    "relationships": [
        {{"from_table": "documents", "to_table": "users", "type": "many_to_one"}}
    ]
}}
"""
        
        response = await self._call_llm_with_retry(prompt, "你是数据库架构师")
        return self._parse_json_response(response, "数据库设计")
    
    async def _step7_langchain_integration(self, business_requirements: Dict) -> Dict:
        """步骤7: LangChain集成方案设计"""
        
        prompt = f"""
基于业务需求设计LangChain集成方案：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

输出JSON格式的LangChain集成设计：
{{
    "framework": "LangChain",
    "components": {{
        "llm": "火山引擎",
        "memory": "ConversationBufferMemory",
        "vector_store": "Weaviate",
        "embeddings": "文本嵌入模型"
    }},
    "chains": [
        {{"name": "DocumentAnalysisChain", "description": "文档分析链"}},
        {{"name": "QuestionAnswerChain", "description": "问答链"}}
    ],
    "tools": [
        {{"name": "DocumentParser", "description": "文档解析工具"}},
        {{"name": "ContentAnalyzer", "description": "内容分析工具"}}
    ]
}}
"""
        
        response = await self._call_llm_with_retry(prompt, "你是AI架构师")
        return self._parse_json_response(response, "LangChain集成设计")
    
    async def _generate_final_architecture(self, results: Dict) -> Dict:
        """生成最终架构方案"""
        
        return {
            "architecture_design": {
                "business_analysis": results.get("business_requirements", {}),
                "api_design": {
                    "api_specification": results.get("api_design", {}),
                    "data_flow": results.get("data_flow", {})
                },
                "system_architecture": {
                    "frontend_architecture": results.get("frontend_arch", {}),
                    "backend_architecture": results.get("backend_arch", {}),
                },
                "security_design": results.get("security_design", {}),
                "infrastructure_design": {
                    "mq_configuration": results.get("mq_design", {}),
                    "scheduler_configuration": results.get("scheduler_design", {}),
                    "database_schema": results.get("database_design", {})
                },
                "implementation_plan": {
                    "phases": [
                        {"phase": 1, "name": "基础架构搭建", "duration": "2周"},
                        {"phase": 2, "name": "核心功能开发", "duration": "4周"},
                        {"phase": 3, "name": "AI分析功能", "duration": "3周"},
                        {"phase": 4, "name": "系统优化", "duration": "2周"}
                    ],
                    "total_duration": "11周",
                    "risk_assessment": "中等风险"
                },
                "langchain_integration": results.get("langchain_integration", {})
            },
            "metadata": {
                "design_timestamp": datetime.now().isoformat(),
                "framework": "AI系统架构设计师",
                "tech_stack": {
                    "frontend": "Vue3",
                    "backend": "Java8 + Spring Boot + Nacos",
                    "database": "MySQL",
                    "mq": "RabbitMQ",
                    "ai_framework": "LangChain"
                },
                "design_principles": ["前后端分离", "微服务架构", "RESTful API", "安全第一"]
            }
        }
    
    def _build_api_prompt(self, business_requirements: Dict) -> str:
        """构建API设计提示"""
        
        functional_reqs = business_requirements.get("functional_requirements", [])
        api_reqs = business_requirements.get("api_requirements", [])
        ui_reqs = business_requirements.get("ui_requirements", [])
        entities = business_requirements.get("business_entities", [])
        
        return f"""
基于以下业务需求设计RESTful API：

功能需求：
{json.dumps(functional_reqs, ensure_ascii=False, indent=2)}

API需求：
{json.dumps(api_reqs, ensure_ascii=False, indent=2)}

界面需求：
{json.dumps(ui_reqs, ensure_ascii=False, indent=2)}

业务实体：
{json.dumps(entities, ensure_ascii=False, indent=2)}

请设计完整的RESTful API接口规范，特别关注：
1. 组织单元额度相关的查询、筛选、导出接口
2. 确权业务申请接口的校验规则调整
3. 多组织企业的权限控制
"""
    
    def _build_flow_prompt(self, business_requirements: Dict) -> str:
        """构建数据流程设计提示"""
        return f"""
基于以下业务需求设计系统数据流程：
{json.dumps(business_requirements, ensure_ascii=False, indent=2)}

请设计系统组件间的数据流程和交互模式。
"""
    
    async def _call_llm_with_retry(self, prompt: str, system_prompt: str, max_retries: int = 3) -> str:
        """带重试机制的LLM调用"""
        import logging
        logger = logging.getLogger(self.__class__.__name__)
        
        for attempt in range(max_retries):
            try:
                response = await self._call_llm(prompt, system_prompt, max_tokens=4000)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"LLM调用失败，尝试 {attempt + 1}/{max_retries}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        raise Exception("LLM调用失败，已达最大重试次数")

    async def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> Optional[str]:
        """调用LLM进行分析"""
        if not self.llm_client:
            raise ValueError("LLM客户端未初始化")
        
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt or "你是一个专业的系统架构师"},
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


class ArchitectureMemory:
    """架构设计记忆管理"""
    
    def __init__(self):
        self.design_context = {}
        self.step_results = {}
        
    def add_step_result(self, step: str, result: Dict):
        """添加步骤结果到记忆"""
        self.step_results[step] = result
        
    def get_context_for_step(self, step: str) -> Dict:
        """获取步骤所需的上下文"""
        return {
            "previous_results": self.step_results,
            "design_context": self.design_context
        } 