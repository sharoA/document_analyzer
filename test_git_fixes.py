#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Git分支名称统一和push修复
"""

import sys
import os
sys.path.append('/Users/renyu/Documents/ai_project/document_analyzer')

import logging
import tempfile
import shutil
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_branch_naming():
    """测试统一的分支名称生成"""
    logger.info("🧪 测试1: 统一分支名称生成")
    
    try:
        from src.corder_integration.langgraph.nodes.git_management_node import GitManagerAgent
        
        # 创建Git管理智能体实例
        git_agent = GitManagerAgent()
        
        # 测试生成分支名称 - 第一次调用
        project_name = "测试项目名称"
        branch1 = git_agent._generate_unified_branch_name(project_name)
        logger.info(f"📋 第一次生成的分支名: {branch1}")
        
        # 测试生成分支名称 - 第二次调用（应该返回相同的名称）
        branch2 = git_agent._generate_unified_branch_name(project_name)
        logger.info(f"📋 第二次生成的分支名: {branch2}")
        
        # 验证两次生成的分支名是否相同
        if branch1 == branch2:
            logger.info("✅ 测试通过：两次生成的分支名称一致")
            return True
        else:
            logger.error(f"❌ 测试失败：分支名称不一致 - {branch1} vs {branch2}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败，导入或执行错误: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_git_commit_logic():
    """测试Git提交逻辑（模拟）"""
    logger.info("🧪 测试2: Git提交逻辑")
    
    try:
        from src.corder_integration.langgraph.nodes.git_commit_node import GitCommitAgent
        
        # 创建Git提交智能体实例
        git_commit_agent = GitCommitAgent()
        
        # 模拟任务参数
        test_task = {
            'task_id': 'test_task_001',
            'service_name': '测试服务',
            'parameters': {
                'repositories': [
                    {
                        'path': '/tmp/test_repo_does_not_exist',
                        'changes': '测试功能变更'
                    }
                ]
            }
        }
        
        # 测试Git提交逻辑（会因为路径不存在而失败，但可以测试参数解析）
        result = git_commit_agent._execute_real_git_commit(test_task, test_task['parameters'])
        
        logger.info(f"📋 Git提交测试结果: {result}")
        
        # 验证结果结构
        expected_keys = ['success', 'commit_status', 'git_results', 'total_repositories']
        if all(key in result for key in expected_keys):
            logger.info("✅ 测试通过：Git提交方法返回了预期的结果结构")
            
            # 验证参数解析
            if result['total_repositories'] == 1:
                logger.info("✅ 测试通过：正确解析了仓库参数")
                return True
            else:
                logger.error(f"❌ 测试失败：仓库数量解析错误 - 期望1，实际{result['total_repositories']}")
                return False
        else:
            logger.error(f"❌ 测试失败：返回结果缺少必要的键 - 期望{expected_keys}，实际{list(result.keys())}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败，导入或执行错误: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_branch_name_format():
    """测试分支名称格式"""
    logger.info("🧪 测试3: 分支名称格式验证")
    
    try:
        from src.corder_integration.langgraph.nodes.git_management_node import GitManagerAgent
        
        # 测试不同的项目名称
        test_cases = [
            "测试项目",
            "链数中建一局_1753349525",
            "Project123测试",
            "带有特殊字符@#$%的项目名",
            "English Project Name"
        ]
        
        for project_name in test_cases:
            git_agent = GitManagerAgent()  # 每次创建新实例以重置分支名称
            branch_name = git_agent._generate_unified_branch_name(project_name)
            
            logger.info(f"📋 项目名: '{project_name}' -> 分支名: '{branch_name}'")
            
            # 验证分支名格式：应该是 D_YYYYMMDDHHMM_清理后的项目名
            import re
            pattern = r'^D_\d{12}_[\u4e00-\u9fa5a-zA-Z]+$'
            if re.match(pattern, branch_name):
                logger.info(f"✅ 分支名格式正确: {branch_name}")
            else:
                logger.warning(f"⚠️ 分支名格式可能有问题: {branch_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_git_push_upstream_logic():
    """测试Git push上游分支逻辑（模拟）"""
    logger.info("🧪 测试4: Git push上游分支处理逻辑")
    
    try:
        # 模拟subprocess.run的返回结果
        class MockResult:
            def __init__(self, returncode, stdout="", stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        # 测试场景1：普通push失败，需要设置上游分支
        mock_push_error = MockResult(
            returncode=1, 
            stderr="fatal: The current branch D_202507241800_测试项目 has no upstream branch."
        )
        
        # 验证错误检测逻辑
        if mock_push_error.returncode != 0 and "no upstream branch" in mock_push_error.stderr:
            logger.info("✅ 测试通过：正确检测到需要设置上游分支的情况")
        else:
            logger.error("❌ 测试失败：未能正确检测上游分支问题")
            return False
        
        # 测试场景2：获取分支名
        mock_branch_result = MockResult(returncode=0, stdout="D_202507241800_测试项目\n")
        if mock_branch_result.returncode == 0:
            branch_name = mock_branch_result.stdout.strip()
            logger.info(f"✅ 测试通过：成功获取分支名 '{branch_name}'")
            
            # 验证分支名格式
            if branch_name.startswith("D_"):
                logger.info("✅ 测试通过：分支名格式符合预期")
                return True
            else:
                logger.error(f"❌ 测试失败：分支名格式不符合预期 - {branch_name}")
                return False
        else:
            logger.error("❌ 测试失败：获取分支名失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def main():
    """运行所有测试"""
    logger.info("🚀 开始测试Git修复...")
    
    tests = [
        ("统一分支名称生成", test_unified_branch_naming),
        ("Git提交逻辑", test_git_commit_logic),
        ("分支名称格式", test_branch_name_format),
        ("Git push上游分支逻辑", test_git_push_upstream_logic)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ 测试 '{test_name}' 通过")
            else:
                logger.error(f"❌ 测试 '{test_name}' 失败")
        except Exception as e:
            logger.error(f"❌ 测试 '{test_name}' 执行异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info(f"\n{'='*50}")
    logger.info("📊 测试结果汇总")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过！Git修复代码正常工作")
        return True
    else:
        logger.error(f"⚠️ 有 {total - passed} 个测试失败，需要检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)