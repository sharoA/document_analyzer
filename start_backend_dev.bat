@echo off
chcp 65001 >nul
title analyDesign 后端开发调试

echo.
echo ========================================
echo 🛠️  analyDesign 后端开发调试模式
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

:: 显示环境信息
echo.
echo 📋 开发环境信息:
echo ========================================
python --version
pip --version
echo 当前工作目录: %CD%
echo Python路径: 
python -c "import sys; print('\n'.join(sys.path))"
echo.

:: 检查关键依赖
echo 🔍 检查关键依赖...
python -c "import flask; print('✅ Flask:', flask.__version__)" 2>nul || echo "❌ Flask 未安装"
python -c "import flask_socketio; print('✅ Flask-SocketIO:', flask_socketio.__version__)" 2>nul || echo "❌ Flask-SocketIO 未安装"
python -c "import requests; print('✅ Requests:', requests.__version__)" 2>nul || echo "❌ Requests 未安装"
echo.

:: 检查配置文件
echo 🔍 检查配置文件...
if exist "src\simple_config.py" (
    echo ✅ 配置文件存在: src\simple_config.py
) else (
    echo ❌ 配置文件不存在: src\simple_config.py
)

if exist ".env" (
    echo ✅ 环境变量文件存在: .env
) else (
    echo ⚠️  环境变量文件不存在: .env
)
echo.

:: 设置开发环境变量
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONPATH=%CD%

echo 🚀 启动开发服务器...
echo ========================================
echo 📡 服务地址: http://localhost:8081
echo 🔗 API文档: http://localhost:8081
echo 💬 HTTP聊天: http://localhost:8081/api/chat
echo 🔌 WebSocket: ws://localhost:8081/socket.io/
echo ❤️  健康检查: http://localhost:8081/api/health
echo ========================================
echo 🛠️  开发模式特性:
echo    • 自动重载代码变更
echo    • 详细错误信息
echo    • 调试模式开启
echo ========================================
echo.
echo ⚠️  按 Ctrl+C 停止服务器
echo.

python start_integrated_server.py

echo.
echo 👋 开发服务器已停止
echo.
echo 📝 开发提示:
echo    • 修改代码后服务器会自动重启
echo    • 查看日志文件: logs\
echo    • 配置文件: src\simple_config.py
echo.
pause 