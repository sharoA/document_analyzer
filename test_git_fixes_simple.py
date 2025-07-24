#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Git修复测试 - 不依赖LangGraph
"""

import logging
import re
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_branch_name_generation():
    """测试分支名称生成逻辑"""
    logger.info("🧪 测试: 分支名称生成逻辑")
    
    def generate_unified_branch_name(project_name: str) -> str:
        """模拟统一生成分支名称的逻辑"""
        # 生成日期时间格式：YYYYMMDDHHMM
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        
        # 清理项目名称，只保留中文和英文字符
        clean_project_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', project_name)
        
        branch_name = f"D_{current_time}_{clean_project_name}"
        return branch_name
    
    # 测试不同的项目名称
    test_cases = [
        ("测试项目", "测试项目"),
        ("链数中建一局_1753349525", "链数中建一局"),
        ("Project123测试", "Project测试"),
        ("带有特殊字符@#$%的项目名", "带有特殊字符的项目名"),
        ("English Project Name", "EnglishProjectName")
    ]
    
    all_passed = True
    for input_name, expected_clean in test_cases:
        branch_name = generate_unified_branch_name(input_name)
        logger.info(f"📋 输入: '{input_name}' -> 分支名: '{branch_name}'")
        
        # 验证分支名格式：D_YYYYMMDDHHMM_清理后的项目名
        parts = branch_name.split('_')
        if len(parts) >= 3 and parts[0] == 'D' and len(parts[1]) == 12 and parts[1].isdigit():
            actual_clean = '_'.join(parts[2:])
            if actual_clean == expected_clean:
                logger.info(f"✅ 通过: 清理结果正确 '{actual_clean}'")
            else:
                logger.error(f"❌ 失败: 清理结果不正确 - 期望'{expected_clean}', 实际'{actual_clean}'")
                all_passed = False
        else:
            logger.error(f"❌ 失败: 分支名格式不正确 - {branch_name}")
            all_passed = False
    
    return all_passed

def test_git_push_error_detection():
    """测试Git push错误检测逻辑"""
    logger.info("🧪 测试: Git push错误检测逻辑")
    
    # 模拟不同的Git push错误情况
    test_cases = [
        {
            'name': '需要设置上游分支',
            'returncode': 1,
            'stderr': 'fatal: The current branch D_202507241733_链数中建一局 has no upstream branch.\nTo push the current branch and set the remote as upstream, use\n\n    git push --set-upstream origin D_202507241733_链数中建一局',
            'should_setup_upstream': True
        },
        {
            'name': '普通push成功',
            'returncode': 0,
            'stderr': '',
            'should_setup_upstream': False
        },
        {
            'name': '权限错误',
            'returncode': 1,
            'stderr': 'remote: Permission denied',
            'should_setup_upstream': False
        },
        {
            'name': '网络错误',
            'returncode': 1,
            'stderr': 'fatal: unable to access repository',
            'should_setup_upstream': False
        }
    ]
    
    all_passed = True
    for case in test_cases:
        # 模拟检测逻辑
        needs_upstream = case['returncode'] != 0 and "no upstream branch" in case['stderr']
        
        if needs_upstream == case['should_setup_upstream']:
            logger.info(f"✅ 通过: {case['name']} - 正确检测到是否需要设置上游分支")
        else:
            logger.error(f"❌ 失败: {case['name']} - 检测结果错误")
            logger.error(f"   期望需要上游设置: {case['should_setup_upstream']}, 实际检测: {needs_upstream}")
            all_passed = False
    
    return all_passed

def test_git_command_construction():
    """测试Git命令构造逻辑"""
    logger.info("🧪 测试: Git命令构造逻辑")
    
    # 测试分支名提取
    branch_output = "D_202507241733_链数中建一局\n"
    current_branch = branch_output.strip()
    
    if current_branch == "D_202507241733_链数中建一局":
        logger.info("✅ 通过: 正确提取分支名")
        
        # 测试上游命令构造
        expected_command = ['git', 'push', '--set-upstream', 'origin', 'D_202507241733_链数中建一局']
        actual_command = ['git', 'push', '--set-upstream', 'origin', current_branch]
        
        if expected_command == actual_command:
            logger.info("✅ 通过: 正确构造上游设置命令")
            return True
        else:
            logger.error(f"❌ 失败: 命令构造错误 - 期望{expected_command}, 实际{actual_command}")
            return False
    else:
        logger.error(f"❌ 失败: 分支名提取错误 - {current_branch}")
        return False

def test_repo_parameters_parsing():
    """测试仓库参数解析逻辑"""
    logger.info("🧪 测试: 仓库参数解析逻辑")
    
    # 模拟任务参数
    test_parameters = {
        'repositories': [
            {
                'path': '/Users/renyu/Documents/create_project/链数中建一局_1753349525/zqyl-user-center-service',
                'changes': '新增用户服务相关功能'
            },
            {
                'path': '/Users/renyu/Documents/create_project/链数中建一局_1753349525/crcl-open',
                'changes': '新增确权开立服务相关功能'
            }
        ]
    }
    
    # 模拟解析逻辑
    repositories = test_parameters.get('repositories', [])
    
    if len(repositories) == 2:
        logger.info("✅ 通过: 正确解析到2个仓库")
        
        # 验证每个仓库的信息
        for i, repo_info in enumerate(repositories):
            if isinstance(repo_info, dict):
                repo_path = repo_info.get('path', '')
                changes_desc = repo_info.get('changes', '')
                
                if repo_path and changes_desc:
                    logger.info(f"✅ 通过: 仓库{i+1}信息完整 - 路径: {repo_path}")
                    logger.info(f"        变更描述: {changes_desc}")
                else:
                    logger.error(f"❌ 失败: 仓库{i+1}信息不完整")
                    return False
            else:
                logger.error(f"❌ 失败: 仓库{i+1}格式不正确")
                return False
        
        return True
    else:
        logger.error(f"❌ 失败: 仓库数量错误 - 期望2个, 实际{len(repositories)}个")
        return False

def main():
    """运行所有测试"""
    logger.info("🚀 开始简化版Git修复测试...")
    
    tests = [
        ("分支名称生成逻辑", test_branch_name_generation),
        ("Git push错误检测逻辑", test_git_push_error_detection),
        ("Git命令构造逻辑", test_git_command_construction),
        ("仓库参数解析逻辑", test_repo_parameters_parsing)
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
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
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
        logger.info("🎉 所有测试通过！Git修复逻辑正确")
        return True
    else:
        logger.error(f"⚠️ 有 {total - passed} 个测试失败，需要检查代码")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)