#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试"放款"关键词的向量查询
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentence_transformers import SentenceTransformer
from src.utils.weaviate_helper import get_weaviate_client

def test_fangkuan_query():
    """测试放款查询"""
    print("=" * 50)
    print("测试'放款'关键词查询")
    print("=" * 50)
    
    client = None
    try:
        # 初始化客户端和模型
        client = get_weaviate_client()
        print("✓ 成功连接到Weaviate")
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ 成功加载SentenceTransformer模型")
        
        # 查询关键词
        query_text = "放款"
        print(f"\n查询关键词: {query_text}")
        
        # 检查所有可用的集合
        print("\n--- 可用的集合 ---")
        collections = client.collections.list_all()
        for collection_name in collections:
            print(f"- {collection_name}")
        
        # 如果有默认集合，查询它
        if collections:
            for collection_name in collections:
                print(f"\n--- 在集合 '{collection_name}' 中搜索 ---")
                try:
                    collection = client.collections.get(collection_name)
                    
                    # 1. 向量搜索
                    print(f"\n1. 向量搜索:")
                    query_vector = model.encode(query_text).tolist()
                    response = collection.query.near_vector(
                        near_vector=query_vector,
                        limit=5,
                        return_metadata=['distance']
                    )
                    
                    if response.objects:
                        print(f"找到 {len(response.objects)} 个相关文档:")
                        for i, obj in enumerate(response.objects, 1):
                            distance = obj.metadata.distance if obj.metadata.distance else 'N/A'
                            print(f"{i}. 距离: {distance}")
                            # 打印所有属性
                            for key, value in obj.properties.items():
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"   {key}: {value[:100]}...")
                                else:
                                    print(f"   {key}: {value}")
                            print()
                    else:
                        print("未找到相关文档")
                    
                    # 2. 关键词搜索
                    print(f"\n2. 关键词搜索:")
                    try:
                        response = collection.query.bm25(
                            query=query_text,
                            limit=5,
                            return_metadata=['score']
                        )
                        
                        if response.objects:
                            print(f"找到 {len(response.objects)} 个相关文档:")
                            for i, obj in enumerate(response.objects, 1):
                                score = obj.metadata.score if obj.metadata.score else 'N/A'
                                print(f"{i}. BM25得分: {score}")
                                for key, value in obj.properties.items():
                                    if isinstance(value, str) and len(value) > 100:
                                        print(f"   {key}: {value[:100]}...")
                                    else:
                                        print(f"   {key}: {value}")
                                print()
                        else:
                            print("未找到相关文档")
                    except Exception as e:
                        print(f"关键词搜索失败: {e}")
                    
                    # 3. 混合搜索
                    print(f"\n3. 混合搜索:")
                    try:
                        response = collection.query.hybrid(
                            query=query_text,
                            vector=query_vector,
                            alpha=0.5,
                            limit=5,
                            return_metadata=['score']
                        )
                        
                        if response.objects:
                            print(f"找到 {len(response.objects)} 个相关文档:")
                            for i, obj in enumerate(response.objects, 1):
                                score = obj.metadata.score if obj.metadata.score else 'N/A'
                                print(f"{i}. 混合得分: {score}")
                                for key, value in obj.properties.items():
                                    if isinstance(value, str) and len(value) > 100:
                                        print(f"   {key}: {value[:100]}...")
                                    else:
                                        print(f"   {key}: {value}")
                                print()
                        else:
                            print("未找到相关文档")
                    except Exception as e:
                        print(f"混合搜索失败: {e}")
                        
                    # 4. 显示集合中的所有文档（前5个）
                    print(f"\n4. 集合中的文档示例:")
                    try:
                        response = collection.query.fetch_objects(limit=5)
                        if response.objects:
                            print(f"集合中共有文档，显示前 {len(response.objects)} 个:")
                            for i, obj in enumerate(response.objects, 1):
                                print(f"{i}. 文档ID: {obj.uuid}")
                                for key, value in obj.properties.items():
                                    if isinstance(value, str) and len(value) > 100:
                                        print(f"   {key}: {value[:100]}...")
                                    else:
                                        print(f"   {key}: {value}")
                                print()
                        else:
                            print("集合中没有文档")
                    except Exception as e:
                        print(f"获取文档失败: {e}")
                        
                except Exception as e:
                    print(f"查询集合 {collection_name} 失败: {e}")
        else:
            print("没有找到任何集合")
    
    except Exception as e:
        print(f"测试失败: {e}")
    
    finally:
        if client:
            try:
                client.close()
                print("\n✓ Weaviate客户端连接已关闭")
            except Exception as e:
                print(f"\n⚠️ 关闭客户端连接时出错: {e}")

if __name__ == "__main__":
    test_fangkuan_query() 