#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能编码节点的功能
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_intelligent_coding_agent_basic():
    """测试智能编码智能体的基本功能"""
    logger.info("🚀 开始测试智能编码智能体基本功能...")
    
    try:
        # 导入智能编码智能体
        from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
        
        # 创建智能体实例
        agent = IntelligentCodingAgent()
        
        # 测试1: 检查初始化状态
        logger.info("📋 测试1: 检查初始化状态")
        logger.info(f"   - LLM客户端: {'已初始化' if agent.llm_client else '未初始化'}")
        logger.info(f"   - LLM提供商: {agent.llm_provider}")
        logger.info(f"   - 支持的任务类型: {agent.supported_task_types}")
        logger.info(f"   - ReAct配置: {agent.react_config}")
        
        # 测试2: 检查ReAct状态
        logger.info("📋 测试2: 检查ReAct状态")
        react_status = agent.get_react_status()
        logger.info(f"   - ReAct启用: {react_status['react_enabled']}")
        logger.info(f"   - LLM可用: {react_status['llm_available']}")
        logger.info(f"   - 支持功能: {react_status['supported_features']}")
        
        # 测试3: 检查可用工具
        logger.info("📋 测试3: 检查可用工具")
        tools = agent.get_available_tools()
        for tool_name, tool_info in tools.items():
            logger.info(f"   - {tool_name}: {tool_info['description']}")
        
        # 测试4: 测试路径优先级计算方法
        logger.info("📋 测试4: 测试路径优先级计算方法")
        test_path = "/test/project/src/main/java"
        test_service = "TestService"
        test_java_count = 10
        
        priority = agent._calculate_enhanced_path_priority(test_path, test_service, test_java_count)
        logger.info(f"   - 测试路径: {test_path}")
        logger.info(f"   - 服务名: {test_service}")
        logger.info(f"   - Java文件数: {test_java_count}")
        logger.info(f"   - 计算优先级: {priority}")
        
        logger.info("✅ 智能编码智能体基本功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 智能编码智能体基本功能测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_intelligent_coding_node_function():
    """测试智能编码节点函数"""
    logger.info("🚀 开始测试智能编码节点函数...")
    
    try:
        # 导入节点函数
        from src.corder_integration.langgraph.nodes.intelligent_coding_node import intelligent_coding_node
        
        # 构造测试状态
        test_state = {
            'design_doc': '测试设计文档',
            'project_name': 'test_project',
            'identified_services': ['test_service'],
            'service_dependencies': {},
            'task_execution_plan': {},
            'parallel_tasks': [],
            'git_repo_url': None,
            'target_branch': 'test_branch',
            'project_paths': {},
            'output_path': '/test/output',
            'repo_initialized': False,
            'generated_services': {},
            'generated_apis': {},
            'generated_sql': {},
            'service_interconnections': {},
            'unit_test_results': {},
            'test_coverage': {},
            'interface_compatibility': {},
            'code_review_results': {},
            'static_analysis_results': {},
            'security_scan_results': {},
            'commit_hashes': {},
            'push_results': {},
            'pr_urls': {},
            'current_phase': 'intelligent_coding',
            'completed_services': [],
            'failed_services': [],
            'retry_count': 0,
            'execution_errors': []
        }
        
        logger.info("📋 测试智能编码节点函数")
        
        # 运行异步函数
        async def run_test():
            result = await intelligent_coding_node(test_state)
            return result
        
        # 执行测试
        result = asyncio.run(run_test())
        
        logger.info(f"   - 返回结果类型: {type(result)}")
        logger.info(f"   - 返回键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            if 'coding_operations' in result:
                logger.info(f"   - 编码操作数量: {len(result['coding_operations'])}")
            if 'intelligent_coding_completed' in result:
                logger.info(f"   - 智能编码完成: {result['intelligent_coding_completed']}")
            if 'error' in result:
                logger.warning(f"   - 错误信息: {result['error']}")
        
        logger.info("✅ 智能编码节点函数测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 智能编码节点函数测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_task_manager_integration():
    """测试任务管理器集成"""
    logger.info("🚀 开始测试任务管理器集成...")
    
    try:
        # 导入任务管理器
        from src.corder_integration.langgraph.task_manager import NodeTaskManager
        
        # 创建任务管理器实例
        task_manager = NodeTaskManager()
        
        logger.info("📋 测试任务管理器基本功能")
        
        # 测试获取任务
        task_types = ['code_analysis', 'database', 'api', 'config']
        available_tasks = task_manager.get_node_tasks(task_types)
        
        logger.info(f"   - 支持的任务类型: {task_types}")
        logger.info(f"   - 可用任务数量: {len(available_tasks)}")
        
        if available_tasks:
            logger.info("   - 前几个任务:")
            for i, task in enumerate(available_tasks[:3]):
                logger.info(f"     {i+1}. 任务ID: {task.get('task_id', 'N/A')}")
                logger.info(f"        任务类型: {task.get('task_type', 'N/A')}")
                logger.info(f"        服务名: {task.get('service_name', 'N/A')}")
        else:
            logger.info("   - 当前没有可用任务")
        
        logger.info("✅ 任务管理器集成测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 任务管理器集成测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def test_service_decision_maker():
    """测试Service决策制定器"""
    logger.info("🚀 开始测试Service决策制定器...")
    
    try:
        # 导入Service决策制定器
        from src.corder_integration.code_generator.service_decision_maker import ServiceDecisionMaker
        
        # 创建决策制定器实例
        decision_maker = ServiceDecisionMaker()
        
        logger.info("📋 测试Service决策制定器基本功能")
        
        # 构造测试数据
        test_controller_info = {
            'services': [
                {'type': 'UserService', 'variable': 'userService'},
                {'type': 'OrderService', 'variable': 'orderService'}
            ],
            'file_path': '/test/controller/TestController.java'
        }
        
        test_interface_name = "QueryUserOrder"
        test_api_path = "/api/user/order/query"
        
        # 测试分析Service需求
        analysis_result = decision_maker.analyze_service_requirements(
            test_controller_info, test_interface_name, test_api_path
        )
        
        logger.info(f"   - 分析结果类型: {type(analysis_result)}")
        if isinstance(analysis_result, dict):
            logger.info(f"   - 分析结果键: {list(analysis_result.keys())}")
            
            decision = analysis_result.get('decision', {})
            logger.info(f"   - 决策行动: {decision.get('action', 'N/A')}")
            logger.info(f"   - 决策理由: {decision.get('reason', 'N/A')}")
            logger.info(f"   - 需要新Service: {decision.get('need_new_service', False)}")
            logger.info(f"   - 修改现有Service: {decision.get('modify_existing', False)}")
            
            recommendations = analysis_result.get('recommendations', [])
            logger.info(f"   - 推荐建议数量: {len(recommendations)}")
        
        logger.info("✅ Service决策制定器测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service决策制定器测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False

def main():
    """主测试函数"""
    logger.info("🎯 开始智能编码节点综合测试")
    
    # 统计测试结果
    test_results = []
    
    # 执行各个测试
    tests = [
        ("智能编码智能体基本功能", test_intelligent_coding_agent_basic),
        ("智能编码节点函数", test_intelligent_coding_node_function),
        ("任务管理器集成", test_task_manager_integration),
        ("Service决策制定器", test_service_decision_maker)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"开始测试: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    logger.info(f"\n{'='*60}")
    logger.info("📊 测试总结")
    logger.info(f"{'='*60}")
    
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    logger.info(f"总测试数: {total_count}")
    logger.info(f"通过测试: {passed_count}")
    logger.info(f"失败测试: {total_count - passed_count}")
    logger.info(f"通过率: {passed_count/total_count*100:.1f}%")
    
    logger.info("\n详细结果:")
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  - {test_name}: {status}")
    
    if passed_count == total_count:
        logger.info("\n🎉 所有测试都通过了！智能编码节点功能正常。")
        return True
    else:
        logger.warning(f"\n⚠️ {total_count - passed_count} 个测试失败，需要检查相关功能。")
        return False

if __name__ == "__main__":
    # 设置工作目录
    os.chdir(project_root)
    
    # 运行测试
    success = main()
    
    # 退出码
    sys.exit(0 if success else 1)