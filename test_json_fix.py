#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON修复功能
"""

import sys
sys.path.append('.')

from src.corder_integration.code_generator.function_calling_code_generator import FunctionCallingCodeGenerator
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建测试实例
class MockLLMClient:
    pass

generator = FunctionCallingCodeGenerator(MockLLMClient(), ".")

# 测试实际的错误JSON（基于日志）
problematic_json = '{"file_path":"src/main/java/com/yljr/crcl/limit/domain/mapper/LsLimitMapper.java","old_text":"@Param(\\"limitSource\\") String limitSource","new_text":"@Param(\\"limitSource\\") String limitSource, new method"}'

print("🔍 测试JSON修复功能")
print(f"原始JSON: {problematic_json}")

# 尝试直接解析
try:
    result = json.loads(problematic_json)
    print("✅ 原始JSON解析成功")
except json.JSONDecodeError as e:
    print(f"❌ 原始JSON解析失败: {e}")
    
    # 测试修复功能
    print("\n🔧 尝试修复JSON...")
    fixed_result = generator._try_fix_json_string(problematic_json)
    
    if fixed_result:
        print("✅ JSON修复成功\!")
        print("修复后的数据:", fixed_result)
    else:
        print("❌ JSON修复失败")
EOF < /dev/null