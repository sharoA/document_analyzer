#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试intelligent_coding_node的循环修复
"""

import asyncio
import logging
from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_intelligent_coding_fix():
    """测试intelligent_coding_node的循环修复"""
    print("🧪 开始测试intelligent_coding_node的循环修复...")
    
    try:
        # 创建智能编码代理
        coding_agent = IntelligentCodingAgent()
        
        print(f"✅ 智能编码代理创建成功")
        print(f"📋 支持的任务类型: {coding_agent.supported_task_types}")
        
        # 执行数据库中的任务
        print("\n🚀 开始执行数据库中的任务...")
        execution_results = coding_agent.execute_task_from_database()
        
        print(f"\n📊 执行结果摘要:")
        print(f"   - 总共执行任务数: {len(execution_results)}")
        
        # 按任务类型统计
        task_type_stats = {}
        success_count = 0
        
        for result in execution_results:
            task_type = result['task_type']
            task_type_stats[task_type] = task_type_stats.get(task_type, 0) + 1
            
            if result['result'].get('success'):
                success_count += 1
            
            print(f"   - {result['task_id']}: {task_type} - {'✅成功' if result['result'].get('success') else '❌失败'}")
        
        print(f"\n📈 统计信息:")
        print(f"   - 成功执行: {success_count}/{len(execution_results)}")
        print(f"   - 任务类型分布: {task_type_stats}")
        
        # 检查是否执行了期望的任务类型
        expected_types = ["code_analysis", "config", "database", "api"]
        executed_types = set(task_type_stats.keys())
        
        print(f"\n🎯 期望执行的任务类型: {expected_types}")
        print(f"🎯 实际执行的任务类型: {list(executed_types)}")
        
        if executed_types.intersection(set(expected_types)):
            print("✅ 循环修复生效，执行了多种类型的任务")
        else:
            print("⚠️ 可能还有问题，请检查任务依赖关系")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_intelligent_coding_fix()) 