#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git设置和推送脚本
手动完成git初始化、配置和推送
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        if result.returncode != 0:
            print(f"❌ 命令执行失败: {cmd}")
            print(f"错误输出: {result.stderr}")
            return False, result.stderr
        else:
            print(f"✅ 命令执行成功: {cmd}")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
            return True, result.stdout.strip()
    except Exception as e:
        print(f"❌ 命令执行异常: {cmd}, 错误: {e}")
        return False, str(e)

def setup_git_and_push():
    """设置git并推送代码"""
    print("🚀 开始设置Git仓库并推送代码")
    print("=" * 50)
    
    project_path = "D:/new_project"
    remote_url = "https://github.com/sharoA/testproject.git"
    branch_name = f"D_{datetime.now().strftime('%Y%m%d%H%M')}_aigc"
    
    # 检查项目目录是否存在
    if not os.path.exists(project_path):
        print(f"❌ 项目目录不存在: {project_path}")
        return False
    
    print(f"📁 项目目录: {project_path}")
    print(f"🌐 远程仓库: {remote_url}")
    print(f"🌿 分支名称: {branch_name}")
    
    # 1. 检查是否已经是git仓库
    print("\n📋 步骤1: 检查Git状态")
    success, output = run_command("git status", cwd=project_path)
    
    if not success:
        print("💾 初始化Git仓库...")
        success, output = run_command("git init", cwd=project_path)
        if not success:
            return False
    
    # 2. 配置git用户信息（如果需要）
    print("\n📋 步骤2: 配置Git用户信息")
    run_command('git config user.name "AI Coder Agent"', cwd=project_path)
    run_command('git config user.email "ai-coder@example.com"', cwd=project_path)
    
    # 3. 添加远程仓库
    print("\n📋 步骤3: 配置远程仓库")
    success, output = run_command("git remote get-url origin", cwd=project_path)
    if not success:
        success, output = run_command(f"git remote add origin {remote_url}", cwd=project_path)
        if not success:
            return False
    else:
        print(f"✅ 远程仓库已存在: {output}")
    
    # 4. 从远程拉取最新代码
    print("\n📋 步骤4: 拉取远程代码")
    success, output = run_command("git fetch origin", cwd=project_path)
    if not success:
        print("⚠️ 拉取失败，可能是新仓库，继续...")
    
    # 5. 检查并切换分支
    print("\n📋 步骤5: 处理分支")
    
    # 检查是否有main分支
    success, output = run_command("git branch -r", cwd=project_path)
    if success and "origin/main" in output:
        print("🔄 基于远程main分支创建新分支")
        run_command("git checkout -b main origin/main", cwd=project_path)
    elif success and "origin/master" in output:
        print("🔄 基于远程master分支创建新分支")  
        run_command("git checkout -b main origin/master", cwd=project_path)
    
    # 创建新的工作分支
    success, output = run_command(f"git checkout -b {branch_name}", cwd=project_path)
    if not success:
        print("⚠️ 分支创建失败，尝试切换到现有分支")
        run_command(f"git checkout {branch_name}", cwd=project_path)
    
    # 6. 添加所有文件
    print("\n📋 步骤6: 添加文件到Git")
    success, output = run_command("git add .", cwd=project_path)
    if not success:
        return False
    
    # 7. 检查有哪些文件被添加
    print("\n📋 步骤7: 检查添加的文件")
    success, output = run_command("git status --porcelain", cwd=project_path)
    if success and output:
        print("📄 将要提交的文件:")
        for line in output.split('\n'):
            if line.strip():
                print(f"  {line}")
    
    # 8. 提交代码
    print("\n📋 步骤8: 提交代码")
    commit_message = f"AI生成代码 - SimpleTestProject - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, output = run_command(f'git commit -m "{commit_message}"', cwd=project_path)
    if not success:
        print("⚠️ 提交失败，可能没有变更")
    
    # 9. 推送到远程仓库
    print("\n📋 步骤9: 推送到远程仓库")
    success, output = run_command(f"git push -u origin {branch_name}", cwd=project_path)
    if not success:
        print("❌ 推送失败，尝试强制推送...")
        success, output = run_command(f"git push -u origin {branch_name} --force", cwd=project_path)
    
    if success:
        print("🎉 Git推送成功!")
        print(f"📂 项目已推送到: {remote_url}")
        print(f"🌿 分支: {branch_name}")
        return True
    else:
        print("❌ Git推送失败")
        return False

def check_generated_files():
    """检查生成的文件"""
    print("\n📂 检查生成的文件:")
    project_path = "D:/new_project"
    
    if not os.path.exists(project_path):
        print("❌ 项目目录不存在")
        return
    
    file_count = 0
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if not file.startswith('.git') and file != '.gitkeep':
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_path)
                file_size = os.path.getsize(file_path)
                print(f"  📄 {rel_path} ({file_size} 字节)")
                file_count += 1
    
    print(f"\n📊 总计生成文件: {file_count} 个")

if __name__ == "__main__":
    # 先检查生成的文件
    check_generated_files()
    
    # 执行git设置和推送
    success = setup_git_and_push()
    
    if success:
        print("\n✅ Git设置和推送完成!")
    else:
        print("\n❌ Git设置和推送失败!")
        sys.exit(1) 