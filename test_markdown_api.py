#!/usr/bin/env python3
"""
测试Markdown API接口的脚本
用于验证保存和获取markdown内容的功能
"""

import requests
import json
import sys
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8082"
TASK_ID = "bc193654-c7f9-4f8e-a083-c0b6d8926922"

def test_get_markdown():
    """测试获取markdown内容"""
    print("=" * 60)
    print("🔍 测试获取Markdown内容")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/file/markdown/{TASK_ID}"
    
    try:
        print(f"📡 请求URL: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 获取成功!")
            print(f"📝 任务ID: {data.get('task_id', 'N/A')}")
            print(f"📏 内容长度: {data.get('content_length', 'N/A')} 字符")
            print(f"🗂️ 存储来源: {data.get('storage_source', 'N/A')}")
            print(f"⏰ 获取时间: {data.get('retrieved_at', 'N/A')}")
            
            # 显示内容预览（前200字符）
            content = data.get('markdown_content', '')
            if content:
                print(f"📄 内容预览 (前200字符):")
                print("-" * 40)
                print(content[:200] + ("..." if len(content) > 200 else ""))
                print("-" * 40)
            else:
                print("⚠️ 内容为空")
                
        elif response.status_code == 404:
            data = response.json()
            print("❌ 内容不存在")
            print(f"📝 错误信息: {data.get('error', 'N/A')}")
            print(f"💡 提示: {data.get('message', 'N/A')}")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误详情: {error_data}")
            except:
                print(f"📝 响应内容: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 无法连接到服务器")
        print("💡 请确保后端服务器正在运行 (http://localhost:8082)")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_save_markdown():
    """测试保存markdown内容"""
    print("=" * 60)
    print("💾 测试保存Markdown内容")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/file/markdown/{TASK_ID}"
    
    # 测试用的markdown内容
    test_content = f"""# 测试设计方案

## 概述
这是一个测试保存的设计方案内容。

## 测试信息
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 任务ID: {TASK_ID}
- 测试目的: 验证Markdown保存功能

## 功能特性
1. **文档解析**: 支持多种文档格式
2. **内容分析**: 智能提取关键信息  
3. **AI分析**: 基于大语言模型的深度分析
4. **报告生成**: 自动生成结构化报告

## 技术架构
```
前端 (Vue3) --> 后端 (Flask) --> 存储 (Redis/SQLite)
```

## 总结
测试内容保存功能正常。

---
*测试脚本生成于: {datetime.now().isoformat()}*
"""
    
    payload = {
        "markdown_content": test_content
    }
    
    try:
        print(f"📡 请求URL: {url}")
        print(f"📦 请求方法: PUT")
        print(f"📏 内容长度: {len(test_content)} 字符")
        
        response = requests.put(
            url, 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 保存成功!")
            print(f"📝 任务ID: {data.get('task_id', 'N/A')}")
            print(f"📏 内容长度: {data.get('content_length', 'N/A')} 字符")
            print(f"🗂️ 存储位置: {data.get('storage', 'N/A')}")
            print(f"⏰ 更新时间: {data.get('updated_at', 'N/A')}")
            print(f"💬 消息: {data.get('message', 'N/A')}")
            
        elif response.status_code == 404:
            data = response.json()
            print("❌ 任务不存在")
            print(f"📝 错误信息: {data.get('error', 'N/A')}")
            
        elif response.status_code == 400:
            data = response.json()
            print("❌ 请求参数错误")
            print(f"📝 错误信息: {data.get('error', 'N/A')}")
            
        else:
            print(f"❌ 保存失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 错误详情: {error_data}")
            except:
                print(f"📝 响应内容: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 无法连接到服务器")
        print("💡 请确保后端服务器正在运行 (http://localhost:8082)")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

def test_health_check():
    """测试服务器健康状态"""
    print("=" * 60)
    print("🏥 测试服务器健康状态")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/health"
    
    try:
        print(f"📡 请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务器运行正常!")
            print(f"📝 状态: {data.get('status', 'N/A')}")
            print(f"⏰ 时间: {data.get('timestamp', 'N/A')}")
            print(f"🔧 版本: {data.get('version', 'N/A')}")
            return True
        else:
            print(f"❌ 服务器状态异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请确保后端服务器正在运行 (http://localhost:8082)")
        return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Markdown API 测试脚本")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 目标任务: {TASK_ID}")
    
    # 1. 健康检查
    if not test_health_check():
        print("\n❌ 服务器不可用，退出测试")
        sys.exit(1)
    
    print("\n" + "="*80)
    
    # 2. 先获取当前内容
    print("第一步: 获取当前Markdown内容")
    test_get_markdown()
    
    print("\n" + "="*80)
    
    # 3. 保存测试内容
    print("第二步: 保存测试Markdown内容")
    test_save_markdown()
    
    print("\n" + "="*80)
    
    # 4. 再次获取验证
    print("第三步: 验证保存结果")
    test_get_markdown()
    
    print("\n" + "="*80)
    print("🎉 测试完成!")
    print("💡 如果看到保存成功的消息，说明API工作正常")

if __name__ == "__main__":
    main() 