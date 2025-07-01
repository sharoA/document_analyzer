#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单API测试脚本
"""

import requests
import json
import time

def test_simple_process_document():
    """测试简单的文档处理"""
    print("🚀 测试编码智能体API")
    print("=" * 40)
    
    # 删除旧项目目录
    print("📁 清理旧项目...")
    import shutil
    import os
    
    project_path = "D:/new_project"
    if os.path.exists(project_path):
        try:
            shutil.rmtree(project_path)
            print(f"✅ 已删除旧项目: {project_path}")
        except Exception as e:
            print(f"⚠️ 删除旧项目失败: {e}")
    
    # API地址
    api_url = "http://localhost:8082/api/coder-agent/process-document"
    
    # 简单的测试文档
    test_document = """
# 简单测试项目

## 功能概述
一个简单的用户系统。

## 技术栈
- 后端：Java 8 + Spring Boot
- 前端：Vue 2

## 功能模块
### 用户模块
- 用户注册
- 用户登录

## 数据库设计
### 用户表 (users)
- id: 主键
- username: 用户名
- email: 邮箱

## API设计
### 用户接口
- POST /api/users/register - 注册
- POST /api/users/login - 登录
"""
    
    # 请求数据
    request_data = {
        "document_content": test_document,
        "project_name": "SimpleTestProject"
    }
    
    try:
        print("🔄 发送API请求...")
        print(f"📡 URL: {api_url}")
        print(f"📄 文档长度: {len(test_document)} 字符")
        
        # 发送请求
        response = requests.post(
            api_url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分钟超时
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功")
            print(f"📋 任务ID: {result.get('task_id', 'N/A')}")
            print(f"📝 消息: {result.get('message', 'N/A')}")
            
            # 检查生成的文件
            print("\\n📂 检查生成的文件...")
            if os.path.exists(project_path):
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_path)
                        file_size = os.path.getsize(file_path)
                        print(f"  📄 {rel_path} ({file_size} 字节)")
            else:
                print("⚠️ 项目目录不存在")
                
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误信息: {error_data}")
            except:
                print(f"📝 错误内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ API请求超时")
        return False
    except Exception as e:
        print(f"❌ API请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_process_document()
    if success:
        print("\\n✅ 测试完成!")
    else:
        print("\\n❌ 测试失败!") 