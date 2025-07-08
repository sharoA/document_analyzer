#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sqlite3
import os

def check_database():
    """检查数据库表结构"""
    print(f"当前目录: {os.getcwd()}")
    
    db_file = "coding_agent_workflow.db"
    if not os.path.exists(db_file):
        print(f"❌ 数据库文件不存在: {db_file}")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 数据库表: {tables}")
        
        # 如果有execution_tasks表，检查其结构
        if 'execution_tasks' in tables:
            cursor.execute("PRAGMA table_info(execution_tasks)")
            columns = cursor.fetchall()
            print(f"📊 execution_tasks表结构:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # 检查数据
            cursor.execute("SELECT COUNT(*) FROM execution_tasks")
            count = cursor.fetchone()[0]
            print(f"📈 execution_tasks记录数: {count}")
            
            if count > 0:
                cursor.execute("SELECT task_id, task_type, status FROM execution_tasks LIMIT 5")
                tasks = cursor.fetchall()
                print(f"🔍 前5条任务:")
                for task in tasks:
                    print(f"  - {task[0]} ({task[1]}) - {task[2]}")
        else:
            print("❌ execution_tasks表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

if __name__ == "__main__":
    check_database() 