#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文 Weaviate 演示脚本
用于演示在 Weaviate 数据库中进行中文输入和输出
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.weaviate_helper import (
    get_weaviate_client,
    create_default_collection,
    WeaviateManager,
    get_weaviate_config_dict,
    test_weaviate_connection
)


def main():
    """主函数，演示中文输入输出功能"""
    print("\n" + "="*50)
    print("\n🌏 中文 Weaviate 演示 🌏\n")
    print("="*50 + "\n")
    
    # 测试连接
    connection_ok = test_weaviate_connection()
    if not connection_ok:
        print("❌ Weaviate 连接失败，请检查服务是否运行")
        return
    
    print("✅ 成功连接到 Weaviate 服务器\n")
    
    # 获取配置
    config = get_weaviate_config_dict()
    collection_name = config.get('default_collection', {}).get('name', 'AnalyDesignDocuments')
    
    # 创建中文测试文档
    chinese_doc_title = f"中文测试文档-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    chinese_doc_content = "这是一个专门用于测试中文处理能力的文档。它包含了各种中文词汇，如：人工智能、机器学习、深度学习、自然语言处理、知识图谱、语义分析等技术概念。"
    
    print(f"📝 创建中文测试文档: {chinese_doc_title}")
    print(f"📄 文档内容: {chinese_doc_content[:50]}...\n")
    
    with WeaviateManager() as client:
        # 确保集合存在
        create_default_collection(client)
        collection = client.collections.get(collection_name)
        
        # 插入中文测试文档
        doc_uuid = collection.data.insert(
            properties={
                "title": chinese_doc_title,
                "content": chinese_doc_content,
                "file_type": "txt",
                "file_path": "/test/chinese_document.txt",
                "created_at": datetime.now(),
                "file_size": 1024,
                "tags": ["中文", "测试", "人工智能", "机器学习"]
            },
            vector=[0.1] * 768  # 测试向量
        )
        
        print(f"✅ 中文测试文档创建成功，UUID: {doc_uuid}\n")
        
        # 使用中文关键词进行搜索
        chinese_keywords = ["人工智能", "机器学习", "自然语言处理"]
        
        for keyword in chinese_keywords:
            print(f"\n🔍 使用中文关键词 '{keyword}' 搜索...")
            
            # 基于内容的文本搜索
            search_result = collection.query.bm25(
                query=keyword,
                limit=3
            )
            
            # 打印搜索结果
            if search_result and hasattr(search_result, 'objects') and len(search_result.objects) > 0:
                print(f"✅ 找到 {len(search_result.objects)} 个匹配结果:\n")
                
                for i, obj in enumerate(search_result.objects, 1):
                    print(f"  {i}. 文档标题: {obj.properties['title']}")
                    print(f"     文档类型: {obj.properties['file_type']}")
                    print(f"     文档内容: {obj.properties['content'][:50]}...")
                    
                    if 'tags' in obj.properties and obj.properties['tags']:
                        print(f"     文档标签: {', '.join(obj.properties['tags'])}")
                    print()
            else:
                print(f"❌ 未找到与 '{keyword}' 相关的文档\n")
        
        # 删除测试文档
        print(f"\n🗑️ 清理中文测试文档: {chinese_doc_title}")
        collection.data.delete_by_id(doc_uuid)
        print("✅ 中文测试文档已删除")
    
    print("\n" + "="*50)
    print("\n🏁 演示完成 🏁\n")
    print("="*50)


if __name__ == "__main__":
    main()