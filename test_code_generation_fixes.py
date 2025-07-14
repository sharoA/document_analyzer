#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码生成修复验证脚本
用于测试DDD架构、完整组件生成和备份文件清理功能
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.corder_integration.langgraph.nodes.intelligent_coding_node import IntelligentCodingAgent
from src.corder_integration.code_generator.interface_adder import InterfaceAdder

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ddd_architecture_paths():
    """测试DDD架构路径映射"""
    logger.info("🧪 测试DDD架构路径映射...")
    
    agent = IntelligentCodingAgent()
    
    # 模拟项目上下文
    project_context = {
        'package_patterns': {
            'base_package': 'com.yljr.crcl'
        },
        'current_api_path': '/crcl-open-api/lsLimit/listUnitLimitByCompanyId'
    }
    
    # 测试路径映射
    layer_paths = agent._get_contextual_package_structure(
        "/test/project/path", 
        "/crcl-open-api/lsLimit/listUnitLimitByCompanyId",
        project_context
    )
    
    # 验证DDD架构分层
    expected_layers = [
        'controller', 'service', 'service_impl', 'feign_client', 
        'application_service', 'domain_service', 'request_dto', 
        'response_dto', 'entity', 'mapper', 'mapper_xml'
    ]
    
    missing_layers = [layer for layer in expected_layers if layer not in layer_paths]
    
    if missing_layers:
        logger.error(f"❌ 缺少DDD架构层: {missing_layers}")
        return False
    else:
        logger.info("✅ DDD架构分层配置完整")
        
    # 验证XML路径
    xml_path = layer_paths.get('mapper_xml', '')
    if 'src/main/resources/mapper' in xml_path or xml_path == 'resources/mapper':
        logger.info("✅ Mapper XML路径配置正确")
    else:
        logger.error(f"❌ Mapper XML路径错误: {xml_path}")
        return False
        
    return True

def test_code_generation_completeness():
    """测试代码生成完整性检查"""
    logger.info("🧪 测试代码生成完整性检查...")
    
    agent = IntelligentCodingAgent()
    
    # 模拟生成的代码
    generated_code = {
        'controller': '@RestController public class TestController {}',
        'application_service': '@Service public class TestApplicationService {}',
        'domain_service': '@Service public class TestDomainService {}',
        'mapper': '@Mapper public interface TestMapper {}',
        'mapper_xml': '<?xml version="1.0" encoding="UTF-8"?>',
        'request_dto': 'public class TestRequest {}',
        'response_dto': 'public class TestResponse {}'
    }
    
    project_context = {
        'current_api_path': '/api/test/listData',
        'project_info': {'is_mybatis_plus': True}
    }
    
    # 测试完整性检查
    is_complete, status = agent._is_react_generation_complete_with_details(generated_code, project_context)
    
    if is_complete:
        logger.info(f"✅ 代码生成完整性检查通过: {status['message']}")
        return True
    else:
        logger.error(f"❌ 代码生成不完整: {status['message']}")
        return False

def test_backup_file_cleanup():
    """测试备份文件清理功能"""
    logger.info("🧪 测试备份文件清理功能...")
    
    # 创建临时测试目录
    test_dir = Path("test_cleanup_dir")
    test_dir.mkdir(exist_ok=True)
    
    # 创建一些模拟的.backup文件
    backup_files = [
        test_dir / "TestController.java.backup",
        test_dir / "subdir" / "TestService.java.backup"
    ]
    
    for backup_file in backup_files:
        backup_file.parent.mkdir(exist_ok=True)
        backup_file.write_text("// backup content")
    
    # 测试清理功能
    interface_adder = InterfaceAdder()
    cleaned_count = interface_adder.cleanup_backup_files(str(test_dir))
    
    # 验证清理结果
    remaining_backup_files = list(test_dir.rglob("*.backup"))
    
    if len(remaining_backup_files) == 0 and cleaned_count == len(backup_files):
        logger.info(f"✅ 备份文件清理成功，清理了 {cleaned_count} 个文件")
        success = True
    else:
        logger.error(f"❌ 备份文件清理失败，还有 {len(remaining_backup_files)} 个文件")
        success = False
    
    # 清理测试目录
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return success

def test_component_matching():
    """测试组件匹配功能"""
    logger.info("🧪 测试组件匹配功能...")
    
    agent = IntelligentCodingAgent()
    
    # 测试数据
    test_cases = [
        {
            'required_component': 'controller',
            'code_type': 'rest_controller',
            'code_content': '@RestController public class TestController {}',
            'should_match': True
        },
        {
            'required_component': 'mapper_xml',
            'code_type': 'sql_mapper',
            'code_content': '<?xml version="1.0" encoding="UTF-8"?>',
            'should_match': True
        },
        {
            'required_component': 'feign_client',
            'code_type': 'external_client',
            'code_content': '@FeignClient public interface TestFeignClient {}',
            'should_match': True
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = agent._is_component_match(
            test_case['required_component'],
            test_case['code_type'],
            test_case['code_content']
        )
        
        if result == test_case['should_match']:
            logger.info(f"✅ 组件匹配测试通过: {test_case['required_component']}")
        else:
            logger.error(f"❌ 组件匹配测试失败: {test_case['required_component']}")
            all_passed = False
    
    return all_passed

def main():
    """主测试函数"""
    logger.info("🚀 开始代码生成修复验证测试...")
    
    tests = [
        ("DDD架构路径映射", test_ddd_architecture_paths),
        ("代码生成完整性检查", test_code_generation_completeness),
        ("备份文件清理功能", test_backup_file_cleanup),
        ("组件匹配功能", test_component_matching),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行测试: {test_name}")
        try:
            if test_func():
                passed_tests += 1
                logger.info(f"✅ {test_name} - 通过")
            else:
                logger.error(f"❌ {test_name} - 失败")
        except Exception as e:
            logger.error(f"❌ {test_name} - 异常: {e}")
    
    logger.info(f"\n📊 测试结果: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有测试通过！代码生成修复验证成功")
        return True
    else:
        logger.warning("⚠️ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 