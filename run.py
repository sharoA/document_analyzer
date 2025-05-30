#!/usr/bin/env python3
"""
智能需求分析与设计文档生成系统启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """检查环境配置"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 未找到 .env 文件")
        print("请复制 .env.example 为 .env 并配置相关参数")
        return False
    
    # 检查必要的目录
    directories = ["uploads", "templates", "outputs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ 环境检查完成")
    return True

def start_weaviate():
    """启动Weaviate服务（如果需要）"""
    try:
        # 检查Docker是否可用
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ Docker未安装，请手动启动Weaviate服务")
            return
        
        # 检查Weaviate是否已运行
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if "weaviate" in result.stdout:
            print("✅ Weaviate服务已运行")
            return
        
        print("🚀 启动Weaviate服务...")
        subprocess.run([
            "docker", "run", "-d",
            "-p", "8080:8080",
            "--name", "weaviate",
            "semitechnologies/weaviate:1.19.6"
        ])
        print("✅ Weaviate服务启动完成")
        
    except Exception as e:
        print(f"⚠️ 启动Weaviate失败: {e}")
        print("请手动启动Weaviate服务")

def main():
    """主函数"""
    print("🤖 智能需求分析与设计文档生成系统")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 启动Weaviate（可选）
    start_weaviate()
    
    # 启动Streamlit应用
    print("🚀 启动Web应用...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/enhanced_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main() 