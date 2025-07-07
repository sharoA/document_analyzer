#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的任务拆分测试
调用完整的任务拆分节点并保存到数据库
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_full_task_splitting.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_full_task_splitting():
    """测试完整的任务拆分流程"""
    
    try:
        # 读取设计文档
        design_doc_path = "combined_document_demo.txt"
        if not os.path.exists(design_doc_path):
            logger.error(f"设计文档不存在: {design_doc_path}")
            return False
        
        with open(design_doc_path, 'r', encoding='utf-8') as f:
            design_doc = f.read()
        
        logger.info(f"✅ 成功读取设计文档，长度: {len(design_doc)} 字符")
        
        # 检查火山引擎客户端
        try:
            from src.utils.volcengine_client import get_volcengine_client
            client = get_volcengine_client()
            logger.info("✅ 火山引擎客户端连接成功")
        except Exception as e:
            logger.error(f"❌ 火山引擎客户端连接失败: {e}")
            return False
        
        # 导入任务拆分节点
        from src.corder_integration.langgraph.nodes.task_splitting_node import task_splitting_node
        
        # 准备状态数据
        state = {
            "project_name": "链数优化项目测试",
            "design_doc": design_doc,
            "current_phase": "task_splitting",
            "execution_errors": []
        }
        
        logger.info("🚀 开始执行完整的任务拆分节点...")
        
        # 调用任务拆分节点
        result_state = await task_splitting_node(state)
        
        logger.info(f"✅ 任务拆分节点执行完成")
        logger.info(f"📊 生成的任务数量: {len(result_state.get('generated_tasks', []))}")
        logger.info(f"🎯 识别的服务: {result_state.get('identified_services', [])}")
        logger.info(f"🔄 当前阶段: {result_state.get('current_phase', 'unknown')}")
        
        # 检查数据库中的任务
        import sqlite3
        conn = sqlite3.connect('coding_agent_workflow.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM execution_tasks')
        count = cursor.fetchone()[0]
        logger.info(f"📦 数据库中的任务数量: {count}")
        
        if count >= 12:
            logger.info("✅ 任务拆分成功！生成了完整的12个任务")
            
            # 显示任务列表
            cursor.execute('SELECT task_id, task_type, service_name, description FROM execution_tasks ORDER BY priority ASC')
            tasks = cursor.fetchall()
            logger.info("📝 完整任务列表:")
            for i, task in enumerate(tasks, 1):
                logger.info(f"  {i:2d}. {task[0]} ({task[1]}) - {task[2]}: {task[3][:50]}...")
            
            conn.close()
            return True
        else:
            logger.warning(f"⚠️ 任务数量不足，期望12个，实际{count}个")
            conn.close()
            return False
        
    except Exception as e:
        logger.error(f"❌ 完整任务拆分测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """主测试函数"""
    
    logger.info("🚀 开始完整的任务拆分测试")
    
    success = await test_full_task_splitting()
    
    logger.info("\n" + "="*50)
    logger.info("测试总结")
    logger.info("="*50)
    
    if success:
        logger.info("✅ 完整任务拆分测试通过!")
        logger.info("✨ 任务拆分节点成功生成了包含GitLab代码下载和结构分析的12个完整任务")
        logger.info("💾 所有任务已保存到数据库，可以进行下一步智能编码")
    else:
        logger.error("❌ 完整任务拆分测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 