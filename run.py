#!/usr/bin/env python3
"""
analyDesign 后端服务启动脚本
支持多种启动模式
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

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
    config_file = Path("src/utils/volcengine_client.py")
    if not config_file.exists():
        print("⚠️ 配置文件不存在: src/utils/volcengine_client.py")
        print("请检查配置文件")
    
    print("✅ 环境检查完成")
    return True

def check_dependencies():
    """检查关键依赖"""
    try:
        import flask
        import flask_socketio
        import flask_cors
        import requests
        print("✅ 关键依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def start_api_server():
    """启动API服务器"""
    print("🚀 启动API服务器...")
    print("📡 服务地址: http://localhost:8082")
    print("💬 聊天接口: http://localhost:8082/api/chat")
    print("📁 文件上传: http://localhost:8082/api/file/upload")
    print("❤️  健康检查: http://localhost:8082/api/health")
    
    try:
        # 切换到src/apis目录并启动服务器
        os.chdir('src/apis')
        subprocess.run([sys.executable, 'enhanced_api.py'])
    except KeyboardInterrupt:
        print("\n👋 API服务器已停止")
    except Exception as e:
        print(f"❌ API服务器启动失败: {e}")
    finally:
        # 切换回原目录
        os.chdir('../..')

def start_websocket_server():
    """启动WebSocket服务器"""
    print("🔌 启动WebSocket服务器...")
    print("🔌 WebSocket地址: ws://localhost:8081/socket.io/")
    print("📡 服务地址: http://localhost:8081")
    
    try:
        original_dir = os.getcwd()
        os.chdir('src/websockets')
        subprocess.run([sys.executable, 'websocket_server.py'])
    except KeyboardInterrupt:
        print("\n👋 WebSocket服务器已停止")
    except Exception as e:
        print(f"❌ WebSocket服务器启动失败: {e}")
    finally:
        os.chdir(original_dir)

def start_full_service():
    """启动完整服务（API + WebSocket）"""
    print("🚀 启动完整服务...")
    print("=" * 60)
    print("📡 API服务器: http://localhost:8082")
    print("🔌 WebSocket服务器: ws://localhost:8081/socket.io/")
    print("=" * 60)
    
    # 使用线程池同时启动两个服务器
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            # 启动API服务器
            def start_api():
                try:
                    subprocess.run([sys.executable, 'run_api_server.py'])
                except Exception as e:
                    print(f"API服务器启动错误: {e}")
            
            api_future = executor.submit(start_api)
            
            # 稍等一下再启动WebSocket服务器
            time.sleep(2)
            
            # 启动WebSocket服务器
            def start_websocket():
                try:
                    subprocess.run([sys.executable, 'src/websockets/websocket_server.py'])
                except Exception as e:
                    print(f"WebSocket服务器启动错误: {e}")
            
            ws_future = executor.submit(start_websocket)
            
            print("✅ 两个服务器都已启动")
            print("按 Ctrl+C 停止所有服务")
            
            # 保持主线程运行，等待键盘中断
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 正在停止所有服务...")
                # 让子进程自己处理停止信号
            
        except KeyboardInterrupt:
            print("\n👋 所有服务器已停止")
        except Exception as e:
            print(f"❌ 服务启动失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='analyDesign 后端服务启动器')
    parser.add_argument(
        '--mode', 
        choices=['api', 'websocket', 'full'], 
        default='full',
        help='启动模式: api(仅API服务器), websocket(仅WebSocket服务器), full(完整服务)'
    )
    
    args = parser.parse_args()
    
    print("🚀 analyDesign 后端服务启动")
    print("=" * 50)
    print(f"启动模式: {args.mode}")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    print("=" * 50)
    
    # 根据模式启动相应服务
    if args.mode == 'api':
        start_api_server()
    elif args.mode == 'websocket':
        start_websocket_server()
    elif args.mode == 'full':
        start_full_service()
    
    print("=" * 50)
    print("⚠️  请确保已配置火山引擎API密钥")
    print("📝 在src/config.py中设置您的火山引擎配置")
    print("=" * 50)

if __name__ == "__main__":
    main() 