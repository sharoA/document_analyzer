"""
统一代码生成器
整合AI智能生成和传统模板生成，优先使用AI大模型
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 智能编码功能通过IntelligentCodingAgent类提供，避免循环导入
try:
    from ..langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
    INTELLIGENT_CODING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"智能编码节点不可用: {e}")
    INTELLIGENT_CODING_AVAILABLE = False
    IntelligentCodingAgent = None

from .traditional_code_generator import TraditionalCodeGenerator

logger = logging.getLogger(__name__)


class UnifiedCodeGenerator:
    """统一代码生成器 - 优先使用AI大模型生成高质量代码"""
    
    def __init__(self):
        self.traditional_generator = TraditionalCodeGenerator()
    
    async def generate_project_code(
        self,
        document_content: str,
        project_name: str,
        output_path: str,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        生成项目代码 - 优先使用AI大模型
        
        Args:
            document_content: 文档内容（需求+设计）
            project_name: 项目名称
            output_path: 输出路径
            use_ai: 是否使用AI智能生成（传统工作流也应该使用AI）
            
        Returns:
            生成结果字典
        """
        logger.info(f"开始生成项目代码: {project_name} -> {output_path}")
        logger.info(f"AI大模型生成: {use_ai and INTELLIGENT_CODING_AVAILABLE}")
        
        try:
            # 分离需求文档和设计文档
            requirements_doc, design_doc = self._split_document(document_content)
            
            # 识别服务
            services = self._identify_services(document_content)
            
            # 🎯 优先使用AI智能生成（无论是否LangGraph工作流）
            if use_ai and INTELLIGENT_CODING_AVAILABLE:
                logger.info("🚀 使用AI大模型智能生成代码")
                return await self._generate_with_ai(
                    requirements_doc=requirements_doc,
                    design_doc=design_doc,
                    project_name=project_name,
                    output_path=output_path,
                    services=services
                )
            else:
                # 🔄 只有在AI不可用时才降级到模板生成
                logger.warning("⚠️ AI不可用，降级到传统模板生成")
                return self._generate_with_template(
                    document_content=document_content,
                    project_name=project_name,
                    output_path=output_path,
                    services=services
                )
                
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "services": [],
                "output_path": output_path,
                "generation_method": "failed"
            }
    
    async def _generate_with_ai(
        self,
        requirements_doc: str,
        design_doc: str,
        project_name: str,
        output_path: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """🤖 使用AI大模型智能生成代码"""
        logger.info("🤖 AI大模型开始智能分析需求并生成代码...")
        
        try:
            # 构造类似LangGraph工作流的状态
            state = {
                "requirements_doc": requirements_doc,
                "design_doc": design_doc,
                "project_name": project_name,
                "output_path": output_path,
                "identified_services": services,
                "service_dependencies": self._analyze_dependencies(services),
                "project_paths": self._build_project_paths(services, output_path, project_name),
                "completed_services": [],
                "failed_services": [],
                "generated_services": {},
                "generated_apis": {},
                "generated_sql": {},
                "execution_errors": []
            }
            
            # 🎯 使用IntelligentCodingAgent执行数据库中的任务
            coding_agent = IntelligentCodingAgent()
            
            # 执行所有可用的任务
            logger.info("🧠 AI正在执行数据库中的编码任务...")
            task_results = coding_agent.execute_task_from_database()
            
            if task_results:
                for task_result in task_results:
                    if task_result.get("success"):
                        # 从任务结果中提取服务信息
                        if 'service_name' in task_result.get('result', {}):
                            service_name = task_result['result']['service_name']
                            if service_name not in state["completed_services"]:
                                state["completed_services"].append(service_name)
                            state["generated_services"][service_name] = task_result.get('result', {})
                            logger.info(f"✅ AI成功生成服务: {service_name}")
                        else:
                            # 通用任务成功
                            logger.info(f"✅ AI成功执行任务: {task_result.get('task_type', 'unknown')}")
                    else:
                        error_msg = task_result.get('message', 'Unknown error')
                        state["execution_errors"].append(f"任务执行失败: {error_msg}")
                        logger.error(f"❌ AI任务执行失败: {error_msg}")
            else:
                logger.warning("⚠️ 没有找到可执行的编码任务，可能需要先执行任务拆分")
            
            # 📊 生成结果统计
            success_count = len(state["completed_services"])
            total_count = len(services)
            
            logger.info(f"🎉 AI代码生成完成: {success_count}/{total_count} 服务成功")
            
            return {
                "success": success_count > 0,
                "services": state["completed_services"],
                "failed_services": state["failed_services"],
                "output_path": output_path,
                "generation_method": "ai_intelligent",
                "generated_apis": state["generated_apis"],
                "generated_sql": state.get("generated_sql", {}),
                "service_interconnections": state.get("service_interconnections", {}),
                "execution_errors": state["execution_errors"],
                "ai_analysis": {
                    "total_services": total_count,
                    "successful_services": success_count,
                    "success_rate": f"{(success_count/total_count)*100:.1f}%" if total_count > 0 else "0%"
                }
            }
            
        except Exception as e:
            logger.error(f"🚨 AI代码生成失败: {e}")
            # 🔄 AI失败时降级到模板生成
            logger.info("🔄 AI失败，降级到传统模板生成")
            return self._generate_with_template(
                document_content=f"{requirements_doc}\n\n{design_doc}",
                project_name=project_name,
                output_path=output_path,
                services=services
            )
    
    def _generate_with_template(
        self,
        document_content: str,
        project_name: str,
        output_path: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """📝 使用传统模板生成代码（降级方案）"""
        logger.info("📝 使用传统模板生成代码...")
        
        try:
            success = self.traditional_generator.generate_project(
                document_content=document_content,
                project_name=project_name,
                output_path=output_path,
                services=services
            )
            
            logger.info(f"📝 传统模板生成{'成功' if success else '失败'}")
            
            return {
                "success": success,
                "services": services if success else [],
                "failed_services": [] if success else services,
                "output_path": output_path if success else None,
                "generation_method": "traditional_template",
                "generated_apis": {},
                "template_analysis": {
                    "total_services": len(services),
                    "generated_successfully": success
                }
            }
            
        except Exception as e:
            logger.error(f"📝 传统模板生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "services": [],
                "output_path": output_path,
                "generation_method": "failed"
            }
    
    def _split_document(self, document_content: str) -> tuple[str, str]:
        """分离需求文档和设计文档"""
        if "=" * 40 in document_content:
            parts = document_content.split("=" * 40, 1)
            requirements_doc = parts[0].strip()
            design_doc = parts[1].strip() if len(parts) > 1 else ""
        else:
            requirements_doc = document_content
            design_doc = ""
        
        return requirements_doc, design_doc
    
    def _identify_services(self, document_content: str) -> List[str]:
        """🔍 智能识别微服务"""
        services = []
        
        # 基于关键词识别服务
        if "用户" in document_content or "登录" in document_content or "注册" in document_content:
            services.append("user-service")
        
        if "额度" in document_content or "确权" in document_content or "开立" in document_content:
            services.append("quota-service")
        
        if "数据同步" in document_content or "同步" in document_content:
            services.append("sync-service")
        
        if "监控" in document_content or "告警" in document_content:
            services.append("monitor-service")
        
        # 通用业务服务识别
        if "订单" in document_content or "交易" in document_content:
            services.append("order-service")
            
        if "支付" in document_content or "付款" in document_content:
            services.append("payment-service")
            
        if "通知" in document_content or "消息" in document_content:
            services.append("notification-service")
        
        # 如果没有识别到服务，创建默认服务
        if not services:
            services = ["business-service"]  # 更合适的默认名称
        
        logger.info(f"🔍 识别到的微服务: {services}")
        return services
    
    def _analyze_dependencies(self, services: List[str]) -> Dict[str, List[str]]:
        """📊 分析服务依赖关系"""
        dependencies = {}
        
        # 智能依赖关系推断
        for service in services:
            deps = []
            
            # 用户服务通常是基础服务
            if service == "quota-service" and "user-service" in services:
                deps.append("user-service")
            elif service == "order-service" and "user-service" in services:
                deps.append("user-service")
            elif service == "payment-service" and "order-service" in services:
                deps.append("order-service")
            elif service == "sync-service":
                # 同步服务通常依赖业务服务
                deps.extend([s for s in services if s not in ["sync-service", "monitor-service"]])
            elif service == "monitor-service":
                # 监控服务通常监控所有其他服务
                deps.extend([s for s in services if s != "monitor-service"])
            elif service == "notification-service":
                # 通知服务通常依赖业务服务
                deps.extend([s for s in services if s not in ["notification-service", "monitor-service"]])
            
            dependencies[service] = deps
        
        logger.info(f"📊 服务依赖关系: {dependencies}")
        return dependencies
    
    def _build_project_paths(
        self, 
        services: List[str], 
        output_path: str, 
        project_name: str
    ) -> Dict[str, str]:
        """🗂️ 构建项目路径映射"""
        project_paths = {}
        for service_name in services:
            project_paths[service_name] = os.path.join(output_path, project_name, service_name)
        return project_paths 