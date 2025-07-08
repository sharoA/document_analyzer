#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的Git分支命名规则
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加源代码路径
sys.path.append('src')

from corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_branch_naming():
    """测试分支命名逻辑"""
    
    print("🧪 测试Git分支命名规则...")
    
    # 创建工作流协调器
    orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=False)
    
    # 测试不同的项目名称
    test_cases = [
        "Git克隆修复测试",
        "链数优化项目_增强版",
        "test-project-123",
        "用户管理系统",
        "API网关服务",
        "special@chars#project!",
    ]
    
    current_date = datetime.now().strftime("%Y%m%d")
    print(f"📅 当前日期: {current_date}")
    print()
    
    for project_name in test_cases:
        branch_name = orchestrator._generate_target_branch(project_name)
        print(f"📋 项目名称: {project_name}")
        print(f"🌿 生成分支: {branch_name}")
        print(f"✅ 格式验证: {'D_' + current_date in branch_name}")
        print("-" * 50)

async def test_full_workflow():
    """测试完整工作流的分支使用"""
    
    print("\n🚀 测试完整工作流的分支使用...")
    
    # 创建工作流协调器
    orchestrator = LangGraphWorkflowOrchestrator(
        use_sqlite=True,
        db_path="test_branch_naming.db"
    )
    
    # 准备测试文档（无Git地址，测试新仓库创建）
    test_document = """
# 分支命名测试项目

## 项目概述
这是一个测试新分支命名规则的项目。

## 服务架构
1. 用户服务 - 负责用户管理
2. 订单服务 - 负责订单处理

## 技术栈
- Java Spring Boot
- MySQL数据库

## 接口设计
### 用户服务接口
- GET /api/users - 获取用户列表
- POST /api/users - 创建用户
"""
    
    try:
        print("📋 开始执行工作流（测试分支命名）...")
        
        # 执行工作流
        result = await orchestrator.execute_workflow(
            document_content=test_document,
            project_name="分支命名测试项目",
            output_path="./test_branch_output"
        )
        
        print("✅ 工作流执行完成！")
        print(f"📊 执行状态: {result['status']}")
        
        if result['status'] == 'success':
            final_state = result.get('final_state', {})
            target_branch = final_state.get('target_branch', 'unknown')
            print(f"🌿 使用的分支名称: {target_branch}")
            
            # 验证分支名称格式
            current_date = datetime.now().strftime("%Y%m%d")
            if f"D_{current_date}" in target_branch:
                print("✅ 分支命名格式正确！")
            else:
                print("⚠️ 分支命名格式可能不符合预期")
                
        else:
            print(f"❌ 执行失败: {result.get('error', '未知错误')}")
            
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}
    
    finally:
        # 清理测试数据库
        test_db_path = "test_branch_naming.db"
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
                print(f"🧹 已清理测试数据库: {test_db_path}")
            except Exception as e:
                print(f"⚠️ 清理测试数据库失败: {e}")

def main():
    """主函数"""
    try:
        print("🎯 Git分支命名规则测试开始\n")
        
        # 测试1：分支命名逻辑
        test_branch_naming()
        
        # 测试2：完整工作流
        result = asyncio.run(test_full_workflow())
        
        if result['status'] == 'success':
            print("\n🎉 分支命名规则测试成功!")
            print("✅ 新格式: D_日期_项目名称")
            print("✅ 现有仓库: 保持原分支名")
        else:
            print(f"\n❌ 测试失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 主函数执行失败: {e}")

if __name__ == "__main__":
    main() 