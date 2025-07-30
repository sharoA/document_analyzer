#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看Document集合的具体内容详情
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.weaviate_helper import get_weaviate_client

def view_document_details():
    """查看Document集合的详细内容"""
    client = None
    
    try:
        print("🔍 连接到Weaviate数据库...")
        client = get_weaviate_client()
        
        collection = client.collections.get("Document")
        
        # 获取所有文档，按chunk_index排序
        print("\n📄 获取所有文档内容...")
        all_docs = collection.query.fetch_objects(limit=100)
        
        if not all_docs.objects:
            print("❌ 集合为空")
            return
        
        # 按chunk_index排序
        sorted_docs = sorted(all_docs.objects, key=lambda x: x.properties.get('chunk_index', 0))
        
        print(f"\n📊 共 {len(sorted_docs)} 个文档段落\n")
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
                
                # 每5个暂停一下，让用户可以查看
                if (i + 1) % 5 == 0:
                    input(f"\n⏸️ 已显示 {i+1} 个段落，按回车继续查看...")
        
        print(f"\n✅ 所有 {len(sorted_docs)} 个段落显示完成")
        
    except Exception as e:
        print(f"❌ 查看失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    view_document_details()