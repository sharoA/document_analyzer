#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def check_git_tasks():
    conn = sqlite3.connect('coding_agent_workflow.db')
    cursor = conn.cursor()
    
    # 检查git_clone任务
    print("=== Git Clone 任务状态 ===")
    cursor.execute('''
        SELECT task_id, task_type, status, assigned_node, result, created_at, updated_at 
        FROM execution_tasks 
        WHERE task_type = 'git_clone' 
        ORDER BY task_id
    ''')
    
    git_clone_tasks = cursor.fetchall()
    for task in git_clone_tasks:
        task_id, task_type, status, assigned_node, result, created_at, updated_at = task
        result_summary = "无结果"
        if result:
            try:
                result_data = json.loads(result)
                if result_data.get('success'):
                    result_summary = f"成功: {result_data.get('message', 'N/A')}"
                else:
                    result_summary = f"失败: {result_data.get('message', 'N/A')}"
            except:
                result_summary = "结果解析失败"
        
        print(f"  {task_id}: {status} - {assigned_node} - {result_summary}")
        print(f"    创建: {created_at}, 更新: {updated_at}")
    
    # 检查git_extraction任务
    print("\n=== Git Extraction 任务状态 ===")
    cursor.execute('''
        SELECT task_id, task_type, status, assigned_node, result, created_at, updated_at 
        FROM execution_tasks 
        WHERE task_type = 'git_extraction' 
        ORDER BY task_id
    ''')
    
    git_extraction_tasks = cursor.fetchall()
    for task in git_extraction_tasks:
        task_id, task_type, status, assigned_node, result, created_at, updated_at = task
        result_summary = "无结果"
        if result:
            try:
                result_data = json.loads(result)
                if result_data.get('success'):
                    repos = result_data.get('extracted_repositories', [])
                    result_summary = f"成功: 提取了{len(repos)}个仓库"
                else:
                    result_summary = f"失败: {result_data.get('message', 'N/A')}"
            except:
                result_summary = "结果解析失败"
        
        print(f"  {task_id}: {status} - {assigned_node} - {result_summary}")
        print(f"    创建: {created_at}, 更新: {updated_at}")
    
    conn.close()

if __name__ == "__main__":
    check_git_tasks() 