#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码智能体主程序
提供命令行界面和Web API服务
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.corder_integration.coder_agent import CoderAgent
from src.corder_integration.task_planner import TaskPlanner
from src.corder_integration.git_manager import GitManager

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='编码智能体 - AI驱动的代码生成工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 生成命令
    generate_parser = subparsers.add_parser('generate', help='根据设计文档生成代码')
    generate_parser.add_argument('--file', '-f', required=True, help='设计文档文件路径')
    generate_parser.add_argument('--project', '-p', help='项目名称')
    generate_parser.add_argument('--plan-only', action='store_true', help='仅创建执行计划，不执行')
    
    # 执行命令
    execute_parser = subparsers.add_parser('execute', help='执行已保存的计划')
    execute_parser.add_argument('--plan-id', '-i', required=True, help='执行计划ID')
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='查看项目状态')
    status_parser.add_argument('--path', help='项目路径')
    
    # 列表命令
    list_parser = subparsers.add_parser('list', help='列出任务')
    list_parser.add_argument('--limit', type=int, default=10, help='显示数量限制')
    
    # Git命令
    git_parser = subparsers.add_parser('git', help='Git操作')
    git_subparsers = git_parser.add_subparsers(dest='git_command')
    
    git_setup_parser = git_subparsers.add_parser('setup', help='设置Git环境')
    git_setup_parser.add_argument('--project-name', required=True, help='项目名称')
    git_setup_parser.add_argument('--branch', required=True, help='分支名称')
    git_setup_parser.add_argument('--remote', help='远程仓库URL')
    
    git_commit_parser = git_subparsers.add_parser('commit', help='提交代码')
    git_commit_parser.add_argument('--message', '-m', required=True, help='提交信息')
    git_commit_parser.add_argument('--path', help='项目路径')
    git_commit_parser.add_argument('--no-push', action='store_true', help='不推送到远程')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'generate':
            await handle_generate(args)
        elif args.command == 'execute':
            await handle_execute(args)
        elif args.command == 'status':
            await handle_status(args)
        elif args.command == 'list':
            await handle_list(args)
        elif args.command == 'git':
            await handle_git(args)
        else:
            print(f"未知命令: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n操作被用户取消")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

async def handle_generate(args):
    """处理生成命令"""
    print(f"📖 读取设计文档: {args.file}")
    
    if not os.path.exists(args.file):
        print(f"❌ 文件不存在: {args.file}")
        return
    
    with open(args.file, 'r', encoding='utf-8') as f:
        document_content = f.read()
    
    print(f"📄 文档大小: {len(document_content)} 字符")
    
    coder_agent = CoderAgent()
    
    print("🚀 启动编码智能体...")
    
    result = await coder_agent.process_design_document(
        document_content=document_content,
        project_name=args.project,
        execute_immediately=not args.plan_only
    )
    
    if result['status'] == 'success':
        if args.plan_only:
            print("✅ 执行计划创建成功!")
            plan = result.get('execution_plan')
            if plan:
                print(f"📋 计划ID: {plan['plan_id']}")
                print(f"📊 总任务数: {plan['total_tasks']}")
                print(f"⏱️ 预估工时: {plan['estimated_total_hours']} 小时")
                print(f"🌿 Git分支: {plan['branch_name']}")
                print(f"\n💡 执行命令: python coder_agent_main.py execute --plan-id {plan['plan_id']}")
        else:
            print("✅ 代码生成完成!")
            workflow_result = result.get('workflow_result')
            if workflow_result:
                print_workflow_summary(workflow_result)
    else:
        print(f"❌ 失败: {result.get('error')}")

async def handle_execute(args):
    """处理执行命令"""
    print(f"🚀 执行计划: {args.plan_id}")
    
    coder_agent = CoderAgent()
    result = await coder_agent.execute_plan(args.plan_id)
    
    if result['status'] == 'success':
        print("✅ 计划执行完成!")
        workflow_result = result.get('workflow_result')
        if workflow_result:
            print_workflow_summary(workflow_result)
    else:
        print(f"❌ 执行失败: {result.get('error')}")

async def handle_status(args):
    """处理状态命令"""
    print("📊 获取项目状态...")
    
    coder_agent = CoderAgent()
    status = coder_agent.get_project_status(args.path)
    
    print_status_summary(status)

async def handle_list(args):
    """处理列表命令"""
    print(f"📋 获取最近 {args.limit} 个任务...")
    
    coder_agent = CoderAgent()
    tasks = coder_agent.list_recent_tasks(args.limit)
    
    if tasks:
        print(f"\n找到 {len(tasks)} 个任务:")
        for i, task in enumerate(tasks, 1):
            status_icon = get_status_icon(task.get('status'))
            print(f"{i:2d}. {status_icon} {task.get('filename', 'N/A')} - {task.get('status', 'unknown')}")
            print(f"     ID: {task.get('id')} | 创建时间: {task.get('created_at', 'N/A')}")
    else:
        print("📭 没有找到任务")

async def handle_git(args):
    """处理Git命令"""
    git_manager = GitManager()
    
    if args.git_command == 'setup':
        print(f"🔧 设置Git环境: {args.project_name}")
        result = git_manager.setup_project_environment(
            args.project_name, args.branch, args.remote
        )
        
        if result['status'] == 'success':
            print("✅ Git环境设置成功!")
            print(f"📁 项目路径: {result['project_path']}")
            print(f"🌿 分支: {result['branch_name']}")
            for op in result['operations']:
                print(f"   ✓ {op}")
        else:
            print(f"❌ 设置失败: {result.get('error')}")
    
    elif args.git_command == 'commit':
        print(f"📦 提交代码: {args.message}")
        result = git_manager.commit_and_push_code(
            args.message, args.path, not args.no_push
        )
        
        if result['status'] == 'success':
            print("✅ 代码提交成功!")
            print(f"🆔 提交ID: {result.get('commit_id', 'N/A')[:8]}...")
            if result.get('pushed'):
                print("🚀 已推送到远程仓库")
            for op in result['operations']:
                print(f"   ✓ {op}")
        else:
            print(f"❌ 提交失败: {result.get('error')}")

def print_workflow_summary(workflow_result):
    """打印工作流摘要"""
    print(f"\n📊 工作流执行摘要:")
    print(f"状态: {workflow_result.get('status')}")
    
    if 'project_path' in workflow_result:
        print(f"📁 项目路径: {workflow_result['project_path']}")
    
    results = workflow_result.get('results', {})
    
    # 规划阶段
    if 'planning' in results:
        planning = results['planning']
        print(f"📋 规划: {planning.get('total_tasks')}个任务, 预估{planning.get('estimated_hours')}小时")
    
    # 代码生成阶段
    if 'code_generation' in results:
        code_gen = results['code_generation']
        completed = code_gen.get('completed_tasks', 0)
        total = code_gen.get('total_tasks', 0)
        files = len(code_gen.get('generated_files', []))
        print(f"💻 代码生成: {completed}/{total}个任务完成, 生成{files}个文件")
    
    # 测试阶段
    if 'testing' in results:
        testing = results['testing']
        print(f"🧪 测试: {testing.get('total_test_tasks', 0)}个测试任务")
    
    # Git操作
    if 'git_operations' in results:
        git_ops = results['git_operations']
        if git_ops.get('status') == 'success':
            commit_id = git_ops.get('commit_id', 'N/A')
            print(f"📦 Git: 提交 {commit_id[:8] if commit_id != 'N/A' else 'N/A'}...")
            if git_ops.get('pushed'):
                print("🚀 已推送到远程仓库")

def print_status_summary(status):
    """打印状态摘要"""
    print(f"\n📊 项目状态:")
    
    git_status = status.get('git_status', {})
    workflow_status = status.get('workflow_status', {})
    structure = status.get('structure_analysis', {})
    
    print(f"🔗 Git仓库: {'✅' if git_status.get('is_git_repo') else '❌'}")
    if git_status.get('current_branch'):
        print(f"🌿 当前分支: {git_status['current_branch']}")
    
    print(f"⚙️ 工作流状态: {workflow_status.get('current_state', 'N/A')}")
    
    print(f"🏗️ 后端项目: {'✅' if structure.get('has_backend') else '❌'}")
    print(f"🖥️ 前端项目: {'✅' if structure.get('has_frontend') else '❌'}")
    
    files_count = len(structure.get('existing_files', []))
    print(f"📁 文件数量: {files_count}")
    
    if git_status.get('uncommitted_changes'):
        print("⚠️ 有未提交的更改")

def get_status_icon(status):
    """获取状态图标"""
    icons = {
        'pending': '⏳',
        'processing': '🔄',
        'completed': '✅',
        'failed': '❌',
        'planned': '📋'
    }
    return icons.get(status, '❓')

if __name__ == "__main__":
    asyncio.run(main()) 