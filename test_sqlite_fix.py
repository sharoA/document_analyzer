#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SQLite修复是否有效
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.langgraph.workflow_orchestrator import LangGraphWorkflowOrchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_sqlite_checkpoint():
    """测试SQLite检查点是否正常工作"""
    logger.info("🚀 开始测试SQLite检查点...")
    
    try:
        # 创建工作流编排器
        orchestrator = LangGraphWorkflowOrchestrator(use_sqlite=True, db_path="test_workflow.db")
        logger.info("✅ 工作流编排器创建成功")
        
        # 简单的设计文档
        design_doc = """
设计文档 - 测试项目

项目背景：
测试SQLite检查点是否正常工作

功能需求：
1. 用户管理 - 用户注册、登录
2. 数据管理 - 数据CRUD操作

技术要求：Spring Boot + MySQL
"""
        
        project_name = "SQLite测试项目"
        
        logger.info(f"📄 开始执行工作流: {project_name}")
        
        # 执行工作流
        result = await orchestrator.execute_workflow(
            document_content=design_doc,
            project_name=project_name,
            output_path="D:/gitlab/test"
        )
        
        logger.info(f"✅ 工作流执行完成: {result['status']}")
        
        if result['status'] == 'success':
            logger.info("🎉 SQLite检查点测试成功！")
            return True
        else:
            logger.error(f"❌ 工作流执行失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ SQLite检查点测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("SQLite检查点修复验证测试")
    logger.info("=" * 50)
    
    # 运行异步测试
    try:
        result = asyncio.run(test_sqlite_checkpoint())
        
        if result:
            logger.info("🎉 测试通过！SQLite修复有效")
            return True
        else:
            logger.error("❌ 测试失败！需要进一步调试")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试执行异常: {e}")
        return False
    finally:
        # 清理测试数据库文件
        try:
            if os.path.exists("test_workflow.db"):
                os.remove("test_workflow.db")
                logger.info("🧹 清理测试数据库文件")
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 