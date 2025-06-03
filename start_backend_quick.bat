@echo off
chcp 65001 >nul
title analyDesign 后端快速启动

echo.
echo ========================================
echo 🚀 analyDesign 后端快速启动
echo ========================================
echo.

:: 检查虚拟环境
if not exist "analyDesign_env\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在！
    echo 请先运行 setup_env.ps1 创建虚拟环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call analyDesign_env\Scripts\activate.bat

:: 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python环境异常！
    echo 请检查虚拟环境是否正确安装
    pause
    exit /b 1
)

:: 启动集成服务器
echo.
echo 🚀 启动集成服务器 (HTTP API + WebSocket)...
echo ========================================
echo 📡 服务地址: http://localhost:8081
echo 🔗 API文档: http://localhost:8081
echo 💬 HTTP聊天: http://localhost:8081/api/chat
echo 🔌 WebSocket: ws://localhost:8081/socket.io/
echo ❤️  健康检查: http://localhost:8081/api/health
echo ========================================
echo.
echo ⚠️  按 Ctrl+C 停止服务器
echo.

python start_integrated_server.py

echo.
echo 👋 服务器已停止
pause 