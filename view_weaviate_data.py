#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看Weaviate向量数据库所有数据
"""

import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.utils.weaviate_helper import get_weaviate_client
import json
from datetime import datetime

def view_all_weaviate_data():
    """查看Weaviate数据库中的所有数据"""
    print("=" * 60)
    print("Weaviate 向量数据库数据查看器")
    print("=" * 60)
    
    client = None
    try:
        # 初始化客户端
        client = get_weaviate_client()
        print("✓ 成功连接到Weaviate")
        
        # 获取所有集合
        print("\n--- 数据库概览 ---")
        collections = client.collections.list_all()
        print(f"数据库中共有 {len(collections)} 个集合:")
        
        total_objects = 0
        
        for collection_name in collections:
            print(f"\n{'='*50}")
            print(f"集合: {collection_name}")
            print(f"{'='*50}")
            
            try:
                collection = client.collections.get(collection_name)
                
                # 获取集合的基本信息
                print(f"\n📊 集合统计信息:")
                
                # 获取所有对象（分批获取以避免内存问题）
                all_objects = []
                offset = 0
                limit = 50  # 减小批次大小
                max_objects = 1000  # 限制最大对象数量以避免内存问题
                
                print(f"   正在获取数据...")
                
                while len(all_objects) < max_objects:
                    try:
                        response = collection.query.fetch_objects(
                            limit=limit,
                            offset=offset
                        )
                        
                        if not response.objects:
                            break
                            
                        all_objects.extend(response.objects)
                        offset += limit
                        
                        print(f"   已获取 {len(all_objects)} 个文档...")
                        
                        # 防止无限循环
                        if len(response.objects) < limit:
                            break
                            
                    except Exception as e:
                        print(f"   ⚠️ 批次查询失败 (offset={offset}): {e}")
                        # 尝试更小的批次
                        if limit > 10:
                            limit = 10
                            continue
                        else:
                            break
                
                collection_count = len(all_objects)
                total_objects += collection_count
                print(f"   - 文档数量: {collection_count}")
                
                if collection_count > 0:
                    # 分析数据类型
                    print(f"\n📋 数据结构分析:")
                    
                    # 获取第一个对象来分析结构
                    first_obj = all_objects[0]
                    print(f"   - 属性字段:")
                    for key, value in first_obj.properties.items():
                        value_type = type(value).__name__
                        if isinstance(value, str):
                            value_preview = value[:50] + "..." if len(value) > 50 else value
                        else:
                            value_preview = str(value)
                        print(f"     • {key}: {value_type} - {value_preview}")
                    
                    # 统计不同类型的文档
                    if 'file_type' in first_obj.properties:
                        file_types = {}
                        projects = {}
                        source_types = {}
                        
                        for obj in all_objects:
                            # 统计文件类型
                            file_type = obj.properties.get('file_type', 'unknown')
                            file_types[file_type] = file_types.get(file_type, 0) + 1
                            
                            # 统计项目
                            project = obj.properties.get('project', 'unknown')
                            projects[project] = projects.get(project, 0) + 1
                            
                            # 统计来源类型
                            source_type = obj.properties.get('source_type', 'unknown')
                            source_types[source_type] = source_types.get(source_type, 0) + 1
                        
                        print(f"\n📈 数据分布:")
                        print(f"   - 文件类型分布:")
                        for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                            print(f"     • {file_type}: {count} 个文档")
                        
                        print(f"   - 项目分布:")
                        for project, count in sorted(projects.items(), key=lambda x: x[1], reverse=True):
                            print(f"     • {project}: {count} 个文档")
                        
                        print(f"   - 来源类型分布:")
                        for source_type, count in sorted(source_types.items(), key=lambda x: x[1], reverse=True):
                            print(f"     • {source_type}: {count} 个文档")
                    
                    # 显示最近的几个文档
                    print(f"\n📄 最近的文档示例 (显示前5个):")
                    for i, obj in enumerate(all_objects[:5], 1):
                        print(f"\n   {i}. 文档ID: {obj.uuid}")
                        for key, value in obj.properties.items():
                            if isinstance(value, str) and len(value) > 80:
                                display_value = value[:80] + "..."
                            else:
                                display_value = value
                            print(f"      {key}: {display_value}")
                        
                        # 如果有向量信息，显示向量维度
                        if hasattr(obj, 'vector') and obj.vector:
                            print(f"      向量维度: {len(obj.vector)}")
                
                else:
                    print("   - 集合为空")
                    
            except Exception as e:
                print(f"❌ 查询集合 {collection_name} 失败: {e}")
        
        print(f"\n{'='*60}")
        print(f"📊 总体统计:")
        print(f"   - 总集合数: {len(collections)}")
        print(f"   - 总文档数: {total_objects}")
        print(f"   - 查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ 连接或查询失败: {e}")
    
    finally:
        if client:
            try:
                client.close()
                print("\n✓ Weaviate客户端连接已关闭")
            except Exception as e:
                print(f"\n⚠️ 关闭客户端连接时出错: {e}")

def export_collection_data(collection_name, output_file=None):
    """导出指定集合的数据到JSON文件"""
    client = None
    try:
        client = get_weaviate_client()
        collection = client.collections.get(collection_name)
        
        # 获取所有数据
        all_objects = []
        offset = 0
        limit = 50  # 使用较小的批次
        max_objects = 1000  # 限制导出数量
        
        print(f"正在导出集合 {collection_name} 的数据...")
        
        while len(all_objects) < max_objects:
            try:
                response = collection.query.fetch_objects(
                    limit=limit,
                    offset=offset,
                    include_vector=False  # 不包含向量数据以减少文件大小
                )
                
                if not response.objects:
                    break
                    
                for obj in response.objects:
                    obj_data = {
                        'id': str(obj.uuid),
                        'properties': obj.properties
                    }
                    all_objects.append(obj_data)
                
                offset += limit
                print(f"已导出 {len(all_objects)} 个文档...")
                
                if len(response.objects) < limit:
                    break
                    
            except Exception as e:
                print(f"⚠️ 批次导出失败 (offset={offset}): {e}")
                if limit > 10:
                    limit = 10
                    continue
                else:
                    break
        
        # 导出到文件
        if output_file is None:
            output_file = f"{collection_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_objects, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✓ 成功导出 {len(all_objects)} 个文档到 {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='查看Weaviate向量数据库数据')
    parser.add_argument('--export', type=str, help='导出指定集合的数据')
    parser.add_argument('--output', type=str, help='导出文件名')
    
    args = parser.parse_args()
    
    if args.export:
        export_collection_data(args.export, args.output)
    else:
        view_all_weaviate_data() 