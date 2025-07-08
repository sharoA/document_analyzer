#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据库查询问题
"""

import sqlite3
import json

def debug_database_query():
    """调试数据库查询"""
    try:
        print("🔍 开始调试数据库查询...")
        
        # 连接数据库
        conn = sqlite3.connect('coding_agent_workflow.db')
        cursor = conn.cursor()
        
        # 1. 查看所有任务ID
        print("\n=== 1. 所有任务ID ===")
        cursor.execute('SELECT task_id FROM execution_tasks ORDER BY task_id')
        all_tasks = cursor.fetchall()
        print(f'总任务数: {len(all_tasks)}')
        for task in all_tasks:
            print(f'  {task[0]}')
        
        # 2. 测试具体任务查询
        print("\n=== 2. 测试具体任务查询 ===")
        cursor.execute("SELECT task_id FROM execution_tasks WHERE task_id = 'task_001'")
        task_001 = cursor.fetchone()
        print(f"task_001查询结果: {task_001}")
        
        # 3. 测试IN查询
        print("\n=== 3. 测试IN查询 ===")
        test_ids = ['task_001', 'task_002', 'task_003']
        placeholders = ','.join(['?' for _ in test_ids])
        query = f'SELECT task_id FROM execution_tasks WHERE task_id IN ({placeholders}) ORDER BY task_id'
        print(f'SQL查询: {query}')
        print(f'参数: {test_ids}')
        
        cursor.execute(query, test_ids)
        found_tasks = cursor.fetchall()
        print(f'找到任务数: {len(found_tasks)}')
        for task in found_tasks:
            print(f'  {task[0]}')
        
        # 4. 测试生成的任务ID
        print("\n=== 4. 测试生成的任务ID ===")
        task_ids = [f'task_{str(i).zfill(3)}' for i in range(1, 6)]  # 只测试前5个
        print(f'生成的task_ids: {task_ids}')
        
        placeholders = ','.join(['?' for _ in task_ids])
        cursor.execute(f'SELECT task_id FROM execution_tasks WHERE task_id IN ({placeholders}) ORDER BY task_id', task_ids)
        found_tasks2 = cursor.fetchall()
        print(f'找到任务数: {len(found_tasks2)}')
        for task in found_tasks2:
            print(f'  {task[0]}')
        
        # 5. 查看完整记录
        print("\n=== 5. 查看task_001完整记录 ===")
        cursor.execute('SELECT * FROM execution_tasks WHERE task_id = ? LIMIT 1', ('task_001',))
        full_record = cursor.fetchone()
        if full_record:
            print("找到完整记录:")
            cursor.execute("PRAGMA table_info(execution_tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            for i, col in enumerate(columns):
                print(f"  {col}: {full_record[i]}")
        else:
            print("未找到task_001记录")
        
        conn.close()
        print("\n✅ 调试完成")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")

if __name__ == "__main__":
    debug_database_query() 