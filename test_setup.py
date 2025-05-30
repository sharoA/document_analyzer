#!/usr/bin/env python3
"""
系统配置测试脚本
用于验证各个组件是否正确配置
"""

import sys
import os
from pathlib import Path

def test_imports():
    """测试必要的包导入"""
    print("🔍 测试包导入...")
    
    try:
        import streamlit
        print("✅ Streamlit")
    except ImportError:
        print("❌ Streamlit 未安装")
        return False
    
    try:
        import langchain
        print("✅ LangChain")
    except ImportError:
        print("❌ LangChain 未安装")
        return False
    
    try:
        import weaviate
        print("✅ Weaviate Client")
    except ImportError:
        print("❌ Weaviate Client 未安装")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy")
    except ImportError:
        print("❌ SQLAlchemy 未安装")
        return False
    
    try:
        import easyocr
        print("✅ EasyOCR")
    except ImportError:
        print("❌ EasyOCR 未安装")
        return False
    
    return True

def test_directories():
    """测试目录结构"""
    print("\n📁 测试目录结构...")
    
    required_dirs = ["src", "templates", "uploads", "outputs"]
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ 不存在，正在创建...")
            path.mkdir(exist_ok=True)
            print(f"✅ {directory}/ 已创建")
    
    return True

def test_config():
    """测试配置文件"""
    print("\n⚙️ 测试配置...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 文件存在")
    else:
        print("⚠️ .env 文件不存在，请复制 .env.example 并配置")
    
    try:
        from src.config import settings
        print("✅ 配置加载成功")
        print(f"   公司名称: {settings.COMPANY_NAME}")
        print(f"   产品线: {settings.PRODUCT_LINE}")
        
        if settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_KEY != "your_deepseek_api_key_here":
            print("✅ DeepSeek API Key 已配置")
        else:
            print("⚠️ DeepSeek API Key 未配置")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_templates():
    """测试模板文件"""
    print("\n📄 测试模板文件...")
    
    template_files = [
        "templates/backend_design_template.md",
        "templates/frontend_design_template.md"
    ]
    
    for template_file in template_files:
        path = Path(template_file)
        if path.exists():
            print(f"✅ {template_file}")
        else:
            print(f"❌ {template_file} 不存在")
    
    return True

def main():
    """主测试函数"""
    print("🤖 智能需求分析系统 - 配置测试")
    print("=" * 50)
    
    tests = [
        ("包导入测试", test_imports),
        ("目录结构测试", test_directories),
        ("配置文件测试", test_config),
        ("模板文件测试", test_templates)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！系统配置正确。")
        print("💡 现在可以运行 'python run.py' 启动系统")
    else:
        print("⚠️ 部分测试失败，请检查配置")
        print("💡 请参考 README.md 进行正确配置")

if __name__ == "__main__":
    main() 