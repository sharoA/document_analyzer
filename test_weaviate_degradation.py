#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Weaviate降级模式的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.weaviate_helper import get_weaviate_client
from analysis_services.content_analyzer import ContentAnalyzerService

def test_weaviate_degradation():
    """测试Weaviate降级模式"""
    
    print('=== 测试Weaviate连接状态 ===')
    weaviate_client = get_weaviate_client()
    if weaviate_client:
        print('✅ Weaviate连接成功')
        weaviate_client.close()
    else:
        print('⚠️ Weaviate连接失败，系统将使用降级模式')

    print('\n=== 测试ContentAnalyzerService初始化 ===')
    try:
        analyzer = ContentAnalyzerService()
        print('✅ ContentAnalyzerService初始化成功')
        print(f'   - 向量数据库可用: {analyzer.vector_enabled}')
        print(f'   - 向量化模型可用: {analyzer.embedding_enabled}')
        print(f'   - Weaviate客户端: {"可用" if analyzer.weaviate_client else "不可用"}')
        print(f'   - 向量化模型: {"可用" if analyzer.embedding_model else "不可用"}')
        
        # 测试文档预处理功能
        print('\n=== 测试文档预处理功能（降级模式）===')
        test_content = """
# 测试文档
这是一个测试文档内容。

## 功能需求
- 新增用户管理功能
- 修改权限控制逻辑

## 技术要求
- 使用Spring Boot框架
- 支持MySQL数据库
        """
        
        import asyncio
        async def test_preprocessing():
            try:
                result = await analyzer._preprocess_document(test_content)
                print(f'✅ 文档预处理成功，生成 {len(result)} 个内容块')
                for i, chunk in enumerate(result):
                    has_embedding = chunk.get('embedding') is not None
                    print(f'   块{i+1}: {chunk["section"][:20]}... (向量: {"有" if has_embedding else "无"})')
                return True
            except Exception as e:
                print(f'❌ 文档预处理失败: {e}')
                return False
        
        success = asyncio.run(test_preprocessing())
        if success:
            print('✅ 降级模式测试成功 - 系统可以在没有Weaviate的情况下正常工作')
        else:
            print('❌ 降级模式测试失败')
            
    except Exception as e:
        print(f'❌ ContentAnalyzerService初始化失败: {e}')
        import traceback
        traceback.print_exc()
        
    print('\n=== 测试完成 ===')

if __name__ == '__main__':
    test_weaviate_degradation()