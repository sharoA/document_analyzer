#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试智能文档分析API
"""

import requests
import time
import json
import os

API_BASE = 'http://localhost:8082'

def test_health():
    """测试健康检查"""
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{API_BASE}/api/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_upload_analysis():
    """测试文件上传和分析"""
    print("\n2. 测试文件上传和分析...")
    
    # 创建测试文件
    test_content = """
# 测试需求文档

## 项目概述
这是一个测试项目，用于验证智能分析功能。

## 功能需求
1. 用户登录功能
2. 数据管理功能
3. 报表生成功能

## 技术要求
- 使用Python开发
- 数据库使用MySQL
- 前端使用Vue.js

## 变更记录
- v1.0: 初始版本
- v2.0: 新增报表功能
    """
    
    # 保存为临时文件
    test_file_path = "test_document.md"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # 上传文件
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.md', f, 'text/markdown')}
            response = requests.post(f"{API_BASE}/api/analysis", files=files)
        
        print(f"上传状态码: {response.status_code}")
        print(f"上传响应: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'started':
                task_id = result.get('task_id')
                print(f"分析已启动，任务ID: {task_id}")
                return task_id
        
        return None
        
    except Exception as e:
        print(f"上传失败: {e}")
        return None
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_progress_polling(task_id):
    """测试进度轮询"""
    print(f"\n3. 测试进度轮询 (任务ID: {task_id})...")
    
    max_attempts = 30  # 最多轮询30次（1分钟）
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE}/api/analysis/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                progress = data.get('progress', {})
                
                print(f"轮询 {attempt + 1}: 状态={progress.get('status')}, 进度={progress.get('overall_progress', 0)}%")
                
                # 显示各阶段状态
                stages = progress.get('stages', {})
                for stage, info in stages.items():
                    print(f"  - {stage}: {info.get('status')} ({info.get('progress', 0)}%)")
                
                # 检查是否完成
                if progress.get('status') in ['completed', 'error', 'cancelled']:
                    print(f"分析完成，最终状态: {progress.get('status')}")
                    return progress.get('status') == 'completed'
                
            else:
                print(f"获取进度失败: {response.status_code}")
                break
                
        except Exception as e:
            print(f"轮询失败: {e}")
            break
        
        attempt += 1
        time.sleep(2)  # 等待2秒后再次轮询
    
    print("轮询超时")
    return False

def test_get_result(task_id):
    """测试获取分析结果"""
    print(f"\n4. 测试获取分析结果 (任务ID: {task_id})...")
    
    try:
        response = requests.get(f"{API_BASE}/api/analysis/{task_id}/result")
        
        print(f"获取结果状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"结果状态: {data.get('status')}")
            print(f"结果格式: {data.get('format')}")
            
            content = data.get('content', '')
            print(f"结果内容长度: {len(content)} 字符")
            print("结果预览:")
            print("-" * 50)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("-" * 50)
            
            return True
        else:
            error_data = response.json()
            print(f"获取结果失败: {error_data.get('error_message')}")
            return False
            
    except Exception as e:
        print(f"获取结果失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试智能文档分析API...")
    print("=" * 60)
    
    # 1. 测试健康检查
    if not test_health():
        print("健康检查失败，请确保API服务正在运行")
        return
    
    # 2. 测试文件上传和分析
    task_id = test_upload_analysis()
    if not task_id:
        print("文件上传失败")
        return
    
    # 3. 测试进度轮询
    completed = test_progress_polling(task_id)
    if not completed:
        print("分析未完成或失败")
        return
    
    # 4. 测试获取结果
    success = test_get_result(task_id)
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 获取结果测试失败")
    
    print("=" * 60)
    print("测试完成")

if __name__ == '__main__':
    main() 