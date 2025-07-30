#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看AnalyDesignDocuments集合内容
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.weaviate_helper import get_weaviate_client

def view_analydesiggndocuments_content():
    """查看AnalyDesignDocuments集合内容"""
    client = None
    
    try:
        print("🔍 连接到Weaviate数据库...")
        client = get_weaviate_client()
        
        collection_name = "AnalyDesignDocuments"
        
        if client.collections.exists(collection_name):
            collection = client.collections.get(collection_name)
            
            print(f"\n📊 {collection_name} 集合统计:")
            try:
                # 获取所有文档
                all_docs = collection.query.fetch_objects(limit=1000)
                total_count = len(all_docs.objects)
                print(f"   总文档数: {total_count}")
                
                if total_count > 0:
                    # 按属性统计
                    stats = {}
                    
                    for obj in all_docs.objects:
                        props = obj.properties
                        
                        # 收集所有属性名
                        for key in props.keys():
                            if key not in stats:
                                stats[key] = {"count": 0, "samples": []}
                            stats[key]["count"] += 1
                            if len(stats[key]["samples"]) < 3:
                                value = props[key]
                                if isinstance(value, str) and len(value) > 50:
                                    value = value[:50] + "..."
                                stats[key]["samples"].append(value)
                    
                    print(f"\n📝 属性统计:")
                    for attr, data in sorted(stats.items()):
                        print(f"   {attr}: {data['count']} 个文档包含此属性")
                        if data['samples']:
                            print(f"      示例值: {data['samples']}")
                    
                    # 显示几个示例文档
                    print(f"\n📄 文档示例 (前3个):")
                    for i, obj in enumerate(all_docs.objects[:3]):
                        props = obj.properties
                        print(f"\n{i+1}. 文档ID: {obj.uuid}")
                        
                        # 显示所有属性
                        for key, value in props.items():
                            if isinstance(value, str) and len(value) > 100:
                                display_value = value[:100] + "..."
                            else:
                                display_value = value
                            print(f"   {key}: {display_value}")
                    
                    if total_count > 3:
                        print(f"\n... 还有 {total_count - 3} 个文档")
                        
                else:
                    print("   集合为空")
                    
            except Exception as e:
                print(f"❌ 获取文档统计失败: {e}")
                
            # 查看集合模式
            print(f"\n🏗️ {collection_name} 集合模式:")
            try:
                schema_info = collection.config.get()
                print(f"   向量化器: {schema_info.vectorizer}")
                print(f"   属性:")
                for prop in schema_info.properties:
                    print(f"     - {prop.name}: {prop.data_type}")
            except Exception as e:
                print(f"❌ 获取模式信息失败: {e}")
                
        else:
            print(f"❌ {collection_name} 集合不存在")
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    view_analydesiggndocuments_content()