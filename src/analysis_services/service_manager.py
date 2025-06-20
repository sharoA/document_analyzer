"""
分析服务管理器
统一管理文档解析、内容分析、AI智能分析三个服务
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from .document_parser import DocumentParserService
from .content_analyzer import ContentAnalyzerService
from .ai_analyzer import AIAnalyzerService
from .vector_database import VectorDatabaseFactory, initialize_sample_data

class AnalysisServiceManager:
    """分析服务管理器"""
    
    def __init__(self, llm_client=None, vector_db_type: str = "weaviate", **vector_db_kwargs):
        """
        初始化服务管理器
        
        Args:
            llm_client: 大语言模型客户端（火山引擎）
            vector_db_type: 向量数据库类型 ("mock" 或 "chroma" or "weaviate", current "weaviate")
            **vector_db_kwargs: 向量数据库初始化参数
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        # 使用火山引擎作为大语言模型客户端
        self.llm_client = llm_client
        
        # 初始化向量数据库
        try:
            self.vector_db = VectorDatabaseFactory.create_database(vector_db_type, **vector_db_kwargs)
            self.logger.info(f"初始化向量数据库: {vector_db_type}")
        except Exception as e:
            self.logger.error(f"向量数据库初始化失败: {str(e)}")
            # 使用模拟数据库作为备选
            self.vector_db = VectorDatabaseFactory.create_database("mock")
        
        # 初始化三个分析服务
        self.document_parser = DocumentParserService(llm_client=llm_client)
        self.content_analyzer = ContentAnalyzerService(llm_client=llm_client, vector_db=self.vector_db)
        self.ai_analyzer = AIAnalyzerService(llm_client=llm_client)
        
        self.logger.info("分析服务管理器初始化完成")
    
    async def initialize(self):
        """初始化服务（加载示例数据等）"""
        try:
            await initialize_sample_data(self.vector_db)
            self.logger.info("服务初始化完成")
        except Exception as e:
            self.logger.error(f"服务初始化失败: {str(e)}")
    
    async def full_analysis_pipeline(self, task_id: str, file_content: str, 
                                   file_type: str, file_name: str) -> Dict[str, Any]:
        """
        执行完整的分析流水线
        
        Args:
            task_id: 任务ID
            file_content: 文件内容
            file_type: 文件类型
            file_name: 文件名
            
        Returns:
            完整的分析结果
        """
        self.logger.info(f"开始完整分析流水线 - 任务ID: {task_id}")
        
        try:
            # 第一步：文档解析
            parsing_input = {
                "file_content": file_content,
                "file_type": file_type,
                "file_name": file_name
            }
            
            parsing_result = await self.document_parser.analyze(task_id, parsing_input)
            
            if not parsing_result.get("success"):
                return {
                    "success": False,
                    "error": "文档解析失败",
                    "parsing_result": parsing_result
                }
            
            # 第二步：内容分析
            content_input = {
                "parsing_result": parsing_result.get("data", {}),
                "document_content": file_content
            }
            
            content_result = await self.content_analyzer.analyze(task_id, content_input)
            
            if not content_result.get("success"):
                return {
                    "success": False,
                    "error": "内容分析失败",
                    "parsing_result": parsing_result,
                    "content_result": content_result
                }
            
            # 第三步：AI智能分析
            ai_input = {
                "content_analysis": content_result.get("data", {}),
                "parsing_result": parsing_result.get("data", {})
            }
            
            ai_result = await self.ai_analyzer.analyze(task_id, ai_input)
            
            if not ai_result.get("success"):
                return {
                    "success": False,
                    "error": "AI智能分析失败",
                    "parsing_result": parsing_result,
                    "content_result": content_result,
                    "ai_result": ai_result
                }
            
            # 整合所有结果
            final_result = {
                "success": True,
                "task_id": task_id,
                "interfaces": {
                    "document_parsing": {
                        "status": "completed",
                        "data": parsing_result.get("data", {}),
                        "metadata": parsing_result.get("metadata", {})
                    },
                    "content_analysis": {
                        "status": "completed", 
                        "data": content_result.get("data", {}),
                        "metadata": content_result.get("metadata", {})
                    },
                    "ai_analysis": {
                        "status": "completed",
                        "data": ai_result.get("data", {}),
                        "metadata": ai_result.get("metadata", {})
                    }
                },
                "summary": self._generate_analysis_summary(parsing_result, content_result, ai_result)
            }
            
            self.logger.info(f"完整分析流水线完成 - 任务ID: {task_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"分析流水线失败 - 任务ID: {task_id}, 错误: {str(e)}")
            return {
                "success": False,
                "error": f"分析流水线失败: {str(e)}",
                "task_id": task_id
            }
    
    async def parse_document(self, task_id: str, file_content: str, 
                           file_type: str, file_name: str) -> Dict[str, Any]:
        """执行文档解析"""
        input_data = {
            "file_content": file_content,
            "file_type": file_type,
            "file_name": file_name
        }
        return await self.document_parser.analyze(task_id, input_data)
    
    async def analyze_content(self, task_id: str, parsing_result: Dict[str, Any], 
                            document_content: str) -> Dict[str, Any]:
        """执行内容分析"""
        input_data = {
            "parsing_result": parsing_result,
            "document_content": document_content
        }
        return await self.content_analyzer.analyze(task_id, input_data)
    
    async def ai_analyze(self, task_id: str, content_analysis: Dict[str, Any], 
                        parsing_result: Dict[str, Any] = None, 
                        progress_callback: Callable = None) -> Dict[str, Any]:
        """执行AI智能分析"""
        input_data = {
            "content_analysis": content_analysis,
            "parsing_result": parsing_result or {}
        }
        return await self.ai_analyzer.analyze(task_id, input_data, progress_callback)
    
    def parse_document_sync(self, task_id: str, file_content: str, 
                           file_type: str, file_name: str) -> Dict[str, Any]:
        """执行文档解析 - 同步版本"""
        import asyncio
        return asyncio.run(self.parse_document(task_id, file_content, file_type, file_name))
    
    def analyze_content_sync(self, task_id: str, parsing_result: Dict[str, Any], 
                            document_content: str) -> Dict[str, Any]:
        """执行内容分析 - 同步版本"""
        import asyncio
        return asyncio.run(self.analyze_content(task_id, parsing_result, document_content))
    
    def ai_analyze_sync(self, task_id: str, content_analysis: Dict[str, Any], 
                        parsing_result: Dict[str, Any] = None,
                        progress_callback: Callable = None) -> Dict[str, Any]:
        """执行AI智能分析 - 同步版本"""
        import asyncio
        return asyncio.run(self.ai_analyze(task_id, content_analysis, parsing_result, progress_callback))
    
    def _generate_analysis_summary(self, parsing_result: Dict, content_result: Dict, 
                                 ai_result: Dict) -> Dict[str, Any]:
        """生成分析摘要"""
        # 提取关键指标
        parsing_data = parsing_result.get("data", {})
        content_data = content_result.get("data", {})
        ai_data = ai_result.get("data", {})
        
        # 基础信息
        basic_info = parsing_data.get("basic_info", {})
        
        # CRUD操作统计
        crud_analysis = content_data.get("crud_analysis", {})
        crud_summary = crud_analysis.get("summary", {})
        
        # AI分析结果
        api_design = ai_data.get("api_design", {})
        mq_config = ai_data.get("mq_config", {})
        implementation_plan = ai_data.get("implementation_plan", {})
        
        return {
            "document_info": {
                "file_type": basic_info.get("file_type", "未知"),
                "language": basic_info.get("language", "未知"),
                "character_count": basic_info.get("character_count", 0),
                "word_count": basic_info.get("word_count", 0)
            },
            "analysis_results": {
                "total_crud_operations": crud_summary.get("total_operations", 0),
                "create_operations": crud_summary.get("create_count", 0),
                "read_operations": crud_summary.get("read_count", 0),
                "update_operations": crud_summary.get("update_count", 0),
                "delete_operations": crud_summary.get("delete_count", 0)
            },
            "generated_artifacts": {
                "api_interfaces": len(api_design.get("api_interfaces", [])),
                "mq_topics": len(mq_config.get("mq_topics", [])),
                "mq_queues": len(mq_config.get("mq_queues", [])),
                "implementation_phases": implementation_plan.get("total_phases", 0)
            },
            "complexity_assessment": {
                "level": content_data.get("complexity_analysis", {}).get("complexity_level", "未知"),
                "estimated_time": implementation_plan.get("estimated_total_time", 0),
                "risk_level": "低" if implementation_plan.get("estimated_total_time", 0) < 15 else "中"
            },
            "processing_time": {
                "parsing_duration": parsing_result.get("metadata", {}).get("analysis_duration", 0),
                "content_duration": content_result.get("metadata", {}).get("analysis_duration", 0),
                "ai_duration": ai_result.get("metadata", {}).get("analysis_duration", 0)
            }
        }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "document_parser": {
                "status": "active",
                "llm_available": self.llm_client is not None
            },
            "content_analyzer": {
                "status": "active",
                "llm_available": self.llm_client is not None,
                "vector_db_available": self.vector_db is not None
            },
            "ai_analyzer": {
                "status": "active",
                "llm_available": self.llm_client is not None
            },
            "vector_database": {
                "type": self.vector_db.__class__.__name__,
                "status": "active"
            }
        }
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 这里可以添加资源清理逻辑
            self.logger.info("分析服务管理器清理完成")
        except Exception as e:
            self.logger.error(f"服务清理失败: {str(e)}")

# 全局服务管理器实例
_service_manager_instance = None

def get_service_manager() -> Optional[AnalysisServiceManager]:
    """获取服务管理器实例（已废弃，使用get_analysis_service_manager）"""
    return _service_manager_instance

def get_analysis_service_manager() -> Optional[AnalysisServiceManager]:
    """获取分析服务管理器实例"""
    return _service_manager_instance

def initialize_analysis_service_manager(llm_client=None, vector_db_type: str = "mock", **kwargs) -> AnalysisServiceManager:
    """初始化分析服务管理器"""
    global _service_manager_instance
    _service_manager_instance = AnalysisServiceManager(llm_client=llm_client, vector_db_type=vector_db_type, **kwargs)
    return _service_manager_instance

def initialize_service_manager(llm_client=None, vector_db_type: str = "mock", **kwargs) -> AnalysisServiceManager:
    """初始化服务管理器（已废弃，使用initialize_analysis_service_manager）"""
    return initialize_analysis_service_manager(llm_client=llm_client, vector_db_type=vector_db_type, **kwargs)

async def initialize_services(llm_client=None, vector_db_type: str = "mock", **kwargs):
    """初始化所有服务"""
    manager = initialize_analysis_service_manager(llm_client=llm_client, vector_db_type=vector_db_type, **kwargs)
    await manager.initialize()
    return manager 