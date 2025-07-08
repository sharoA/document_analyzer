#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的任务
"""

import sqlite3
import json

def check_database_tasks():
    """检查数据库中的任务"""
    
    # 检查多个可能的数据库文件
    db_files = [
        "coding_agent_workflow.db",
        "src/apis/tasks.db", 
        "tasks.db",
        "test_node_tasks.db"
    ]
    
    for db_file in db_files:
        try:
            print(f"\n📋 检查数据库: {db_file}")
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_tasks'")
            if not cursor.fetchone():
                print(f"  ❌ 表 execution_tasks 不存在")
                conn.close()
                continue
            
            # 获取任务数据
            cursor.execute("""
                SELECT task_id, service_name, task_type, status, dependencies, 
                       implementation_details, completion_criteria
                FROM execution_tasks 
                ORDER BY task_type, task_id
            """)
            
            tasks = cursor.fetchall()
            print(f"  📊 找到 {len(tasks)} 个任务:")
            
            for task in tasks:
                task_id, service_name, task_type, status, dependencies, impl_details, criteria = task
                print(f"    🔸 {task_id}")
                print(f"      📝 服务: {service_name}")
                print(f"      🏷️  类型: {task_type}")
                print(f"      📊 状态: {status}")
                print(f"      🔗 依赖: {dependencies}")
                print(f"      📋 实现详情: {impl_details[:100] if impl_details else 'None'}...")
                print(f"      ✅ 完成标准: {criteria[:100] if criteria else 'None'}...")
                print()
            
            # 检查Git相关任务
            cursor.execute("""
                SELECT COUNT(*) FROM execution_tasks 
                WHERE task_type IN ('git_extraction', 'git_clone') AND status = 'pending'
            """)
            git_pending_count = cursor.fetchone()[0]
            print(f"  🔍 pending状态的Git任务数量: {git_pending_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"  ❌ 检查 {db_file} 失败: {e}")

if __name__ == "__main__":
    check_database_tasks() 