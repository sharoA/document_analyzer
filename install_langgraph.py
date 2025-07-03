#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能编码智能体依赖安装脚本
安装 LangGraph 和相关依赖
"""

import subprocess
import sys
import os

def install_package(package_name):
    """安装Python包"""
    try:
        print(f"📦 正在安装 {package_name}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package_name
        ], check=True, capture_output=True, text=True)
        print(f"✅ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package_name} 安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def main():
    """主安装流程"""
    print("🚀 开始安装智能编码智能体依赖...")
    
    # 要安装的包列表
    packages = [
        "langgraph",
        "langchain-core", 
        "langchain-openai",
        "langchain-community",
        "sqlite3"  # Python内置，但确保可用
    ]
    
    # 检查当前Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ LangGraph 需要 Python 3.8 或更高版本")
        return False
    
    # 安装包
    failed_packages = []
    for package in packages:
        if package == "sqlite3":
            # sqlite3 是Python内置模块
            try:
                import sqlite3
                print(f"✅ {package} 可用")
            except ImportError:
                print(f"❌ {package} 不可用")
                failed_packages.append(package)
        else:
            if not install_package(package):
                failed_packages.append(package)
    
    # 安装结果报告
    if failed_packages:
        print(f"\n❌ 以下包安装失败: {', '.join(failed_packages)}")
        print("请手动安装这些包或检查网络连接")
        return False
    else:
        print("\n🎉 所有依赖安装成功！")
        print("\n📚 使用说明:")
        print("1. 导入智能编码智能体:")
        print("   from src.corder_integration.smart_coder_agent import SmartCoderAgent")
        print("\n2. 创建智能体实例:")
        print("   agent = SmartCoderAgent()")
        print("\n3. 执行智能工作流:")
        print("   result = await agent.execute_smart_workflow(document_content, project_name)")
        
        # 验证安装
        try:
            import langgraph
            from langchain_core.messages import BaseMessage
            print(f"\n✅ LangGraph 版本: {langgraph.__version__ if hasattr(langgraph, '__version__') else '未知'}")
        except ImportError as e:
            print(f"\n⚠️ 导入验证失败: {e}")
        
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 