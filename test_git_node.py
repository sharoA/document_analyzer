#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Git管理节点
"""

import asyncio
import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.langgraph.nodes.git_management_node import git_management_node

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_git_node.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_git_management_node():
    """测试Git管理节点"""
    
    logger.info("🚀 开始测试Git管理节点...")
    
    # 模拟状态
    test_state = {
        'design_doc': '''
        用户服务仓库: https://gitlab.local/zqyl/zqyl-user-center-service.git
        确权开立服务仓库: http://gitlab.local/ls/crcl-open.git
        
        这两个仓库需要从master分支拉取代码。
        ''',
        'output_path': 'D:/gitlab',
        'project_name': 'test_project',
        'repo_initialized': False
    }
    
    try:
        # 执行Git管理节点
        result_state = await git_management_node(test_state)
        
        logger.info("✅ Git管理节点执行完成")
        logger.info(f"📊 结果状态: {result_state}")
        
        # 检查关键结果
        if 'git_operations' in result_state:
            logger.info(f"🔧 Git操作数量: {len(result_state['git_operations'])}")
            for i, operation in enumerate(result_state['git_operations']):
                logger.info(f"  📋 操作 {i+1}: {operation.get('task_type')} - {operation.get('result', {}).get('success', 'Unknown')}")
        
        if 'repo_initialized' in result_state:
            logger.info(f"🏁 仓库初始化状态: {result_state['repo_initialized']}")
        
        if 'cloned_repositories' in result_state:
            logger.info(f"📦 克隆的仓库数量: {len(result_state.get('cloned_repositories', []))}")
            for repo in result_state.get('cloned_repositories', []):
                logger.info(f"  📁 {repo.get('repo_name')} -> {repo.get('local_path')}")
        
        if 'git_summary' in result_state:
            summary = result_state['git_summary']
            logger.info(f"📈 执行摘要:")
            logger.info(f"  🔍 提取仓库: {summary.get('extracted_repos', 0)}")
            logger.info(f"  📥 克隆仓库: {summary.get('cloned_repos', 0)}")
            logger.info(f"  📋 处理任务: {summary.get('database_tasks_processed', 0)}")
        
        return result_state
        
    except Exception as e:
        logger.error(f"❌ Git管理节点测试失败: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_git_management_node()) 