#!/usr/bin/env python3
"""
简单的火山引擎测试脚本
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_volcengine_config():
    """测试火山引擎配置"""
    print("🌋 火山引擎配置测试")
    print("=" * 40)
    
    # 检查环境变量
    api_key = os.getenv("VOLCENGINE_API_KEY")
    model_id = os.getenv("VOLCENGINE_MODEL_ID")
    base_url = os.getenv("VOLCENGINE_BASE_URL")
    
    print(f"API密钥: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
    print(f"模型ID: {model_id}")
    print(f"基础URL: {base_url}")
    
    if not api_key:
        print("❌ API密钥未设置")
        return False
    
    if not model_id:
        print("❌ 模型ID未设置")
        return False
    
    print("✅ 配置检查通过")
    return True

def test_volcengine_api():
    """测试火山引擎API"""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("VOLCENGINE_API_KEY")
        model_id = os.getenv("VOLCENGINE_MODEL_ID", "ep-20250528194304-wbvcf")
        base_url = os.getenv("VOLCENGINE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=30  # 设置较短的超时时间
        )
        
        print("\n📤 测试API调用...")
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "你好"}
            ],
            max_tokens=50
        )
        
        response = completion.choices[0].message.content
        print(f"✅ API调用成功: {response}")
        return True
        
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 火山引擎简单测试")
    print("=" * 50)
    
    # 测试配置
    config_ok = test_volcengine_config()
    
    if config_ok:
        # 测试API
        api_ok = test_volcengine_api()
        
        if api_ok:
            print("\n🎉 所有测试通过！火山引擎配置正确")
        else:
            print("\n⚠️ API测试失败，请检查网络连接")
    else:
        print("\n❌ 配置测试失败，请检查环境变量设置")

if __name__ == "__main__":
    main() 