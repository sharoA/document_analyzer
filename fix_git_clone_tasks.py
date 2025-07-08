#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def fix_git_clone_tasks():
    """检查并修复git_clone任务的问题"""
    conn = sqlite3.connect('coding_agent_workflow.db')
    cursor = conn.cursor()
    
    print("=== 检查Git Clone任务详情 ===")
    
    # 检查task_002和task_003的详细信息
    cursor.execute('''
        SELECT task_id, task_type, status, dependencies, parameters, description
        FROM execution_tasks 
        WHERE task_id IN ('task_002', 'task_003')
        ORDER BY task_id
    ''')
    
    tasks = cursor.fetchall()
    for task in tasks:
        task_id, task_type, status, dependencies, parameters, description = task
        print(f"\n任务: {task_id}")
        print(f"  类型: {task_type}")
        print(f"  状态: {status}")
        print(f"  依赖: {dependencies}")
        print(f"  参数: {parameters}")
        print(f"  描述: {description}")
        
        # 检查依赖是否已完成
        if dependencies:
            deps = json.loads(dependencies)
            print(f"  依赖任务: {deps}")
            
            for dep_id in deps:
                cursor.execute('SELECT status FROM execution_tasks WHERE task_id = ?', (dep_id,))
                dep_result = cursor.fetchone()
                if dep_result:
                    print(f"    {dep_id}: {dep_result[0]}")
                else:
                    print(f"    {dep_id}: 不存在")
    
    # 检查git_extraction任务状态
    print("\n=== 检查Git Extraction任务状态 ===")
    cursor.execute('''
        SELECT task_id, status, result
        FROM execution_tasks 
        WHERE task_type = 'git_extraction'
        ORDER BY task_id
    ''')
    
    extraction_tasks = cursor.fetchall()
    for task in extraction_tasks:
        task_id, status, result = task
        print(f"任务 {task_id}: {status}")
        if result and status == 'completed':
            try:
                result_data = json.loads(result)
                if 'extracted_repositories' in result_data:
                    repos = result_data['extracted_repositories']
                    print(f"  提取的仓库: {len(repos)}个")
                    for i, repo in enumerate(repos):
                        print(f"    {i+1}. {repo.get('name', 'N/A')}: {repo.get('url', 'N/A')}")
            except:
                print(f"  结果解析失败")
    
    # 修复方案：如果依赖已满足，确保任务参数正确
    print("\n=== 修复建议 ===")
    
    # 检查是否存在completed的git_extraction任务
    cursor.execute('''
        SELECT task_id, result FROM execution_tasks 
        WHERE task_type = 'git_extraction' AND status = 'completed'
        LIMIT 1
    ''')
    
    extraction_result = cursor.fetchone()
    if extraction_result:
        extraction_id, result_json = extraction_result
        try:
            result_data = json.loads(result_json)
            repos = result_data.get('extracted_repositories', [])
            
            if len(repos) >= 2:
                # 更新task_002和task_003的参数，确保它们有明确的仓库信息
                for i, task_id in enumerate(['task_002', 'task_003']):
                    if i < len(repos):
                        repo = repos[i]
                        
                        # 获取当前参数
                        cursor.execute('SELECT parameters FROM execution_tasks WHERE task_id = ?', (task_id,))
                        current_params_result = cursor.fetchone()
                        current_params = json.loads(current_params_result[0] or '{}') if current_params_result else {}
                        
                        # 添加仓库信息
                        current_params.update({
                            'repo_url': repo['url'],
                            'repo_name': repo['name'],
                            'source_extraction_task': extraction_id
                        })
                        
                        # 更新任务参数
                        cursor.execute('''
                            UPDATE execution_tasks 
                            SET parameters = ?
                            WHERE task_id = ?
                        ''', (json.dumps(current_params), task_id))
                        
                        print(f"✅ 已更新 {task_id} 的参数，添加仓库信息: {repo['name']}")
        except Exception as e:
            print(f"❌ 处理extraction结果时出错: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ 检查和修复完成")

if __name__ == "__main__":
    fix_git_clone_tasks() 