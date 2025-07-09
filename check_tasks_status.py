#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def check_tasks_status():
    conn = sqlite3.connect('coding_agent_workflow.db')
    cursor = conn.cursor()
    
    print('=== 所有任务状态 ===')
    cursor.execute('SELECT task_id, service_name, task_type, status, dependencies FROM execution_tasks ORDER BY task_id')
    all_tasks = cursor.fetchall()
    
    for row in all_tasks:
        deps = json.loads(row[4] or '[]')
        print(f'{row[0]}: {row[1]} - {row[2]} - {row[3]} - 依赖: {deps}')
    
    print('\n=== 待执行任务 (pending) ===')
    cursor.execute('SELECT task_id, service_name, task_type, dependencies FROM execution_tasks WHERE status = "pending"')
    pending_tasks = cursor.fetchall()
    
    for row in pending_tasks:
        deps = json.loads(row[3] or '[]')
        print(f'{row[0]}: {row[1]} - {row[2]} - 依赖: {deps}')
    
    print('\n=== 已完成任务 ===')
    cursor.execute('SELECT task_id FROM execution_tasks WHERE status = "completed"')
    completed_ids = [row[0] for row in cursor.fetchall()]
    print(f'已完成任务ID: {completed_ids}')
    
    print('\n=== 智能编码节点支持的任务类型 ===')
    supported_types = ["code_analysis", "database", "api", "config"]
    cursor.execute(f'''SELECT task_id, service_name, task_type, status, dependencies 
                      FROM execution_tasks 
                      WHERE task_type IN ({",".join(["?" for _ in supported_types])})
                      ORDER BY task_id''', supported_types)
    
    for row in cursor.fetchall():
        deps = json.loads(row[4] or '[]')
        print(f'{row[0]}: {row[1]} - {row[2]} - {row[3]} - 依赖: {deps}')
    
    conn.close()

if __name__ == '__main__':
    check_tasks_status() 