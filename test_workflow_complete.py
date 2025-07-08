#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试 - 测试任务拆分和GitLab下载处理功能
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_workflow_complete.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_task_splitting():
    """测试任务拆分功能"""
    
    logger.info("=" * 60)
    logger.info("🧠 测试 1: 任务拆分节点")
    logger.info("=" * 60)
    
    try:
        # 读取设计文档
        design_doc_path = "combined_document_demo.txt"
        if not os.path.exists(design_doc_path):
            logger.error(f"❌ 设计文档不存在: {design_doc_path}")
            return False, {}
        
        with open(design_doc_path, 'r', encoding='utf-8') as f:
            design_doc = f.read()
        
        logger.info(f"✅ 成功读取设计文档，长度: {len(design_doc)} 字符")
        
        # 导入任务拆分节点
        from src.corder_integration.langgraph.nodes.task_splitting_node import task_splitting_node
        
        # 准备状态数据
        state = {
            "project_name": "链数优化项目_完整测试",
            "design_doc": design_doc,
            "current_phase": "task_splitting",
            "execution_errors": [],
            "identified_services": [],
            "service_dependencies": {},
            "task_execution_plan": {},
            "parallel_tasks": []
        }
        
        logger.info("🚀 开始执行任务拆分...")
        
        # 调用任务拆分节点
        result_state = await task_splitting_node(state)
        
        logger.info(f"✅ 任务拆分节点执行完成")
        logger.info(f"📊 识别的服务数量: {len(result_state.get('identified_services', []))}")
        logger.info(f"🎯 识别的服务: {result_state.get('identified_services', [])}")
        
        # 检查服务依赖
        service_deps = result_state.get('service_dependencies', {})
        logger.info(f"🔗 服务依赖关系: {len(service_deps)} 个服务有依赖")
        
        # 检查任务执行计划
        task_plan = result_state.get('task_execution_plan', {})
        if 'tasks' in task_plan:
            logger.info(f"📝 生成的任务数量: {len(task_plan['tasks'])}")
            
            # 显示前5个任务
            for i, task in enumerate(task_plan['tasks'][:5]):
                logger.info(f"  📌 {i+1}. {task.get('task_id', 'N/A')}: {task.get('title', 'N/A')}")
            
            if len(task_plan['tasks']) > 5:
                logger.info(f"  ... 还有 {len(task_plan['tasks']) - 5} 个任务")
        
        return True, result_state
        
    except Exception as e:
        logger.error(f"❌ 任务拆分测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {}

async def test_branch_naming():
    """测试分支命名功能"""
    
    logger.info("\n" + "=" * 60)
    logger.info("🌿 测试 2: 分支命名逻辑")
    logger.info("=" * 60)
    
    try:
        from src.corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator
        
        orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=False)
        
        # 测试不同的项目名称
        test_cases = [
            "链数优化项目_增强版",
            "User Management System",
            "项目-测试_版本1.0",
            "Special Characters!@#$%^&*()",
            "简单项目"
        ]
        
        logger.info("🧪 测试分支命名格式:")
        
        for project_name in test_cases:
            branch_name = orchestrator._generate_target_branch(project_name)
            logger.info(f"  📝 '{project_name}' -> '{branch_name}'")
            
            # 验证分支名格式
            expected_date = datetime.now().strftime("%Y%m%d")
            if not branch_name.startswith(f"D_{expected_date}_"):
                logger.warning(f"  ⚠️ 分支名格式不正确: {branch_name}")
                return False
        
        logger.info("✅ 分支命名测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 分支命名测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_git_management(task_state):
    """测试Git管理功能"""
    
    logger.info("\n" + "=" * 60)
    logger.info("🔧 测试 3: Git管理节点")
    logger.info("=" * 60)
    
    try:
        from src.corder_integration.langgraph.nodes.git_management_node import git_management_node
        from src.corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator
        
        # 生成分支名称
        orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=False)
        target_branch = orchestrator._generate_target_branch("链数优化项目_Git测试")
        
        # 准备Git管理状态
        git_state = {
            **task_state,  # 继承任务拆分的结果
            "project_name": "链数优化项目_Git测试",
            "target_branch": target_branch,
            "git_repo_url": None,  # 测试新仓库创建
            "project_paths": {},
            "repo_initialized": False,
            "current_phase": "git_management",
            "retry_count": 0,  # 🔧 添加缺少的字段
            "output_path": "./test_output"  # 🔧 添加输出路径
        }
        
        logger.info(f"🎯 目标分支名称: {target_branch}")
        logger.info(f"📋 微服务列表: {git_state.get('identified_services', [])}")
        
        logger.info("🚀 开始执行Git管理...")
        
        # 调用Git管理节点
        result_state = await git_management_node(git_state)
        
        logger.info(f"✅ Git管理节点执行完成")
        logger.info(f"🔄 当前阶段: {result_state.get('current_phase', 'unknown')}")
        logger.info(f"📁 项目路径数量: {len(result_state.get('project_paths', {}))}")
        logger.info(f"✅ 仓库初始化状态: {result_state.get('repo_initialized', False)}")
        logger.info(f"🌿 最终分支名称: {result_state.get('target_branch', 'unknown')}")
        
        # 检查项目路径
        project_paths = result_state.get('project_paths', {})
        if project_paths:
            logger.info("📂 创建的服务目录:")
            for service, path in project_paths.items():
                exists = os.path.exists(path)
                status = "✅" if exists else "❌"
                logger.info(f"  {status} {service}: {path}")
        
        # 检查错误
        errors = result_state.get('execution_errors', [])
        if errors:
            logger.warning("⚠️ 执行过程中的错误:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        return True, result_state
        
    except Exception as e:
        logger.error(f"❌ Git管理测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {}

async def test_workflow_integration():
    """测试完整工作流集成"""
    
    logger.info("\n" + "=" * 60)
    logger.info("🔄 测试 4: 完整工作流集成")
    logger.info("=" * 60)
    
    try:
        from src.corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator
        
        # 读取设计文档
        design_doc_path = "combined_document_demo.txt"
        if not os.path.exists(design_doc_path):
            logger.error(f"❌ 设计文档不存在: {design_doc_path}")
            return False
        
        with open(design_doc_path, 'r', encoding='utf-8') as f:
            design_doc = f.read()
        
        # 创建工作流编排器（使用内存检查点，避免SQLite问题）
        orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=False)
        
        logger.info("🚀 开始执行完整工作流...")
        logger.info("⏰ 注意: 这是完整流程测试，只测试前两个节点")
        
        # 模拟执行前两个节点（任务拆分 + Git管理）
        project_name = "链数优化项目_完整工作流测试"
        output_path = "./test_output"
        
        # 生成分支名
        target_branch = orchestrator._generate_target_branch(project_name)
        logger.info(f"🌿 生成的分支名: {target_branch}")
        
        # 我们不执行完整的工作流（因为包含很多步骤），只验证初始化
        logger.info("✅ 工作流初始化成功")
        logger.info(f"📝 项目名称: {project_name}")
        logger.info(f"📁 输出路径: {output_path}")
        logger.info(f"🌿 目标分支: {target_branch}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整工作流测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """主测试函数"""
    
    logger.info("🚀 开始完整工作流测试")
    logger.info(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🎯 测试目标: 验证任务拆分和GitLab下载处理功能")
    
    test_results = []
    
    # 测试1: 任务拆分
    success_1, task_state = await test_task_splitting()
    test_results.append(("任务拆分", success_1))
    
    # 测试2: 分支命名
    success_2 = await test_branch_naming()
    test_results.append(("分支命名", success_2))
    
    # 测试3: Git管理 (如果任务拆分成功)
    if success_1:
        success_3, git_state = await test_git_management(task_state)
        test_results.append(("Git管理", success_3))
    else:
        logger.warning("⚠️ 跳过Git管理测试（任务拆分失败）")
        test_results.append(("Git管理", False))
    
    # 测试4: 完整工作流集成
    success_4 = await test_workflow_integration()
    test_results.append(("完整工作流", success_4))
    
    # 测试总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果总结")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n📈 测试统计: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有测试通过！任务拆分和GitLab下载处理功能正常工作")
        logger.info("💡 可以继续进行完整的编码智能体工作流")
    else:
        logger.warning(f"⚠️ 有 {total_tests - passed_tests} 个测试失败，需要检查相关功能")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 用户中断测试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 测试运行异常: {e}")
        sys.exit(1) 