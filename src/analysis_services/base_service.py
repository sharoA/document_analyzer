"""
基础分析服务类
定义所有分析服务的通用接口和方法
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class BaseAnalysisService(ABC):
    """分析服务基类"""
    
    def __init__(self, llm_client=None, vector_db=None):
        """
        初始化基础服务
        
        Args:
            llm_client: 大语言模型客户端
            vector_db: 向量数据库客户端
        """
        self.llm_client = llm_client
        self.vector_db = vector_db
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def analyze(self, task_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分析任务
        
        Args:
            task_id: 任务ID
            input_data: 输入数据
            
        Returns:
            分析结果字典
        """
        pass
    
    def _create_response(self, success: bool, data: Dict[str, Any] = None, 
                        error: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建标准响应格式
        
        Args:
            success: 是否成功
            data: 响应数据
            error: 错误信息
            metadata: 元数据
            
        Returns:
            标准响应字典
        """
        response = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "service": self.__class__.__name__
        }
        
        if data:
            response["data"] = data
        if error:
            response["error"] = error
        if metadata:
            response["metadata"] = metadata
            
        return response
    
    def _log_analysis_start(self, task_id: str, analysis_type: str, input_size: int = 0):
        """记录分析开始日志"""
        self.logger.info(f"开始{analysis_type}分析 - 任务ID: {task_id}, 输入大小: {input_size}")
    
    def _log_analysis_complete(self, task_id: str, analysis_type: str, 
                             duration: float, result_size: int = 0):
        """记录分析完成日志"""
        self.logger.info(f"完成{analysis_type}分析 - 任务ID: {task_id}, "
                        f"耗时: {duration:.2f}秒, 结果大小: {result_size}")
    
    def _log_error(self, task_id: str, analysis_type: str, error: Exception):
        """记录错误日志"""
        # 安全地处理错误信息，避免格式化问题
        error_msg = str(error).replace('{', '{{').replace('}', '}}')
        self.logger.error(f"{analysis_type}分析失败 - 任务ID: {task_id}, 错误: {error_msg}")
    
    async def _call_llm(self, prompt: str, system_prompt: str = None, 
                       max_tokens: int = 10000) -> Optional[str]:
        """
        调用LLM进行分析
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        if not self.llm_client:
            raise ValueError("LLM客户端未初始化")
        
        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt or "你是一个专业的文档分析助手"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            # 安全地处理错误信息，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            self.logger.error(f"LLM调用失败: {error_msg}")
            return None
    
    async def _vector_search(self, query: str, top_k: int = 5) -> list:
        """
        向量数据库搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            相似文档列表
        """
        if not self.vector_db:
            self.logger.warning("向量数据库未初始化，跳过向量搜索")
            return []
        
        try:
            results = await self.vector_db.search(query, top_k=top_k)
            return results
        except Exception as e:
            # 安全地处理错误信息，避免格式化问题
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            self.logger.error(f"向量搜索失败: {error_msg}")
            return [] 