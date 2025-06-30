#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown内容Redis存储管理器
专门用于存储和管理Markdown内容
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict
from .redis_util import get_redis_manager

# 获取日志器
logger = logging.getLogger('markdown_storage')

class MarkdownStorage:
    """
    Markdown内容Redis存储管理器
    提供简单的Markdown内容存储和获取功能
    """
    
    def __init__(self, redis_manager = None):
        """
        初始化Markdown存储管理器
        
        Args:
            redis_manager: Redis管理器实例，如果为None则创建新实例
        """
        self.redis_manager = redis_manager or get_redis_manager()
        self.key_prefix = "markdown:"
        self.default_ttl = 86400 * 7  # 7天过期时间
        
        logger.info("Markdown存储管理器初始化完成")
    
    def _get_content_key(self, task_id: str) -> str:
        """生成Markdown内容的Redis键"""
        return f"{self.key_prefix}{task_id}"
    
    def save_markdown(self, task_id: str, content: str) -> bool:
        """
        保存Markdown内容
        
        Args:
            task_id: 任务ID
            content: Markdown内容
            
        Returns:
            bool: 保存是否成功
        """
        try:
            current_time = datetime.now()
            
            # 构造内容数据
            content_data = {
                "task_id": task_id,
                "content": content,
                "content_length": len(content),
                "saved_at": current_time.isoformat()
            }
            
            # 保存内容到Redis
            content_key = self._get_content_key(task_id)
            success = self.redis_manager.set(content_key, content_data, ttl=self.default_ttl, use_prefix=False)
            
            if success:
                logger.info(f"Markdown内容保存成功: 任务ID={task_id}, 长度={len(content)}")
            else:
                logger.error(f"Markdown内容保存失败: 任务ID={task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"保存Markdown内容失败: 任务ID={task_id}, 错误={e}")
            return False
    
    def get_markdown_content_only(self, task_id: str) -> Optional[str]:
        """
        获取Markdown内容字符串
        
        Args:
            task_id: 任务ID
            
        Returns:
            str: Markdown内容字符串，如果不存在则返回None
        """
        try:
            content_key = self._get_content_key(task_id)
            content_data = self.redis_manager.get(content_key, use_prefix=False)
            
            if content_data:
                logger.info(f"Markdown内容获取成功: 任务ID={task_id}")
                return content_data.get("content")
            else:
                logger.info(f"Markdown内容不存在: 任务ID={task_id}")
                return None
                
        except Exception as e:
            logger.error(f"获取Markdown内容失败: 任务ID={task_id}, 错误={e}")
            return None
    
    def delete_markdown(self, task_id: str) -> bool:
        """
        删除Markdown内容
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            content_key = self._get_content_key(task_id)
            success = self.redis_manager.delete(content_key, use_prefix=False)
            
            if success:
                logger.info(f"Markdown内容删除成功: 任务ID={task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"删除Markdown内容失败: 任务ID={task_id}, 错误={e}")
            return False

# 全局Markdown存储实例
_markdown_storage = None

def get_markdown_storage() -> MarkdownStorage:
    """获取全局Markdown存储实例"""
    global _markdown_storage
    if _markdown_storage is None:
        _markdown_storage = MarkdownStorage()
    return _markdown_storage 