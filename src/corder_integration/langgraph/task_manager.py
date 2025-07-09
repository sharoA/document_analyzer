#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理工具 - 用于各个节点领取和更新任务状态
"""

import sqlite3
import json
import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NodeTaskManager:
    """节点任务管理器 - 专门用于节点任务操作"""
    
    def __init__(self, db_path: str = None):
        # 🔧 使用绝对路径，避免相对路径问题
        if db_path is None:
            # 使用项目根目录的数据库文件
            project_root = Path(__file__).parent.parent.parent.parent  # 回到项目根目录
            db_path = project_root / "coding_agent_workflow.db"
        
        self.db_path = str(db_path)
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # 确保数据库文件存在
        if not os.path.exists(self.db_path):
            logger.error(f"❌ 数据库文件不存在: {self.db_path}")
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        
        logger.info(f"📂 使用数据库: {self.db_path}")
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(
            self.db_path, 
            timeout=30.0,
            isolation_level=None
        )
        conn.execute("PRAGMA synchronous=NORMAL") 
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        return conn
    
    def _execute_with_retry(self, operation_func, *args, **kwargs):
        """带重试机制的数据库操作"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e):
                    logger.warning(f"🔄 数据库锁定，第{attempt + 1}次重试...")
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"❌ 数据库操作失败: {e}")
                raise e
        
        logger.error(f"❌ 数据库操作重试{self.max_retries}次后仍然失败: {last_error}")
        raise last_error
    
    def get_node_tasks(self, task_types: List[str]) -> List[Dict[str, Any]]:
        """获取指定类型的可执行任务（检查依赖关系）"""
        def _get_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                task_type_placeholders = ','.join(['?' for _ in task_types])
                
                cursor.execute(f"""
                    SELECT task_id, service_name, task_type, priority, dependencies,
                           estimated_duration, description, deliverables,
                           implementation_details, completion_criteria, parameters,
                           status
                    FROM execution_tasks 
                    WHERE task_type IN ({task_type_placeholders})
                    ORDER BY priority ASC, created_at ASC
                """, task_types)
                
                all_tasks = []
                executable_tasks = []
                
                for row in cursor.fetchall():
                    # 安全解析JSON字段
                    def safe_json_loads(json_str, default_value):
                        try:
                            if not json_str:
                                return default_value
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ JSON解析失败，使用默认值: {e}")
                            return default_value
                    
                    task = {
                        'task_id': row[0],
                        'service_name': row[1],
                        'task_type': row[2],
                        'priority': row[3],
                        'dependencies': safe_json_loads(row[4], []),
                        'estimated_duration': row[5],
                        'description': row[6],
                        'deliverables': safe_json_loads(row[7], []),
                        'implementation_details': row[8],
                        'completion_criteria': row[9],
                        'parameters': safe_json_loads(row[10], {}),
                        'status': row[11]
                    }
                    all_tasks.append(task)
                
                # 获取所有已完成的任务ID
                cursor.execute("SELECT task_id FROM execution_tasks WHERE status = 'completed'")
                completed_task_ids = set(row[0] for row in cursor.fetchall())
                
                # 检查依赖关系，筛选可执行任务
                for task in all_tasks:
                    if task['status'] == 'pending':
                        # 检查所有依赖是否已完成
                        dependencies = task['dependencies']
                        if not dependencies:  # 没有依赖的任务可以直接执行
                            executable_tasks.append(task)
                        else:
                            # 有依赖的任务，检查依赖是否都已完成
                            dependencies_met = all(dep_id in completed_task_ids for dep_id in dependencies)
                            if dependencies_met:
                                executable_tasks.append(task)
                
                return executable_tasks
        
        try:
            return self._execute_with_retry(_get_operation)
        except Exception as e:
            logger.error(f"❌ 获取节点任务失败: {e}")
            return []
    
    def claim_task(self, task_id: str, node_name: str) -> bool:
        """领取任务（将状态设置为in_progress）"""
        def _claim_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查任务是否仍为pending状态
                cursor.execute("SELECT status FROM execution_tasks WHERE task_id = ?", (task_id,))
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"⚠️ 任务 {task_id} 不存在")
                    return False
                
                if result[0] != 'pending':
                    logger.warning(f"⚠️ 任务 {task_id} 状态为 {result[0]}，无法领取")
                    return False
                
                # 更新任务状态为in_progress
                cursor.execute("""
                    UPDATE execution_tasks 
                    SET status = 'in_progress', 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                """, (task_id,))
                
                logger.info(f"✅ 任务 {task_id} 已被 {node_name} 领取")
                return True
        
        try:
            return self._execute_with_retry(_claim_operation)
        except Exception as e:
            logger.error(f"❌ 领取任务失败: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: str, result_data: Dict[str, Any] = None) -> bool:
        """更新任务状态"""
        def _update_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 准备更新数据
                update_params = [status]
                update_sql = "UPDATE execution_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
                
                # 如果有结果数据，更新parameters字段
                if result_data:
                    # 获取当前参数
                    cursor.execute("SELECT parameters FROM execution_tasks WHERE task_id = ?", (task_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        try:
                            current_params = json.loads(result[0] or '{}')
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ 解析现有参数失败，使用空字典: {e}")
                            current_params = {}
                        
                        # 合并结果数据
                        current_params.update(result_data)
                        
                        update_sql += ", parameters = ?"
                        update_params.append(json.dumps(current_params))
                
                update_sql += " WHERE task_id = ?"
                update_params.append(task_id)
                
                cursor.execute(update_sql, update_params)
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ 任务 {task_id} 状态更新为 {status}")
                    return True
                else:
                    logger.warning(f"⚠️ 任务 {task_id} 状态更新失败，任务不存在")
                    return False
        
        try:
            return self._execute_with_retry(_update_operation)
        except Exception as e:
            logger.error(f"❌ 更新任务状态失败: {e}")
            return False
    
    def get_task_statistics(self) -> Dict[str, int]:
        """获取任务统计信息"""
        def _stats_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM execution_tasks 
                    GROUP BY status
                """)
                
                stats = {}
                for row in cursor.fetchall():
                    stats[row[0]] = row[1]
                
                return stats
        
        try:
            return self._execute_with_retry(_stats_operation)
        except Exception as e:
            logger.error(f"❌ 获取任务统计失败: {e}")
            return {}
    
    def _save_single_task(self, task_data: Dict[str, Any]) -> bool:
        """保存单个任务到数据库"""
        def _save_operation():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 确保execution_tasks表存在
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS execution_tasks (
                        task_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        priority INTEGER DEFAULT 0,
                        dependencies TEXT DEFAULT '[]',
                        estimated_duration INTEGER DEFAULT 0,
                        description TEXT,
                        deliverables TEXT DEFAULT '[]',
                        implementation_details TEXT,
                        completion_criteria TEXT,
                        parameters TEXT DEFAULT '{}',
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 插入任务
                cursor.execute("""
                    INSERT OR REPLACE INTO execution_tasks (
                        task_id, service_name, task_type, priority, dependencies,
                        estimated_duration, description, deliverables,
                        implementation_details, completion_criteria, parameters, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data['task_id'],
                    task_data['service_name'],
                    task_data['task_type'],
                    task_data['priority'],
                    json.dumps(task_data['dependencies']),
                    task_data['estimated_duration'],
                    task_data['description'],
                    json.dumps(task_data['deliverables']),
                    task_data['implementation_details'],
                    task_data['completion_criteria'],
                    json.dumps(task_data['parameters']),
                    task_data['status']
                ))
                
                return True
        
        try:
            return self._execute_with_retry(_save_operation)
        except Exception as e:
            logger.error(f"❌ 保存任务失败: {e}")
            return False 