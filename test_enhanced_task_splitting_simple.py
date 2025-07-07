#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的任务拆分提示词模板
验证是否能生成包含GitLab代码下载和结构分析的任务
"""

import asyncio
import logging
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_enhanced_task_splitting_simple.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_task_splitting_with_git():
    """测试包含GitLab代码下载的任务拆分"""
    
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
        
        # 导入任务拆分节点和提示词管理器
        from src.corder_integration.langgraph.nodes.task_splitting_node import TaskSplittingPrompts
        
        # 初始化提示词管理器
        prompts = TaskSplittingPrompts()
        logger.info("✅ 提示词管理器初始化成功")
        
        # 模拟执行计划数据
        execution_plan = {
            "execution_phases": [
                {"phase": "preparation", "tasks": ["环境配置", "代码下载"]},
                {"phase": "development", "tasks": ["接口开发", "数据库操作"]},
                {"phase": "testing", "tasks": ["集成测试", "部署"]}
            ]
        }
        
        services_summary = "包含用户服务(zqyl-user-center-service)和确权开立服务(crcl-open)两个微服务，需要从GitLab下载现有代码，分析项目结构，然后在相应位置添加新的接口功能。"
        
        # 生成任务拆分提示词
        logger.info("🔧 生成任务拆分提示词...")
        task_generation_prompt = prompts.get_prompt(
            "generate_sqlite_tasks",
            execution_plan=json.dumps(execution_plan, ensure_ascii=False, indent=2),
            services_summary=services_summary
        )
        
        logger.info(f"📝 提示词长度: {len(task_generation_prompt)}")
        logger.info("📝 提示词预览:")
        logger.info(task_generation_prompt[:500] + "...")
        
        # 调用大模型生成任务
        logger.info("🤖 调用大模型生成任务...")
        
        response = client.chat(
            messages=[
                {"role": "system", "content": "你是任务管理专家，基于设计文档和代码结构生成具体的开发任务。"},
                {"role": "user", "content": task_generation_prompt}
            ],
            temperature=0.1
        )
        
        logger.info(f"✅ 大模型响应长度: {len(response)}")
        
        # 尝试解析响应中的JSON
        try:
            # 查找JSON块
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                task_json = json_match.group(1)
            else:
                # 查找第一个JSON对象
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    task_json = json_match.group(0)
                else:
                    logger.warning("⚠️ 无法从响应中提取JSON")
                    task_json = "{}"
            
            # 解析JSON
            task_data = json.loads(task_json)
            tasks = task_data.get('tasks', [])
            
            logger.info(f"✅ 成功解析任务，共 {len(tasks)} 个任务:")
            
            # 检查是否包含预期的Git相关任务
            git_extraction_found = False
            git_clone_found = False
            code_analysis_found = False
            
            for i, task in enumerate(tasks[:10]):  # 只显示前10个任务
                task_id = task.get('task_id', 'unknown')
                task_type = task.get('task_type', 'unknown')
                description = task.get('description', 'no description')
                
                logger.info(f"  {i+1}. {task_id} ({task_type}): {description}")
                
                # 检查Git相关任务类型
                if task_type == 'git_extraction':
                    git_extraction_found = True
                    logger.info("    ✅ 找到Git地址提取任务")
                elif task_type == 'git_clone':
                    git_clone_found = True
                    logger.info("    ✅ 找到Git代码下载任务")
                elif task_type == 'code_analysis':
                    code_analysis_found = True
                    logger.info("    ✅ 找到代码结构分析任务")
                
                # 检查是否包含真实的GitLab地址
                if 'gitlab.local' in description or 'zqyl-user-center-service' in description or 'crcl-open' in description:
                    logger.info("    ✅ 包含真实的GitLab仓库信息")
                
                # 检查是否包含真实的接口路径
                if '/general/multiorgManage/queryCompanyUnitList' in description or '/crcl-open-api/lsLimit/' in description:
                    logger.info("    ✅ 包含真实的接口路径")
            
            # 验证任务流程的完整性
            logger.info("\n📊 任务流程验证:")
            logger.info(f"  Git地址提取任务: {'✅' if git_extraction_found else '❌'}")
            logger.info(f"  Git代码下载任务: {'✅' if git_clone_found else '❌'}")
            logger.info(f"  代码结构分析任务: {'✅' if code_analysis_found else '❌'}")
            
            # 检查任务摘要
            if 'task_summary' in task_data:
                summary = task_data['task_summary']
                logger.info(f"\n📈 任务摘要:")
                logger.info(f"  总任务数: {summary.get('total_tasks', 0)}")
                logger.info(f"  按服务分类: {summary.get('by_service', {})}")
                logger.info(f"  按类型分类: {summary.get('by_type', {})}")
            
            if git_extraction_found and git_clone_found and code_analysis_found:
                logger.info("✅ 任务拆分增强功能验证成功！")
                return True
            else:
                logger.warning("⚠️ 部分Git相关任务缺失")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"响应内容: {response[:1000]}...")
            return False
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """主测试函数"""
    
    logger.info("🚀 开始测试增强的任务拆分功能（简化版）")
    
    success = await test_task_splitting_with_git()
    
    logger.info("\n" + "="*50)
    logger.info("测试总结")
    logger.info("="*50)
    
    if success:
        logger.info("✅ 增强的任务拆分功能测试通过!")
        logger.info("✨ 任务拆分现在能生成包含GitLab代码下载和结构分析的完整流程")
    else:
        logger.error("❌ 增强的任务拆分功能测试失败")

if __name__ == "__main__":
    asyncio.run(main()) 