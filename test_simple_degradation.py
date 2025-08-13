#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Weaviate降级模式测试
"""

import sys
import os
import asyncio

# 添加src目录到Python路径
project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_basic_weaviate_functionality():
    """测试基础Weaviate功能"""
    print('=== 测试基础Weaviate功能 ===')
    
    try:
        # 测试能否导入weaviate模块
        import weaviate
        print('✅ Weaviate模块导入成功')
        
        # 尝试连接本地Weaviate（预期会失败）
        try:
            client = weaviate.connect_to_local()
            if client.is_ready():
                print('✅ Weaviate连接成功')
                client.close()
                return True
            else:
                print('⚠️ Weaviate服务未就绪')
                return False
        except Exception as e:
            print(f'⚠️ Weaviate连接失败: {e}')
            return False
            
    except ImportError as e:
        print(f'❌ Weaviate模块导入失败: {e}')
        return False

def test_content_analyzer_without_weaviate():
    """测试ContentAnalyzerService在没有Weaviate时的表现"""
    print('\n=== 测试ContentAnalyzerService降级模式 ===')
    
    try:
        # 直接导入并实例化ContentAnalyzerService
        from analysis_services.content_analyzer import ContentAnalyzerService
        
        # 创建实例
        analyzer = ContentAnalyzerService()
        print('✅ ContentAnalyzerService创建成功')
        
        # 检查降级状态
        print(f'   - 向量数据库可用: {analyzer.vector_enabled}')
        print(f'   - 向量化模型可用: {analyzer.embedding_enabled}') 
        print(f'   - Weaviate客户端状态: {"连接" if analyzer.weaviate_client else "未连接"}')
        
        # 测试文档预处理
        test_content = """
# 测试需求文档

## 1. 用户管理功能
- 新增用户注册功能
- 修改用户登录逻辑  
- 删除过期用户数据

## 2. 权限控制
- 调整角色权限配置
- 新增权限验证机制

## 3. 数据导出
- 支持Excel格式导出
- 新增PDF报告生成
        """
        
        print('\n=== 测试文档预处理功能 ===')
        
        async def test_preprocessing():
            try:
                result = await analyzer._preprocess_document(test_content)
                print(f'✅ 文档预处理成功')
                print(f'   - 生成内容块数量: {len(result)}')
                
                for i, chunk in enumerate(result):
                    section = chunk.get('section', 'Unknown')[:30]
                    has_embedding = chunk.get('embedding') is not None
                    embedding_status = '有向量' if has_embedding else '无向量'
                    print(f'   - 块{i+1}: "{section}..." ({embedding_status})')
                
                return True
            except Exception as e:
                print(f'❌ 文档预处理失败: {e}')
                import traceback
                traceback.print_exc()
                return False
        
        # 运行异步测试
        success = asyncio.run(test_preprocessing())
        
        if success:
            print('✅ 降级模式测试成功 - 系统可以在没有Weaviate的情况下正常处理文档')
        
        return success
        
    except Exception as e:
        print(f'❌ ContentAnalyzerService测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_historical_comparison_degradation():
    """测试历史对比功能的降级模式"""
    print('\n=== 测试历史对比降级功能 ===')
    
    try:
        from analysis_services.content_analyzer import ContentAnalyzerService
        
        analyzer = ContentAnalyzerService()
        
        # 创建测试数据
        test_chunks = [
            {
                'section': '用户管理功能',
                'content': '新增用户注册和登录功能',
                'level': 2,
                'embedding': None,  # 模拟无向量情况
                'image_refs': []
            }
        ]
        
        print('测试历史相似内容查找...')
        
        async def test_history_search():
            try:
                # 这个函数在没有Weaviate时应该返回空列表
                result = await analyzer._find_similar_history(test_chunks[0])
                print(f'✅ 历史搜索降级成功，返回结果: {len(result)} 个')
                return True
            except Exception as e:
                print(f'❌ 历史搜索降级失败: {e}')
                return False
        
        return asyncio.run(test_history_search())
        
    except Exception as e:
        print(f'❌ 历史对比测试失败: {e}')
        return False

def main():
    """主测试函数"""
    print('🔄 开始Weaviate降级模式测试')
    
    # 测试1: 基础Weaviate连接
    weaviate_available = test_basic_weaviate_functionality()
    
    # 测试2: ContentAnalyzer降级模式
    analyzer_success = test_content_analyzer_without_weaviate()
    
    # 测试3: 历史对比降级模式  
    history_success = test_historical_comparison_degradation()
    
    print('\n=== 测试总结 ===')
    print(f'Weaviate连接状态: {"可用" if weaviate_available else "不可用"}')
    print(f'内容分析器降级模式: {"成功" if analyzer_success else "失败"}')
    print(f'历史对比降级模式: {"成功" if history_success else "失败"}')
    
    overall_success = analyzer_success and history_success
    
    if overall_success:
        print('🎉 所有降级模式测试通过！系统可以在没有Weaviate的情况下正常运行')
    else:
        print('❌ 部分降级模式测试失败，需要进一步检查')
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)