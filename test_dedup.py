#!/usr/bin/env python3
"""
测试去重功能的脚本
"""

import sys
import os
sys.path.append('src')

from analysis_services.content_analyzer import ContentAnalyzerService
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_similarity_detection():
    """测试相似性检测功能"""
    
    # 创建分析器实例
    analyzer = ContentAnalyzerService()
    
    # 测试您提到的两句相似的话
    text1 = "调整了【确权业务申请】接口中关于bizSerialNo的校验规则，允许相同业务编号的数据在核心企业内部系统修改后重新推送"
    text2 = "调整了【确权业务申请】接口中关于bizSerialNo的校验规则，允许相同业务编号的数据在核心企业内部系统修改后再次推送"
    
    print(f"文本1: {text1}")
    print(f"文本2: {text2}")
    print("=" * 80)
    
    # 测试相似度计算
    similarity = analyzer._calculate_text_similarity(text1, text2)
    print(f"计算得出的相似度: {similarity:.3f}")
    print("=" * 80)
    
    # 创建测试变更项
    change1 = {
        "changeType": "修改",
        "changeReason": "接口校验规则调整",
        "changeItems": [text1],
        "version": ["v1.0"]
    }
    
    change2 = {
        "changeType": "修改", 
        "changeReason": "接口校验优化",
        "changeItems": [text2],
        "version": ["v1.1"]
    }
    
    # 测试是否应该合并
    should_merge = analyzer._should_merge_changes(change1, change2)
    print(f"是否应该合并: {should_merge}")
    print("=" * 80)
    
    # 如果应该合并，测试合并效果
    if should_merge:
        merged = analyzer._merge_similar_change_details([change1, change2])
        print("合并结果:")
        print(f"  变更类型: {merged.get('changeType')}")
        print(f"  变更原因: {merged.get('changeReason')}")
        print(f"  变更点: {merged.get('changeItems')}")
        print(f"  版本: {merged.get('version')}")
        print(f"  合并数量: {merged.get('mergedChangesCount')}")
    else:
        print("两个变更项不会被合并")
    
    print("=" * 80)
    
    # 测试完整的去重流程
    test_changes = [change1, change2]
    deduplicated = analyzer._deduplicate_changes(test_changes)
    
    print(f"去重前数量: {len(test_changes)}")
    print(f"去重后数量: {len(deduplicated)}")
    
    for i, change in enumerate(deduplicated):
        print(f"去重后变更项{i+1}:")
        print(f"  类型: {change.get('changeType')}")
        print(f"  变更点: {change.get('changeItems')}")
        if 'mergedChangesCount' in change:
            print(f"  合并了 {change['mergedChangesCount']} 个变更项")

if __name__ == "__main__":
    asyncio.run(test_similarity_detection()) 