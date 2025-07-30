#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看Document集合的前10个具体内容详情（无交互）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.weaviate_helper import get_weaviate_client

def view_document_details_simple():
    """查看Document集合的详细内容（前10个）"""
    client = None
    
    try:
        print("🔍 连接到Weaviate数据库...")
        client = get_weaviate_client()
        
        collection = client.collections.get("Document")
        
        # 获取前15个文档，按chunk_index排序
        print("\n📄 获取前15个文档内容...")
        all_docs = collection.query.fetch_objects(limit=100)
        
        if not all_docs.objects:
            print("❌ 集合为空")
            return
        
        # 按chunk_index排序，只显示前15个
        sorted_docs = sorted(all_docs.objects, key=lambda x: x.properties.get('chunk_index', 0))[:15]
        
        print(f"\n📊 显示前 {len(sorted_docs)} 个文档段落（共{len(all_docs.objects)}个）\n")
        print("=" * 100)
        
        for i, obj in enumerate(sorted_docs):
            props = obj.properties
            
            print(f"\n📋 段落 {i+1}/{len(sorted_docs)}")
            print(f"🆔 ID: {obj.uuid}")
            print(f"📂 文件: {props.get('file_name', 'N/A')}")
            print(f"🏷️ 标题: {props.get('title', 'N/A')}")
            print(f"🏢 项目: {props.get('project', 'N/A')}")
            print(f"📝 类型: {props.get('source_type', 'N/A')}")
            print(f"🔢 段落索引: {props.get('chunk_index', 'N/A')}/{props.get('total_chunks', 'N/A')}")
            print(f"⏰ 创建时间: {props.get('created_at', 'N/A')}")
            print(f"📏 内容长度: {len(props.get('content', ''))} 字符")
            
            # 显示完整内容
            content = props.get('content', '')
            print(f"\n📖 完整内容:")
            print("-" * 80)
            print(content)
            print("-" * 80)
            
            if i < len(sorted_docs) - 1:
                print("\n" + "=" * 100)
        
        print(f"\n✅ 显示了前 {len(sorted_docs)} 个段落，总共有 {len(all_docs.objects)} 个段落")
        
        # 显示一些统计信息
        print(f"\n📊 内容类型统计:")
        titles = [obj.properties.get('title', 'N/A') for obj in all_docs.objects]
        content_lengths = [len(obj.properties.get('content', '')) for obj in all_docs.objects]
        
        print(f"   📏 内容长度: 最短 {min(content_lengths)} 字符, 最长 {max(content_lengths)} 字符, 平均 {sum(content_lengths)//len(content_lengths)} 字符")
        print(f"   📝 不同标题数量: {len(set(titles))} 个")
        
    except Exception as e:
        print(f"❌ 查看失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    view_document_details_simple()