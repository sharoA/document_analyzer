#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库查询脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.knowledge_init_weaviate import KnowledgeBaseInitializer

def main():
    """主函数"""
    initializer = None
    
    try:
        # 创建初始化器（不重新初始化，只用于查询）
        print("🚀 连接知识库...")
        initializer = KnowledgeBaseInitializer()
        
        print("✅ 知识库连接成功！")
        print("📊 知识库统计信息:")
        
        # 获取集合信息
        try:
            collection = initializer.weaviate_client.collections.get("KnowledgeDocument")
            # 获取文档总数
            result = collection.aggregate.over_all(total_count=True)
            total_count = result.total_count
            print(f"   总文档数: {total_count}")
        except Exception as e:
            print(f"   无法获取统计信息: {e}")
        
        print("\n" + "="*60)
        print("🔍 知识库查询系统")
        print("="*60)
        print("输入查询内容，输入 'quit' 或 'exit' 退出")
        print("-"*60)
        
        while True:
            try:
                query = input("\n请输入查询内容: ").strip()
                
                if query.lower() in ['quit', 'exit', '退出']:
                    print("👋 再见！")
                    break
                
                if not query:
                    print("⚠️ 请输入有效的查询内容")
                    continue
                
                print(f"\n🔍 搜索: {query}")
                print("-" * 40)
                
                # 执行查询
                results = initializer.query_knowledge_base(query, limit=5)
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"\n{i}. 📄 {result['file_name']}")
                        print(f"   📁 项目: {result['project']}")
                        print(f"   🏷️  类型: {result['file_type']} | 来源: {result['source_type']}")
                        print(f"   📊 相似度: {1 - result['distance']:.3f}")
                        print(f"   📝 内容预览: {result['content'][:150]}...")
                        if len(result['content']) > 150:
                            print("      ...")
                else:
                    print("❌ 没有找到相关结果")
                
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，再见！")
                break
            except Exception as e:
                print(f"❌ 查询出错: {e}")
        
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if initializer:
            initializer.close()

if __name__ == "__main__":
    main() 