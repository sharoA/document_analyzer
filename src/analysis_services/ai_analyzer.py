"""
AI智能分析服务
简化流程，直接使用DesignDocumentGenerator生成标准设计文档
遵循单一职责原则，专注于协调分析流程
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from .base_service import BaseAnalysisService
from .design_document_generator import DesignDocumentGenerator
from ..utils import markdown_storage # 导入存储模块

class AIAnalyzerService(BaseAnalysisService):
    """AI智能分析服务"""
    
    def __init__(self, llm_client=None, vector_db=None):
        super().__init__(llm_client, vector_db)
        self.design_generator = DesignDocumentGenerator(llm_client, vector_db)
        
    def analyze(self, task_id: str, input_data: Dict[str, Any], 
                     progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        执行AI智能分析
        
        Args:
            task_id: 任务ID
            input_data: 包含内容分析结果的数据
            progress_callback: 进度回调函数
            
        Returns:
            包含markdown_content的分析结果
        """
        start_time = time.time()
        
        try:
            # 提取输入数据
            content_analysis = input_data.get("content_analysis", {})
            parsing_result = input_data.get("parsing_result", {})

            # 临时方案：如果有原始文档内容，直接传递给AI分析器
            document_content = input_data.get("document_content", "")

            self.logger.info(f"document_content: {document_content}")
            
            self._log_analysis_start(task_id, "AI设计文档生成", 0)
            
            # 直接使用设计文档生成器生成标准化文档
            document_result = self.design_generator.generate_design_document(
                task_id, document_content, content_analysis, parsing_result
            )
            
            # 构建最终结果
            if document_result.get("success"):
                doc_data = document_result.get("data", {})
                
                # 提取form_data并保存到Redis
                form_data = doc_data.get("form_data", {})
                if form_data:
                    # 直接保存到Redis，使用和前端一致的键名格式
                    try:
                        # 打印存储的form_data全部结构
                        logging.info(f"任务 {task_id}: 即将保存的form_data内容: {form_data}")
                        from ..utils.redis_task_storage import get_redis_task_storage
                        redis_storage = get_redis_task_storage()
                        redis_storage.redis_manager.set(
                            f"form_data:{task_id}", 
                            form_data,
                            ttl=86400 * 7  # 7天过期
                        )
                        logging.info(f"任务 {task_id}: 表单数据已保存到Redis")
                    except Exception as e:
                        logging.error(f"保存表单数据到Redis失败: {e}")
                
                final_result = {
                    "markdown_content": doc_data.get("design_document", ""),
                    "generation_metadata": doc_data.get("metadata", {}),
                    "design_data": doc_data.get("design_data", {}),
                    # "architecture_diagram": doc_data.get("architecture_diagram", {}),
                    "form_data": form_data  # 包含表单数据
                }

                # AI分析完成，保存结果
                logging.info(f"任务 {task_id}: AI分析结果保存完成。")
            else:
                final_result = {
                    "markdown_content": "",
                    "error": document_result.get("error", "文档生成失败")
                }
            
            duration = time.time() - start_time
            self._log_analysis_complete(task_id, "AI设计文档生成", duration, len(str(final_result)))
            
            return self._create_response(
                success=document_result.get("success", False),
                data=final_result,
                metadata={
                    "analysis_method": "DesignDocumentGenerator直接生成",
                    "framework": "简化版AI分析流程",
                    "compliance": "遵循combined_document_demo.txt模板规范",
                    "analysis_duration": duration,
                    "template_source": "大模型智能生成",
                    "markdown_generated": bool(final_result.get("markdown_content"))
                }
            )
            
        except Exception as e:
            self._log_error(task_id, "AI设计文档生成", e)
            return self._create_response(
                success=False,
                error=f"AI设计文档生成失败: {str(e)}"
            ) 