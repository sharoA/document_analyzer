#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试内容分析功能 - 使用现有向量化数据
"""

import requests
import json
import base64
from datetime import datetime

def test_content_analysis_with_current_data():
    """使用当前向量化数据测试内容分析功能"""
    print("🚀 测试内容分析功能 - 使用当前向量化数据")
    print("=" * 60)
    
    # 准备测试文档 - 模拟一个简单的需求变更
    test_document = """
# 需求文档 - 确权业务申请接口优化V1.2

## 1. 项目背景
一局对接链数的项目上线后，核心企业反馈，希望就已推送至平台的数据，在核心企业内部系统内修改部分信息（如额度信息）后，使用原业务编号再次推送至平台。

## 2. 功能调整

### 2.1 确权业务申请接口调整
调整说明：对确权业务申请接口中关于bizSerialNo的校验规则进行调整，允许相同业务编号的数据在核心企业内部系统修改后重新推送。

具体变更：
- 调整接口校验逻辑，支持相同业务编号重复提交
- 新增数据版本控制机制
- 增加重推标识字段

### 2.2 额度管理功能调整
对原"链数额度"功能进行以下调整：
- 功能名称由"链数额度"变更为"额度管理"
- 新增"组织单元额度"按钮
- 列表新增"额度类型"字段

## 3. 技术要求
- 使用现有的接口框架
- 保持数据一致性
- 确保向后兼容
"""
    
    # API端点
    api_url = "http://localhost:8082/api/v2/analysis/start"
    
    # 将文档内容编码为Base64
    encoded_content = base64.b64encode(test_document.encode('utf-8')).decode('ascii')
    
    # 请求数据 - 按照API V2格式，内容需要Base64编码
    request_data = {
        "file_info": {
            "name": "test_requirement_doc.md",
            "content": encoded_content
        },
        "task_id": f"test_current_data_{int(datetime.now().timestamp())}"
    }
    
    print(f"📋 测试文档长度: {len(test_document)} 字符")
    print(f"🔗 API端点: {api_url}")
    print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        print("🚀 发送请求...")
        response = requests.post(api_url, json=request_data, timeout=300)
        
        print(f"📈 HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            
            # 保存完整结果
            result_file = f"content_analysis_test_{int(datetime.now().timestamp())}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"📁 完整结果已保存到: {result_file}")
            
            # 显示关键结果信息
            print("\n📊 分析结果概览:")
            print(f"  ✅ 成功状态: {result.get('success', 'unknown')}")
            
            if result.get('success'):
                data = result.get('data', {})
                metadata = data.get('metadata', {})
                print(f"  🔧 分析方法: {metadata.get('analysis_method', 'unknown')}")
                print(f"  ⏱️ 分析耗时: {metadata.get('analysis_time', 'unknown')} 秒")
                print(f"  📏 内容长度: {metadata.get('content_length', 'unknown')} 字符")
                print(f"  📑 文档块数: {metadata.get('chunks_count', 'unknown')} 个")
                
                # 显示变更分析结果
                change_analysis = data.get('change_analysis', {})
                
                if 'change_analyses' in change_analysis:
                    changes = change_analysis['change_analyses']
                    print(f"\n🔍 发现变更项: {len(changes)} 个")
                    
                    for i, change in enumerate(changes[:5], 1):  # 显示前5个
                        print(f"\n  📝 变更项 {i}:")
                        print(f"    🏷️ 类型: {change.get('changeType', 'unknown')}")
                        
                        reason = change.get('changeReason', 'unknown')
                        print(f"    📄 原因: {reason[:80]}{'...' if len(reason) > 80 else ''}")
                        
                        items = change.get('changeItems', [])
                        print(f"    🔢 变更点数量: {len(items)}")
                        
                        if items:
                            first_item = items[0]
                            print(f"    📌 首个变更点: {first_item[:80]}{'...' if len(first_item) > 80 else ''}")
                        
                        if 'changeDetails' in change:
                            details = change['changeDetails']
                            if details and details.strip():
                                print(f"    📋 详细说明: {details[:100]}{'...' if len(details) > 100 else ''}")
                        
                        version = change.get('version', [])
                        if version:
                            print(f"    📦 涉及版本: {', '.join(version)}")
                    
                    if len(changes) > 5:
                        print(f"    ... 还有 {len(changes) - 5} 个变更项")
                
                # 显示删除分析结果
                if 'deletion_analyses' in change_analysis:
                    deletions = change_analysis['deletion_analyses']
                    if deletions:
                        print(f"\n🗑️ 发现删除项: {len(deletions)} 个")
                        for i, deletion in enumerate(deletions[:3], 1):
                            print(f"  🗂️ 删除项 {i}: {deletion.get('deletedItem', 'unknown')}")
                
                # 显示摘要信息
                summary = change_analysis.get('summary', {})
                if summary:
                    print(f"\n📊 分析摘要:")
                    print(f"  📑 总文档块: {summary.get('total_chunks', 'unknown')}")
                    print(f"  🆕 新增项: {summary.get('new_items', 'unknown')}")
                    print(f"  🔄 修改项: {summary.get('modified_items', 'unknown')}")
                    print(f"  ✅ 相同项: {summary.get('same_items', 'unknown')}")
                    print(f"  🗑️ 删除项: {summary.get('deleted_items', 'unknown')}")
                
            else:
                error = result.get('error', 'unknown')
                print(f"  ❌ 错误信息: {error}")
            
            print(f"\n🎉 测试完成！")
            return True
            
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 错误详情:")
                print(json.dumps(error_data, ensure_ascii=False, indent=2))
            except:
                print(f"📋 响应内容: {response.text[:500]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("💡 请确保API服务器已启动:")
        print("   cd /Users/renyu/Documents/ai_project/document_analyzer")  
        print("   source venv/bin/activate")
        print("   python src/apis/api_server.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ API调用超时 (5分钟)")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_content_analysis_with_current_data()