#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体API测试脚本
测试 /process-document 接口的完整工作流程
"""

import requests
import json
import time
from datetime import datetime

# API服务器地址
API_BASE_URL = "http://localhost:8082"
CODER_AGENT_API_URL = f"{API_BASE_URL}/api/coder-agent"

def test_simple_crud_project():
    """测试简单的CRUD项目生成"""
    
    # 简单的设计文档
    design_document = """
# 用户管理系统设计文档

## 项目概述
- **项目名称**: UserManagementSystem
- **技术栈**: Java8 + Spring Boot + Vue2
- **分支**: main
- **Git仓库**: https://github.com/sharoA/testproject.git

## 功能需求

### 1. 用户管理
- 用户注册
- 用户登录
- 用户信息查看
- 用户信息编辑
- 用户密码修改

### 2. 数据库设计
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3. API接口设计

#### 用户注册
- **URL**: POST /api/users/register
- **参数**: username, password, email, phone
- **返回**: 用户信息

#### 用户登录
- **URL**: POST /api/users/login
- **参数**: username, password
- **返回**: JWT Token

#### 获取用户信息
- **URL**: GET /api/users/profile
- **Headers**: Authorization: Bearer {token}
- **返回**: 用户信息

#### 更新用户信息
- **URL**: PUT /api/users/profile
- **Headers**: Authorization: Bearer {token}
- **参数**: email, phone
- **返回**: 更新后的用户信息

#### 修改密码
- **URL**: PUT /api/users/password
- **Headers**: Authorization: Bearer {token}
- **参数**: oldPassword, newPassword
- **返回**: 成功状态

### 4. 前端页面设计

#### 登录页面 (Login.vue)
- 用户名输入框
- 密码输入框
- 登录按钮
- 注册链接

#### 注册页面 (Register.vue)
- 用户名输入框
- 密码输入框
- 确认密码输入框
- 邮箱输入框
- 手机号输入框
- 注册按钮

#### 用户信息页面 (Profile.vue)
- 显示用户信息
- 编辑用户信息
- 修改密码功能

### 5. 后端架构

#### Controller层
- UserController: 处理用户相关请求
- AuthController: 处理认证相关请求

#### Service层
- UserService: 用户业务逻辑
- AuthService: 认证业务逻辑

#### Repository层
- UserRepository: 用户数据访问

#### Entity层
- User: 用户实体类
- UserDto: 用户数据传输对象

### 6. 安全配置
- JWT认证
- 密码加密(BCrypt)
- CORS配置
- 异常处理

### 7. 测试要求
- 单元测试覆盖率达到80%
- 集成测试覆盖主要API
- 前端组件测试

### 8. 部署要求
- Maven构建
- npm构建
- Docker支持(可选)

## 开发计划
1. 初始化项目结构
2. 实现后端API
3. 实现前端界面
4. 编写测试用例
5. 部署验证
"""

    print("=" * 60)
    print(f"🚀 开始测试编码智能体API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试健康检查
    print("📡 1. 测试API健康检查...")
    try:
        response = requests.get(f"{CODER_AGENT_API_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API服务器健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ API服务器健康检查失败: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到API服务器: {e}")
        print("   请确保API服务器正在运行在 http://localhost:8082")
        return
    
    # 测试处理设计文档
    print("\n🔥 2. 开始处理设计文档...")
    try:
        payload = {
            "document_content": design_document,
            "project_name": "UserManagementSystem",
            "execute_immediately": True
        }
        
        print(f"   正在发送请求到: {CODER_AGENT_API_URL}/process-document")
        print(f"   项目名称: UserManagementSystem")
        print(f"   设计文档长度: {len(design_document)} 字符")
        
        response = requests.post(
            f"{CODER_AGENT_API_URL}/process-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文档处理成功!")
            
            # 打印结果摘要
            if result.get("status") == "success":
                data = result.get("data", {})
                print(f"\n📋 执行结果摘要:")
                print(f"   任务ID: {data.get('task_id', 'N/A')}")
                print(f"   状态: {data.get('status', 'N/A')}")
                
                # 工作流结果
                workflow_result = data.get("workflow_result", {})
                if workflow_result:
                    print(f"   工作流状态: {workflow_result.get('status', 'N/A')}")
                    if workflow_result.get('project_path'):
                        print(f"   项目路径: {workflow_result.get('project_path')}")
                    
                    # 各阶段结果
                    results = workflow_result.get('results', {})
                    if results:
                        print(f"\n📊 各阶段执行结果:")
                        for stage, stage_result in results.items():
                            if isinstance(stage_result, dict):
                                status = "✅" if stage_result.get('success') else "❌"
                                print(f"   {status} {stage}: {stage_result.get('status', 'N/A')}")
                            else:
                                print(f"   📝 {stage}: {stage_result}")
                
                # 保存详细结果到文件
                with open("test_result.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n💾 详细结果已保存到: test_result.json")
                
            else:
                print(f"❌ 处理失败: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   错误信息: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   响应内容: {response.text}")
                
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (5分钟)")
        print("   代码生成可能需要较长时间，请稍后检查任务状态")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_api_status():
    """测试API状态查询"""
    print("\n🔍 3. 测试API状态查询...")
    try:
        response = requests.get(f"{CODER_AGENT_API_URL}/status", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 状态查询成功")
            data = result.get("data", {})
            
            # 显示配置信息
            config = data.get("config", {})
            if config:
                print(f"   项目根路径: {config.get('project_root', 'N/A')}")
                print(f"   后端框架: {config.get('backend_framework', 'N/A')}")
                print(f"   前端框架: {config.get('frontend_framework', 'N/A')}")
                
        else:
            print(f"❌ 状态查询失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")

def test_task_list():
    """测试任务列表查询"""
    print("\n📋 4. 测试任务列表查询...")
    try:
        response = requests.get(f"{CODER_AGENT_API_URL}/tasks?limit=5", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 任务列表查询成功")
            data = result.get("data", {})
            tasks = data.get("tasks", [])
            print(f"   任务总数: {data.get('total', 0)}")
            
            for i, task in enumerate(tasks[:3], 1):
                print(f"   任务{i}: {task.get('task_id', 'N/A')} - {task.get('status', 'N/A')}")
                
        else:
            print(f"❌ 任务列表查询失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 任务列表查询异常: {e}")

def main():
    """主测试函数"""
    print("🧪 编码智能体API完整测试")
    print("=" * 60)
    print("测试目标:")
    print("1. API健康检查")
    print("2. 设计文档处理和代码生成")
    print("3. API状态查询")
    print("4. 任务列表查询")
    print("=" * 60)
    
    # 执行测试
    test_simple_crud_project()
    test_api_status()
    test_task_list()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60)
    print("💡 提示:")
    print("- 如果生成成功，检查 D:/new_project 目录")
    print("- 查看 test_result.json 了解详细结果")
    print("- Git操作将推送到: https://github.com/sharoA/testproject.git")
    print("=" * 60)

if __name__ == "__main__":
    main() 