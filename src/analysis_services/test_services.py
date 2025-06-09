"""
分析服务模块测试文件
用于验证各个服务的基本功能
"""

import asyncio
import logging
from typing import Dict, Any

# 导入分析服务模块
from . import (
    AnalysisServiceManager,
    get_analysis_config,
    validate_input,
    setup_analysis_logger,
    clean_text,
    generate_analysis_id,
    get_timestamp
)

# 设置日志
logger = setup_analysis_logger("analysis_test", "test_analysis.log")

class AnalysisServiceTester:
    """分析服务测试类"""
    
    def __init__(self):
        self.config = get_analysis_config()
        self.manager = None
        
    async def setup(self):
        """初始化测试环境"""
        logger.info("初始化分析服务测试环境...")
        
        # 初始化服务管理器
        self.manager = AnalysisServiceManager(
            llm_client=None,  # 使用模拟客户端
            vector_db_type="mock"
        )
        
        await self.manager.initialize_services()
        logger.info("服务管理器初始化完成")
    
    def test_config(self):
        """测试配置功能"""
        logger.info("测试配置功能...")
        
        # 测试获取配置
        config = get_analysis_config()
        assert isinstance(config, dict), "配置应该是字典类型"
        assert "llm" in config, "配置应该包含LLM配置"
        assert "vector_db" in config, "配置应该包含向量数据库配置"
        
        # 测试获取特定配置
        llm_config = get_analysis_config("llm")
        assert "max_tokens" in llm_config, "LLM配置应该包含max_tokens"
        
        logger.info("✓ 配置功能测试通过")
    
    def test_utils(self):
        """测试工具函数"""
        logger.info("测试工具函数...")
        
        # 测试文本清理
        dirty_text = "  这是一个   测试文本  \n\n  "
        clean = clean_text(dirty_text)
        assert clean == "这是一个 测试文本", f"文本清理失败: {clean}"
        
        # 测试输入验证
        validation = validate_input("test_task_001", "测试内容", "txt")
        assert all(validation.values()), f"输入验证失败: {validation}"
        
        # 测试无效输入
        invalid_validation = validate_input("", "", "invalid")
        assert not any(invalid_validation.values()), "无效输入应该验证失败"
        
        # 测试ID生成
        analysis_id = generate_analysis_id("test_task", "test content")
        assert len(analysis_id) == 64, "分析ID应该是64位哈希"
        
        # 测试时间戳
        timestamp = get_timestamp()
        assert "T" in timestamp, "时间戳应该是ISO格式"
        
        logger.info("✓ 工具函数测试通过")
    
    async def test_document_parser(self):
        """测试文档解析服务"""
        logger.info("测试文档解析服务...")
        
        test_content = """
        这是一个测试文档。
        
        功能需求：
        1. 用户注册功能
        2. 用户登录功能
        3. 用户信息查询
        4. 用户信息修改
        5. 用户注销功能
        
        技术要求：
        - 使用RESTful API
        - 支持JWT认证
        - 数据库使用MySQL
        """
        
        result = await self.manager.parse_document(
            task_id="test_parse_001",
            content=test_content,
            file_type="txt"
        )
        
        assert result["success"], f"文档解析失败: {result.get('error')}"
        assert "parsing_result" in result, "解析结果应该包含parsing_result"
        
        parsing_result = result["parsing_result"]
        assert parsing_result["character_count"] > 0, "字符数应该大于0"
        assert parsing_result["file_type"] == "txt", "文件类型应该正确"
        
        logger.info("✓ 文档解析服务测试通过")
        return result
    
    async def test_content_analyzer(self):
        """测试内容分析服务"""
        logger.info("测试内容分析服务...")
        
        # 先进行文档解析
        parse_result = await self.test_document_parser()
        parsing_result = parse_result["parsing_result"]
        
        # 进行内容分析
        result = await self.manager.analyze_content(
            task_id="test_analyze_001",
            parsing_result=parsing_result
        )
        
        assert result["success"], f"内容分析失败: {result.get('error')}"
        assert "content_analysis" in result, "分析结果应该包含content_analysis"
        
        content_analysis = result["content_analysis"]
        assert "crud_analysis" in content_analysis, "应该包含CRUD分析"
        assert len(content_analysis["crud_analysis"]["crud_operations"]) > 0, "应该识别出CRUD操作"
        
        logger.info("✓ 内容分析服务测试通过")
        return result
    
    async def test_ai_analyzer(self):
        """测试AI分析服务"""
        logger.info("测试AI分析服务...")
        
        # 先进行内容分析
        content_result = await self.test_content_analyzer()
        content_analysis = content_result["content_analysis"]
        crud_operations = content_analysis["crud_analysis"]["crud_operations"]
        
        # 进行AI分析
        result = await self.manager.analyze_with_ai(
            task_id="test_ai_001",
            content_analysis_result=content_analysis,
            crud_operations=crud_operations
        )
        
        assert result["success"], f"AI分析失败: {result.get('error')}"
        assert "ai_analysis" in result, "分析结果应该包含ai_analysis"
        
        ai_analysis = result["ai_analysis"]
        assert "api_design" in ai_analysis, "应该包含API设计"
        assert "mq_configuration" in ai_analysis, "应该包含MQ配置"
        
        logger.info("✓ AI分析服务测试通过")
        return result
    
    async def test_full_analysis(self):
        """测试完整分析流程"""
        logger.info("测试完整分析流程...")
        
        test_content = """
        电商系统需求文档
        
        用户管理模块：
        1. 用户注册 - 创建新用户账户
        2. 用户登录 - 验证用户身份
        3. 用户信息查询 - 获取用户详细信息
        4. 用户信息更新 - 修改用户资料
        5. 用户删除 - 注销用户账户
        
        商品管理模块：
        1. 商品添加 - 新增商品信息
        2. 商品查询 - 搜索和浏览商品
        3. 商品更新 - 修改商品信息
        4. 商品删除 - 移除商品
        
        订单管理模块：
        1. 订单创建 - 生成新订单
        2. 订单查询 - 查看订单状态
        3. 订单更新 - 修改订单信息
        4. 订单取消 - 取消订单
        """
        
        result = await self.manager.execute_full_analysis(
            task_id="test_full_001",
            content=test_content,
            file_type="txt"
        )
        
        assert result["success"], f"完整分析失败: {result.get('error')}"
        assert "summary" in result, "应该包含分析摘要"
        
        summary = result["summary"]
        assert summary["total_crud_operations"] > 0, "应该识别出CRUD操作"
        assert summary["api_endpoints_count"] > 0, "应该生成API端点"
        
        logger.info("✓ 完整分析流程测试通过")
        return result
    
    async def test_service_status(self):
        """测试服务状态"""
        logger.info("测试服务状态...")
        
        status = await self.manager.get_service_status()
        
        assert "document_parser" in status, "应该包含文档解析服务状态"
        assert "content_analyzer" in status, "应该包含内容分析服务状态"
        assert "ai_analyzer" in status, "应该包含AI分析服务状态"
        assert "vector_database" in status, "应该包含向量数据库状态"
        
        logger.info("✓ 服务状态测试通过")
    
    async def cleanup(self):
        """清理测试环境"""
        logger.info("清理测试环境...")
        
        if self.manager:
            await self.manager.cleanup()
        
        logger.info("测试环境清理完成")

async def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行分析服务模块测试...")
    
    tester = AnalysisServiceTester()
    
    try:
        # 初始化
        await tester.setup()
        
        # 运行测试
        tester.test_config()
        tester.test_utils()
        await tester.test_document_parser()
        await tester.test_content_analyzer()
        await tester.test_ai_analyzer()
        await tester.test_full_analysis()
        await tester.test_service_status()
        
        logger.info("🎉 所有测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise
    
    finally:
        # 清理
        await tester.cleanup()

def run_tests():
    """运行测试的同步入口"""
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    run_tests() 