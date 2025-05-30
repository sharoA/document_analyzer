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
        import flask
        print("✅ Flask")
    except ImportError:
        print("❌ Flask 未安装")
        return False
    
    try:
        import flask_socketio
        print("✅ Flask-SocketIO")
    except ImportError:
        print("❌ Flask-SocketIO 未安装")
        return False
    
    try:
        import requests
        print("✅ Requests")
    except ImportError:
        print("❌ Requests 未安装")
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
    
    required_dirs = ["src", "templates", "uploads", "outputs", "logs"]
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
    
    config_file = Path("src/simple_config.py")
    if config_file.exists():
        print("✅ 配置文件存在: src/simple_config.py")
    else:
        print("⚠️ 配置文件不存在: src/simple_config.py")
    
    try:
        from src.simple_config import settings
        print("✅ 配置加载成功")
        
        if hasattr(settings, 'VOLCENGINE_API_KEY') and settings.VOLCENGINE_API_KEY:
            print("✅ 火山引擎 API Key 已配置")
        else:
            print("⚠️ 火山引擎 API Key 未配置")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def test_backend_services():
    """测试后端服务文件"""
    print("\n🚀 测试后端服务文件...")
    
    service_files = [
        "start_integrated_server.py",
        "start_api_server.py",
        "src/integrated_server.py",
        "src/api_server.py"
    ]
    
    for service_file in service_files:
        path = Path(service_file)
        if path.exists():
            print(f"✅ {service_file}")
        else:
            print(f"❌ {service_file} 不存在")
    
    return True

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
    print("🚀 analyDesign 后端服务 - 配置测试")
    print("=" * 50)
    
    tests = [
        ("包导入测试", test_imports),
        ("目录结构测试", test_directories),
        ("配置文件测试", test_config),
        ("后端服务测试", test_backend_services),
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
        print("🎉 所有测试通过！后端服务配置正确。")
        print("💡 现在可以运行以下命令启动服务:")
        print("   • python run.py")
        print("   • start_backend_quick.bat")
        print("   • start_backend.bat")
    else:
        print("⚠️ 部分测试失败，请检查配置")
        print("💡 请参考 后端启动说明.md 进行正确配置")

if __name__ == "__main__":
    main() 