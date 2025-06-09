@echo off
chcp 65001 >nul
title analyDesign 后端服务启动器

echo.
echo ========================================
echo    analyDesign 后端服务启动器
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到PATH
    echo 请先安装Python并添加到系统PATH
    pause
    exit /b 1
)

:: 显示Python版本
echo ✅ Python 版本:
python --version

:: 检查当前目录是否正确
if not exist "src\api_server.py" (
    echo ❌ 错误：请在项目根目录运行此脚本
    echo 当前目录：%CD%
    echo 应该包含 src\api_server.py 文件
    pause
    exit /b 1
)

:: 检查虚拟环境
if exist "analyDesign_env\Scripts\activate.bat" (
    echo ✅ 发现虚拟环境，正在激活...
    call analyDesign_env\Scripts\activate.bat
) else (
    echo ⚠️  未发现虚拟环境，使用系统Python
)

:: 检查必要的依赖
echo.
echo 🔍 检查依赖包...
python -c "import flask, flask_socketio, flask_cors, requests" 2>nul
if errorlevel 1 (
    echo ❌ 缺少必要的依赖包
    echo 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)
echo ✅ 依赖检查完成

:: 创建必要的目录
echo.
echo 📁 创建必要目录...
if not exist "uploads" mkdir uploads
if not exist "templates" mkdir templates
if not exist "outputs" mkdir outputs
if not exist "logs" mkdir logs
echo ✅ 目录创建完成

:: 检查配置文件
echo.
echo 🔧 检查配置文件...
if not exist "src\simple_config.py" (
    echo ⚠️  配置文件不存在: src\simple_config.py
    echo 请检查配置文件
)

:: 检查任务存储模块
if not exist "src\task_storage.py" (
    echo ❌ 任务存储模块不存在: src\task_storage.py
    echo 请确保所有文件完整
    pause
    exit /b 1
)

echo.
echo ========================================
echo    准备启动后端服务
echo ========================================
echo.
echo 📡 API服务器: http://localhost:8080
echo 🔌 WebSocket服务器: ws://localhost:8081/socket.io/
echo.
echo 💡 提示：
echo    - 按 Ctrl+C 可以停止服务
echo    - 服务启动后请不要关闭此窗口
echo    - 如需查看详细日志，请查看控制台输出
echo.

:: 询问启动模式
echo 请选择启动模式：
echo [1] 完整服务 (API + WebSocket) - 推荐
echo [2] 仅API服务器 (端口8080)
echo [3] 仅WebSocket服务器 (端口8081)
echo.
set /p choice="请输入选择 (1-3，默认为1): "

if "%choice%"=="" set choice=1
if "%choice%"=="2" goto start_api_only
if "%choice%"=="3" goto start_websocket_only

:: 默认启动完整服务
echo.
echo 🚀 启动完整服务...
python run.py --mode=full
goto end

:start_api_only
echo.
echo 🚀 启动API服务器...
python run.py --mode=api
goto end

:start_websocket_only
echo.
echo 🚀 启动WebSocket服务器...
python run.py --mode=websocket
goto end

:end
echo.
echo ========================================
echo    服务已停止
echo ========================================
echo.
echo 感谢使用 analyDesign 后端服务！
echo.
pause 