#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试脚本
测试从文档分析到代码生成再到git推送的完整流程
"""

import sys
import os
import json
sys.path.append('.')

from src.corder_integration.coder_agent import CoderAgent
from src.resource.config import get_config

async def test_complete_workflow():
    """测试完整的编码智能体工作流"""
    print("🚀 开始完整工作流测试")
    print("=" * 50)
    
    try:
        # 1. 初始化配置
        config = get_config()
        coder_config = config.get_coder_agent_config()
        print(f"📋 项目根目录: {coder_config['project_root']}")
        print(f"🌐 Git远程仓库: {coder_config['git_config']['default_remote_url']}")
        
        # 2. 初始化编码智能体
        print(f"\n🤖 初始化编码智能体...")
        coder_agent = CoderAgent()
        
        # 3. 准备测试文档
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
        
        print(f"\n📄 使用测试文档...")
        print(f"文档长度: {len(test_document)} 字符")
        
        # 4. 处理文档并生成代码
        print(f"\n⚙️ 开始处理文档...")
        result = await coder_agent.process_design_document(test_document, "UserManagementSystem")
        
        print(f"\n📊 处理结果:")
        print(f"状态: {result['status']}")
        print(f"任务ID: {result.get('task_id')}")
        
        if result['status'] == 'success':
            print(f"✅ 工作流执行成功!")
            
            # 显示执行的阶段
            if 'workflow_result' in result:
                workflow = result['workflow_result']
                print(f"\n📋 执行的工作流阶段:")
                for stage_name, stage_result in workflow.items():
                    if isinstance(stage_result, dict) and 'status' in stage_result:
                        status_emoji = "✅" if stage_result['status'] == 'success' else "❌"
                        print(f"   {status_emoji} {stage_name}: {stage_result['status']}")
                        
                        # 显示代码生成的文件
                        if stage_name == 'code_generation' and 'generated_files' in stage_result:
                            files = stage_result['generated_files']
                            print(f"      生成文件数: {len(files)}")
                            for file_path in files[:5]:  # 只显示前5个文件
                                print(f"      - {file_path}")
                            if len(files) > 5:
                                print(f"      ... 还有 {len(files) - 5} 个文件")
            
            # 5. 验证生成的代码文件
            print(f"\n🔍 验证生成的代码文件...")
            project_root = coder_config['project_root']
            
            # 检查Java文件
            java_dir = os.path.join(project_root, "src", "main", "java")
            if os.path.exists(java_dir):
                java_files = []
                for root, dirs, files in os.walk(java_dir):
                    for file in files:
                        if file.endswith('.java'):
                            java_files.append(os.path.join(root, file))
                
                print(f"📁 Java文件数量: {len(java_files)}")
                for java_file in java_files:
                    rel_path = os.path.relpath(java_file, java_dir)
                    file_size = os.path.getsize(java_file)
                    print(f"   - {rel_path} ({file_size} bytes)")
            
            # 检查Vue文件  
            frontend_dir = os.path.join(project_root, "frontend", "src")
            if os.path.exists(frontend_dir):
                vue_files = []
                for root, dirs, files in os.walk(frontend_dir):
                    for file in files:
                        if file.endswith('.vue'):
                            vue_files.append(os.path.join(root, file))
                
                print(f"📁 Vue文件数量: {len(vue_files)}")
                for vue_file in vue_files:
                    rel_path = os.path.relpath(vue_file, frontend_dir)
                    file_size = os.path.getsize(vue_file)
                    print(f"   - {rel_path} ({file_size} bytes)")
            
            # 6. 检查Git状态
            print(f"\n🔍 检查Git状态...")
            git_dir = os.path.join(project_root, ".git")
            if os.path.exists(git_dir):
                print(f"✅ Git仓库存在")
                
                # 检查远程仓库
                import subprocess
                try:
                    cmd_result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    remote_url = cmd_result.stdout.strip()
                    print(f"🌐 远程仓库: {remote_url}")
                except subprocess.CalledProcessError:
                    print(f"⚠️ 获取远程仓库URL失败")
                
                # 检查当前分支
                try:
                    cmd_result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    current_branch = cmd_result.stdout.strip()
                    print(f"🌿 当前分支: {current_branch}")
                except subprocess.CalledProcessError:
                    print(f"⚠️ 获取当前分支失败")
                
                # 检查是否有未提交的更改
                try:
                    cmd_result = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=project_root,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    changes = cmd_result.stdout.strip()
                    if changes:
                        change_lines = changes.split('\n')
                        print(f"📝 未提交的更改: {len(change_lines)} 个文件")
                        for line in change_lines[:5]:
                            print(f"   - {line}")
                        if len(change_lines) > 5:
                            print(f"   ... 还有 {len(change_lines) - 5} 个文件")
                    else:
                        print(f"✅ 没有未提交的更改")
                except subprocess.CalledProcessError:
                    print(f"⚠️ 检查Git状态失败")
            else:
                print(f"❌ Git仓库不存在")
            
        else:
            print(f"❌ 工作流执行失败: {result.get('error')}")
            return False
        
        print(f"\n🎉 完整工作流测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_complete_workflow())
    if success:
        print("\n✅ 完整工作流测试通过!")
    else:
        print("\n❌ 完整工作流测试失败!")
        sys.exit(1) 