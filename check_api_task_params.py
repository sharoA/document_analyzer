#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def check_api_task_params():
    conn = sqlite3.connect('coding_agent_workflow.db')
    cursor = conn.cursor()
    
    print('=== API任务详细信息 ===')
    cursor.execute('SELECT task_id, service_name, task_type, parameters FROM execution_tasks WHERE task_type = ?', ('api',))
    
    for row in cursor.fetchall():
        task_id, service_name, task_type, params_json = row
        print(f'任务ID: {task_id}')
        print(f'服务名: {service_name}')
        print(f'任务类型: {task_type}')
        
        try:
            if params_json:
                params = json.loads(params_json)
                print(f'参数: {json.dumps(params, ensure_ascii=False, indent=2)}')
            else:
                print('参数: 无')
        except Exception as e:
            print(f'参数解析失败: {e}')
        
        print('---')
    
    print('\n=== 所有任务的接口规格信息 ===')
    cursor.execute('SELECT task_id, service_name, parameters FROM execution_tasks')
    
    for row in cursor.fetchall():
        task_id, service_name, params_json = row
        try:
            if params_json:
                params = json.loads(params_json)
                interface_spec = params.get('interface_spec')
                if interface_spec:
                    print(f'任务 {task_id} ({service_name}):')
                    print(f'  接口规格: {json.dumps(interface_spec, ensure_ascii=False, indent=4)}')
                    print('---')
        except:
            continue
    
    conn.close()

if __name__ == '__main__':
    check_api_task_params() 