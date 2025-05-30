#!/usr/bin/env python3
"""
大模型连接测试脚本
测试火山引擎、OpenAI、DeepSeek等API连接
"""

import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI包未安装，请运行: pip install openai")
    sys.exit(1)

def test_volcengine_api():
    """测试火山引擎API"""
    print("\n🌋 测试火山引擎API")
    print("-" * 40)
    
    # 从环境变量获取API密钥
    api_key = os.getenv("VOLCENGINE_API_KEY")
    model_id = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
    
    if not api_key:
        print("❌ 未设置VOLCENGINE_API_KEY环境变量")
        print("💡 请在.env文件中设置: VOLCENGINE_API_KEY=你的API密钥")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
        
        # 非流式请求测试
        print("📤 测试非流式请求...")
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": "请简单介绍一下自己"},
            ],
        )
        
        response = completion.choices[0].message.content
        print(f"✅ 非流式请求成功: {response[:50]}...")
        
        # 流式请求测试
        print("\n📤 测试流式请求...")
        stream = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "你是人工智能助手"},
                {"role": "user", "content": "数到5"},
            ],
            stream=True
        )
        
        print("✅ 流式响应: ", end="")
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 火山引擎API测试失败: {e}")
        return False

def test_openai_api():
    """测试OpenAI API"""
    print("\n🤖 测试OpenAI API")
    print("-" * 40)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ 未设置OPENAI_API_KEY环境变量")
        print("💡 请在.env文件中设置: OPENAI_API_KEY=你的API密钥")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, please introduce yourself briefly"}
            ],
            max_tokens=100
        )
        
        response = completion.choices[0].message.content
        print(f"✅ OpenAI API测试成功: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API测试失败: {e}")
        return False

def test_deepseek_api():
    """测试DeepSeek API"""
    print("\n🧠 测试DeepSeek API")
    print("-" * 40)
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ 未设置DEEPSEEK_API_KEY环境变量")
        print("💡 请在.env文件中设置: DEEPSEEK_API_KEY=你的API密钥")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "你好，请简单介绍一下自己"}
            ],
            max_tokens=100
        )
        
        response = completion.choices[0].message.content
        print(f"✅ DeepSeek API测试成功: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API测试失败: {e}")
        return False

def test_openai_client_component():
    """测试OpenAI客户端组件"""
    print("\n🔧 测试OpenAI客户端组件")
    print("-" * 40)
    
    try:
        from src.openai_client import api_manager, chat_with_ai
        
        clients = api_manager.list_clients()
        print(f"📋 可用客户端: {clients}")
        
        if not clients:
            print("❌ 没有可用的客户端")
            return False
        
        # 测试聊天功能
        response = chat_with_ai([
            {"role": "user", "content": "你好"}
        ])
        print(f"✅ 组件测试成功: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 大模型连接测试")
    print("=" * 50)
    
    # 检查.env文件
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ 找到配置文件: {env_file}")
        # 加载.env文件
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ 环境变量加载成功")
        except ImportError:
            print("⚠️  python-dotenv未安装，手动检查环境变量")
    else:
        print(f"⚠️  未找到配置文件: {env_file}")
    
    # 运行测试
    tests = [
        ("火山引擎API", test_volcengine_api),
        ("OpenAI API", test_openai_api),
        ("DeepSeek API", test_deepseek_api),
        ("OpenAI客户端组件", test_openai_client_component),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name}测试异常: {e}")
            results[name] = False
    
    # 总结结果
    print("\n📊 测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == 0:
        print("\n💡 建议:")
        print("1. 检查.env文件中的API密钥设置")
        print("2. 确保网络连接正常")
        print("3. 验证API密钥的有效性")

if __name__ == "__main__":
    main()