#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实的JSON修复场景
"""

import json
import logging
import re
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedJSONFixer:
    """增强的JSON修复器"""
    
    def _fix_control_characters(self, json_str: str) -> str:
        """修复控制字符 - 增强版"""
        logger.info("🔧 修复控制字符")
        
        # 先处理常见的换行问题
        json_str = json_str.replace('\n', '\\n')
        json_str = json_str.replace('\r', '\\r')
        json_str = json_str.replace('\t', '\\t')
        
        # 移除或转义其他控制字符
        import re
        # 移除ASCII控制字符（除了已处理的换行、回车、制表符）
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
        
        return json_str
    
    def _fix_large_content_json(self, json_str: str) -> str:
        """修复包含大量内容的JSON"""
        if len(json_str) < 500 or '"content"' not in json_str:
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
            
            # 提取content开始位置
            content_start = content_match.end()
            
            # 提取内容部分
            content_part = json_str[content_start:]
            
            # 智能查找结束位置
            # 方法1：查找最后的 "}
            last_quote_brace = content_part.rfind('"}')
            if last_quote_brace != -1:
                content_value = content_part[:last_quote_brace]
                # 清理内容
                content_value = self._clean_content_for_json(content_value)
                reconstructed = f'{{"file_path": "{file_path}", "content": "{content_value}"}}'
                logger.info(f"🔧 重构JSON成功，长度: {len(reconstructed)}")
                return reconstructed
            
            # 方法2：截断处理
            if len(content_part) > 2000:
                content_value = content_part[:1500]  # 截取前1500字符
                # 找到最后一个完整的词
                last_space = content_value.rfind(' ')
                if last_space > 1000:  # 确保不会截取太短
                    content_value = content_value[:last_space]
                
                content_value = self._clean_content_for_json(content_value)
                content_value += "\\n...[内容已截断]"
                reconstructed = f'{{"file_path": "{file_path}", "content": "{content_value}"}}'
                logger.info("🔧 应用截断策略修复JSON")
                return reconstructed
                
        except Exception as e:
            logger.warning(f"⚠️ 大内容JSON修复失败: {e}")
        
        return json_str
    
    def _clean_content_for_json(self, content: str) -> str:
        """清理内容使其适合JSON格式 - 增强版"""
        if not content:
            return ""
        
        # 1. 首先处理已存在的转义序列，避免重复转义
        # 临时替换已经正确转义的序列
        temp_markers = {
            '\\"': '__ESCAPED_QUOTE__',
            '\\\\': '__ESCAPED_BACKSLASH__',
            '\\n': '__ESCAPED_NEWLINE__',
            '\\r': '__ESCAPED_CARRIAGE__',
            '\\t': '__ESCAPED_TAB__'
        }
        
        for escaped, marker in temp_markers.items():
            content = content.replace(escaped, marker)
        
        # 2. 转义反斜杠（必须在其他转义之前）
        content = content.replace('\\', '\\\\')
        
        # 3. 转义引号
        content = content.replace('"', '\\"')
        
        # 4. 转义换行符和制表符
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        
        # 5. 恢复原本正确的转义序列
        for escaped, marker in temp_markers.items():
            content = content.replace(marker, escaped)
        
        # 6. 移除控制字符
        import re
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        return content
    
    def _fix_truncated_json(self, json_str: str) -> str:
        """修复被截断的JSON - 增强版"""
        if json_str.endswith('}'):
            return json_str
            
        logger.info("🔧 检测到可能被截断的JSON，尝试补全")
        
        # 计算括号平衡
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        
        # 计算引号平衡
        quote_count = json_str.count('"')
        
        # 先关闭未完成的字符串
        if quote_count % 2 == 1:
            json_str += '"'
            logger.info("🔧 添加了闭合引号")
        
        # 然后补充缺失的大括号
        if open_braces > close_braces:
            missing_braces = open_braces - close_braces
            json_str += '}' * missing_braces
            logger.info(f"🔧 补充了 {missing_braces} 个闭合括号")
        
        return json_str
    
    def _fix_unterminated_string(self, json_str: str) -> str:
        """修复未终止的字符串"""
        # 简单的引号平衡检查
        if json_str.count('"') % 2 != 0:
            if not json_str.endswith('"') and not json_str.endswith('"}'):
                json_str = json_str + '"}'
                logger.info("🔧 添加了闭合引号和括号")
        return json_str
    
    def try_fix_json_string(self, json_str: str) -> Optional[Dict[str, Any]]:
        """尝试修复JSON字符串 - 增强版"""
        if not json_str or not isinstance(json_str, str):
            logger.warning("⚠️ JSON字符串为空或不是字符串类型")
            return None
        
        original_str = json_str.strip()
        logger.info(f"🔧 尝试修复JSON字符串: {len(original_str)} 字符")
        
        # 修复策略列表 - 按优先级排序
        fix_strategies = [
            self._fix_control_characters,      # 🔥 优先处理控制字符
            self._fix_large_content_json,      # 处理大内容JSON
            self._fix_truncated_json,          # 处理截断的JSON
            self._fix_unterminated_string      # 处理未终止字符串
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
        
        # 最后尝试一次解析当前字符串
        try:
            result = json.loads(current_str)
            logger.info("✅ JSON修复成功，使用组合策略")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"❌ 最终解析失败: {e}")
            logger.error(f"最终字符串预览: {current_str[:200]}...")
        
        logger.error("❌ 所有JSON修复策略都失败了")
        return None

def test_real_errors():
    """测试真实的错误场景"""
    
    fixer = EnhancedJSONFixer()
    
    # 真实错误场景1：包含控制字符的大内容
    test_case_1 = '''{"file_path":"src/main/java/com/yljr/crcl/limit/domain/mapper/LsLimitMapper.java","content":"package com.yljr.crcl.limit.domain.mapper;

import org.apache.ibatis.annotations.Mapper;
/**
 * LsLimit数据访问层
 */
@Mapper
public interface LsLimitMapper {
    List<Map<String, Object>> listUnitLimitByCompanyId(@Param("companyId") String companyId);
}'''
    
    # 真实错误场景2：第2871列类型的长内容错误
    test_case_2_content = 'package com.example;\\n\\npublic class Test {\\n    public void method() {\\n        String msg = "Hello World";\\n    }\\n}'
    test_case_2 = f'{{"file_path":"Test.java","content":"{test_case_2_content}"'  # 故意缺少闭合
    
    test_cases = [
        ("包含换行的大内容JSON", test_case_1),
        ("长内容截断错误", test_case_2)
    ]
    
    print("🧪 开始测试真实JSON错误修复...\n")
    
    for i, (description, test_json) in enumerate(test_cases, 1):
        print(f"📋 测试用例 {i}: {description}")
        print(f"JSON长度: {len(test_json)} 字符")
        
        # 验证确实有错误
        try:
            json.loads(test_json)
            print("⚠️ 原始JSON居然能解析，测试用例可能有问题")
        except json.JSONDecodeError as e:
            print(f"✅ 确认JSON有错误: {e}")
            print(f"错误位置: 第{e.lineno}行，第{e.colno}列")
        
        # 使用增强修复功能
        fixed_result = fixer.try_fix_json_string(test_json)
        if fixed_result:
            print("✅ 修复成功!")
            print(f"文件路径: {fixed_result.get('file_path', 'N/A')}")
            content = fixed_result.get('content', '')
            print(f"内容长度: {len(content)} 字符")
            print(f"内容预览: {content[:100]}...")
        else:
            print("❌ 修复失败")
        
        print("-" * 80)
        print()

if __name__ == "__main__":
    test_real_errors()