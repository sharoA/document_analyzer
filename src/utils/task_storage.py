#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务存储管理器
用于管理文件解析任务的存储和检索
"""

import os
import sqlite3
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TaskStorage:
    """任务存储管理器"""
    
    def __init__(self, db_path: str = "tasks.db"):
        """
        初始化任务存储
        
        Args:
            db_path: 数据库文件路径
        """
        # 确保数据库文件在项目根目录
        if not os.path.isabs(db_path):
            self.db_path = os.path.join(os.getcwd(), db_path)
        else:
            self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_size INTEGER,
                        file_type TEXT,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        result_data TEXT,
                        parsing_result TEXT,
                        content_analysis TEXT,
                        ai_analysis TEXT,
                        markdown_content TEXT
                    )
                ''')
                
                # 检查并添加markdown_content字段（如果表已存在）
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN markdown_content TEXT")
                    logger.info("已添加markdown_content字段到现有数据库表")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        # 字段已存在，忽略错误
                        pass
                    else:
                        logger.warning(f"添加markdown_content字段时出现错误: {e}")
                
                # 创建步骤表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_steps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        step_name TEXT NOT NULL,
                        step_status TEXT DEFAULT 'pending',
                        step_progress INTEGER DEFAULT 0,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        result_data TEXT,
                        FOREIGN KEY (task_id) REFERENCES tasks (id)
                    )
                ''')
                
                conn.commit()
                logger.info("数据库初始化成功")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def create_task(
        self,
        filename: str,
        file_size: int,
        file_type: str,
        task_id: Optional[str] = None
    ) -> str:
        """
        创建新任务
        
        Args:
            filename: 文件名
            file_size: 文件大小
            file_type: 文件类型
            task_id: 任务ID（可选）
            
        Returns:
            任务ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO tasks (id, filename, file_size, file_type, status, progress)
                    VALUES (?, ?, ?, ?, 'pending', 0)
                ''', (task_id, filename, file_size, file_type))
                
                # 创建默认步骤
                steps = [
                    'document_parsing',
                    'content_analysis', 
                    'ai_analysis'
                ]
                
                for step in steps:
                    cursor.execute('''
                        INSERT INTO task_steps (task_id, step_name, step_status, step_progress)
                        VALUES (?, ?, 'pending', 0)
                    ''', (task_id, step))
                
                conn.commit()
                logger.info(f"任务创建成功: {task_id}")
                return task_id
                
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态
            progress: 进度
            error_message: 错误信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]
                
                if progress is not None:
                    update_fields.append("progress = ?")
                    params.append(progress)
                
                if error_message is not None:
                    update_fields.append("error_message = ?")
                    params.append(error_message)
                
                if status == 'completed':
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                params.append(task_id)
                
                cursor.execute(f'''
                    UPDATE tasks 
                    SET {", ".join(update_fields)}
                    WHERE id = ?
                ''', params)
                
                conn.commit()
                logger.info(f"任务状态更新成功: {task_id} -> {status}")
                
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["step_status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]
                
                if progress is not None:
                    update_fields.append("step_progress = ?")
                    params.append(progress)
                
                if error_message is not None:
                    update_fields.append("error_message = ?")
                    params.append(error_message)
                
                if result_data is not None:
                    update_fields.append("result_data = ?")
                    params.append(json.dumps(result_data, ensure_ascii=False))
                
                if status == 'running':
                    update_fields.append("started_at = CURRENT_TIMESTAMP")
                elif status == 'completed':
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                params.extend([task_id, step_name])
                
                cursor.execute(f'''
                    UPDATE task_steps 
                    SET {", ".join(update_fields)}
                    WHERE task_id = ? AND step_name = ?
                ''', params)
                
                conn.commit()
                logger.info(f"步骤状态更新成功: {task_id}/{step_name} -> {status}")
                
        except Exception as e:
            logger.error(f"更新步骤状态失败: {e}")
            raise
    
    def save_parsing_result(self, task_id: str, result: Dict):
        """保存解析结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE tasks 
                    SET parsing_result = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(result, ensure_ascii=False), task_id))
                
                conn.commit()
                logger.info(f"解析结果保存成功: {task_id}")
                
        except Exception as e:
            logger.error(f"保存解析结果失败: {e}")
            raise
    
    def save_content_analysis(self, task_id: str, analysis: Dict):
        """保存内容分析结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE tasks 
                    SET content_analysis = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(analysis, ensure_ascii=False), task_id))
                
                conn.commit()
                logger.info(f"内容分析结果保存成功: {task_id}")
                
        except Exception as e:
            logger.error(f"保存内容分析结果失败: {e}")
            raise
    
    def save_ai_analysis(self, task_id: str, analysis: Dict):
        """保存AI分析结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE tasks 
                    SET ai_analysis = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(analysis, ensure_ascii=False), task_id))
                
                conn.commit()
                logger.info(f"AI分析结果保存成功: {task_id}")
                
        except Exception as e:
            logger.error(f"保存AI分析结果失败: {e}")
            raise
    
    def save_markdown_content(self, task_id: str, markdown_content: str):
        """保存Markdown内容"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE tasks 
                    SET markdown_content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (markdown_content, task_id))
                
                conn.commit()
                logger.info(f"Markdown内容保存成功: {task_id}")
                
        except Exception as e:
            logger.error(f"保存Markdown内容失败: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM tasks WHERE id = ?
                ''', (task_id,))
                
                row = cursor.fetchone()
                if row:
                    task = dict(row)
                    
                    # 解析JSON字段
                    for field in ['result_data', 'parsing_result', 'content_analysis', 'ai_analysis']:
                        if task[field]:
                            try:
                                task[field] = json.loads(task[field])
                            except json.JSONDecodeError:
                                task[field] = None
                    
                    # 获取步骤信息
                    cursor.execute('''
                        SELECT * FROM task_steps WHERE task_id = ? ORDER BY id
                    ''', (task_id,))
                    
                    steps = []
                    for step_row in cursor.fetchall():
                        step = dict(step_row)
                        if step['result_data']:
                            try:
                                step['result_data'] = json.loads(step['result_data'])
                            except json.JSONDecodeError:
                                step['result_data'] = None
                        steps.append(step)
                    
                    task['steps'] = steps
                    return task
                
                return None
                
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
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
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                tasks = []
                for row in cursor.fetchall():
                    task = dict(row)
                    
                    # 解析JSON字段
                    for field in ['result_data', 'parsing_result', 'content_analysis', 'ai_analysis']:
                        if task[field]:
                            try:
                                task[field] = json.loads(task[field])
                            except json.JSONDecodeError:
                                task[field] = None
                    
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
    
    def delete_task(self, task_id: str):
        """
        删除任务
        
        Args:
            task_id: 任务ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除步骤
                cursor.execute('DELETE FROM task_steps WHERE task_id = ?', (task_id,))
                
                # 删除任务
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                
                conn.commit()
                logger.info(f"任务删除成功: {task_id}")
                
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            raise

# 全局任务存储实例
_task_storage = None

def get_task_storage() -> TaskStorage:
    """获取全局任务存储实例"""
    global _task_storage
    if _task_storage is None:
        _task_storage = TaskStorage()
    return _task_storage 