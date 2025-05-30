@echo off
chcp 65001 >nul
title analyDesign 后端服务器启动器

echo.
echo ========================================
echo 🚀 analyDesign 后端服务器启动器
echo ========================================
echo.

:: 检查虚拟环境是否存在
if not exist "analyDesign_env\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在！
    echo 请先运行 setup_env.ps1 创建虚拟环境
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔧 激活虚拟环境...
call analyDesign_env\Scripts\activate.bat

:: 检查Python版本
echo.
echo 📋 环境信息:
python --version
echo.

:menu
:: 显示启动选项菜单
echo ========================================
echo 请选择启动方式:
echo ========================================
echo [1] 集成服务器 (推荐) - HTTP API + WebSocket
echo [2] 纯API服务器 - 仅HTTP API
echo [3] 简单HTTP服务器 - 静态文件服务
echo [4] 退出
echo ========================================
echo.

set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto integrated_server
if "%choice%"=="2" goto api_server
if "%choice%"=="3" goto simple_server
if "%choice%"=="4" goto exit
echo 无效选项，请重新选择
goto menu

:integrated_server
echo.
echo 🚀 启动集成服务器...
echo ========================================
echo 📡 服务地址: http://localhost:8081
echo 🔗 API文档: http://localhost:8081
echo 💬 HTTP聊天: http://localhost:8081/api/chat
echo 🔌 WebSocket: ws://localhost:8081/socket.io/
echo ❤️  健康检查: http://localhost:8081/api/health
echo ========================================
echo 💡 提示: 前端请连接到 ws://localhost:8081
echo.
python start_integrated_server.py
goto end

:api_server
echo.
echo 🚀 启动API服务器...
echo ========================================
echo 📡 服务地址: http://localhost:8080
echo 🔗 API文档: http://localhost:8080/docs
echo ========================================
echo 💡 提示: 仅提供HTTP API，不支持WebSocket
echo.
python start_api_server.py
goto end

:simple_server
echo.
echo 🚀 启动简单HTTP服务器...
echo ========================================
echo 📡 服务地址: http://localhost:8000
echo ========================================
echo 💡 提示: 仅用于静态文件服务和测试
echo.
python simple_server.py
goto end

:exit
echo 👋 退出启动器
goto end

:end
echo.
echo 按任意键退出...
pause >nul 