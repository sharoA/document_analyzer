#!/usr/bin/env python3
"""
智能文档分析系统启动脚本
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def check_redis():
    """检查Redis是否运行"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        print("✅ Redis服务正在运行")
        return True
    except Exception as e:
        print(f"❌ Redis服务未运行: {e}")
        print("请先启动Redis服务")
        return False

def start_api_server():
    """启动API服务器"""
    print("🚀 启动API服务器 (端口 8082)...")
    try:
        # 切换到项目根目录
        os.chdir(Path(__file__).parent)
        
        # 启动API服务器
        process = subprocess.Popen([
            sys.executable, '-m', 'src.apis.enhanced_api'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"❌ API服务器启动失败: {e}")
        return None

def start_frontend():
    """启动前端开发服务器"""
    print("🌐 启动前端服务器 (端口 3000)...")
    try:
        # 切换到frontend目录
        frontend_dir = Path(__file__).parent / "frontend"
        
        # 启动前端服务器
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"❌ 前端服务器启动失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 智能文档分析系统启动")
    print("=" * 50)
    
    # 检查Redis
    if not check_redis():
        print("\n请先启动Redis服务，然后重新运行此脚本")
        sys.exit(1)
    
    processes = []
    
    try:
        # 启动API服务器
        api_process = start_api_server()
        if api_process:
            processes.append(("API服务器", api_process))
            time.sleep(3)  # 等待API服务器启动
        
        # 启动前端服务器
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("前端服务器", frontend_process))
        
        if not processes:
            print("❌ 没有成功启动任何服务")
            sys.exit(1)
        
        print("\n✅ 系统启动完成!")
        print("=" * 50)
        print("📡 API服务器: http://localhost:8082")
        print("🌐 前端界面: http://localhost:3000")
        print("❤️  健康检查: http://localhost:8082/api/v2/health")
        print("=" * 50)
        print("按 Ctrl+C 停止所有服务")
        
        # 等待用户中断
        try:
            while True:
                time.sleep(1)
                # 检查进程是否还在运行
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} 已停止")
        except KeyboardInterrupt:
            print("\n👋 正在停止所有服务...")
    
    finally:
        # 停止所有进程
        for name, process in processes:
            try:
                print(f"停止 {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"强制停止 {name}...")
                process.kill()
            except Exception as e:
                print(f"停止 {name} 时出错: {e}")
        
        print("✅ 所有服务已停止")

if __name__ == "__main__":
    main() 