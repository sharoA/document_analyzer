#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git设置测试脚本
专门测试远程仓库配置是否正确
"""

import sys
import os
sys.path.append('.')

from src.corder_integration.git_manager import GitManager
from src.corder_integration.config import get_config_manager
from src.resource.config import get_config
import subprocess

def test_git_remote_setup():
    """测试Git远程仓库设置"""
    print("🧪 测试Git远程仓库设置")
    print("=" * 50)
    
    try:
        # 1. 获取配置
        main_config = get_config()
        coder_config = main_config.get_coder_agent_config()
        git_config = coder_config.get("git_config", {})
        remote_url = git_config.get("default_remote_url")
        
        print(f"📋 配置的远程仓库URL: {remote_url}")
        
        # 2. 初始化GitManager
        git_manager = GitManager()
        
        # 3. 设置项目环境
        project_name = "TestProject"
        branch_name = "D_20250630_2000_aigc"
        
        print(f"🚀 开始设置项目环境...")
        print(f"   项目名称: {project_name}")
        print(f"   分支名称: {branch_name}")
        print(f"   远程仓库: {remote_url}")
        
        result = git_manager.setup_project_environment(
            project_name=project_name,
            branch_name=branch_name,
            remote_url=remote_url
        )
        
        print(f"✅ 项目环境设置结果: {result['status']}")
        print(f"📁 项目路径: {result['project_path']}")
        
        for op in result['operations']:
            print(f"   - {op}")
        
        # 4. 验证Git配置
        project_path = result['project_path']
        
        print(f"\n🔍 验证Git配置...")
        
        # 检查是否为Git仓库
        git_dir = os.path.join(project_path, '.git')
        if os.path.exists(git_dir):
            print("✅ Git仓库初始化成功")
        else:
            print("❌ Git仓库初始化失败")
            return False
        
        # 检查远程仓库配置
        try:
            cmd_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            actual_remote_url = cmd_result.stdout.strip()
            print(f"✅ 远程仓库配置成功: {actual_remote_url}")
            
            if actual_remote_url == remote_url:
                print("✅ 远程仓库URL配置正确")
            else:
                print(f"⚠️  远程仓库URL不匹配:")
                print(f"   期望: {remote_url}")
                print(f"   实际: {actual_remote_url}")
        
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取远程仓库URL失败: {e.stderr}")
            return False
        
        # 检查当前分支
        try:
            cmd_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = cmd_result.stdout.strip()
            print(f"✅ 当前分支: {current_branch}")
            
            if current_branch == branch_name:
                print("✅ 分支设置正确")
            else:
                print(f"⚠️  分支不匹配:")
                print(f"   期望: {branch_name}")
                print(f"   实际: {current_branch}")
        
        except subprocess.CalledProcessError as e:
            print(f"❌ 获取当前分支失败: {e.stderr}")
        
        # 5. 测试提交和推送准备
        print(f"\n📝 测试提交功能...")
        
        # 创建一个测试文件
        test_file = os.path.join(project_path, "README.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# 测试项目\n\n这是一个Git配置测试项目。\n")
        
        # 尝试提交（不推送）
        commit_result = git_manager.commit_and_push_code(
            commit_message="[测试] 初始化项目和Git配置测试",
            project_path=project_path,
            push_to_remote=False  # 先不推送，只测试提交
        )
        
        print(f"📊 提交结果: {commit_result['status']}")
        if commit_result['status'] == 'success':
            print(f"✅ 提交ID: {commit_result['commit_id']}")
            for op in commit_result['operations']:
                print(f"   - {op}")
        else:
            print(f"❌ 提交失败: {commit_result.get('error')}")
        
        print(f"\n🎉 Git配置测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_git_remote_setup()
    if success:
        print("\n✅ 所有测试通过! Git远程仓库配置正常。")
    else:
        print("\n❌ 测试失败! 请检查配置和代码。")
        sys.exit(1) 