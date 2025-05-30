#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动analyDesign集成服务器
同时支持HTTP API和WebSocket
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并启动集成服务器
from src.integrated_server import socketio, app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 analyDesign 集成服务器启动中...")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:8081")
    print(f"🔗 API文档: http://localhost:8081")
    print(f"💬 HTTP聊天: http://localhost:8081/api/chat")
    print(f"🔌 WebSocket: ws://localhost:8081/socket.io/")
    print(f"❤️  健康检查: http://localhost:8081/api/health")
    print("=" * 60)
    print("✨ 功能特性:")
    print("   • HTTP RESTful API")
    print("   • WebSocket 实时通信")
    print("   • 火山引擎 AI 集成")
    print("   • 会话管理")
    print("   • CORS 跨域支持")
    print("=" * 60)
    print("⚠️  请确保已配置火山引擎API密钥")
    print("📝 在src/simple_config.py中设置您的火山引擎配置")
    print("=" * 60)
    
    # 使用SocketIO运行应用
    socketio.run(
        app,
        host='0.0.0.0',
        port=8081,
        debug=True,
        allow_unsafe_werkzeug=True
    ) 