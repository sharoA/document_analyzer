#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看Weaviate数据库内容
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.weaviate_helper import get_weaviate_client

def view_weaviate_content():
    """查看Weaviate数据库内容"""
    client = None
    
    try:
        print("🔍 连接到Weaviate数据库...")
        client = get_weaviate_client()
        
        # 获取所有集合
        collections = client.collections.list_all()
        print(f"📋 数据库中的集合: {list(collections.keys())}")
        
        if "Document" in collections:
            collection = client.collections.get("Document")
            
            # 获取文档总数
            print("\n📊 Document集合统计:")
            try:
                # 获取所有文档
                all_docs = collection.query.fetch_objects(limit=1000)
                total_count = len(all_docs.objects)
                print(f"   总文档数: {total_count}")
                
                if total_count > 0:
                    # 按文件名统计
                    file_stats = {}
                    project_stats = {}
                    source_type_stats = {}
                    
                    for obj in all_docs.objects:
                        props = obj.properties
                        
                        # 统计文件
                        file_name = props.get('file_name', 'unknown')
                        file_stats[file_name] = file_stats.get(file_name, 0) + 1
                        
                        # 统计项目
                        project = props.get('project', 'unknown')
                        project_stats[project] = project_stats.get(project, 0) + 1
                        
                        # 统计来源类型
                        source_type = props.get('source_type', 'unknown')
                        source_type_stats[source_type] = source_type_stats.get(source_type, 0) + 1
                    # 打印Document集合所有内容
                    print(f"\n📚 打印Document集合所有内容（最多1000条）:")
                    for idx, obj in enumerate(all_docs.objects):
                        props = obj.properties
                        print(f"\n--- 文档 {idx+1} ---")
                        print(f"文档ID: {obj.uuid}")
                        print(f"文件: {props.get('file_name', 'N/A')}")
                        print(f"标题: {props.get('title', 'N/A')}")
                        print(f"项目: {props.get('project', 'N/A')}")
                        print(f"段落索引: {props.get('chunk_index', 'N/A')}")
                        print(f"来源类型: {props.get('source_type', 'N/A')}")
                        print(f"内容长度: {len(props.get('content', ''))} 字符")
                        print(f"内容: {props.get('content', '')}")
                        print(f"创建时间: {props.get('created_at', 'N/A')}")
                    import json
                    print(f"props JSON: {json.dumps(props, ensure_ascii=False, indent=2)}")
                        
               
                    
            except Exception as e:
                print(f"❌ 获取文档统计失败: {e}")
        else:
            print("❌ Document集合不存在")
            
        # 查看数据库模式
        print(f"\n🏗️ Document集合模式:")
        try:
            schema_info = client.collections.get("Document").config.get()
            print(f"   向量化器: {schema_info.vectorizer}")
            print(f"   属性:")
            for prop in schema_info.properties:
                print(f"     - {prop.name}: {prop.data_type}")
        except Exception as e:
            print(f"❌ 获取模式信息失败: {e}")
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    view_weaviate_content()