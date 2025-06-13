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
    venv_python = Path("analyDesign_env/Scripts/python.exe")
    if not venv_python.exists():
        print("❌ 虚拟环境不存在")
        print("请先运行 setup_env.ps1 创建虚拟环境")
        return False, None
    
    # 检查当前是否已在虚拟环境中
    current_python = Path(sys.executable).resolve()
    venv_python_resolved = venv_python.resolve()
    
    if current_python != venv_python_resolved:
        print("⚠️ 当前未使用虚拟环境")
        print(f"当前Python: {current_python}")
        print(f"虚拟环境Python: {venv_python_resolved}")
        print("🔄 将自动使用虚拟环境Python执行")
        return True, str(venv_python_resolved)
    else:
        print("✅ 已在虚拟环境中")
    
    # 检查必要的目录
    directories = ["uploads", "templates", "outputs", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 确保uploads子目录存在
    upload_subdirs = ["uploads/temp", "uploads/analysis_results", "uploads/cache"]
    for directory in upload_subdirs:
        Path(directory).mkdir(exist_ok=True)
    
    # 检查配置文件
    config_file = Path("src/resource/config.py")
    if not config_file.exists():
        print("⚠️ 配置文件不存在: src/config.py")
        print("请检查配置文件")
    
    print("✅ 环境检查完成")
    return True, None

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
    print("=" * 60)
    
    try:
        # 检查API服务器脚本
        api_script = Path("src/apis/api_server.py")
        if not api_script.exists():
            print(f"❌ API服务器脚本不存在: {api_script}")
            return
        
        # 优先使用虚拟环境中的Python
        venv_python = Path("analyDesign_env/Scripts/python.exe")
        if venv_python.exists():
            python_executable = str(venv_python)
            print(f"✅ 使用虚拟环境Python: {python_executable}")
        else:
            python_executable = sys.executable
            print(f"⚠️ 使用系统Python: {python_executable}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path.cwd())
        
        print("🔥 正在启动服务器...")
        subprocess.run([python_executable, str(api_script)], env=env, cwd=str(Path.cwd()))
    except KeyboardInterrupt:
        print("\n👋 API服务器已停止")
    except Exception as e:
        print(f"❌ API服务器启动失败: {e}")
        import traceback
        traceback.print_exc()

def start_websocket_server():
    """启动WebSocket服务器"""
    print("🔌 启动WebSocket服务器...")
    print("🔌 WebSocket地址: ws://localhost:8081/socket.io/")
    print("📡 服务地址: http://localhost:8081")
    print("=" * 60)
    
    try:
        ws_script = Path("src/websockets/websocket_server.py")
        if not ws_script.exists():
            print(f"❌ WebSocket服务器脚本不存在: {ws_script}")
            return
        
        # 优先使用虚拟环境中的Python
        venv_python = Path("analyDesign_env/Scripts/python.exe")
        if venv_python.exists():
            python_executable = str(venv_python)
            print(f"✅ 使用虚拟环境Python: {python_executable}")
        else:
            python_executable = sys.executable
            print(f"⚠️ 使用系统Python: {python_executable}")
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path.cwd())
        
        print("🔥 正在启动WebSocket服务器...")
        subprocess.run([python_executable, str(ws_script)], env=env, cwd=str(Path.cwd()))
    except KeyboardInterrupt:
        print("\n👋 WebSocket服务器已停止")
    except Exception as e:
        print(f"❌ WebSocket服务器启动失败: {e}")
        import traceback
        traceback.print_exc()

def start_full_service():
    """启动完整服务（API + WebSocket）"""
    print("🚀 启动完整服务...")
    print("=" * 60)
    print("📡 API服务器: http://localhost:8082")
    print("🔌 WebSocket服务器: ws://localhost:8081/socket.io/")
    print("=" * 60)
    
    # 检查脚本是否存在
    api_script = Path("src/apis/api_server.py")
    ws_script = Path("src/websockets/websocket_server.py")
    
    if not api_script.exists():
        print(f"❌ API服务器脚本不存在: {api_script}")
        return
    
    if not ws_script.exists():
        print(f"❌ WebSocket服务器脚本不存在: {ws_script}")
        return
    
    # 使用线程池同时启动两个服务器
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path.cwd())
            
            # 启动API服务器
            def start_api():
                subprocess.run([sys.executable, str(api_script)], env=env, cwd=str(Path.cwd()))
            
            api_future = executor.submit(start_api)
            
            # 稍等一下再启动WebSocket服务器
            time.sleep(2)
            
            # 启动WebSocket服务器
            def start_ws():
                subprocess.run([sys.executable, str(ws_script)], env=env, cwd=str(Path.cwd()))
            
            ws_future = executor.submit(start_ws)
            
            print("✅ 两个服务器都已启动")
            print("按 Ctrl+C 停止所有服务")
            
            # 等待任一服务器结束
            api_future.result()
            ws_future.result()
            
        except KeyboardInterrupt:
            print("\n👋 所有服务器已停止")
        except Exception as e:
            print(f"❌ 服务启动失败: {e}")
            import traceback
            traceback.print_exc()

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
    env_ok, venv_python = check_environment()
    if not env_ok:
        sys.exit(1)
    
    # 如果需要切换到虚拟环境，重新启动脚本
    if venv_python:
        print("🔄 使用虚拟环境重新启动...")
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path.cwd())
        
        # 构建新的命令行参数
        new_args = [venv_python, __file__, "--mode", args.mode]
        subprocess.run(new_args, env=env, cwd=str(Path.cwd()))
        return
    
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