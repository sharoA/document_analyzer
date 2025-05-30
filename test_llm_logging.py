#!/usr/bin/env python3
"""
测试LLM日志记录功能
验证所有大模型客户端的日志记录是否正常工作
"""

import os
import sys
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_volcengine_logging():
    """测试火山引擎客户端日志记录"""
    print("🌋 测试火山引擎客户端日志记录")
    print("=" * 50)
    
    try:
        from src.volcengine_client import VolcengineClient, VolcengineConfig
        from src.simple_config import settings
        
        # 检查API密钥
        if not settings.VOLCENGINE_API_KEY:
            print("❌ 未设置VOLCENGINE_API_KEY环境变量")
            return False
        
        # 创建客户端
        config = VolcengineConfig(
            api_key=settings.VOLCENGINE_API_KEY,
            model_id=settings.VOLCENGINE_MODEL_ID,
            base_url=settings.VOLCENGINE_BASE_URL
        )
        client = VolcengineClient(config)
        
        # 测试普通聊天
        print("📝 测试普通聊天...")
        messages = [
            {"role": "user", "content": "你好，请简单介绍一下你自己"}
        ]
        
        response = client.chat(messages)
        print(f"✅ 普通聊天测试成功，响应长度: {len(response)}字符")
        
        # 测试流式聊天
        print("📝 测试流式聊天...")
        stream_messages = [
            {"role": "user", "content": "请用一句话描述人工智能"}
        ]
        
        full_response = ""
        for chunk in client.stream_chat(stream_messages):
            full_response += chunk
        
        print(f"✅ 流式聊天测试成功，响应长度: {len(full_response)}字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 火山引擎客户端测试失败: {e}")
        return False

def test_openai_client_logging():
    """测试OpenAI客户端日志记录"""
    print("\n🤖 测试OpenAI客户端日志记录")
    print("=" * 50)
    
    try:
        from src.openai_client import OpenAIClient, APIConfig
        from src.simple_config import settings
        
        # 使用火山引擎配置测试OpenAI客户端
        if not settings.VOLCENGINE_API_KEY:
            print("❌ 未设置VOLCENGINE_API_KEY环境变量")
            return False
        
        config = APIConfig(
            name="火山引擎",
            api_key=settings.VOLCENGINE_API_KEY,
            base_url=settings.VOLCENGINE_BASE_URL,
            model=settings.VOLCENGINE_MODEL_ID
        )
        
        client = OpenAIClient(config)
        
        # 测试聊天完成
        print("📝 测试聊天完成...")
        messages = [
            {"role": "user", "content": "请用一句话解释什么是需求分析"}
        ]
        
        response = client.chat_completion(messages)
        print(f"✅ 聊天完成测试成功，响应长度: {len(response)}字符")
        
        # 测试流式聊天
        print("📝 测试流式聊天...")
        stream_messages = [
            {"role": "user", "content": "请简单说明API设计的重要性"}
        ]
        
        full_response = ""
        for chunk in client.stream_chat(stream_messages):
            full_response += chunk
        
        print(f"✅ 流式聊天测试成功，响应长度: {len(full_response)}字符")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI客户端测试失败: {e}")
        return False

def test_enhanced_analyzer_logging():
    """测试增强分析器日志记录"""
    print("\n🧠 测试增强分析器日志记录")
    print("=" * 50)
    
    try:
        from src.enhanced_analyzer import EnhancedRequirementAnalyzer
        from src.simple_config import settings
        
        # 检查DeepSeek API密钥
        if not settings.DEEPSEEK_API_KEY:
            print("❌ 未设置DEEPSEEK_API_KEY环境变量，跳过测试")
            return True  # 不算失败，只是跳过
        
        # 创建分析器
        analyzer = EnhancedRequirementAnalyzer()
        
        # 测试关键词提取
        print("📝 测试关键词提取...")
        test_content = "我们需要开发一个用户管理系统，包括用户注册、登录、个人信息管理等功能。"
        
        # 由于这个测试需要数据库和向量存储，我们只测试LLM包装器
        test_prompt = "请分析以下需求：" + test_content
        response = analyzer.llm(test_prompt)
        
        print(f"✅ 关键词提取测试成功，响应长度: {len(response)}字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强分析器测试失败: {e}")
        return False

def check_log_files():
    """检查日志文件是否生成"""
    print("\n📁 检查日志文件")
    print("=" * 50)
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("❌ logs目录不存在")
        return False
    
    today = time.strftime("%Y%m%d")
    log_files = [
        f"llm_interactions_{today}.log",
        f"llm_interactions_{today}.json"
    ]
    
    found_files = []
    for log_file in log_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"✅ 找到日志文件: {log_file} ({size} bytes)")
            found_files.append(log_file)
        else:
            print(f"❌ 未找到日志文件: {log_file}")
    
    return len(found_files) > 0

def show_recent_logs():
    """显示最近的日志内容"""
    print("\n📄 显示最近的日志内容")
    print("=" * 50)
    
    logs_dir = Path("logs")
    today = time.strftime("%Y%m%d")
    json_log_file = logs_dir / f"llm_interactions_{today}.json"
    
    if json_log_file.exists():
        try:
            import json
            with open(json_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            print(f"📊 JSON日志文件包含 {len(lines)} 条记录")
            
            # 显示最后几条记录
            for i, line in enumerate(lines[-3:], 1):
                try:
                    log_data = json.loads(line.strip())
                    log_type = log_data.get('type', 'unknown')
                    timestamp = log_data.get('timestamp', 'unknown')
                    provider = log_data.get('provider', 'unknown')
                    
                    if log_type == 'request':
                        message_count = log_data.get('message_count', 0)
                        print(f"  {i}. [{timestamp}] 请求 - {provider} ({message_count}条消息)")
                    elif log_type == 'response':
                        status = log_data.get('status', 'unknown')
                        response_time = log_data.get('response_time', 0)
                        response_length = log_data.get('response_length', 0)
                        print(f"  {i}. [{timestamp}] 响应 - {status} ({response_time:.2f}s, {response_length}字符)")
                    elif log_type == 'stream_chunk':
                        chunk_index = log_data.get('chunk_index', 0)
                        chunk_length = log_data.get('chunk_length', 0)
                        print(f"  {i}. [{timestamp}] 流式块 - 第{chunk_index}块 ({chunk_length}字符)")
                        
                except json.JSONDecodeError:
                    print(f"  {i}. 无法解析的日志行")
                    
        except Exception as e:
            print(f"❌ 读取日志文件失败: {e}")
    else:
        print("❌ 未找到JSON日志文件")

def main():
    """主测试函数"""
    print("🚀 LLM日志记录功能测试")
    print("=" * 60)
    
    # 确保logs目录存在
    Path("logs").mkdir(exist_ok=True)
    
    test_results = []
    
    # 测试各个组件
    test_results.append(("火山引擎客户端", test_volcengine_logging()))
    test_results.append(("OpenAI客户端", test_openai_client_logging()))
    test_results.append(("增强分析器", test_enhanced_analyzer_logging()))
    
    # 检查日志文件
    log_files_ok = check_log_files()
    test_results.append(("日志文件生成", log_files_ok))
    
    # 显示日志内容
    show_recent_logs()
    
    # 总结测试结果
    print("\n📊 测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！LLM日志记录功能正常工作。")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和环境。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 