#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从src目录启动analyDesign API服务器
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并启动API服务器
from src.api_server import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 analyDesign API服务器启动中...")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:8081")
    print(f"🔗 API文档: http://localhost:8081")
    print(f"💬 聊天接口: http://localhost:8081/api/chat")
    print(f"❤️  健康检查: http://localhost:8081/api/health")
    print("=" * 60)
    print("⚠️  请确保已配置火山引擎API密钥")
    print("📝 在src/config.py中设置您的火山引擎配置")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=8081,
        debug=True,
        threaded=True
    ) 