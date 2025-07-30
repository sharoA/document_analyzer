#!/usr/bin/env python3
"""
测试V2分析接口的脚本
直接调用API接口，查看详细的错误信息
"""

import requests
import json
import time
import sys
import base64

def test_v2_analysis():
    """测试V2分析接口"""
    
    # 测试内容
    test_content = """# 用户管理系统需求文档

## 项目背景
本项目旨在构建一个用户管理系统，支持用户注册、登录、权限管理等功能。

## 功能需求

### 1. 用户注册
- 用户可以通过邮箱注册账号
- 需要验证邮箱有效性
- 密码需要加密存储

### 2. 用户登录
- 支持邮箱登录
- 登录失败3次后锁定15分钟

### 3. 权限管理
- 支持角色权限控制
- 管理员可以分配用户权限

## 技术要求
- 使用Spring Boot框架
- 数据库使用MySQL
- 缓存使用Redis"""
    
    # 将内容编码为base64
    content_bytes = test_content.encode('utf-8')
    content_base64 = base64.b64encode(content_bytes).decode('ascii')
    
    # 测试数据
    test_data = {
        "file_info": {
            "name": "测试需求文档.txt",
            "content": content_base64,  # 使用base64编码的内容
            "type": "text/plain"
        }
    }
    
    # API地址
    base_url = "http://localhost:8082"
    start_url = f"{base_url}/api/v2/analysis/start"
    
    print("🚀 开始测试V2分析接口...")
    print(f"请求URL: {start_url}")
    print(f"请求数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print("=" * 60)
    
    try:
        # 发送启动分析请求
        print("📤 发送启动分析请求...")
        response = requests.post(
            start_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
            
        # 解析响应
        try:
            result = response.json()
            print(f"✅ 启动分析成功")
            print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 获取任务ID
            task_id = result.get("task_id")
            if not task_id:
                print("❌ 未获取到任务ID")
                return
                
            print(f"📋 任务ID: {task_id}")
            
            # 轮询检查任务状态
            progress_url = f"{base_url}/api/v2/analysis/progress/{task_id}"
            print(f"\n🔄 开始轮询任务进度: {progress_url}")
            
            max_attempts = 100  # 最多轮询100次
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                time.sleep(3)  # 每3秒检查一次
                
                try:
                    progress_response = requests.get(progress_url, timeout=10)
                    
                    if progress_response.status_code != 200:
                        print(f"❌ 进度查询失败，状态码: {progress_response.status_code}")
                        print(f"响应内容: {progress_response.text}")
                        break
                    
                    progress_data = progress_response.json()
                    status = progress_data.get("status", "")
                    progress = progress_data.get("progress", 0)
                    message = progress_data.get("message", "")
                    
                    print(f"[{attempt:2d}] 进度: {progress}%, 状态: {status}, 消息: {message}")
                    
                    # 检查是否完成
                    if status in ["completed", "fully_completed"]:
                        print(f"🎉 任务完成! 最终状态: {status}")
                        print(f"最终响应: {json.dumps(progress_data, indent=2, ensure_ascii=False)}")
                        
                        # 测试获取表单数据
                        form_url = f"{base_url}/api/file/design-form/{task_id}"
                        print(f"\n📋 测试获取表单数据: {form_url}")
                        
                        form_response = requests.get(form_url, timeout=10)
                        print(f"表单数据响应状态码: {form_response.status_code}")
                        
                        if form_response.status_code == 200:
                            form_data = form_response.json()
                            print(f"✅ 表单数据获取成功")
                            print(f"表单数据摘要: 项目名称={form_data.get('project_name')}, 服务数量={form_data.get('service_numbers')}")
                        else:
                            print(f"❌ 表单数据获取失败: {form_response.text}")
                        
                        return
                        
                    elif status == "failed":
                        print(f"❌ 任务失败! 状态: {status}")
                        print(f"错误信息: {progress_data.get('error', '未知错误')}")
                        print(f"完整响应: {json.dumps(progress_data, indent=2, ensure_ascii=False)}")
                        return
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ 进度查询请求异常: {e}")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ 进度响应JSON解析失败: {e}")
                    print(f"原始响应: {progress_response.text}")
                    break
            
            print(f"⏰ 轮询超时，已尝试 {max_attempts} 次")
            
        except json.JSONDecodeError as e:
            print(f"❌ 响应JSON解析失败: {e}")
            print(f"原始响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保API服务器正在运行在 http://localhost:8082")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()

def check_server_status():
    """检查服务器状态"""
    try:
        response = requests.get("http://localhost:8082/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"⚠️ 服务器响应异常，状态码: {response.status_code}")
    except:
        print("❌ 无法连接到服务器，请确保API服务器正在运行")
        return False
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("V2分析接口测试脚本")
    print("=" * 60)
    
    # 检查服务器状态
    if not check_server_status():
        print("\n请先启动API服务器:")
        print("cd /Users/renyu/Documents/ai_project/document_analyzer")
        print("python -m src.apis.api_server")
        sys.exit(1)
    
    # 运行测试
    test_v2_analysis()
    print("\n测试完成")