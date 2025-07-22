#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的JSON修复测试 - 测试真实的错误场景
"""

import json
import logging
import re
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedJSONFixer:
    """改进的JSON修复器"""
    
    def _fix_control_characters(self, json_str: str) -> str:
        """修复控制字符"""
        logger.info("🔧 修复控制字符")
        
        # 处理换行问题 - 首先保护已经正确转义的
        json_str = json_str.replace('\\n', '__PROTECTED_NEWLINE__')
        json_str = json_str.replace('\\r', '__PROTECTED_CARRIAGE__')
        json_str = json_str.replace('\\t', '__PROTECTED_TAB__')
        
        # 转义真实的控制字符
        json_str = json_str.replace('\n', '\\n')
        json_str = json_str.replace('\r', '\\r')
        json_str = json_str.replace('\t', '\\t')
        
        # 恢复保护的字符
        json_str = json_str.replace('__PROTECTED_NEWLINE__', '\\n')
        json_str = json_str.replace('__PROTECTED_CARRIAGE__', '\\r')
        json_str = json_str.replace('__PROTECTED_TAB__', '\\t')
        
        # 移除其他控制字符
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        return json_str
    
    def _fix_unescaped_quotes(self, json_str: str) -> str:
        """修复未转义的引号"""
        logger.info("🔧 修复未转义的引号")
        
        # 在字符串值中查找并转义未转义的引号
        # 这个实现简化了，实际场景可能更复杂
        
        # 首先保护已经转义的引号
        json_str = json_str.replace('\\"', '__PROTECTED_QUOTE__')
        
        # 查找content字段中的问题
        content_pattern = r'"content"\s*:\s*"([^"]*(?:"[^"]*)*)"'
        
        def fix_content_quotes(match):
            content = match.group(1)
            # 转义内部的引号
            content = content.replace('"', '\\"')
            return f'"content": "{content}"'
        
        json_str = re.sub(content_pattern, fix_content_quotes, json_str)
        
        # 恢复保护的引号
        json_str = json_str.replace('__PROTECTED_QUOTE__', '\\"')
        
        return json_str
    
    def _fix_large_content_json(self, json_str: str) -> str:
        """修复大内容JSON"""
        if len(json_str) < 200 or '"content"' not in json_str:
            return json_str
        
        logger.info("🔧 检测到大内容JSON，应用特殊修复策略")
        
        try:
            # 提取file_path
            file_path_match = re.search(r'"file_path"\s*:\s*"([^"]+)"', json_str)
            if not file_path_match:
                return json_str
            
            file_path = file_path_match.group(1)
            
            # 查找content字段开始位置
            content_match = re.search(r'"content"\s*:\s*"', json_str)
            if not content_match:
                return json_str
            
            content_start = content_match.end()
            
            # 提取content内容
            remaining = json_str[content_start:]
            
            # 尝试智能查找结束位置
            # 方法1：从后往前查找"}
            if remaining.endswith('"}'):
                content_value = remaining[:-2]
            elif remaining.endswith('"'):
                content_value = remaining[:-1]
            else:
                # 查找最后可能的结束位置
                last_quote = remaining.rfind('"')
                if last_quote > 0:
                    content_value = remaining[:last_quote]
                else:
                    content_value = remaining
            
            # 清理内容
            content_value = self._clean_content_for_json(content_value)
            
            # 重构JSON
            result = f'{{"file_path": "{file_path}", "content": "{content_value}"}}'
            logger.info(f"🔧 重构JSON成功，长度: {len(result)}")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ 大内容JSON修复失败: {e}")
        
        return json_str
    
    def _clean_content_for_json(self, content: str) -> str:
        """清理内容使其适合JSON格式"""
        if not content:
            return ""
        
        # 转义特殊字符
        # 首先保护已经转义的
        content = content.replace('\\\\', '__PROTECTED_BACKSLASH__')
        content = content.replace('\\"', '__PROTECTED_QUOTE__')
        
        # 转义反斜杠
        content = content.replace('\\', '\\\\')
        
        # 转义引号
        content = content.replace('"', '\\"')
        
        # 转义控制字符
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        
        # 恢复保护的字符
        content = content.replace('__PROTECTED_BACKSLASH__', '\\\\')
        content = content.replace('__PROTECTED_QUOTE__', '\\"')
        
        # 移除其他控制字符
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        return content
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """修复被截断的JSON"""
        if json_str.endswith('}'):
            return json_str
            
        logger.info("🔧 检测到可能被截断的JSON，尝试补全")
        
        # 计算括号平衡
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        # 计算引号平衡
        quote_count = json_str.count('"')
        escaped_quote_count = json_str.count('\\"')
        actual_quote_count = quote_count - escaped_quote_count
        
        # 先关闭未完成的字符串
        if actual_quote_count % 2 == 1:
            json_str += '"'
            logger.info("🔧 添加了闭合引号")
        
        # 然后补充缺失的大括号
        if open_braces > close_braces:
            missing_braces = open_braces - close_braces
            json_str += '}' * missing_braces
            logger.info(f"🔧 补充了 {missing_braces} 个闭合括号")
        
        return json_str
    
    def try_fix_json_string(self, json_str: str) -> Optional[Dict[str, Any]]:
        """尝试修复JSON字符串"""
        if not json_str or not isinstance(json_str, str):
            logger.warning("⚠️ JSON字符串为空或不是字符串类型")
            return None
        
        original_str = json_str.strip()
        logger.info(f"🔧 尝试修复JSON字符串: {len(original_str)} 字符")
        
        # 修复策略列表
        fix_strategies = [
            self._fix_control_characters,
            self._fix_unescaped_quotes,
            self._fix_large_content_json,
            self._fix_truncated_json
        ]
        
        current_str = original_str
        
        for strategy in fix_strategies:
            try:
                fixed_str = strategy(current_str)
                if fixed_str != current_str:
                    logger.info(f"🔧 应用修复策略: {strategy.__name__}")
                    current_str = fixed_str
                
                # 每次修复后都尝试解析
                try:
                    result = json.loads(current_str)
                    logger.info(f"✅ JSON修复成功，使用策略: {strategy.__name__}")
                    return result
                except json.JSONDecodeError:
                    continue
                    
            except Exception as e:
                logger.warning(f"策略 {strategy.__name__} 出现异常: {e}")
                continue
        
        logger.error("❌ 所有JSON修复策略都失败了")
        logger.error(f"最终字符串预览: {current_str[:200]}...")
        return None

def test_improved_json_repair():
    """测试改进的JSON修复功能"""
    
    fixer = ImprovedJSONFixer()
    
    # 测试用例1：包含真实换行符的代码内容（模拟第2871列错误）
    java_code_with_newlines = """package com.yljr.crcl.limit.domain.mapper;

import org.apache.ibatis.annotations.Mapper;
/**
 * LsLimit数据访问层
 */
@Mapper
public interface LsLimitMapper {
    List<Map<String, Object>> listUnitLimitByCompanyId(@Param("companyId") String companyId);
}"""
    
    test_case_1 = f'{{"file_path":"LsLimitMapper.java","content":"{java_code_with_newlines}"}}'
    
    # 测试用例2：包含未转义引号的内容
    test_case_2 = '''{"file_path":"Quote.java","content":"public class Test {
    String msg = "Hello "World"";
}"}'''
    
    # 测试用例3：截断的JSON
    test_case_3 = '''{"file_path":"Test.java","content":"public class Test {}"}'''  # 缺少最后的}
    
    # 测试用例4：复杂的真实场景
    complex_code = """package com.example;

public class Complex {
    public void method() {
        String sql = "SELECT * FROM table WHERE name = 'test'";
        System.out.println("Debug: " + sql);
    }
}"""
    test_case_4 = f'{{"file_path":"Complex.java","content":"{complex_code}"'  # 缺少闭合
    
    test_cases = [
        ("包含真实换行符的代码", test_case_1),
        ("包含未转义引号", test_case_2),
        ("截断的JSON", test_case_3),
        ("复杂真实场景", test_case_4)
    ]
    
    print("🧪 开始测试改进的JSON修复功能...\n")
    
    success_count = 0
    
    for i, (description, test_json) in enumerate(test_cases, 1):
        print(f"📋 测试用例 {i}: {description}")
        print(f"JSON长度: {len(test_json)} 字符")
        print(f"JSON预览: {test_json[:100]}...")
        
        # 验证确实有错误
        try:
            json.loads(test_json)
            print("⚠️ 原始JSON居然能解析，可能不是有效的测试用例")
        except json.JSONDecodeError as e:
            print(f"✅ 确认JSON有错误: {e}")
            print(f"错误位置: 第{e.lineno}行，第{e.colno}列")
        
        # 使用修复功能
        fixed_result = fixer.try_fix_json_string(test_json)
        if fixed_result:
            print("✅ 修复成功!")
            print(f"文件路径: {fixed_result.get('file_path', 'N/A')}")
            content = fixed_result.get('content', '')
            print(f"内容长度: {len(content)} 字符")
            print(f"内容预览: {content[:100]}...")
            
            # 验证修复后的JSON确实可以解析
            try:
                json.dumps(fixed_result)
                print("✅ 修复后的结果可以正常序列化")
                success_count += 1
            except Exception as e:
                print(f"⚠️ 修复后的结果序列化失败: {e}")
        else:
            print("❌ 修复失败")
        
        print("-" * 80)
        print()
    
    print(f"🎯 测试总结: {success_count}/{len(test_cases)} 个测试用例修复成功")
    
    if success_count == len(test_cases):
        print("🎉 所有测试用例都修复成功！JSON修复功能工作正常。")
    elif success_count > 0:
        print(f"✅ 修复了 {success_count} 个测试用例，功能基本正常。")
    else:
        print("❌ 所有测试用例都修复失败，需要进一步优化修复策略。")

if __name__ == "__main__":
    test_improved_json_repair()