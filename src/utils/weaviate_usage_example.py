#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weaviate 使用示例
展示如何在项目中使用配置好的 Weaviate 功能
"""

import logging
from datetime import datetime
from weaviate_helper import (
    get_weaviate_client, 
    create_default_collection, 
    WeaviateManager,
    get_weaviate_config_dict,
    test_weaviate_connection
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 1. 测试连接
    if not test_weaviate_connection():
        print("❌ Weaviate 连接失败")
        return
    
    # 2. 获取配置
    config = get_weaviate_config_dict()
    print(f"📋 Weaviate 配置: {config}")
    
    # 3. 使用上下文管理器
    with WeaviateManager() as client:
        print(f"✅ 连接成功，Weaviate 版本: {client.get_meta()['version']}")
        
        # 创建默认集合
        create_default_collection(client)
        
        # 获取集合
        collection = client.collections.get("AnalyDesignDocuments")
        
        # 插入示例文档
        doc_uuid = collection.data.insert(
            properties={
                "title": "示例文档",
                "content": "这是一个示例文档的内容，用于演示 Weaviate 的使用。",
                "file_type": "txt",
                "file_path": "/example/document.txt",
                "created_at": datetime.now(),
                "file_size": 1024,
                "tags": ["示例", "文档", "测试"]
            },
            vector=[0.1] * 768  # 示例向量
        )
        
        print(f"📄 插入文档成功，UUID: {doc_uuid}")
        
        # 查询文档
        result = collection.query.fetch_objects(limit=5)
        print(f"📚 查询到 {len(result.objects)} 个文档:")
        for obj in result.objects:
            print(f"  - {obj.properties['title']} ({obj.properties['file_type']})")

def example_search_documents():
    """文档搜索示例"""
    print("\n=== 文档搜索示例 ===")
    
    with WeaviateManager() as client:
        collection = client.collections.get("AnalyDesignDocuments")
        
        # 基于内容的文本搜索
        search_result = collection.query.bm25(
            query="示例文档",
            limit=3
        )
        
        print(f"🔍 搜索结果 ({len(search_result.objects)} 个):")
        for obj in search_result.objects:
            print(f"  - {obj.properties['title']}: {obj.properties['content'][:50]}...")

def example_vector_search():
    """向量搜索示例"""
    print("\n=== 向量搜索示例 ===")
    
    with WeaviateManager() as client:
        collection = client.collections.get("AnalyDesignDocuments")
        
        # 向量相似性搜索
        query_vector = [0.1] * 768  # 查询向量
        
        vector_result = collection.query.near_vector(
            near_vector=query_vector,
            limit=3
        )
        
        print(f"🎯 向量搜索结果 ({len(vector_result.objects)} 个):")
        for obj in vector_result.objects:
            print(f"  - {obj.properties['title']} (相似度: {obj.metadata.distance:.4f})")

def example_filter_documents():
    """文档过滤示例"""
    print("\n=== 文档过滤示例 ===")
    
    with WeaviateManager() as client:
        collection = client.collections.get("AnalyDesignDocuments")
        
        # 按文件类型过滤
        from weaviate.classes.query import Filter
        
        filter_result = collection.query.fetch_objects(
            where=Filter.by_property("file_type").equal("txt"),
            limit=5
        )
        
        print(f"📁 TXT 文件 ({len(filter_result.objects)} 个):")
        for obj in filter_result.objects:
            print(f"  - {obj.properties['title']} ({obj.properties['file_size']} bytes)")

def example_cleanup():
    """清理示例数据"""
    print("\n=== 清理示例数据 ===")
    
    with WeaviateManager() as client:
        collection = client.collections.get("AnalyDesignDocuments")
        
        # 删除所有示例文档
        result = collection.query.fetch_objects(
            where=Filter.by_property("title").like("示例*"),
            limit=100
        )
        
        for obj in result.objects:
            collection.data.delete_by_id(obj.uuid)
            print(f"🗑️  删除文档: {obj.properties['title']}")

if __name__ == "__main__":
    try:
        # 运行所有示例
        example_basic_usage()
        example_search_documents()
        example_vector_search()
        example_filter_documents()
        
        # 询问是否清理数据
        cleanup = input("\n是否清理示例数据? (y/N): ").lower().strip()
        if cleanup == 'y':
            example_cleanup()
            
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        print(f"❌ 示例运行失败: {e}")
    
    print("\n✅ 示例运行完成！") 