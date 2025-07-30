#!/usr/bin/env python3
"""
简单查询当前分析任务的进度
"""

import requests
import json

def check_progress():
    """检查进度"""
    task_id = "c13ecd0b-8907-4085-be57-528174abc9e6"  # 从日志中看到的任务ID
    progress_url = f"http://localhost:8082/api/v2/analysis/progress/{task_id}"
    
    try:
        response = requests.get(progress_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"任务ID: {task_id}")
            print(f"状态: {data.get('status')}")
            print(f"进度: {data.get('progress')}%")
            print(f"消息: {data.get('message')}")
            print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 如果完成了，尝试获取表单数据
            if data.get('status') in ['completed', 'fully_completed']:
                print("\n=== 尝试获取表单数据 ===")
                form_url = f"http://localhost:8082/api/file/design-form/{task_id}"
                form_response = requests.get(form_url, timeout=10)
                print(f"表单数据状态码: {form_response.status_code}")
                if form_response.status_code == 200:
                    form_data = form_response.json()
                    print(f"项目名称: {form_data.get('project_name')}")
                    print(f"服务数量: {form_data.get('service_numbers')}")
                else:
                    print(f"表单数据获取失败: {form_response.text}")
        else:
            print(f"查询失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"查询异常: {e}")

if __name__ == "__main__":
    check_progress()