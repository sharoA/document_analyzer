#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weaviate查询测试脚本
使用SentenceTransformer进行文本向量化
"""

import weaviate
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from .weaviate_helper import get_weaviate_client

# 配置参数
WEAVIATE_URL = "http://localhost:8080"  # 修改为你的Weaviate实例URL
CLASS_NAME = "Document"  # 修改为你的类名
MODEL_NAME = 'all-MiniLM-L6-v2'

def initialize_client():
    """初始化Weaviate客户端"""
    try:
        get_weaviate_client()
        print(f"✓ 成功连接到Weaviate: {WEAVIATE_URL}")
        
    except Exception as e:
        print(f"✗ 连接Weaviate失败: {e}")
        return None

def initialize_sentence_transformer():
    """初始化SentenceTransformer模型"""
    try:
        model = SentenceTransformer(MODEL_NAME)
        print(f"✓ 成功加载SentenceTransformer模型: {MODEL_NAME}")
        return model
    except Exception as e:
        print(f"✗ 加载SentenceTransformer模型失败: {e}")
        return None

def create_schema_if_not_exists(client):
    """创建schema（如果不存在）"""
    try:
        # 检查类是否已存在
        schema = client.schema.get()
        class_exists = any(cls['class'] == CLASS_NAME for cls in schema.get('classes', []))
        
        if not class_exists:
            class_definition = {
                "class": CLASS_NAME,
                "description": "测试文档类",
                "vectorizer": "none",  # 我们手动提供向量
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "文档内容"
                    },
                    {
                        "name": "title",
                        "dataType": ["string"],
                        "description": "文档标题"
                    }
                ]
            }
            
            client.schema.create_class(class_definition)
            print(f"✓ 成功创建类: {CLASS_NAME}")
        else:
            print(f"✓ 类 {CLASS_NAME} 已存在")
            
    except Exception as e:
        print(f"✗ 创建schema失败: {e}")

def add_test_documents(client, model):
    """添加测试文档"""
    test_documents = [
        {
            "title": "人工智能简介",
            "content": "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
        },
        {
            "title": "机器学习基础",
            "content": "机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习和改进。"
        },
        {
            "title": "深度学习概述",
            "content": "深度学习是机器学习的一个分支，使用多层神经网络来模拟和理解复杂的模式。"
        },
        {
            "title": "自然语言处理",
            "content": "自然语言处理是人工智能的一个领域，专注于计算机与人类语言之间的交互。"
        }
    ]
    
    try:
        # 检查是否已有数据
        result = client.query.get(CLASS_NAME).with_limit(1).do()
        if result['data']['Get'][CLASS_NAME]:
            print("✓ 测试数据已存在，跳过添加")
            return
        
        print("正在添加测试文档...")
        
        with client.batch as batch:
            for doc in test_documents:
                # 向量化文档内容
                vector = model.encode(doc["content"])
                
                # 添加到批处理
                batch.add_data_object(
                    data_object=doc,
                    class_name=CLASS_NAME,
                    vector=vector.tolist()
                )
        
        print(f"✓ 成功添加 {len(test_documents)} 个测试文档")
        
    except Exception as e:
        print(f"✗ 添加测试文档失败: {e}")

def vector_search(client, model, query_text, limit=3):
    """执行向量搜索"""
    try:
        print(f"\n--- 向量搜索 ---")
        print(f"查询文本: {query_text}")
        
        # 向量化查询文本
        query_vector = model.encode(query_text).tolist()
        
        # 执行向量搜索
        result = (
            client.query
            .get(CLASS_NAME, ["title", "content"])
            .with_near_vector({"vector": query_vector})
            .with_limit(limit)
            .with_additional(["distance"])
            .do()
        )
        
        documents = result['data']['Get'][CLASS_NAME]
        
        if documents:
            print(f"找到 {len(documents)} 个相关文档:")
            for i, doc in enumerate(documents, 1):
                distance = doc.get('_additional', {}).get('distance', 'N/A')
                print(f"{i}. 标题: {doc['title']}")
                print(f"   距离: {distance}")
                print(f"   内容: {doc['content'][:100]}...")
                print()
        else:
            print("未找到相关文档")
            
    except Exception as e:
        print(f"✗ 向量搜索失败: {e}")

def hybrid_search(client, model, query_text, limit=3):
    """执行混合搜索（向量+关键词）"""
    try:
        print(f"\n--- 混合搜索 ---")
        print(f"查询文本: {query_text}")
        
        # 向量化查询文本
        query_vector = model.encode(query_text).tolist()
        
        # 执行混合搜索
        result = (
            client.query
            .get(CLASS_NAME, ["title", "content"])
            .with_hybrid(
                query=query_text,
                vector=query_vector,
                alpha=0.5  # 0=纯关键词搜索, 1=纯向量搜索, 0.5=混合
            )
            .with_limit(limit)
            .with_additional(["score"])
            .do()
        )
        
        documents = result['data']['Get'][CLASS_NAME]
        
        if documents:
            print(f"找到 {len(documents)} 个相关文档:")
            for i, doc in enumerate(documents, 1):
                score = doc.get('_additional', {}).get('score', 'N/A')
                print(f"{i}. 标题: {doc['title']}")
                print(f"   得分: {score}")
                print(f"   内容: {doc['content'][:100]}...")
                print()
        else:
            print("未找到相关文档")
            
    except Exception as e:
        print(f"✗ 混合搜索失败: {e}")

def keyword_search(client, query_text, limit=3):
    """执行关键词搜索"""
    try:
        print(f"\n--- 关键词搜索 ---")
        print(f"查询文本: {query_text}")
        
        # 执行BM25关键词搜索
        result = (
            client.query
            .get(CLASS_NAME, ["title", "content"])
            .with_bm25(query=query_text)
            .with_limit(limit)
            .with_additional(["score"])
            .do()
        )
        
        documents = result['data']['Get'][CLASS_NAME]
        
        if documents:
            print(f"找到 {len(documents)} 个相关文档:")
            for i, doc in enumerate(documents, 1):
                score = doc.get('_additional', {}).get('score', 'N/A')
                print(f"{i}. 标题: {doc['title']}")
                print(f"   BM25得分: {score}")
                print(f"   内容: {doc['content'][:100]}...")
                print()
        else:
            print("未找到相关文档")
            
    except Exception as e:
        print(f"✗ 关键词搜索失败: {e}")

def get_all_documents(client):
    """获取所有文档"""
    try:
        print(f"\n--- 所有文档 ---")
        
        result = (
            client.query
            .get(CLASS_NAME, ["title", "content"])
            .with_limit(100)
            .do()
        )
        
        documents = result['data']['Get'][CLASS_NAME]
        
        if documents:
            print(f"数据库中共有 {len(documents)} 个文档:")
            for i, doc in enumerate(documents, 1):
                print(f"{i}. {doc['title']}")
                print(f"   {doc['content'][:50]}...")
                print()
        else:
            print("数据库中没有文档")
            
    except Exception as e:
        print(f"✗ 获取文档失败: {e}")

def main():
    """主函数"""
    print("=" * 50)
    print("Weaviate + SentenceTransformer 测试脚本")
    print("=" * 50)
    
    # 初始化客户端和模型
    client = initialize_client()
    if not client:
        return
    
    model = initialize_sentence_transformer()
    if not model:
        return
    
    # 创建schema
    create_schema_if_not_exists(client)
    
    # 添加测试数据
    add_test_documents(client, model)
    
    # 获取所有文档
    get_all_documents(client)
    
    # 测试查询
    test_queries = [
        "什么是人工智能？",
        "机器学习的基本概念",
        "深度学习和神经网络",
        "计算机如何理解语言"
    ]
    
    for query in test_queries:
        print("\n" + "=" * 50)
        
        # 向量搜索
        vector_search(client, model, query)
        
        # 混合搜索
        hybrid_search(client, model, query)
        
        # 关键词搜索
        keyword_search(client, query)

if __name__ == "__main__":
    main()