#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis任务存储管理器
用于管理文件解析任务的Redis存储和检索
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .redis_util import get_redis_manager

logger = logging.getLogger(__name__)

class RedisTaskStorage:
    """Redis任务存储管理器"""
    
    def __init__(self):
        """初始化Redis任务存储"""
        self.redis_manager = get_redis_manager()
        self.key_prefix = "task:"
        self.step_prefix = "step:"
        self.result_prefix = "result:"
        
    def _get_task_key(self, task_id: str) -> str:
        """获取任务键"""
        return f"{self.key_prefix}{task_id}"
    
    def _get_step_key(self, task_id: str, step_name: str) -> str:
        """获取步骤键"""
        return f"{self.step_prefix}{task_id}:{step_name}"
    
    def _get_result_key(self, task_id: str, result_type: str) -> str:
        """获取结果键"""
        return f"{self.result_prefix}{task_id}:{result_type}"
    
    def create_task(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        task_id: Optional[str] = None
    ) -> str:
        """创建新任务"""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        try:
            # 创建任务基本信息
            task_data = {
                "id": task_id,
                "filename": filename,
                "file_size": file_size,
                "file_type": file_type,
                "status": "pending",
                "progress": 0,
                "current_step": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": None,
                "error_message": None
            }
            
            # 存储任务信息（24小时过期）
            task_key = self._get_task_key(task_id)
            if not self.redis_manager.set(task_key, task_data, ttl=86400, use_prefix=False):
                raise Exception("无法保存任务到Redis")
            
            logger.info(f"任务创建成功(Redis): {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"创建任务失败(Redis): {e}")
            raise
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态
            progress: 进度
            current_step: 当前步骤
            error_message: 错误信息
        """
        try:
            task_key = self._get_task_key(task_id)
            task_data = self.redis_manager.get(task_key, use_prefix=False, default={})
            
            if not task_data:
                raise Exception(f"任务不存在: {task_id}")
            
            # 更新任务数据
            task_data["status"] = status
            task_data["updated_at"] = datetime.now().isoformat()
            
            if progress is not None:
                task_data["progress"] = progress
            
            if current_step is not None:
                task_data["current_step"] = current_step
            
            if error_message is not None:
                task_data["error_message"] = error_message
            
            if status in ['completed', 'fully_completed']:
                task_data["completed_at"] = datetime.now().isoformat()
            
            # 保存到Redis
            self.redis_manager.set(task_key, task_data, ttl=86400, use_prefix=False)
            logger.info(f"任务状态更新成功(Redis): {task_id} -> {status}")
            
        except Exception as e:
            logger.error(f"更新任务状态失败(Redis): {e}")
            raise
    
    def update_step_status(
        self,
        task_id: str,
        step_name: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        result_data: Optional[Dict] = None
    ):
        """
        更新步骤状态
        
        Args:
            task_id: 任务ID
            step_name: 步骤名称
            status: 状态
            progress: 进度
            error_message: 错误信息
            result_data: 结果数据
        """
        try:
            step_key = self._get_step_key(task_id, step_name)
            step_data = self.redis_manager.get(step_key, use_prefix=False, default={})
            
            if not step_data:
                step_data = {
                    "task_id": task_id,
                    "step_name": step_name,
                    "step_status": "pending",
                    "step_progress": 0,
                    "started_at": None,
                    "completed_at": None,
                    "error_message": None,
                    "result_data": None
                }
            
            # 更新步骤数据
            step_data["step_status"] = status
            
            if progress is not None:
                step_data["step_progress"] = progress
            
            if error_message is not None:
                step_data["error_message"] = error_message
            
            if result_data is not None:
                step_data["result_data"] = result_data
            
            if status == 'started' and step_data["started_at"] is None:
                step_data["started_at"] = datetime.now().isoformat()
            
            if status in ['completed', 'failed']:
                step_data["completed_at"] = datetime.now().isoformat()
            
            # 保存到Redis
            self.redis_manager.set(step_key, step_data, ttl=86400, use_prefix=False)
            logger.info(f"步骤状态更新成功(Redis): {task_id}:{step_name} -> {status}")
            
        except Exception as e:
            logger.error(f"更新步骤状态失败(Redis): {e}")
            raise
    
    def save_parsing_result(self, task_id: str, result: Dict):
        """保存文档解析结果到Redis"""
        try:
            result_key = self._get_result_key(task_id, "parsing")
            result_data = {
                "task_id": task_id,
                "result_type": "parsing",
                "result": result,
                "saved_at": datetime.now().isoformat()
            }
            
            self.redis_manager.set(result_key, result_data, ttl=86400, use_prefix=False)
            logger.info(f"文档解析结果保存成功(Redis): {task_id}")
            
        except Exception as e:
            logger.error(f"保存文档解析结果失败(Redis): {e}")
            raise
    
    def save_content_analysis(self, task_id: str, analysis: Dict):
        """保存内容分析结果到Redis"""
        try:
            result_key = self._get_result_key(task_id, "content_analysis")
            result_data = {
                "task_id": task_id,
                "result_type": "content_analysis",
                "result": analysis,
                "saved_at": datetime.now().isoformat()
            }
            
            self.redis_manager.set(result_key, result_data, ttl=86400, use_prefix=False)
            logger.info(f"内容分析结果保存成功(Redis): {task_id}")
            
        except Exception as e:
            logger.error(f"保存内容分析结果失败(Redis): {e}")
            raise
    
    def save_ai_analysis(self, task_id: str, analysis: Dict):
        """保存AI分析结果到Redis"""
        try:
            result_key = self._get_result_key(task_id, "ai_analysis")
            result_data = {
                "task_id": task_id,
                "result_type": "ai_analysis",
                "result": analysis,
                "saved_at": datetime.now().isoformat()
            }
            
            self.redis_manager.set(result_key, result_data, ttl=86400, use_prefix=False)
            logger.info(f"AI分析结果保存成功(Redis): {task_id}")
            
        except Exception as e:
            logger.error(f"保存AI分析结果失败(Redis): {e}")
            raise
    
    def save_markdown_content(self, task_id: str, markdown_content: str):
        """保存Markdown内容到Redis"""
        try:
            result_key = self._get_result_key(task_id, "markdown")
            result_data = {
                "task_id": task_id,
                "result_type": "markdown",
                "content": markdown_content,
                "saved_at": datetime.now().isoformat()
            }
            
            self.redis_manager.set(result_key, result_data, ttl=86400, use_prefix=False)
            logger.info(f"Markdown内容保存成功(Redis): {task_id}")
            
        except Exception as e:
            logger.error(f"保存Markdown内容失败(Redis): {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        try:
            task_key = self._get_task_key(task_id)
            task_data = self.redis_manager.get(task_key, use_prefix=False)
            
            if not task_data:
                return None
            
            # 获取所有分析结果
            parsing_result = self.get_parsing_result(task_id)
            content_analysis = self.get_content_analysis(task_id)
            ai_analysis = self.get_ai_analysis(task_id)
            
            # 组合完整的任务信息
            task_data["parsing_result"] = parsing_result
            task_data["content_analysis"] = content_analysis
            task_data["ai_analysis"] = ai_analysis
            
            return task_data
            
        except Exception as e:
            logger.error(f"获取任务失败(Redis): {e}")
            return None
    
    def get_parsing_result(self, task_id: str) -> Optional[Dict]:
        """获取文档解析结果"""
        try:
            result_key = self._get_result_key(task_id, "parsing")
            result_data = self.redis_manager.get(result_key, use_prefix=False)
            return result_data["result"] if result_data else None
        except Exception as e:
            logger.error(f"获取文档解析结果失败(Redis): {e}")
            return None
    
    def get_content_analysis(self, task_id: str) -> Optional[Dict]:
        """获取内容分析结果"""
        try:
            result_key = self._get_result_key(task_id, "content_analysis")
            result_data = self.redis_manager.get(result_key, use_prefix=False)
            return result_data["result"] if result_data else None
        except Exception as e:
            logger.error(f"获取内容分析结果失败(Redis): {e}")
            return None
    
    def get_ai_analysis(self, task_id: str) -> Optional[Dict]:
        """获取AI分析结果"""
        try:
            result_key = self._get_result_key(task_id, "ai_analysis")
            result_data = self.redis_manager.get(result_key, use_prefix=False)
            return result_data["result"] if result_data else None
        except Exception as e:
            logger.error(f"获取AI分析结果失败(Redis): {e}")
            return None
    
    def get_markdown_content(self, task_id: str) -> Optional[str]:
        """获取Markdown内容"""
        try:
            result_key = self._get_result_key(task_id, "markdown")
            result_data = self.redis_manager.get(result_key, use_prefix=False)
            return result_data["content"] if result_data else None
        except Exception as e:
            logger.error(f"获取Markdown内容失败(Redis): {e}")
            return None
    
    def get_all_tasks(self, limit: int = 100) -> List[Dict]:
        """
        获取所有任务
        
        Args:
            limit: 限制数量
            
        Returns:
            任务列表
        """
        try:
            # 获取所有任务键
            pattern = f"{self.key_prefix}*"
            client = self.redis_manager.client
            keys = client.keys(pattern)
            
            tasks = []
            for key in keys[:limit]:
                task_data = self.redis_manager.get(key.decode() if isinstance(key, bytes) else key, use_prefix=False)
                if task_data:
                    tasks.append(task_data)
            
            # 按创建时间倒序排列
            tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return tasks
            
        except Exception as e:
            logger.error(f"获取所有任务失败(Redis): {e}")
            return []
    
    def delete_task(self, task_id: str):
        """
        删除任务及其所有相关数据
        
        Args:
            task_id: 任务ID
        """
        try:
            # 删除任务基本信息
            task_key = self._get_task_key(task_id)
            self.redis_manager.delete(task_key, use_prefix=False)
            
            # 删除步骤信息
            steps = ['document_parsing', 'content_analysis', 'ai_analysis', 'document_generation']
            for step in steps:
                step_key = self._get_step_key(task_id, step)
                self.redis_manager.delete(step_key, use_prefix=False)
            
            # 删除结果数据
            result_types = ['parsing', 'content_analysis', 'ai_analysis', 'markdown']
            for result_type in result_types:
                result_key = self._get_result_key(task_id, result_type)
                self.redis_manager.delete(result_key, use_prefix=False)
            
            logger.info(f"任务删除成功(Redis): {task_id}")
            
        except Exception as e:
            logger.error(f"删除任务失败(Redis): {e}")
            raise
    
    def clear_expired_tasks(self, days: int = 7):
        """
        清理过期任务
        
        Args:
            days: 保留天数
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            tasks = self.get_all_tasks()
            deleted_count = 0
            
            for task in tasks:
                created_at = datetime.fromisoformat(task.get("created_at", ""))
                if created_at < cutoff_date:
                    self.delete_task(task["id"])
                    deleted_count += 1
            
            logger.info(f"清理过期任务完成(Redis): 删除了 {deleted_count} 个任务")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理过期任务失败(Redis): {e}")
            return 0

# 全局Redis任务存储实例
_redis_task_storage = None

def get_redis_task_storage() -> RedisTaskStorage:
    """获取全局Redis任务存储实例"""
    global _redis_task_storage
    if _redis_task_storage is None:
        _redis_task_storage = RedisTaskStorage()
    return _redis_task_storage 