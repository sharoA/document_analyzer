#!/usr/bin/env python3
"""
API服务器启动脚本
直接启动enhanced_api，避免模块导入问题
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    # 直接导入并运行
    from src.apis.enhanced_api import app
    
    print("🚀 启动智能文档分析API服务器...")
    print("📡 服务地址: http://localhost:8082")
    print("❤️  健康检查: http://localhost:8082/api/v2/health")
    print("按 Ctrl+C 停止服务器")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=8082, debug=True)
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请检查依赖是否正确安装")
except Exception as e:
    print(f"❌ 启动失败: {e}") 