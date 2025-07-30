#!/usr/bin/env python3
"""
快速测试V2分析接口
"""

import requests
import json
import base64

def quick_test():
    """快速测试"""
    
    # 简单测试内容
    test_content = """用户管理系统需求文档

项目背景：
本项目旨在构建一个用户管理系统，支持用户注册、登录、权限管理等功能。

功能需求：
1. 用户注册 - 用户可以通过邮箱注册账号
2. 用户登录 - 支持邮箱登录
3. 权限管理 - 支持角色权限控制"""
    
    # 编码为base64
    content_base64 = base64.b64encode(test_content.encode('utf-8')).decode('ascii')
    
    # 测试数据
    test_data = {
        "file_info": {
            "name": "快速测试.txt",
            "content": content_base64,
            "type": "text/plain"
        }
    }
    
    print("🚀 开始快速测试...")
    
    try:
        # 发送请求
        url = "http://localhost:8082/api/v2/analysis/start"
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ 测试启动成功，任务ID: {task_id}")
            return task_id
        else:
            print(f"❌ 启动失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return None

def check_task_status(task_id):
    """检查任务状态"""
    try:
        url = f"http://localhost:8082/api/v2/analysis/progress/{task_id}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("overall_status", "")
            progress = data.get("overall_progress", 0)
            print(f"📊 任务状态: {status}, 进度: {progress}%")
            return status, progress
        else:
            print(f"❌ 状态查询失败: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")
        return None, None

def check_form_data(task_id):
    """检查表单数据"""
    try:
        url = f"http://localhost:8082/api/file/design-form/{task_id}"
        response = requests.get(url, timeout=5)
        
        print(f"📋 表单数据响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            form_data = data.get("form_data", {})
            print(f"✅ 表单数据获取成功")
            print(f"项目名称: {form_data.get('project_name', 'N/A')}")
            print(f"服务数量: {form_data.get('service_numbers', 'N/A')}")
            return True
        else:
            print(f"❌ 表单数据获取失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 表单数据查询异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("快速测试V2分析接口")
    print("=" * 50)
    
    # 启动测试
    task_id = quick_test()
    if not task_id:
        print("测试启动失败")
        exit(1)
    
    print(f"\n等待3秒后检查状态...")
    import time
    time.sleep(3)
    
    # 检查状态
    status, progress = check_task_status(task_id)
    print(f"当前状态: {status}")
    
    # 无论什么状态，都尝试检查表单数据
    print(f"\n检查表单数据...")
    form_success = check_form_data(task_id)
    
    print(f"\n测试完成")