#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版中文 Weaviate 测试脚本
专注于演示在 Weaviate 数据库中进行中文输入和输出，输出更加简洁清晰
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.weaviate_helper import (
    WeaviateManager,
    create_default_collection,
    get_weaviate_config_dict,
    test_weaviate_connection
)


def main():
    """主函数，简化版中文输入输出测试"""
    print("\n" + "="*60)
    print("\n🌏 简化版中文 Weaviate 测试 🌏\n")
    print("="*60 + "\n")
    
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
    chinese_doc_title = f"中文测试-{datetime.now().strftime('%H%M%S')}"
    chinese_doc_content = "这是一个简单的中文测试文档，包含关键词：人工智能、机器学习、自然语言处理。"
    
    print(f"📝 创建中文测试文档: {chinese_doc_title}")
    print(f"📄 文档内容: {chinese_doc_content}\n")
    
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
                "file_path": "/test/simple_chinese_test.txt",
                "created_at": datetime.now(),
                "file_size": 512,
                "tags": ["中文", "测试", "简化"]
            },
            vector=[0.1] * 768  # 测试向量
        )
        
        print(f"✅ 中文测试文档创建成功，UUID: {doc_uuid}\n")
        
        # 使用中文关键词进行搜索
        chinese_keyword = "人工智能"
        
        print(f"\n🔍 使用中文关键词 '{chinese_keyword}' 搜索...")
        
        # 基于内容的文本搜索
        search_result = collection.query.bm25(
            query=chinese_keyword,
            limit=3
        )
        
        # 打印搜索结果
        if search_result and hasattr(search_result, 'objects') and len(search_result.objects) > 0:
            print(f"✅ 找到 {len(search_result.objects)} 个匹配结果:\n")
            
            for i, obj in enumerate(search_result.objects, 1):
                print(f"  {i}. 文档标题: {obj.properties['title']}")
                print(f"     文档内容: {obj.properties['content']}")
                print(f"     文档标签: {', '.join(obj.properties['tags'])}\n")
        else:
            print(f"❌ 未找到与 '{chinese_keyword}' 相关的文档\n")
        
        # 通过标题查询并打印文档
        print(f"\n📋 通过标题查询文档: {chinese_doc_title}")
        
        # 使用BM25搜索方法查询文档
        results = collection.query.bm25(
            query=chinese_doc_title,
            limit=1
        )
        
        if results and hasattr(results, 'objects') and len(results.objects) > 0:
            retrieved_doc = results.objects[0]
            print(f"✅ 成功获取文档:\n")
            print(f"  标题: {retrieved_doc.properties['title']}")
            print(f"  内容: {retrieved_doc.properties['content']}")
            print(f"  标签: {', '.join(retrieved_doc.properties['tags'])}\n")
        else:
            print("❌ 无法获取文档\n")
        
        # 删除测试文档
        print(f"\n🗑️ 清理中文测试文档: {chinese_doc_title}")
        collection.data.delete_by_id(doc_uuid)
        print("✅ 中文测试文档已删除")
    
    print("\n" + "="*60)
    print("\n🏁 测试完成 🏁\n")
    print("="*60)


if __name__ == "__main__":
    main()