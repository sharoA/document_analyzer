#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API工作流测试脚本
测试编码智能体的/process-document接口
"""

import requests
import json
import time

def test_process_document_api():
    """测试编码智能体API"""
    print("🚀 测试编码智能体API - /process-document")
    print("=" * 60)
    
    # API地址
    api_url = "http://localhost:8082/api/coder-agent/process-document"
    
    # 测试文档
    test_document = """
# 用户管理系统设计文档

## 功能概述
开发一个用户管理系统，包含用户注册、登录、个人信息管理等功能。

## 技术栈
- 后端：Java 8 + Spring Boot 2.7.x + JPA
- 前端：Vue 2 + Element UI
- 数据库：MySQL

## 功能模块

### 1. 用户模块
- 用户注册（用户名、邮箱、密码）
- 用户登录（邮箱+密码或用户名+密码）
- 用户信息查看和编辑
- 密码修改

### 2. 数据库设计

#### 用户表 (users)
- id: 主键，自增
- username: 用户名，唯一，非空
- email: 邮箱，唯一，非空
- password: 密码，非空
- created_at: 创建时间
- updated_at: 更新时间

## API设计

### 用户接口
- POST /api/users/register - 用户注册
- POST /api/users/login - 用户登录
- GET /api/users/profile - 获取用户信息
- PUT /api/users/profile - 更新用户信息
- PUT /api/users/password - 修改密码

## 前端页面
- 登录页面：/login
- 注册页面：/register
- 个人资料页面：/profile
    """
    
    # 请求数据
    payload = {
        "document_content": test_document,
        "project_name": "UserManagementSystem"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📡 发送请求到: {api_url}")
        print(f"📄 文档长度: {len(test_document)} 字符")
        print(f"🏷️ 项目名称: UserManagementSystem")
        print(f"\n⏳ 开始处理...")
        
        # 发送POST请求
        response = requests.post(
            api_url, 
            data=json.dumps(payload), 
            headers=headers,
            timeout=300  # 5分钟超时
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"\n📋 响应结果:")
            print(f"   状态: {result.get('status')}")
            print(f"   任务ID: {result.get('task_id')}")
            
            if 'workflow_result' in result:
                workflow = result['workflow_result']
                print(f"\n🔄 工作流执行结果:")
                
                for stage_name, stage_result in workflow.items():
                    if isinstance(stage_result, dict):
                        status = stage_result.get('status', 'unknown')
                        status_emoji = "✅" if status == 'success' else "❌" if status == 'failed' else "🔄"
                        print(f"   {status_emoji} {stage_name}: {status}")
                        
                        # 显示更多详细信息
                        if 'operations' in stage_result:
                            for op in stage_result['operations'][:3]:  # 只显示前3个操作
                                print(f"      - {op}")
                        
                        if 'generated_files' in stage_result:
                            files = stage_result['generated_files']
                            print(f"      📁 生成文件: {len(files)} 个")
                            for file_path in files[:3]:  # 只显示前3个文件
                                print(f"         - {file_path}")
                            if len(files) > 3:
                                print(f"         ... 还有 {len(files) - 3} 个文件")
            
            return True
            
        else:
            print(f"❌ 请求失败!")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ 请求超时! 处理时间超过5分钟")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 连接错误! 请确保服务器已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_agent_status():
    """测试智能体状态接口"""
    print(f"\n🔍 测试智能体状态...")
    
    try:
        status_url = "http://localhost:8082/api/coder-agent/status"
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 智能体状态: {result.get('status')}")
            print(f"📊 工作流状态: {result.get('workflow_status', {}).get('current_state')}")
        else:
            print(f"⚠️ 状态查询失败: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ 状态查询异常: {e}")

def test_health_check():
    """测试健康检查接口"""
    print(f"\n💓 健康检查...")
    
    try:
        health_url = "http://localhost:8082/api/coder-agent/health"
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 服务健康状态: {result.get('status')}")
        else:
            print(f"⚠️ 健康检查失败: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ 健康检查异常: {e}")

if __name__ == "__main__":
    print("🧪 编码智能体API测试")
    print("=" * 60)
    
    # 1. 健康检查
    test_health_check()
    
    # 2. 状态检查
    test_agent_status()
    
    # 3. 主要功能测试
    success = test_process_document_api()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 API测试完成! 请检查生成的代码文件和git推送状态")
        print("📁 项目目录: D:/new_project")
        print("🌐 Git仓库: https://github.com/sharoA/testproject.git")
    else:
        print("❌ API测试失败! 请检查服务器日志")
    print("=" * 60) 