#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试Git分支命名规则
"""

import sys
import os
from datetime import datetime

# 添加源代码路径
sys.path.append('src')

from corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator

def main():
    """快速测试分支命名逻辑"""
    print("🧪 快速测试Git分支命名规则\n")
    
    # 创建工作流协调器
    orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=False)
    
    # 测试项目名称
    test_cases = [
        "Git克隆修复测试",
        "链数优化项目_增强版",
        "test-project-123",
        "用户管理系统",
        "API网关服务",
        "special@chars#project!",
    ]
    
    current_date = datetime.now().strftime("%Y%m%d")
    print(f"📅 当前日期: {current_date}\n")
    
    print("🌿 分支命名测试结果:")
    print("=" * 60)
    
    for i, project_name in enumerate(test_cases, 1):
        try:
            branch_name = orchestrator._generate_target_branch(project_name)
            is_valid = f"D_{current_date}" in branch_name
            status = "✅" if is_valid else "❌"
            
            print(f"{i}. 项目名称: {project_name}")
            print(f"   生成分支: {branch_name}")
            print(f"   格式验证: {status} {'正确' if is_valid else '错误'}")
            print("-" * 60)
            
        except Exception as e:
            print(f"{i}. 项目名称: {project_name}")
            print(f"   ❌ 错误: {e}")
            print("-" * 60)
    
    print("\n📋 期望格式: D_YYYYMMDD_项目名称")
    print("🎯 测试完成！")

if __name__ == "__main__":
    main() 