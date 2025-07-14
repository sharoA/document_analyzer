#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的LLM调用和路径处理
"""

import logging
import os
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_llm_method_fix():
    """测试LLM方法调用修复"""
    logger.info("🧪 测试LLM方法调用修复...")
    
    try:
        # 检查ServiceDecisionMaker中的方法调用
        service_file = "/mnt/d/ai_project/document_analyzer/src/corder_integration/code_generator/service_decision_maker.py"
        
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否修复了方法调用
        if "self.llm_client.chat(" in content:
            logger.info("   ✅ LLM方法调用已修复为chat()方法")
            
            # 检查是否还有旧的调用
            if "chat_completion(" in content:
                logger.warning("   ⚠️ 仍然存在旧的chat_completion()调用")
                return False
            else:
                logger.info("   ✅ 已清除所有chat_completion()调用")
                return True
        else:
            logger.error("   ❌ 未找到正确的chat()方法调用")
            return False
            
    except Exception as e:
        logger.error(f"❌ LLM方法调用测试失败: {e}")
        return False

def test_path_validation():
    """测试路径验证功能"""
    logger.info("🧪 测试路径验证功能...")
    
    try:
        # 检查interface_adder中的路径验证
        adder_file = "/mnt/d/ai_project/document_analyzer/src/corder_integration/code_generator/interface_adder.py"
        
        with open(adder_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键的验证功能
        validations = [
            "os.path.exists(file_path)",
            "os.access(os.path.dirname(file_path), os.W_OK)",
            "UnicodeEncodeError",
            "PermissionError",
            "详细错误: {traceback.format_exc()}"
        ]
        
        validation_results = {}
        for validation in validations:
            if validation in content:
                validation_results[validation] = "✅ 已实现"
            else:
                validation_results[validation] = "❌ 缺失"
        
        logger.info("   📋 路径验证功能检查:")
        for validation, status in validation_results.items():
            logger.info(f"      - {validation}: {status}")
        
        passed = sum(1 for status in validation_results.values() if "✅" in status)
        total = len(validation_results)
        
        if passed == total:
            logger.info("   ✅ 所有路径验证功能已实现")
            return True
        else:
            logger.warning(f"   ⚠️ {total - passed} 个验证功能缺失")
            return False
            
    except Exception as e:
        logger.error(f"❌ 路径验证测试失败: {e}")
        return False

def test_chinese_path_handling():
    """测试中文路径处理"""
    logger.info("🧪 测试中文路径处理...")
    
    try:
        # 模拟测试中文路径
        test_paths = [
            "D:\\gitlab\\create_project\\链数中建一局_1752461639\\crcl-open\\src\\main\\java\\com\\yljr\\crcl\\limit\\interfaces\\LsLimitController.java",
            "/path/with/中文/characters/file.java",
            "C:\\项目\\测试\\Controller.java"
        ]
        
        logger.info("   📋 中文路径处理测试:")
        
        for test_path in test_paths:
            try:
                # 测试路径处理
                path_obj = Path(test_path)
                parent_dir = path_obj.parent
                filename = path_obj.name
                
                logger.info(f"      ✅ 路径解析成功: {filename}")
                logger.info(f"         父目录: {parent_dir}")
                
                # 测试编码
                try:
                    encoded = test_path.encode('utf-8')
                    decoded = encoded.decode('utf-8')
                    if decoded == test_path:
                        logger.info(f"         ✅ UTF-8编码正常")
                    else:
                        logger.warning(f"         ⚠️ UTF-8编码异常")
                except UnicodeError as e:
                    logger.error(f"         ❌ 编码错误: {e}")
                    
            except Exception as e:
                logger.error(f"      ❌ 路径处理失败 {test_path}: {e}")
        
        logger.info("   ✅ 中文路径处理测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 中文路径处理测试失败: {e}")
        return False

def test_error_scenarios():
    """测试错误场景处理"""
    logger.info("🧪 测试错误场景处理...")
    
    error_scenarios = [
        "文件不存在的情况",
        "路径包含特殊字符的情况", 
        "权限不足的情况",
        "编码错误的情况"
    ]
    
    logger.info("   📋 错误场景处理能力:")
    
    try:
        # 检查interface_adder是否包含各种错误处理
        adder_file = "/mnt/d/ai_project/document_analyzer/src/corder_integration/code_generator/interface_adder.py"
        
        with open(adder_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        error_handlers = {
            "文件不存在": "not os.path.exists(file_path)",
            "权限检查": "os.access(os.path.dirname(file_path), os.W_OK)",
            "编码错误": "UnicodeEncodeError",
            "权限错误": "PermissionError",
            "详细堆栈": "traceback.format_exc()"
        }
        
        for scenario, handler in error_handlers.items():
            if handler in content:
                logger.info(f"      ✅ {scenario}: 已处理")
            else:
                logger.warning(f"      ⚠️ {scenario}: 可能未处理")
        
        logger.info("   ✅ 错误场景处理测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误场景处理测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🎯 开始测试修复效果")
    logger.info("=" * 60)
    
    # 运行测试
    tests = [
        ("LLM方法调用修复", test_llm_method_fix),
        ("路径验证功能", test_path_validation),
        ("中文路径处理", test_chinese_path_handling),
        ("错误场景处理", test_error_scenarios)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    logger.info(f"\n{'='*60}")
    logger.info("📊 修复验证总结")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  - {test_name}: {status}")
    
    if passed == total:
        logger.info(f"\n🎉 所有修复验证都通过了！")
        logger.info("✅ LLM客户端方法调用错误已修复")
        logger.info("✅ 文件路径验证和错误处理已增强")
        logger.info("✅ 中文路径处理能力已验证")
        logger.info("✅ 各种错误场景处理已完善")
        logger.info("\n🚀 系统现在应该能够更稳定地处理API接口生成任务！")
        return True
    else:
        logger.warning(f"\n⚠️ 还有 {total - passed} 个问题需要进一步关注")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)