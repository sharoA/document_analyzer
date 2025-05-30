#!/usr/bin/env python3
"""
analyDesign 后端服务启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """检查环境配置"""
    # 检查虚拟环境
    if not Path("analyDesign_env/Scripts/activate.bat").exists():
        print("❌ 虚拟环境不存在")
        print("请先运行 setup_env.ps1 创建虚拟环境")
        return False
    
    # 检查必要的目录
    directories = ["uploads", "templates", "outputs", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 检查配置文件
    config_file = Path("src/simple_config.py")
    if not config_file.exists():
        print("⚠️ 配置文件不存在: src/simple_config.py")
        print("请检查配置文件")
    
    print("✅ 环境检查完成")
    return True

def check_dependencies():
    """检查关键依赖"""
    try:
        import flask
        import flask_socketio
        import requests
        print("✅ 关键依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("🚀 analyDesign 后端服务启动")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 启动集成服务器
    print("🚀 启动集成服务器...")
    print("📡 服务地址: http://localhost:8081")
    print("🔌 WebSocket: ws://localhost:8081/socket.io/")
    print("💬 HTTP聊天: http://localhost:8081/api/chat")
    print("❤️  健康检查: http://localhost:8081/api/health")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "start_integrated_server.py"])
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查配置和依赖是否正确安装")

if __name__ == "__main__":
    main() 