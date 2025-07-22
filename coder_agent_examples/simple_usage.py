#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体简单使用示例
演示如何使用CoderAgent进行自动化代码生成
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.corder_integration import CoderAgent


def simple_example():
    """简单的使用示例"""
    print("=== 编码智能体简单使用示例 ===")
    
    # 创建编码智能体实例
    agent = CoderAgent()
    
    # 示例设计文档内容
    design_doc = """
# 用户管理系统设计文档

## 项目概述
开发一个简单的用户管理系统，包含用户注册、登录、信息管理等功能。

## 技术要求
- 后端：Java8 + Spring Boot
- 前端：Vue2
- 数据库：MySQL

## API设计
### 用户注册
- 路径：POST /api/users/register
- 参数：username, password, email
- 返回：用户ID和注册状态

### 用户登录
- 路径：POST /api/users/login
- 参数：username, password
- 返回：用户信息和token

### 获取用户信息
- 路径：GET /api/users/{id}
- 参数：用户ID
- 返回：用户详细信息

## 数据库设计
### 用户表 (users)
- id: 主键，自增
- username: 用户名，唯一
- password: 密码（加密存储）
- email: 邮箱
- created_at: 创建时间
- updated_at: 更新时间

## 项目配置
- 分支：D_20250101_项目名称
- 项目路径：/Users/renyu/Documents/create_project/user-management
"""
    
    try:
        # 执行任务规划
        print("\n1. 开始任务规划...")
        plan_result = agent.plan_tasks(design_doc)
        print(f"任务规划完成，共生成 {len(plan_result.get('tasks', []))} 个任务")
        
        # 执行代码生成（同步版本）
        print("\n2. 开始代码生成...")
        generation_result = agent.generate_code_sync(design_doc)
        print(f"代码生成完成，生成文件数：{len(generation_result.get('generated_files', []))}")
        
        # 显示生成的文件列表
        if generation_result.get('generated_files'):
            print("\n生成的文件列表：")
            for file_path in generation_result['generated_files']:
                print(f"  - {file_path}")
        
        print("\n=== 示例执行完成 ===")
        return True
        
    except Exception as e:
        print(f"执行出错: {str(e)}")
        return False


async def async_example():
    """异步执行示例"""
    print("\n=== 编码智能体异步执行示例 ===")
    
    # 创建编码智能体实例
    agent = CoderAgent()
    
    # 简单的设计文档
    design_doc = """
# 简单博客系统

## 项目概述
开发一个简单的博客系统，包含文章发布和浏览功能。

## API设计
### 获取文章列表
- 路径：GET /api/articles
- 返回：文章列表

### 发布文章
- 路径：POST /api/articles
- 参数：title, content, author
- 返回：文章ID和发布状态

## 数据库设计
### 文章表 (articles)
- id: 主键
- title: 标题
- content: 内容
- author: 作者
- created_at: 创建时间
"""
    
    try:
        print("\n1. 开始异步任务规划...")
        plan_result = agent.plan_tasks(design_doc)
        print(f"任务规划完成：{len(plan_result.get('tasks', []))} 个任务")
        
        print("\n2. 开始异步代码生成...")
        generation_result = await agent.generate_code(design_doc)
        print(f"异步代码生成完成")
        
        print("\n=== 异步示例执行完成 ===")
        return True
        
    except Exception as e:
        print(f"异步执行出错: {str(e)}")
        return False


def workflow_example():
    """工作流引擎使用示例"""
    print("\n=== 工作流引擎使用示例 ===")
    
    agent = CoderAgent()
    
    # 工作流配置
    workflow_config = {
        "steps": [
            {"name": "解析文档", "type": "document_parsing"},
            {"name": "任务规划", "type": "task_planning"},
            {"name": "代码生成", "type": "code_generation"},
            {"name": "测试生成", "type": "test_generation"}
        ],
        "parallel_execution": False
    }
    
    design_doc = """
# API网关设计文档

## 项目概述
开发一个简单的API网关，实现请求路由和负载均衡。

## 技术要求
- 后端：Java8 + Spring Boot
- 数据库：Redis

## 核心功能
- 请求路由
- 负载均衡
- 访问日志
"""
    
    try:
        print("\n1. 初始化工作流...")
        workflow_result = agent.execute_workflow(design_doc, workflow_config)
        print(f"工作流执行完成")
        
        print("\n=== 工作流示例执行完成 ===")
        return True
        
    except Exception as e:
        print(f"工作流执行出错: {str(e)}")
        return False


def main():
    """主函数"""
    print("编码智能体使用示例")
    print("=" * 50)
    
    # 选择执行模式
    mode = input("\n请选择执行模式:\n1. 简单同步示例\n2. 异步执行示例\n3. 工作流示例\n4. 全部执行\n请输入选项 (1-4): ").strip()
    
    success_count = 0
    
    if mode in ['1', '4']:
        print("\n执行简单同步示例...")
        if simple_example():
            success_count += 1
    
    if mode in ['2', '4']:
        print("\n执行异步示例...")
        try:
            if asyncio.run(async_example()):
                success_count += 1
        except Exception as e:
            print(f"异步示例执行失败: {e}")
    
    if mode in ['3', '4']:
        print("\n执行工作流示例...")
        if workflow_example():
            success_count += 1
    
    print(f"\n执行完成，成功 {success_count} 个示例")


if __name__ == "__main__":
    main() 