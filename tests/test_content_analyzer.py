#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ContentAnalyzerService内容分析服务
"""

import sys
import os
import asyncio
import json
from unittest.mock import Mock, AsyncMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis_services.content_analyzer import ContentAnalyzerService

class MockLLMClient:
    """模拟LLM客户端"""
    
    def chat(self, messages, max_tokens=4000):
        """模拟聊天响应"""
        user_content = messages[-1]['content']
        
        # 根据提示内容返回不同的模拟响应
        if "JSON 格式输出分析结果" in user_content:
            return '''
{
    "current_change": [
        {
            "changeType": "修改",
            "changeReason": "系统自动审批功能从人工审批改为自动评分",
            "changeItems": ["评分模型自动审批", "取消人工审批流程"],
            "version": ["历史版本V1.6.docx"]
        }
    ]
}
'''
        elif "删除项" in user_content:
            return '''
{
    "changeType": "删除",
    "deletedItem": "手动审批功能",
    "section": "3.1 额度申请",
    "analysisResult": "删除手动审批功能，改为系统自动审批，提高效率"
}
'''
        else:
            return "这是一个模拟的LLM响应"

def create_test_markdown_content():
    """创建测试用的markdown内容"""
    return """
# 需求文档 - 银行信贷系统V2.0

## 1. 系统概述
本系统是银行信贷业务的核心系统，负责处理客户的信贷申请、审批和放款流程。

## 2. 功能模块

### 2.1 客户管理
- 客户信息录入和维护
- 客户征信查询
- 客户风险评估

### 2.2 信贷申请
- 在线申请提交
- 申请材料上传
- 申请状态跟踪

## 3. 业务流程

### 3.1 额度申请
用户通过App发起额度申请，系统自动调用审批服务，采用评分模型自动审批。
分值低于80分的申请将被自动拒绝。

~~删除了手动审批功能~~

### 3.2 放款流程
1. 审批通过后自动生成放款指令
2. 系统调用银行核心系统完成放款
3. 发送放款成功通知给客户

![流程图](images/loan_process.png)

## 4. 技术架构

### 4.1 系统架构
采用微服务架构，包含以下服务：
- 用户服务
- 审批服务
- 放款服务
- 通知服务

### 4.2 数据库设计
使用MySQL作为主数据库，Redis作为缓存数据库。

## 5. 接口设计

### 5.1 申请接口
- POST /api/v1/applications
- 参数：客户信息、申请金额、申请期限

### 5.2 查询接口  
- GET /api/v1/applications/{id}
- 返回：申请详情和状态

取消了 /api/v1/manual-approval 接口，不再支持手动审批。
"""

async def test_content_analyzer():
    """测试内容分析器"""
    print("=" * 60)
    print("🧪 测试ContentAnalyzerService")
    print("=" * 60)
    
    # 创建模拟的LLM客户端
    mock_llm_client = MockLLMClient()
    
    try:
        # 初始化ContentAnalyzerService
        print("🔧 初始化ContentAnalyzerService...")
        analyzer = ContentAnalyzerService(llm_client=mock_llm_client)
        print("✅ ContentAnalyzerService初始化成功")
        
        # 准备测试数据
        test_data = {
            "document_content": create_test_markdown_content()
        }
        
        print(f"\n📄 测试文档长度: {len(test_data['document_content'])} 字符")
        
        # 执行分析
        print("\n🔍 开始执行内容分析...")
        result = await analyzer.analyze("test_task_001", test_data)
        
        # 检查结果
        if result["success"]:
            print("✅ 内容分析成功!")
            
            # 打印分析结果
            data = result["data"]
            
            print(f"\n📊 分析结果统计:")
            print(f"   - 结构化内容块数量: {len(data['structured_chunks'])}")
            print(f"   - 分析耗时: {data['metadata']['analysis_time']:.2f}秒")
            print(f"   - 内容长度: {data['metadata']['content_length']} 字符")
            
            # 显示结构化内容块
            print(f"\n📋 结构化内容块:")
            for i, chunk in enumerate(data['structured_chunks'], 1):
                print(f"   {i}. [{chunk['level']}级] {chunk['section']}")
                print(f"      内容: {chunk['content'][:50]}...")
                if chunk['image_refs']:
                    print(f"      图片: {chunk['image_refs']}")
            
            # 显示历史对比结果
            history_comp = data['history_comparison']
            print(f"\n🔍 历史对比结果:")
            print(f"   - 总内容块: {history_comp['summary']['total_chunks']}")
            print(f"   - 新增项: {history_comp['summary']['new_items']}")
            print(f"   - 修改项: {history_comp['summary']['modified_items']}")
            print(f"   - 删除项: {history_comp['summary']['deleted_items']}")
            
            # 显示识别到的删除项
            if history_comp['deleted_items']:
                print(f"\n🗑️ 识别到的删除项:")
                for item in history_comp['deleted_items']:
                    print(f"   - 章节: {item['section']}")
                    print(f"     删除内容: {item['deleted_item']}")
                    print(f"     检测方法: {item['detection_method']}")
            
            # 显示变更分析
            change_analysis = data['change_analysis']
            print(f"\n📈 变更分析:")
            print(f"   - 变更分析数量: {change_analysis['summary']['total_changes']}")
            print(f"   - 删除分析数量: {change_analysis['summary']['total_deletions']}")
            
            # 显示详细的变更分析（如果有）
            if change_analysis['change_analyses']:
                print(f"\n📝 详细变更分析:")
                for analysis in change_analysis['change_analyses']:
                    if 'current_change' in analysis:
                        for change in analysis['current_change']:
                            print(f"   - 变更类型: {change['changeType']}")
                            print(f"   - 变更原因: {change['changeReason']}")
                            print(f"   - 变更项: {change['changeItems']}")
            
            # 显示删除分析（如果有）
            if change_analysis['deletion_analyses']:
                print(f"\n🗑️ 删除分析:")
                for analysis in change_analysis['deletion_analyses']:
                    print(f"   - 删除项: {analysis['deletedItem']}")
                    print(f"   - 章节: {analysis['section']}")
                    print(f"   - 分析结果: {analysis['analysisResult']}")
            
        else:
            print(f"❌ 内容分析失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_document_preprocessing():
    """测试文档预处理功能"""
    print("\n" + "=" * 60)
    print("📄 测试文档预处理功能")
    print("=" * 60)
    
    try:
        mock_llm_client = MockLLMClient()
        analyzer = ContentAnalyzerService(llm_client=mock_llm_client)
        
        # 测试markdown内容
        markdown_content = create_test_markdown_content()
        
        print("🔧 执行文档预处理...")
        chunks = await analyzer._preprocess_document(markdown_content)
        
        print(f"✅ 预处理完成，生成 {len(chunks)} 个内容块")
        
        # 显示每个内容块的详细信息
        for i, chunk in enumerate(chunks, 1):
            print(f"\n📋 内容块 {i}:")
            print(f"   标题: {chunk['section']}")
            print(f"   级别: {chunk['level']}")
            print(f"   内容长度: {len(chunk['content'])} 字符")
            print(f"   内容预览: {chunk['content'][:100]}...")
            print(f"   向量维度: {len(chunk['embedding'])}")
            if chunk['image_refs']:
                print(f"   图片引用: {chunk['image_refs']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文档预处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_deletion_detection():
    """测试删除项识别功能"""
    print("\n" + "=" * 60)
    print("🗑️ 测试删除项识别功能")
    print("=" * 60)
    
    try:
        mock_llm_client = MockLLMClient()
        analyzer = ContentAnalyzerService(llm_client=mock_llm_client)
        
        # 创建包含删除描述的测试内容
        test_chunks = [
            {
                "section": "3.1 额度申请",
                "content": "删除了手动审批功能，改为系统自动审批。去除了人工干预环节。",
                "level": 3
            },
            {
                "section": "5.1 接口设计", 
                "content": "取消了 /api/v1/manual-approval 接口，不再支持手动审批。",
                "level": 3
            },
            {
                "section": "4.2 功能模块",
                "content": "~~移除了短信通知功能~~，改为邮件通知。",
                "level": 3
            }
        ]
        
        print("🔍 执行删除项识别...")
        deleted_items = await analyzer._identify_deleted_items(test_chunks)
        
        print(f"✅ 识别完成，找到 {len(deleted_items)} 个删除项")
        
        for i, item in enumerate(deleted_items, 1):
            print(f"\n🗑️ 删除项 {i}:")
            print(f"   章节: {item['section']}")
            print(f"   删除内容: {item['deleted_item']}")
            print(f"   检测方法: {item['detection_method']}")
            print(f"   上下文: {item['context'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 删除项识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 ContentAnalyzerService 测试套件")
    print("=" * 60)
    
    tests = [
        ("文档预处理", test_document_preprocessing),
        ("删除项识别", test_deletion_detection),
        ("完整内容分析", test_content_analyzer),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n▶️ 开始测试: {test_name}")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ 测试 {test_name} 异常: {e}")
            results[test_name] = False
    
    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{len(tests)} 个测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查日志")

if __name__ == "__main__":
    asyncio.run(main()) 