#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试节点任务执行机制 - 验证所有节点能正确领取和执行任务
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.langgraph.task_manager import NodeTaskManager
from src.corder_integration.langgraph.nodes.git_management_node import GitManagerAgent
from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
from src.corder_integration.langgraph.nodes.code_review_node import CodeReviewAgent
from src.corder_integration.langgraph.nodes.unit_testing_node import UnitTestingAgent
from src.corder_integration.langgraph.nodes.git_commit_node import GitCommitAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_test_tasks():
    """设置测试任务"""
    logger.info("🔧 设置测试任务...")
    
    task_manager = NodeTaskManager("test_node_tasks.db")
    
    # 创建测试任务
    test_tasks = [
        # Git管理任务
        {
            'task_id': 'git_extract_001',
            'service_name': '用户服务',
            'task_type': 'git_extraction',
            'priority': 1,
            'dependencies': [],
            'estimated_duration': 300,
            'description': '从设计文档中提取Git仓库信息',
            'deliverables': ['git_repositories'],
            'implementation_details': '解析设计文档中的Git URL',
            'completion_criteria': '成功提取所有Git仓库URL',
            'parameters': {
                'design_doc': 'https://github.com/example/user-service.git\nhttps://gitlab.com/example/auth-service.git'
            },
            'status': 'pending'
        },
        {
            'task_id': 'git_clone_001',
            'service_name': '用户服务',
            'task_type': 'git_clone',
            'priority': 2,
            'dependencies': ['git_extract_001'],
            'estimated_duration': 600,
            'description': '克隆用户服务仓库',
            'deliverables': ['cloned_repository'],
            'implementation_details': '克隆Git仓库到本地目录',
            'completion_criteria': '仓库成功克隆到指定目录',
            'parameters': {
                'repo_url': 'https://github.com/example/user-service.git',
                'target_dir': 'workspace/user-service'
            },
            'status': 'pending'
        },
        
        # 智能编码任务
        {
            'task_id': 'coding_analysis_001',
            'service_name': '订单服务',
            'task_type': 'code_analysis',
            'priority': 3,
            'dependencies': [],
            'estimated_duration': 900,
            'description': '分析订单服务代码结构',
            'deliverables': ['analysis_report'],
            'implementation_details': '静态代码分析',
            'completion_criteria': '生成详细的代码分析报告',
            'parameters': {},
            'status': 'pending'
        },
        {
            'task_id': 'coding_database_001',
            'service_name': '订单服务',
            'task_type': 'database',
            'priority': 4,
            'dependencies': ['coding_analysis_001'],
            'estimated_duration': 1200,
            'description': '设计订单服务数据库',
            'deliverables': ['database_schema'],
            'implementation_details': 'MySQL数据库设计',
            'completion_criteria': '完成数据库表结构设计',
            'parameters': {},
            'status': 'pending'
        },
        {
            'task_id': 'coding_api_001',
            'service_name': '订单服务',
            'task_type': 'api',
            'priority': 5,
            'dependencies': ['coding_database_001'],
            'estimated_duration': 1500,
            'description': '设计订单服务API',
            'deliverables': ['api_specification'],
            'implementation_details': 'RESTful API设计',
            'completion_criteria': '完成API接口设计',
            'parameters': {},
            'status': 'pending'
        },
        
        # 代码审查任务
        {
            'task_id': 'review_api_001',
            'service_name': '订单服务',
            'task_type': 'api',
            'priority': 6,
            'dependencies': ['coding_api_001'],
            'estimated_duration': 600,
            'description': '审查订单服务API设计',
            'deliverables': ['review_report'],
            'implementation_details': 'API设计审查',
            'completion_criteria': 'API审查通过',
            'parameters': {},
            'status': 'pending'
        },
        
        # 测试任务
        {
            'task_id': 'test_integration_001',
            'service_name': '订单服务',
            'task_type': 'integration_test',
            'priority': 7,
            'dependencies': ['review_api_001'],
            'estimated_duration': 1800,
            'description': '执行订单服务集成测试',
            'deliverables': ['test_report'],
            'implementation_details': '集成测试执行',
            'completion_criteria': '测试通过率90%以上',
            'parameters': {},
            'status': 'pending'
        },
        
        # 部署任务
        {
            'task_id': 'deploy_001',
            'service_name': '订单服务',
            'task_type': 'deployment',
            'priority': 8,
            'dependencies': ['test_integration_001'],
            'estimated_duration': 900,
            'description': '部署订单服务',
            'deliverables': ['deployed_service'],
            'implementation_details': 'Docker容器部署',
            'completion_criteria': '服务成功部署到预发布环境',
            'parameters': {
                'deployment_type': 'docker',
                'target_branch': 'main'
            },
            'status': 'pending'
        }
    ]
    
    # 保存任务到数据库
    for task in test_tasks:
        # 构造完整的任务数据
        full_task = {
            'task_id': task['task_id'],
            'service_name': task['service_name'],
            'task_type': task['task_type'],
            'priority': task['priority'],
            'dependencies': task['dependencies'],
            'estimated_duration': task['estimated_duration'],
            'description': task['description'],
            'deliverables': task['deliverables'],
            'implementation_details': task['implementation_details'],
            'completion_criteria': task['completion_criteria'],
            'parameters': task['parameters'],
            'status': task['status']
        }
        
        # 使用内部方法保存单个任务
        task_manager._save_single_task(full_task)
    
    logger.info(f"✅ 成功创建 {len(test_tasks)} 个测试任务")
    return test_tasks

async def test_node_execution():
    """测试各个节点的任务执行"""
    logger.info("🚀 开始测试节点任务执行...")
    
    # 创建各个节点的代理
    agents = {
        'git_management': GitManagerAgent(),
        'intelligent_coding': IntelligentCodingAgent(),
        'code_review': CodeReviewAgent(),
        'unit_testing': UnitTestingAgent(),
        'git_commit': GitCommitAgent()
    }
    
    execution_results = {}
    
    # 依次执行各个节点的任务
    for node_name, agent in agents.items():
        logger.info(f"🎯 测试 {node_name} 节点...")
        
        try:
            results = agent.execute_task_from_database()
            execution_results[node_name] = {
                'success': True,
                'tasks_executed': len(results),
                'results': results
            }
            
            logger.info(f"✅ {node_name} 节点执行完成，处理了 {len(results)} 个任务")
            
            # 等待一下再执行下一个节点，确保依赖关系正确处理
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ {node_name} 节点执行失败: {e}")
            execution_results[node_name] = {
                'success': False,
                'error': str(e),
                'tasks_executed': 0
            }
    
    return execution_results

async def check_task_statistics():
    """检查任务统计信息"""
    logger.info("📊 检查任务统计信息...")
    
    task_manager = NodeTaskManager("test_node_tasks.db")
    stats = task_manager.get_task_statistics()
    
    logger.info("📈 任务统计:")
    for status, count in stats.items():
        logger.info(f"   {status}: {count}")
    
    return stats

async def main():
    """主测试函数"""
    logger.info("🧪 开始节点任务执行测试...")
    
    try:
        # 1. 设置测试任务
        test_tasks = await setup_test_tasks()
        
        # 2. 检查初始统计
        initial_stats = await check_task_statistics()
        
        # 3. 执行节点任务
        execution_results = await test_node_execution()
        
        # 4. 检查最终统计
        final_stats = await check_task_statistics()
        
        # 5. 汇总结果
        logger.info("\n" + "="*60)
        logger.info("📋 测试结果汇总:")
        logger.info("="*60)
        
        total_tasks_executed = 0
        successful_nodes = 0
        
        for node_name, result in execution_results.items():
            if result['success']:
                successful_nodes += 1
                total_tasks_executed += result['tasks_executed']
                logger.info(f"✅ {node_name}: {result['tasks_executed']} 个任务")
            else:
                logger.info(f"❌ {node_name}: 执行失败 - {result.get('error', 'Unknown error')}")
        
        logger.info(f"\n📊 统计信息:")
        logger.info(f"   总任务数: {len(test_tasks)}")
        logger.info(f"   执行任务数: {total_tasks_executed}")
        logger.info(f"   成功节点数: {successful_nodes}/{len(execution_results)}")
        
        logger.info(f"\n📈 任务状态变化:")
        logger.info(f"   初始pending: {initial_stats.get('pending', 0)}")
        logger.info(f"   最终completed: {final_stats.get('completed', 0)}")
        logger.info(f"   最终failed: {final_stats.get('failed', 0)}")
        logger.info(f"   最终in_progress: {final_stats.get('in_progress', 0)}")
        
        # 判断测试是否成功
        if successful_nodes == len(execution_results) and total_tasks_executed > 0:
            logger.info(f"\n🎉 测试成功！所有节点都能正确领取和执行任务")
            return True
        else:
            logger.info(f"\n⚠️ 测试部分成功，有一些节点执行失败")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {e}")
        return False
    finally:
        # 清理测试文件
        try:
            import os
            if os.path.exists("test_node_tasks.db"):
                os.remove("test_node_tasks.db")
                logger.info("🧹 清理测试数据库文件")
        except Exception as e:
            logger.warning(f"清理测试文件失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 